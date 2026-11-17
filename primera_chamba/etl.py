"""ETL del dataset de LinkedIn (Kaggle): CSV crudo → `datos/procesado/vacantes.parquet`.

Se ejecuta una sola vez: `python3 -m primera_chamba.etl`. Leer el CSV completo cuesta ~2 GB de RAM; el parquet
resultante es lo que usan los bloques siguientes.
"""
import json
import re
import time
from pathlib import Path

import pandas as pd

from primera_chamba import config

COLUMNAS = [
    "job_id", "company_name", "title", "description", "location", "formatted_work_type",
    "formatted_experience_level", "remote_allowed", "normalized_salary", "pay_period", "currency",
    "views", "applies", "job_posting_url", "listed_time",
]

# Palabras de nivel que no cambian el puesto ("Senior Data Analyst" y "Data Analyst II" son el mismo puesto).
_NIVEL = r"\b(senior|sr|junior|jr|entry level|i{1,3}|iv|[1-4])\b"
# Jornada o modalidad pegada al título ("RN Home Health Full Time").
_JORNADA = r"\b(full time|part time|fulltime|parttime|per diem|prn|remote|hybrid|onsite|on site|temporary)\b"


def ruta_crudo() -> Path:
    import kagglehub
    return Path(kagglehub.dataset_download(config.DATASET_KAGGLE))


def normalizar_titulo(t: str) -> str:
    """Título comparable entre vacantes: minúsculas, sin paréntesis, sin sufijos tras ' - ' / '|' / ',' y sin nivel."""
    original = t
    t = t.lower()
    t = re.sub(r"[\(\[].*?[\)\]]", " ", t)
    t = re.split(r"\s[-–|/]\s|,|\|", t)[0]
    t = re.sub(r"[^a-z0-9&+# ]", " ", t)
    t = re.sub(_NIVEL, " ", t)
    t = re.sub(_JORNADA, " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t or original.lower().strip()


def estado_de(loc: str) -> str | None:
    """'Chicago, IL' → 'IL'. Ubicaciones sin estado ('United States') → None."""
    m = re.search(r",\s*([A-Z]{2})\b", loc or "")
    return m.group(1) if m else None


def construir(raiz: Path) -> tuple[pd.DataFrame, dict]:
    t0 = time.time()
    df = pd.read_csv(raiz / "postings.csv", usecols=COLUMNAS)  # engine="pyarrow" falla: hay saltos de línea en celdas
    est = {"filas_crudas": len(df)}

    df["description"] = df["description"].fillna("").str.strip()
    df["title"] = df["title"].fillna("").str.strip()

    # Duplicados: misma empresa, título y descripción = el mismo anuncio publicado varias veces.
    dup = df.duplicated(["company_name", "title", "description"])
    est["duplicados_exactos"] = int(dup.sum())
    df = df[~dup]
    vacia = df["description"].str.split().str.len().fillna(0) < 20
    est["descripcion_menor_20_palabras"] = int(vacia.sum())
    df = df[~vacia].copy()

    skills = pd.read_csv(raiz / "jobs/job_skills.csv")
    nombres_sk = pd.read_csv(raiz / "mappings/skills.csv").set_index("skill_abr")["skill_name"]
    ind = pd.read_csv(raiz / "jobs/job_industries.csv")
    nombres_ind = pd.read_csv(raiz / "mappings/industries.csv").set_index("industry_id")["industry_name"]
    est["job_skills_ids_fuera_de_postings"] = int((~skills.job_id.isin(df.job_id)).sum())

    df = df.merge(skills.groupby("job_id")["skill_abr"].agg(sorted).rename("skills"), on="job_id", how="left")
    ind["industria"] = ind["industry_id"].map(nombres_ind)
    df = df.merge(ind.groupby("job_id")["industria"].agg(lambda s: sorted(s.dropna())).rename("industrias"),
                  on="job_id", how="left")
    for c in ("skills", "industrias"):
        df[c] = df[c].apply(lambda v: v if isinstance(v, list) else [])

    df["titulo_norm"] = df["title"].map(normalizar_titulo)
    df["estado"] = df["location"].map(estado_de)
    df["remoto"] = df["remote_allowed"].eq(1)
    df["palabras"] = df["description"].str.split().str.len().astype("int32")
    # Grupo de plantilla: vacantes con la descripción idéntica (otra ciudad u otro título). En la evaluación una
    # vacante no puede contar como acierto para otra de su mismo grupo, porque sería encontrar el mismo texto.
    df["grupo_plantilla"] = df.groupby("description", sort=False).ngroup().astype("int32")
    # normalized_salary ya está anualizado (mediana por hora ≈ 25.75 USD × 2,080 h), pero trae valores imposibles
    # (118 USD/año, quincenales de 1.5 M). Fuera de [10 mil, 1 M] USD o en otra moneda → nulo.
    valido = df["normalized_salary"].between(10_000, 1_000_000) & df["currency"].eq("USD")
    est["sueldos_invalidados"] = int((df["normalized_salary"].notna() & ~valido).sum())
    df["normalized_salary"] = df["normalized_salary"].where(valido)
    df = df.drop(columns=["remote_allowed"]).rename(columns={
        "formatted_work_type": "tipo_empleo", "formatted_experience_level": "nivel",
        "normalized_salary": "sueldo_anual", "views": "vistas", "applies": "postulaciones"})

    est.update({
        "filas_finales": len(df),
        "con_skills_pct": round(df["skills"].str.len().gt(0).mean() * 100, 1),
        "con_industria_pct": round(df["industrias"].str.len().gt(0).mean() * 100, 1),
        "titulos_distintos": int(df["title"].nunique()),
        "titulos_norm_distintos": int(df["titulo_norm"].nunique()),
        "vacantes_con_titulo_norm_compartido_pct":
            round(df["titulo_norm"].map(df["titulo_norm"].value_counts()).gt(1).mean() * 100, 1),
        "con_estado_pct": round(df["estado"].notna().mean() * 100, 1),
        "con_sueldo_pct": round(df["sueldo_anual"].notna().mean() * 100, 1),
        "vacantes_en_plantilla_compartida": int(df["grupo_plantilla"].duplicated(keep=False).sum()),
        "segundos": round(time.time() - t0, 1),
    })
    nombres = {"skills_nombres": nombres_sk.to_dict()}
    return df.reset_index(drop=True), est | nombres


def main():
    salida = config.DATOS / "procesado"
    salida.mkdir(parents=True, exist_ok=True)
    df, est = construir(ruta_crudo())
    df.to_parquet(salida / "vacantes.parquet", index=False)
    (salida / "etl_estadisticas.json").write_text(json.dumps(est, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in est.items() if k != "skills_nombres"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
