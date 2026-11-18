"""Motor de recomendación de la app.

Modelo elegido en el bloque 3 (`notebooks/evaluacion.ipynb`): multilingual-e5-small, con el perfil traducido al inglés
(MarianMT es → en) antes de buscar. Si la traducción falla, se busca con el texto original (e5 es multilingüe).

Puntaje (PRD §5.1) en dos etapas:
1. Se toman las `CANDIDATOS` vacantes más parecidas al perfil (coseno). Así una preferencia cumplida nunca cuela una
   vacante que no tiene que ver con el puesto.
2. puntaje = z + BONO × (preferencias cumplidas), con z = coseno estandarizado contra todo el catálogo para esa
   consulta. Se estandariza porque los cosenos de e5 se amontonan (0.86–0.89 en el top) y un bono absoluto los
   aplastaría. Medido con perfiles de prueba: z ≈ 6.4 en el 1.º lugar y ≈ 3.5 en el 300.º, así que con las cuatro
   preferencias cumplidas (+2.0) una vacante del lugar 300 sube a cerca del top 15.

Vacantes en vivo de México (bloque 5, `en_vivo.py`): se comparan con la misma consulta en inglés y se estandarizan con la
media y la desviación del catálogo, así quedan en la misma escala que las 110,928. Elegido con las 30 vacantes reales del
sondeo (`docs/ESTADO.md`): comparar el perfil en español con vacantes en español las sube para cualquier perfil (con
"Enfermera" quedaban en el lugar ~1,200), mientras que el perfil traducido las separa igual que traducir también las
vacantes (lugar ~250 con "Analista de datos", más allá del 9,000 con perfiles ajenos) sin cargar un segundo traductor.
Como la API ya filtra por puesto, entran al ranking las que tienen coincidencia Media o mejor (`LUGAR_MAX_VIVAS`).
"""
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from primera_chamba import config
from primera_chamba import embeddings as em

CLAVE = "e5"
CANDIDATOS = 300
BONO = 0.5
ALFA, BETA, GAMMA = 1.0, 0.75, 0.15  # Rocchio (PRD §5.2)
LUGAR_MAX_VIVAS = 5000  # coincidencia Media o mejor

# Etiqueta del formulario → (valor del dataset, texto en inglés para la consulta).
NIVELES = {
    "Prácticas / becario": ("Internship", "internship"),
    "Sin experiencia / recién egresado": ("Entry level", "entry level"),
    "Junior (1 a 3 años)": ("Associate", "associate"),
    "Intermedio o senior": ("Mid-Senior level", "mid-senior level"),
    "Director": ("Director", "director"),
    "Ejecutivo": ("Executive", "executive"),
}
NIVEL_ES = {v[0]: k for k, v in NIVELES.items()}
MODALIDADES = ["Me da igual", "Remoto", "Híbrido", "Presencial"]
TIPOS = {"Tiempo completo": "Full-time", "Medio tiempo": "Part-time", "Por contrato": "Contract",
         "Temporal": "Temporary", "Prácticas": "Internship", "Voluntariado": "Volunteer", "Otro": "Other"}
TIPO_ES = {v: k for k, v in TIPOS.items()}
COLUMNAS = ["job_id", "company_name", "title", "location", "estado", "remoto", "tipo_empleo", "nivel",
            "sueldo_anual", "job_posting_url", "listed_time"]


@dataclass
class Perfil:
    puesto: str
    habilidades: list[str]
    nivel: str | None = None              # llave de NIVELES
    ubicacion: str = ""
    modalidad: str = "Me da igual"
    sueldo_mxn_mensual: float | None = None
    tipos_empleo: list[str] = field(default_factory=list)  # llaves de TIPOS; vacío = todos
    # Solo para el CV (bloque 6); no entran al ranking.
    experiencias: str = ""
    educacion: str = ""
    descripcion: str = ""


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())

# Estados de EE. UU.: abreviatura → nombres en inglés y en español (para que el usuario no tenga que saber "TX").
ESTADOS = {
    "AL": ["alabama"], "AK": ["alaska"], "AZ": ["arizona"], "AR": ["arkansas"], "CA": ["california"],
    "CO": ["colorado"], "CT": ["connecticut"], "DE": ["delaware"], "DC": ["district of columbia", "distrito de columbia"],
    "FL": ["florida"], "GA": ["georgia"], "HI": ["hawaii", "hawai"], "ID": ["idaho"], "IL": ["illinois"],
    "IN": ["indiana"], "IA": ["iowa"], "KS": ["kansas"], "KY": ["kentucky"], "LA": ["louisiana", "luisiana"],
    "ME": ["maine"], "MD": ["maryland"], "MA": ["massachusetts"], "MI": ["michigan"], "MN": ["minnesota"],
    "MS": ["mississippi", "misisipi"], "MO": ["missouri", "misuri"], "MT": ["montana"], "NE": ["nebraska"],
    "NV": ["nevada"], "NH": ["new hampshire", "nuevo hampshire"], "NJ": ["new jersey", "nueva jersey"],
    "NM": ["new mexico", "nuevo mexico"], "NY": ["new york", "nueva york"],
    "NC": ["north carolina", "carolina del norte"], "ND": ["north dakota", "dakota del norte"], "OH": ["ohio"],
    "OK": ["oklahoma"], "OR": ["oregon"], "PA": ["pennsylvania", "pensilvania"], "RI": ["rhode island"],
    "SC": ["south carolina", "carolina del sur"], "SD": ["south dakota", "dakota del sur"], "TN": ["tennessee"],
    "TX": ["texas"], "UT": ["utah"], "VT": ["vermont"], "VA": ["virginia"],
    "WA": ["washington"], "WV": ["west virginia", "virginia occidental"], "WI": ["wisconsin"], "WY": ["wyoming"],
}
_NOMBRE_A_ESTADO = {n: c for c, ns in ESTADOS.items() for n in ns} | {c.lower(): c for c in ESTADOS}


def leer_ubicacion(texto: str) -> tuple[list[str], list[str]]:
    """'Austin, Texas' → (['austin'], ['TX']). Cada parte separada por coma es un estado (nombre o abreviatura) o una ciudad."""
    ciudades, estados = [], []
    for parte in (texto or "").split(","):
        parte = _norm(parte)
        if not parte:
            continue
        if parte in _NOMBRE_A_ESTADO:
            estados.append(_NOMBRE_A_ESTADO[parte])
        else:
            ciudades.append(parte)
    return ciudades, estados


def consulta_en(perfil: Perfil) -> tuple[str, bool]:
    """Texto con el formato evaluado: 'puesto. Skills: … . Experience level: … .'. Devuelve (texto, ¿se tradujo?).
    Solo se traduce el texto libre; el nivel sale de la lista fija (MarianMT traducía "nivel de entrada" como "input level")."""
    libres = [perfil.puesto.strip(), ", ".join(h.strip() for h in perfil.habilidades if h.strip())]
    try:
        from primera_chamba.traduccion import traducir
        puesto, habs = traducir([t or "-" for t in libres], "es", "en")
        habs = habs if libres[1] else ""
        traducido = True
    except Exception:
        puesto, habs = libres
        traducido = False
    texto = f"{puesto.rstrip('.')}."
    if habs:
        texto += f" Skills: {habs.rstrip('.')}."
    if perfil.nivel:
        texto += f" Experience level: {NIVELES[perfil.nivel][1]}."
    return texto, traducido


class Motor:
    def __init__(self):
        self.cat = pd.read_parquet(em.PROCESADO / "vacantes.parquet", columns=COLUMNAS)
        self.E = np.asarray(em.cargar_indice(CLAVE), dtype=np.float32)
        self.modelo = em.cargar_modelo(CLAVE)

    def vector(self, texto: str) -> np.ndarray:
        return self.modelo.encode([em.MODELOS[CLAVE][2] + texto], normalize_embeddings=True)[0]

    def preparar_vivas(self, vacantes: list[dict]) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
        """Vacantes en vivo → (tabla con las columnas del catálogo, {id: vector}). Mismo texto que el índice:
        título + 70 palabras de la descripción."""
        if not vacantes:
            return pd.DataFrame(), {}
        df = pd.DataFrame(vacantes).drop_duplicates("id")
        textos = [em.MODELOS[CLAVE][1] + f"{t}. " + " ".join(d.split()[:em.N_PALABRAS])
                  for t, d in zip(df["titulo"], df["descripcion"])]
        V = self.modelo.encode(textos, normalize_embeddings=True)
        tabla = pd.DataFrame({
            "idx": df["id"], "job_id": df["id"], "company_name": df["empresa"], "title": df["titulo"],
            "location": df["ubicacion"], "estado": None, "remoto": df["remoto"],
            "tipo_empleo": df["tipo_texto"].fillna(df["tipos"].map(lambda t: TIPO_ES.get(t[0]) if t else None)),
            "tipos": df["tipos"], "nivel": None, "sueldo_mensual": df["sueldo_mensual"], "job_posting_url": df["url"],
            "publicador": df["publicador"], "publicada": df["publicada"], "descripcion": df["descripcion"],
            "origen": "vivo"}).reset_index(drop=True)
        return tabla, dict(zip(tabla["idx"], V))

    def _vectores(self, ids: list, vivas: dict[str, np.ndarray]) -> np.ndarray:
        """Vectores de vacantes calificadas; se omiten las en vivo que ya no están (p. ej., tras volver a consultar)."""
        V = [vivas[i] if isinstance(i, str) else self.E[i] for i in ids if not isinstance(i, str) or i in vivas]
        return np.stack(V) if V else np.empty((0, self.E.shape[1]), dtype=np.float32)

    def rocchio(self, q0: np.ndarray, gustan: list, no_gustan: list, vivas: dict[str, np.ndarray] | None = None) -> np.ndarray:
        """q' = α·q + β·media(👍) − γ·media(👎), normalizado. Los ids pueden ser del catálogo (int) o en vivo (str)."""
        vivas = vivas or {}
        q = ALFA * q0
        G, N = self._vectores(gustan, vivas), self._vectores(no_gustan, vivas)
        if len(G):
            q = q + BETA * G.mean(axis=0)
        if len(N):
            q = q - GAMMA * N.mean(axis=0)
        return q / np.linalg.norm(q)

    def rankear(self, q: np.ndarray, perfil: Perfil, excluir: list = (), n: int = 20,
                tipo_cambio: float = config.TIPO_CAMBIO_MXN_USD, vivas: pd.DataFrame | None = None,
                vectores_vivas: dict[str, np.ndarray] | None = None, origen: str = "todas") -> pd.DataFrame:
        """Ranking del catálogo y, si se dan, de las vacantes en vivo. `origen`: "todas", "catalogo" o "vivo"."""
        cos = self.E @ q
        media, desv = cos.mean(), cos.std()
        z = (cos - media) / desv
        orden_cos = np.sort(cos)
        tipos = [TIPOS[t] for t in perfil.tipos_empleo]
        partes = []
        if origen != "vivo":
            filtro = np.zeros(len(cos), dtype=bool)
            if tipos:
                filtro |= ~self.cat["tipo_empleo"].isin(tipos).to_numpy()
            filtro[[i for i in excluir if not isinstance(i, str)]] = True
            zc = np.where(filtro, -np.inf, z)
            cand = np.argpartition(-zc, CANDIDATOS)[:CANDIDATOS]
            cand = cand[np.isfinite(zc[cand])]
            sub = self.cat.iloc[cand].copy()
            sub["idx"] = cand
            sub["coseno"] = cos[cand]
            sub["origen"] = "catalogo"
            sub["desglose"] = [self._preferencias(self._fila(i, tipo_cambio), perfil) for i in cand]
            partes.append(sub)
        if origen != "catalogo" and vivas is not None and len(vivas):
            viv = vivas[~vivas["idx"].isin(list(excluir))].copy()
            if tipos:  # sin dato de tipo no se descarta
                viv = viv[viv["tipos"].map(lambda t: not t or any(x in tipos for x in t))]
            viv["coseno"] = [float(vectores_vivas[i] @ q) for i in viv["idx"]]
            partes.append(viv)
        if not partes:
            return pd.DataFrame()
        sub = pd.concat(partes, ignore_index=True)
        if not len(sub):
            return sub
        sub["z"] = (sub["coseno"] - media) / desv
        sub["lugar_similitud"] = len(cos) - np.searchsorted(orden_cos, sub["coseno"].to_numpy(), side="right") + 1
        es_viva = sub["origen"].eq("vivo")
        sub = sub[~es_viva | (sub["lugar_similitud"] <= LUGAR_MAX_VIVAS)].copy()
        es_viva = sub["origen"].eq("vivo")
        sub.loc[es_viva, "desglose"] = pd.Series([self._preferencias(f, perfil) for _, f in sub[es_viva].iterrows()],
                                                 index=sub.index[es_viva], dtype=object)
        sub["cumplidas"] = [sum(e == "✓" for e, _, _ in d) for d in sub["desglose"]]
        sub["puntaje"] = sub["z"] + BONO * sub["cumplidas"]
        return sub.sort_values("puntaje", ascending=False).head(n).reset_index(drop=True)

    def por_lugar(self, q: np.ndarray, perfil: Perfil, lugares: list[int], excluir: list[int] = (),
                  tipo_cambio: float = config.TIPO_CAMBIO_MXN_USD) -> pd.DataFrame:
        """Vacantes que ocupan ciertos lugares por parecido con el perfil (1 = la más parecida), sin preferencias ni
        filtros. Sirve para comparar el ranking con vacantes de coincidencia media y baja."""
        orden = np.argsort(-(self.E @ q))  # orden[k] = vacante en el lugar k + 1 de todo el catálogo
        fuera = set(excluir)
        posiciones = []
        for lugar in lugares:
            k = min(lugar, len(orden)) - 1
            while orden[k] in fuera and k > 0:  # si la vacante de ese lugar está descartada, la anterior
                k -= 1
            posiciones.append(k)
        idxs = orden[posiciones]
        sub = self.cat.iloc[idxs].copy()
        sub["idx"] = idxs
        sub["lugar_similitud"] = [k + 1 for k in posiciones]
        sub["desglose"] = [self._preferencias(self._fila(i, tipo_cambio), perfil) for i in idxs]
        return sub.reset_index(drop=True)

    def _fila(self, i: int, tipo_cambio: float) -> dict:
        """Vacante del catálogo con el sueldo en pesos al mes (el catálogo está en USD al año)."""
        v = self.cat.iloc[i].to_dict()
        v["sueldo_mensual"] = v["sueldo_anual"] * tipo_cambio / 12 if pd.notna(v["sueldo_anual"]) else None
        return v

    def _preferencias(self, v, p: Perfil) -> list[tuple[str, str, str]]:
        """[(✓ / ✗ / –, preferencia, explicación en lenguaje común)]. ✓ suma BONO; ✗ y – no suman.
        `v` es una vacante del catálogo (`_fila`) o en vivo (fila de `preparar_vivas`)."""
        out = []
        # Ubicación: ciudad (texto dentro de la ubicación) y/o estado (abreviatura); si se dan ambos, deben cumplirse ambos.
        ciudades, estados = leer_ubicacion(p.ubicacion)
        if not ciudades and not estados:
            out.append(("–", "Ubicación", "No indicaste dónde quieres trabajar."))
        else:
            ubic = _norm(v["location"])
            ok_ciudad = not ciudades or any(c in ubic for c in ciudades)
            ok_estado = not estados or v["estado"] in estados
            if ok_ciudad and ok_estado:
                out.append(("✓", "Ubicación", f"Está en {v['location']}, donde quieres trabajar."))
            else:
                out.append(("✗", "Ubicación", f"Está en {v['location']}; tú buscas en {p.ubicacion.strip()}."))
        # Modalidad: el catálogo solo marca "remoto permitido"; no hay dato de presencial ni de híbrido.
        if p.modalidad == "Me da igual":
            out.append(("–", "Modalidad", "No indicaste una modalidad."))
        elif p.modalidad == "Remoto":
            if v["remoto"] is None or (isinstance(v["remoto"], float) and pd.isna(v["remoto"])):
                out.append(("–", "Modalidad", "El anuncio no dice si se puede trabajar desde casa."))
            else:
                out.append(("✓", "Modalidad", "Se puede trabajar desde casa.") if v["remoto"]
                           else ("✗", "Modalidad", "El anuncio no dice que se pueda trabajar desde casa."))
        else:
            out.append(("–", "Modalidad", f"El anuncio no dice si es {p.modalidad.lower()}."))
        # Sueldo, en pesos al mes
        mensual = v["sueldo_mensual"]
        if not p.sueldo_mxn_mensual:
            out.append(("–", "Sueldo", "No indicaste un sueldo."))
        elif mensual is None or pd.isna(mensual):
            out.append(("–", "Sueldo", "El anuncio no publica el sueldo."))
        else:
            if mensual >= p.sueldo_mxn_mensual:
                out.append(("✓", "Sueldo", f"Paga alrededor de ${mensual:,.0f} al mes, más de lo que pides "
                                           f"(${p.sueldo_mxn_mensual:,.0f})."))
            else:
                out.append(("✗", "Sueldo", f"Paga alrededor de ${mensual:,.0f} al mes, menos de lo que pides "
                                           f"(${p.sueldo_mxn_mensual:,.0f})."))
        # Nivel
        if not p.nivel:
            out.append(("–", "Experiencia", "No indicaste tu nivel de experiencia."))
        elif v["nivel"] is None or pd.isna(v["nivel"]):
            out.append(("–", "Experiencia", "El anuncio no dice cuánta experiencia pide."))
        elif v["nivel"] == NIVELES[p.nivel][0]:
            out.append(("✓", "Experiencia", f"Busca a alguien con tu nivel: {NIVEL_ES[v['nivel']].lower()}."))
        else:
            out.append(("✗", "Experiencia", f"Pide otro nivel: {NIVEL_ES.get(v['nivel'], v['nivel']).lower()} "
                                            f"(tú: {p.nivel.lower()})."))
        return out


def coincidencia(lugar: int) -> tuple[str, int]:
    """Etiqueta para todo público a partir del lugar por parecido entre las 110,928 vacantes (1 = la más parecida).
    Devuelve (etiqueta, nivel de 1 a 4)."""
    if lugar <= 50:
        return "Muy alta", 4
    if lugar <= 500:
        return "Alta", 3
    if lugar <= 5000:
        return "Media", 2
    return "Baja", 1

def descripciones(job_ids: list[int]) -> dict[int, str]:
    """Lee solo las descripciones pedidas (cargarlas todas costaría ~0.5 GB de RAM)."""
    t = pq.read_table(em.PROCESADO / "vacantes.parquet", columns=["job_id", "description"],
                      filters=[("job_id", "in", [int(j) for j in job_ids])])
    return dict(zip(t["job_id"].to_pylist(), t["description"].to_pylist()))
