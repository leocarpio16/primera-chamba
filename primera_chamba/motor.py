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
        """[(✓ / ✗ / –, preferencia, detalle)]. ✓ suma BONO; ✗ y – (sin preferencia o sin dato) no suman."""
        v = self.cat.iloc[i]
        out = []
        # Ubicación
        if not p.ubicacion.strip():
            out.append(("–", "Ubicación", "sin preferencia"))
        elif _norm(p.ubicacion) in self._ubic[i]:
            out.append(("✓", "Ubicación", v["location"]))
        else:
            out.append(("✗", "Ubicación", f"la vacante es en {v['location']}"))
        # Modalidad: el catálogo solo marca "remoto permitido"; no hay dato de presencial ni de híbrido.
        if p.modalidad == "Me da igual":
            out.append(("–", "Modalidad", "sin preferencia"))
        elif p.modalidad == "Remoto":
            out.append(("✓", "Modalidad", "permite remoto") if v["remoto"]
                       else ("✗", "Modalidad", "el anuncio no dice que sea remoto"))
        else:
            out.append(("–", "Modalidad", f"el catálogo no indica si es {p.modalidad.lower()}"))
        # Sueldo: el catálogo está en USD al año
        if not p.sueldo_mxn_mensual:
            out.append(("–", "Sueldo", "sin preferencia"))
        elif pd.isna(v["sueldo_anual"]):
            out.append(("–", "Sueldo", "el anuncio no publica sueldo"))
        else:
            mensual = v["sueldo_anual"] * tipo_cambio / 12
            ok = mensual >= p.sueldo_mxn_mensual
            out.append(("✓" if ok else "✗", "Sueldo", f"≈ ${mensual:,.0f} MXN al mes"))
        # Nivel
        if not p.nivel:
            out.append(("–", "Nivel", "sin preferencia"))
        elif pd.isna(v["nivel"]):
            out.append(("–", "Nivel", "el anuncio no indica nivel"))
        elif v["nivel"] == NIVELES[p.nivel][0]:
            out.append(("✓", "Nivel", NIVEL_ES[v["nivel"]]))
        else:
            out.append(("✗", "Nivel", f"pide {NIVEL_ES.get(v['nivel'], v['nivel']).lower()}"))
        return out


def descripciones(job_ids: list[int]) -> dict[int, str]:
    """Lee solo las descripciones pedidas (cargarlas todas costaría ~0.5 GB de RAM)."""
    t = pq.read_table(em.PROCESADO / "vacantes.parquet", columns=["job_id", "description"],
                      filters=[("job_id", "in", [int(j) for j in job_ids])])
    return dict(zip(t["job_id"].to_pylist(), t["description"].to_pylist()))
