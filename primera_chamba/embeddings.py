"""Índices del catálogo: TF-IDF y embeddings densos de las vacantes de `vacantes.parquet`.

Uso: `python3 -m primera_chamba.embeddings [tfidf] [minilm] [e5]` (sin argumentos construye todo).

Texto que se representa (decisión del bloque 2, medida con 2,000 vacantes): título + primeras 70 palabras de la
descripción. Ambos modelos usan el tokenizador de XLM-R (1.56 tokens por palabra); así el 97 % cabe en 128 tokens.
Los dos modelos densos reciben la misma entrada para que la comparación mida el modelo y no el largo del texto.
e5 con 512 tokens tardaría ~84 min y usaría 5.6 GB de `mps` → descartado. TF-IDF se construye además con la
descripción completa (`tfidf_completo`) para medir cuánto se pierde al recortar.

Las filas de cada índice siguen el orden del parquet; `indice_job_ids.npy` guarda ese orden para verificarlo.
"""
import json
import pickle
import sys
import time

import numpy as np
import pandas as pd

from primera_chamba import config

PROCESADO = config.DATOS / "procesado"
N_PALABRAS = 70
MAX_TOKENS = 128

# clave → (modelo de Hugging Face, prefijo de vacante, prefijo de consulta). e5 exige los prefijos.
MODELOS = {
    "minilm": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "", ""),
    "e5": ("intfloat/multilingual-e5-small", "passage: ", "query: "),
}


def texto_vacante(titulo: pd.Series, descripcion: pd.Series, n_palabras: int | None = N_PALABRAS) -> pd.Series:
    """Título + primeras `n_palabras` de la descripción (None = descripción completa)."""
    desc = descripcion if n_palabras is None else descripcion.str.split().str[:n_palabras].str.join(" ")
    return titulo + ". " + desc


def _rss_gb() -> float:
    import psutil
    return psutil.Process().memory_info().rss / 1e9


def _guardar_meta(clave: str, info: dict) -> None:
    ruta = PROCESADO / "embeddings_meta.json"
    meta = json.loads(ruta.read_text()) if ruta.exists() else {}
    meta[clave] = info
    ruta.write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def construir_tfidf(df: pd.DataFrame, completo: bool) -> None:
    from scipy import sparse
    from sklearn.feature_extraction.text import TfidfVectorizer

    clave = "tfidf_completo" if completo else "tfidf"
    t0 = time.time()
    textos = texto_vacante(df["title"], df["description"], None if completo else N_PALABRAS)
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=3, max_df=0.5,
                          max_features=200_000, sublinear_tf=True, dtype=np.float32)
    X = vec.fit_transform(textos)
    sparse.save_npz(PROCESADO / f"indice_{clave}.npz", X)
    with open(PROCESADO / f"vectorizador_{clave}.pkl", "wb") as f:
        pickle.dump(vec, f)
    info = {"segundos": round(time.time() - t0, 1), "rss_gb": round(_rss_gb(), 2), "forma": list(X.shape),
            "no_ceros": int(X.nnz), "texto": "descripción completa" if completo else f"título + {N_PALABRAS} palabras"}
    _guardar_meta(clave, info)
    print(f"{clave}: {info}")


def cargar_modelo(clave: str):
    import torch
    from sentence_transformers import SentenceTransformer

    disp = "mps" if torch.backends.mps.is_available() else "cpu"
    modelo = SentenceTransformer(MODELOS[clave][0], device=disp)
    modelo.max_seq_length = MAX_TOKENS
    return modelo


def construir_denso(df: pd.DataFrame, clave: str, bloque: int = 4096) -> None:
    import torch

    nombre, prefijo, _ = MODELOS[clave]
    t0 = time.time()
    modelo = cargar_modelo(clave)
    t_carga = time.time() - t0
    textos = (prefijo + texto_vacante(df["title"], df["description"])).tolist()
    n = len(textos)
    salida = np.lib.format.open_memmap(PROCESADO / f"indice_{clave}.npy", mode="w+", dtype=np.float16,
                                       shape=(n, modelo.get_sentence_embedding_dimension()))
    usa_mps = modelo.device.type == "mps"
    pico_mps = 0.0
    t1 = time.time()
    for i in range(0, n, bloque):
        E = modelo.encode(textos[i:i + bloque], batch_size=64, normalize_embeddings=True, convert_to_numpy=True)
        salida[i:i + len(E)] = E.astype(np.float16)
        if usa_mps:
            pico_mps = max(pico_mps, torch.mps.driver_allocated_memory() / 1e9)
        hechas = i + len(E)
        ritmo = hechas / (time.time() - t1)
        print(f"  {clave}: {hechas:,}/{n:,} ({hechas / n:.0%}) · {ritmo:.0f} vac/s · faltan "
              f"{(n - hechas) / ritmo / 60:.1f} min · RSS {_rss_gb():.2f} GB", flush=True)
    salida.flush()
    info = {"modelo": nombre, "dispositivo": str(modelo.device), "segundos_carga": round(t_carga, 1),
            "segundos_codificar": round(time.time() - t1, 1), "vac_por_s": round(n / (time.time() - t1), 1),
            "rss_gb": round(_rss_gb(), 2), "pico_mps_gb": round(pico_mps, 2) if usa_mps else None,
            "forma": list(salida.shape), "dtype": "float16", "max_tokens": MAX_TOKENS,
            "texto": f"{prefijo}título + {N_PALABRAS} palabras"}
    _guardar_meta(clave, info)
    print(f"{clave}: {info}")


def cargar_indice(clave: str):
    """Matriz de vacantes: dispersa (TF-IDF) o densa float16 con filas normalizadas."""
    if clave.startswith("tfidf"):
        from scipy import sparse
        return sparse.load_npz(PROCESADO / f"indice_{clave}.npz")
    return np.load(PROCESADO / f"indice_{clave}.npy", mmap_mode="r")


def main(claves: list[str]) -> None:
    df = pd.read_parquet(PROCESADO / "vacantes.parquet", columns=["job_id", "title", "description"])
    np.save(PROCESADO / "indice_job_ids.npy", df["job_id"].to_numpy())
    print(f"{len(df):,} vacantes · RSS {_rss_gb():.2f} GB", flush=True)
    for clave in claves:
        if clave == "tfidf":
            construir_tfidf(df, completo=False)
            construir_tfidf(df, completo=True)
        else:
            construir_denso(df, clave)


if __name__ == "__main__":
    main(sys.argv[1:] or ["tfidf", "minilm", "e5"])
