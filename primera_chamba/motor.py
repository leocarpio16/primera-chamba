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
        self._ubic = self.cat["location"].map(_norm).to_numpy()

    def vector(self, texto: str) -> np.ndarray:
        return self.modelo.encode([em.MODELOS[CLAVE][2] + texto], normalize_embeddings=True)[0]

    def rocchio(self, q0: np.ndarray, gustan: list[int], no_gustan: list[int]) -> np.ndarray:
        """q' = α·q + β·media(👍) − γ·media(👎), normalizado."""
        q = ALFA * q0
        if gustan:
            q = q + BETA * self.E[gustan].mean(axis=0)
        if no_gustan:
            q = q - GAMMA * self.E[no_gustan].mean(axis=0)
        return q / np.linalg.norm(q)

    def rankear(self, q: np.ndarray, perfil: Perfil, excluir: list[int] = (), n: int = 20,
                tipo_cambio: float = config.TIPO_CAMBIO_MXN_USD) -> pd.DataFrame:
        cos = self.E @ q
        z = (cos - cos.mean()) / cos.std()
        orden_cos = np.sort(cos)
        filtro = np.zeros(len(cos), dtype=bool)
        if perfil.tipos_empleo:
            filtro |= ~self.cat["tipo_empleo"].isin([TIPOS[t] for t in perfil.tipos_empleo]).to_numpy()
        filtro[list(excluir)] = True
        zc = np.where(filtro, -np.inf, z)
        cand = np.argpartition(-zc, CANDIDATOS)[:CANDIDATOS]
        cand = cand[np.isfinite(zc[cand])]

        sub = self.cat.iloc[cand].copy()
        sub["idx"] = cand
        sub["coseno"] = cos[cand]
        sub["z"] = z[cand]
        sub["lugar_similitud"] = len(cos) - np.searchsorted(orden_cos, cos[cand], side="right") + 1  # 1 = la más parecida
        sub["desglose"] = [self._preferencias(i, perfil, tipo_cambio) for i in cand]
        sub["cumplidas"] = [sum(e == "✓" for e, _, _ in d) for d in sub["desglose"]]
        sub["puntaje"] = sub["z"] + BONO * sub["cumplidas"]
        return sub.sort_values("puntaje", ascending=False).head(n).reset_index(drop=True)

    def _preferencias(self, i: int, p: Perfil, tipo_cambio: float) -> list[tuple[str, str, str]]:
        """[(✓ / ✗ / –, preferencia, explicación en lenguaje común)]. ✓ suma BONO; ✗ y – no suman."""
        v = self.cat.iloc[i]
        out = []
        # Ubicación: ciudad (texto dentro de la ubicación) y/o estado (abreviatura); si se dan ambos, deben cumplirse ambos.
        ciudades, estados = leer_ubicacion(p.ubicacion)
        if not ciudades and not estados:
            out.append(("–", "Ubicación", "No indicaste dónde quieres trabajar."))
        else:
            ok_ciudad = not ciudades or any(c in self._ubic[i] for c in ciudades)
            ok_estado = not estados or v["estado"] in estados
            if ok_ciudad and ok_estado:
                out.append(("✓", "Ubicación", f"Está en {v['location']}, donde quieres trabajar."))
            else:
                out.append(("✗", "Ubicación", f"Está en {v['location']}; tú buscas en {p.ubicacion.strip()}."))
        # Modalidad: el catálogo solo marca "remoto permitido"; no hay dato de presencial ni de híbrido.
        if p.modalidad == "Me da igual":
            out.append(("–", "Modalidad", "No indicaste una modalidad."))
        elif p.modalidad == "Remoto":
            out.append(("✓", "Modalidad", "Se puede trabajar desde casa.") if v["remoto"]
                       else ("✗", "Modalidad", "El anuncio no dice que se pueda trabajar desde casa."))
        else:
            out.append(("–", "Modalidad", f"El anuncio no dice si es {p.modalidad.lower()}."))
        # Sueldo: el catálogo está en USD al año
        if not p.sueldo_mxn_mensual:
            out.append(("–", "Sueldo", "No indicaste un sueldo."))
        elif pd.isna(v["sueldo_anual"]):
            out.append(("–", "Sueldo", "El anuncio no publica el sueldo."))
        else:
            mensual = v["sueldo_anual"] * tipo_cambio / 12
            if mensual >= p.sueldo_mxn_mensual:
                out.append(("✓", "Sueldo", f"Paga alrededor de ${mensual:,.0f} al mes, más de lo que pides "
                                           f"(${p.sueldo_mxn_mensual:,.0f})."))
            else:
                out.append(("✗", "Sueldo", f"Paga alrededor de ${mensual:,.0f} al mes, menos de lo que pides "
                                           f"(${p.sueldo_mxn_mensual:,.0f})."))
        # Nivel
        if not p.nivel:
            out.append(("–", "Experiencia", "No indicaste tu nivel de experiencia."))
        elif pd.isna(v["nivel"]):
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
