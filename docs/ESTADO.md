# Estado · Primera chamba

**Bloque actual:** 0 — arnés, repo y verificaciones (mar 2026-11-17)

## Hecho
- 2026-11-17 · Entrevista socrática y PRD v1.0 aprobado.
- 2026-11-17 · Paquetes: fpdf2 2.9.0, google-genai 1.73.1, python-dotenv 1.2.2, streamlit 1.67.0 (la 1.55 exigía
  pandas<3 y lo había bajado a 2.3.3; se restauró pandas 3.0.6).
- 2026-11-17 · `.env` (vacío) + `.env.example` + `.gitignore`; `primera_chamba/config.py` carga `GEMINI_API_KEY` con
  python-dotenv.

## Pendiente del bloque 0
- [ ] Repo público `leocarpio16/primera-chamba` creado y con primer commit.
- [ ] API en vivo: ¿JSearch o Adzuna? Cobertura de México, plan gratuito, límite.
- [ ] Dataset de Kaggle descargado; columnas reales y tablas de habilidades/industrias anotadas aquí.

## Decisiones
- Claves en `.env` vía python-dotenv (en lugar de `.streamlit/secrets.toml`); en la nube, la variable de entorno tiene
  prioridad.

## Hallazgos verificados
_(vacío)_
