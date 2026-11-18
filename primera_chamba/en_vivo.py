"""Vacantes en vivo de México (bloque 5): JSearch como fuente principal y Adzuna como respaldo, con caché en disco.

Formato de las respuestas verificado con el sondeo real del 2026-11-17 (`cache/sondeo/`):
- JSearch `GET /search-v2` (`query`, `country="mx"`, `language="es"`) → `data.jobs`, 10 vacantes por llamada, descripción
  completa. `job_city`/`job_country` a veces vienen nulos, así que la ubicación sale de `job_location`
  ("Ciudad de México, CDMX     •  a través de LinkedIn"). La cuota restante llega en `X-RateLimit-Requests-Remaining`.
- Adzuna `GET /v1/api/jobs/mx/search/1` (`what`, `where`) → `results`, descripción recortada (~500 caracteres); a veces
  trae `salary_min`/`salary_max` (anual, en pesos: 115,200–300,000 para "analista de datos").

Política de caché (cada consulta gasta cuota: JSearch 200 al mes, Adzuna 25):
1. Si la misma consulta se hizo hace menos de `VIGENCIA_H` horas, se usa la caché sin llamar a ninguna API.
2. Si no, JSearch; si falla o no trae nada, Adzuna.
3. Si las dos fallan, lo último guardado para esa consulta, marcado como tal (`vencida=True`).
"""
import hashlib
import json
import os
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime

import requests

from primera_chamba import config

DIR = config.CACHE / "en_vivo"
VIGENCIA_H = 24
ESPERA_S = 12
JSEARCH_URL = "https://jsearch.p.rapidapi.com/search-v2"
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/mx/search/1"
SIN_RED = os.getenv("PC_SIN_RED") == "1"  # pruebas: nunca llamar a las APIs (no gastar cuota)

# Tipos de empleo de cada API → valores del catálogo (`motor.TIPOS`).
TIPOS_JSEARCH = {"FULLTIME": "Full-time", "PARTTIME": "Part-time", "CONTRACTOR": "Contract", "INTERN": "Internship",
                 "TEMPORARY": "Temporary"}
TIPOS_ADZUNA = {"full_time": "Full-time", "part_time": "Part-time", "contract": "Contract"}


@dataclass
class Resultado:
    vacantes: list[dict] = field(default_factory=list)
    fuente: str = ""            # "JSearch" o "Adzuna"
    consultada: str = ""        # fecha ISO en que la API respondió
    desde_cache: bool = False   # True = no se llamó a ninguna API en esta búsqueda
    vencida: bool = False       # True = las APIs fallaron y se muestra lo último guardado
    errores: list[str] = field(default_factory=list)
    llamadas: int = 0           # llamadas gastadas en esta búsqueda


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def consulta(puesto: str, ubicacion: str = "") -> tuple[str, str]:
    """(texto para JSearch, lugar para Adzuna): ('Analista de datos en CDMX', 'CDMX'). Una ubicación de EE. UU. no se
    manda (la búsqueda en vivo es en México)."""
    from primera_chamba.motor import leer_ubicacion
    _, estados_eua = leer_ubicacion(ubicacion)
    donde = "" if estados_eua else ubicacion.strip()
    return (f"{puesto.strip()} en {donde}" if donde else puesto.strip()), donde


def _ruta(q: str):
    return DIR / f"{hashlib.sha1(_norm(q).encode()).hexdigest()[:16]}.json"


def _id(fuente: str, original: str) -> str:
    return "mx_" + hashlib.sha1(f"{fuente}:{original}".encode()).hexdigest()[:10]


def _registrar(fuente: str, estado: str, restantes: int | None = None) -> None:
    """Bitácora de llamadas (sin claves) para llevar la cuenta de la cuota."""
    DIR.mkdir(parents=True, exist_ok=True)
    with open(DIR / "llamadas.jsonl", "a") as f:
        f.write(json.dumps({"cuando": datetime.now().isoformat(timespec="seconds"), "fuente": fuente,
                            "estado": estado, "restantes": restantes}) + "\n")


def cuota() -> dict:
    """{'JSearch': restantes según la API o None, 'Adzuna': llamadas hechas este mes, 'Gemini': llamadas de hoy (el
    nivel gratuito limita por día), 'total': llamadas registradas}."""
    ruta = DIR / "llamadas.jsonl"
    filas = [json.loads(x) for x in ruta.read_text().splitlines()] if ruta.exists() else []
    mes = datetime.now().strftime("%Y-%m")
    js = [f["restantes"] for f in filas if f["fuente"] == "JSearch" and f["restantes"] is not None]
    return {"JSearch": js[-1] if js else None,
            "Adzuna": sum(f["fuente"] == "Adzuna" and f["cuando"].startswith(mes) for f in filas),
            "Gemini": sum(f["fuente"] == "Gemini" and f["cuando"].startswith(datetime.now().strftime("%Y-%m-%d"))
                          for f in filas),
            "total": len(filas)}


# ---------------- normalización ----------------
def _jsearch_vacante(j: dict) -> dict:
    ubic = (j.get("job_location") or "").split("•")[0]
    ubic = ", ".join(p.strip() for p in ubic.split(",") if p.strip())
    if not ubic:
        ubic = ", ".join(x for x in (j.get("job_city"), j.get("job_state"), j.get("job_country")) if x) or "México"
    # Sueldo: el sondeo no trajo ninguno. Por verificar: JSearch no indica la moneda; con country="mx" se asume MXN.
    lo, hi, periodo = j.get("job_min_salary"), j.get("job_max_salary"), j.get("job_salary_period")
    sueldo = None
    if (lo or hi) and periodo in ("MONTH", "YEAR"):
        medio = ((lo or hi) + (hi or lo)) / 2
        sueldo = medio if periodo == "MONTH" else medio / 12
    tipos = [TIPOS_JSEARCH[t] for t in (j.get("job_employment_types") or []) if t in TIPOS_JSEARCH]
    return {"id": _id("JSearch", j["job_id"]), "titulo": j.get("job_title") or "", "empresa": j.get("employer_name"),
            "ubicacion": ubic, "tipos": tipos, "tipo_texto": j.get("job_employment_type"),
            "remoto": j.get("job_is_remote"), "sueldo_mensual": sueldo, "url": j.get("job_apply_link"),
            "publicador": j.get("job_publisher"), "publicada": j.get("job_posted_at"),
            "descripcion": j.get("job_description") or ""}


def _adzuna_vacante(j: dict) -> dict:
    lo, hi = j.get("salary_min"), j.get("salary_max")
    sueldo = ((lo or hi) + (hi or lo)) / 2 / 12 if (lo or hi) else None  # Adzuna da el sueldo anual
    tipos = [TIPOS_ADZUNA[t] for t in (j.get("contract_time"), j.get("contract_type")) if t in TIPOS_ADZUNA]
    creada = j.get("created", "")[:10]
    return {"id": _id("Adzuna", str(j["id"])), "titulo": j.get("title") or "",
            "empresa": (j.get("company") or {}).get("display_name"),
            "ubicacion": (j.get("location") or {}).get("display_name") or "México", "tipos": tipos, "tipo_texto": None,
            "remoto": None, "sueldo_mensual": sueldo, "url": j.get("redirect_url"), "publicador": "Adzuna",
            "publicada": datetime.strptime(creada, "%Y-%m-%d").strftime("el %d/%m/%Y") if creada else None,
            "descripcion": j.get("description") or ""}


# ---------------- llamadas ----------------
def _jsearch(q: str) -> list[dict]:
    if not config.JSEARCH_API_KEY:
        raise RuntimeError("falta la clave de JSearch")
    r = requests.get(JSEARCH_URL, params={"query": q, "country": "mx", "language": "es", "num_pages": 1},
                     headers={"X-RapidAPI-Key": config.JSEARCH_API_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                     timeout=ESPERA_S)
    restantes = r.headers.get("X-RateLimit-Requests-Remaining")
    _registrar("JSearch", str(r.status_code), int(restantes) if restantes and restantes.isdigit() else None)
    r.raise_for_status()
    return [_jsearch_vacante(j) for j in r.json()["data"]["jobs"]]


def _adzuna(puesto: str, donde: str) -> list[dict]:
    if not (config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY):
        raise RuntimeError("faltan las claves de Adzuna")
    params = {"app_id": config.ADZUNA_APP_ID, "app_key": config.ADZUNA_APP_KEY, "what": puesto,
              "results_per_page": 20, "content-type": "application/json"}
    if donde:
        params["where"] = donde
    r = requests.get(ADZUNA_URL, params=params, timeout=ESPERA_S)
    _registrar("Adzuna", str(r.status_code))
    r.raise_for_status()
    return [_adzuna_vacante(j) for j in r.json()["results"]]


def buscar(puesto: str, ubicacion: str = "", sin_red: bool = False, forzar: bool = False) -> Resultado:
    """Vacantes en vivo para el puesto (y la ubicación, si no es de EE. UU.). `sin_red` simula que las APIs no
    responden (prueba del respaldo); `forzar` ignora la caché vigente y vuelve a llamar (gasta cuota)."""
    q, donde = consulta(puesto, ubicacion)
    ruta = _ruta(q)
    guardado = json.loads(ruta.read_text()) if ruta.exists() else None
    if guardado and not forzar and not sin_red:
        horas = (datetime.now() - datetime.fromisoformat(guardado["consultada"])).total_seconds() / 3600
        if horas < VIGENCIA_H:
            return Resultado(guardado["vacantes"], guardado["fuente"], guardado["consultada"], desde_cache=True)

    res = Resultado()
    if sin_red or SIN_RED:  # la caché vigente sí se usa con PC_SIN_RED; la simulación la ignora a propósito
        res.errores.append("simulación: las APIs no responden")
    else:
        for fuente, llamar in (("JSearch", lambda: _jsearch(q)), ("Adzuna", lambda: _adzuna(puesto.strip(), donde))):
            try:
                res.llamadas += 1
                vacantes = llamar()
            except Exception as e:  # red caída, cuota agotada, clave inválida…
                # Sin str(e): el mensaje de requests incluye la URL, y la de Adzuna lleva la clave.
                codigo = getattr(getattr(e, "response", None), "status_code", None)
                res.errores.append(f"{fuente}: {type(e).__name__}" + (f" (HTTP {codigo})" if codigo else ""))
                continue
            if vacantes:
                consultada = datetime.now().isoformat(timespec="seconds")
                DIR.mkdir(parents=True, exist_ok=True)
                ruta.write_text(json.dumps({"consulta": q, "fuente": fuente, "consultada": consultada,
                                            "vacantes": vacantes}, ensure_ascii=False, indent=1))
                res.vacantes, res.fuente, res.consultada = vacantes, fuente, consultada
                return res
            res.errores.append(f"{fuente}: sin resultados")
    if guardado:
        res.vacantes, res.fuente, res.consultada = guardado["vacantes"], guardado["fuente"], guardado["consultada"]
        res.desde_cache = res.vencida = True
    return res


def desde_sondeo() -> list[dict]:
    """Normaliza las respuestas guardadas del sondeo (sirve para probar sin gastar llamadas)."""
    s = config.CACHE / "sondeo"
    js = json.loads((s / "jsearch_mx.json").read_text())["data"]["jobs"]
    az = json.loads((s / "adzuna_mx.json").read_text())["results"]
    return [_jsearch_vacante(j) for j in js] + [_adzuna_vacante(j) for j in az]
