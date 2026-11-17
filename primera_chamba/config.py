"""Configuración del proyecto: rutas y variables de entorno.

Las claves se leen de `.env` (local, ignorado por git) con python-dotenv. Una variable que ya
exista en el entorno tiene prioridad sobre `.env`, así que en Streamlit Cloud basta con
declararla como secreto.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DATOS = RAIZ / "datos"
CACHE = RAIZ / "cache"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "").strip()
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()

DATASET_KAGGLE = "arshkon/linkedin-job-postings"


def hay_gemini() -> bool:
    """True si hay una clave de Gemini configurada (no comprueba que funcione)."""
    return bool(GEMINI_API_KEY)
