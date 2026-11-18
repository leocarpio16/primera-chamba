"""Evaluación fuera de línea del motor (PRD §7). La usa `notebooks/evaluacion.ipynb`.

Cada consulta es una vacante del catálogo convertida en un perfil sintético (puesto + categorías de habilidad + nivel).
La relevancia sale de campos estructurados que el modelo no ve como etiqueta:
- Etiqueta "con título": 2 = mismo `titulo_norm`; 1 = comparte categoría de habilidad e industria; 0 = el resto.
- Etiqueta "solo estructural": 1 = comparte categoría de habilidad e industria; 0 = el resto (no usa el título).
Del ranking de cada consulta se excluye todo su `grupo_plantilla` (la propia vacante y sus copias exactas): una copia
de la misma descripción sería un acierto regalado.
"""
import pickle

import numpy as np
import pandas as pd
from scipy import sparse

from primera_chamba import config
from primera_chamba import embeddings as em
from primera_chamba.traduccion import traducir  # noqa: F401 (lo usa el notebook como ev.traducir)

K = 10
# Títulos de una palabra que no definen un puesto ("manager" de qué). No se usan como consulta.
GENERICOS = {
    "manager", "director", "associate", "analyst", "engineer", "supervisor", "vp", "travel", "intern", "scientist",
    "specialist", "technician", "coordinator", "consultant", "designer", "developer", "operator", "executive",
    "administrator", "assistant", "representative", "lead", "officer", "president", "partner", "owner", "agent",
    "advisor", "clerk", "worker", "staff", "team member", "contract", "remote", "other", "general manager",
}
NIVEL_EN = {"Entry level": "entry level", "Associate": "associate", "Mid-Senior level": "mid-senior level",
            "Director": "director", "Executive": "executive", "Internship": "internship"}


def cargar_catalogo() -> pd.DataFrame:
    cols = ["job_id", "title", "titulo_norm", "skills", "industrias", "nivel", "grupo_plantilla", "vistas"]
    df = pd.read_parquet(em.PROCESADO / "vacantes.parquet", columns=cols)
    assert (df["job_id"].to_numpy() == np.load(em.PROCESADO / "indice_job_ids.npy", allow_pickle=True)).all()
    df["vistas"] = df["vistas"].fillna(0)
    return df


def nombres_habilidades() -> dict[str, str]:
    import kagglehub
    raiz = kagglehub.dataset_download(config.DATASET_KAGGLE)
    m = pd.read_csv(f"{raiz}/mappings/skills.csv")
    return dict(zip(m["skill_abr"], m["skill_name"]))


def multihot(listas: pd.Series) -> tuple[sparse.csc_matrix, dict]:
    """Matriz vacantes × etiquetas (CSC, para sacar columnas rápido) y el diccionario etiqueta → columna."""
    vocab = {e: i for i, e in enumerate(sorted({x for l in listas for x in l}))}
    filas = np.repeat(np.arange(len(listas)), listas.str.len())
    cols = [vocab[x] for l in listas for x in l]
    M = sparse.csr_matrix((np.ones(len(cols), dtype=np.int8), (filas, cols)), shape=(len(listas), len(vocab)))
    return M.tocsc(), vocab


class Etiquetas:
    """Calcula la relevancia de todo el catálogo para una consulta."""

    def __init__(self, df: pd.DataFrame):
        self.titulo = df["titulo_norm"].to_numpy()
        self.grupo = df["grupo_plantilla"].to_numpy()
        self.S, self.vs = multihot(df["skills"])
        self.I, self.vi = multihot(df["industrias"])

    def _comparte(self, M, vocab, valores) -> np.ndarray:
        cols = [vocab[v] for v in valores if v in vocab]
        return np.asarray(M[:, cols].sum(axis=1)).ravel() > 0

    def de(self, fila: pd.Series) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(etiqueta con título 0/1/2, etiqueta solo estructural 0/1, máscara de excluidas)."""
        estructural = (self._comparte(self.S, self.vs, fila["skills"])
                       & self._comparte(self.I, self.vi, fila["industrias"]))
        con_titulo = np.where(self.titulo == fila["titulo_norm"], 2, estructural.astype(np.int8))
        return con_titulo.astype(np.int8), estructural.astype(np.int8), self.grupo == fila["grupo_plantilla"]


def elegir_consultas(df: pd.DataFrame, n: int = 1000, max_por_titulo: int = 3, semilla: int = 0) -> pd.DataFrame:
    """Vacantes que sirven de consulta: título no genérico con ≥5 relevantes fuera de su grupo, con habilidades e
    industria. Como mucho `max_por_titulo` por título para que los puestos frecuentes no dominen."""
    grupos_por_titulo = df.groupby("titulo_norm")["grupo_plantilla"].nunique()
    ok = (~df["titulo_norm"].isin(GENERICOS)
          & (df["titulo_norm"].map(grupos_por_titulo) >= 6)
          & (df["skills"].str.len() > 0) & (df["industrias"].str.len() > 0))
    cand = df[ok].sample(frac=1, random_state=semilla)
    cand = cand.groupby("titulo_norm", sort=False).head(max_por_titulo)
    return cand.head(n)


def perfil(fila: pd.Series, habilidades: dict[str, str]) -> str:
    """Lo que escribiría alguien que busca ese puesto: puesto, habilidades y nivel (si se conoce)."""
    txt = f"{fila['titulo_norm']}. Skills: {', '.join(habilidades[s] for s in fila['skills'])}."
    if isinstance(fila["nivel"], str):
        txt += f" Experience level: {NIVEL_EN[fila['nivel']]}."
    return txt


# ---------- rankings ----------

def _top(puntajes: np.ndarray, excluidas: np.ndarray, k: int = K) -> np.ndarray:
    p = puntajes.astype(np.float32, copy=True)
    p[excluidas] = -np.inf
    idx = np.argpartition(-p, k)[:k]
    return idx[np.argsort(-p[idx])]


class Ranker:
    """Puntúa el catálogo para una lista de perfiles con uno de los índices de `embeddings`."""

    def __init__(self, clave: str):
        self.clave = clave
        if clave.startswith("tfidf"):
            self.X = em.cargar_indice(clave).tocsr()
            with open(em.PROCESADO / f"vectorizador_{clave}.pkl", "rb") as f:
                self.vec = pickle.load(f)
        else:
            self.X = np.asarray(em.cargar_indice(clave), dtype=np.float32)
            self.modelo = em.cargar_modelo(clave)

    def puntajes(self, perfiles: list[str]) -> np.ndarray:
        """Matriz consultas × vacantes (float32)."""
        if self.clave.startswith("tfidf"):
            Q = self.vec.transform(perfiles)
            return np.asarray((self.X @ Q.T).T.todense(), dtype=np.float32)
        pref = em.MODELOS[self.clave][2]
        Q = self.modelo.encode([pref + p for p in perfiles], batch_size=64, normalize_embeddings=True)
        return Q @ self.X.T


# ---------- métricas ----------

def ndcg(rel_top: np.ndarray, rel_todas: np.ndarray, k: int = K) -> float:
    desc = 1 / np.log2(np.arange(2, k + 2))
    dcg = ((2.0 ** rel_top - 1) * desc[:len(rel_top)]).sum()
    ideal = np.sort(rel_todas)[::-1][:k]
    idcg = ((2.0 ** ideal - 1) * desc[:len(ideal)]).sum()
    return float(dcg / idcg) if idcg > 0 else np.nan


def recall_acotado(rel_top: np.ndarray, rel_todas: np.ndarray, nivel: int, k: int = K) -> float:
    """Aciertos del nivel máximo en el top-k entre min(k, total de relevantes): 1.0 = top-k perfecto."""
    total = int((rel_todas >= nivel).sum())
    return float((rel_top >= nivel).sum() / min(k, total)) if total else np.nan


def evaluar(tops: dict[str, np.ndarray], consultas: pd.DataFrame, etiquetas: Etiquetas) -> pd.DataFrame:
    """Una fila por (consulta, método) con nDCG@10 y Recall@10 en las dos versiones de etiqueta."""
    filas = []
    for q, (_, fila) in enumerate(consultas.iterrows()):
        rel_t, rel_e, excl = etiquetas.de(fila)
        ideal_t, ideal_e = rel_t[~excl], rel_e[~excl]  # el ideal se calcula sin las excluidas
        for metodo, top in tops.items():
            t = top[q]  # los tops ya no contienen excluidas
            filas.append({"consulta": q, "metodo": metodo,
                          "ndcg_titulo": ndcg(rel_t[t], ideal_t), "recall_titulo": recall_acotado(rel_t[t], ideal_t, 2),
                          "ndcg_estructural": ndcg(rel_e[t], ideal_e),
                          "recall_estructural": recall_acotado(rel_e[t], ideal_e, 1)})
    return pd.DataFrame(filas)


def bootstrap(res: pd.DataFrame, metrica: str, n: int = 2000, semilla: int = 0) -> pd.DataFrame:
    """Media e intervalo al 95 % por método, remuestreando consultas (las mismas para todos los métodos)."""
    piv = res.pivot(index="consulta", columns="metodo", values=metrica)
    rng = np.random.default_rng(semilla)
    muestras = rng.integers(0, len(piv), size=(n, len(piv)))
    medias = np.stack([np.nanmean(piv.to_numpy()[m], axis=0) for m in muestras])
    return pd.DataFrame({"media": piv.mean(), "ic_inf": np.percentile(medias, 2.5, axis=0),
                         "ic_sup": np.percentile(medias, 97.5, axis=0)}, index=piv.columns)


def diferencia_pareada(res: pd.DataFrame, metrica: str, a: str, b: str, n: int = 2000, semilla: int = 0):
    """Media de (a − b) por consulta, con intervalo al 95 % por bootstrap y fracción de remuestreos con a > b."""
    piv = res.pivot(index="consulta", columns="metodo", values=metrica)
    d = (piv[a] - piv[b]).dropna().to_numpy()
    rng = np.random.default_rng(semilla)
    medias = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    return d.mean(), np.percentile(medias, 2.5), np.percentile(medias, 97.5), (medias > 0).mean()


def tops_modelo(ranker: Ranker, perfiles: list[str], consultas: pd.DataFrame, grupo: np.ndarray,
                lote: int = 100) -> np.ndarray:
    """Top-k de cada consulta (consultas × k índices del catálogo), sin su grupo de plantilla."""
    g = consultas["grupo_plantilla"].to_numpy()
    tops = []
    for i in range(0, len(perfiles), lote):
        P = ranker.puntajes(perfiles[i:i + lote])
        tops += [_top(P[j], grupo == g[i + j]) for j in range(len(P))]
    return np.array(tops)


def tops_aleatorio(consultas: pd.DataFrame, grupo: np.ndarray, semilla: int = 0) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    return np.array([_top(rng.random(len(grupo)), grupo == g) for g in consultas["grupo_plantilla"]])


def tops_popularidad(consultas: pd.DataFrame, grupo: np.ndarray, vistas: np.ndarray) -> np.ndarray:
    """Las vacantes más vistas del catálogo, iguales para todos (salvo las excluidas)."""
    return np.array([_top(vistas, grupo == g) for g in consultas["grupo_plantilla"]])

