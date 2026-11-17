# Estado · Primera chamba

**Bloque actual:** 0 cerrado. Siguiente: bloque 1 (ETL).

## Hecho
- 2026-11-17 · Entrevista socrática y PRD v1.0 aprobado.
- 2026-11-17 · Paquetes: fpdf2 2.9.0, google-genai 1.73.1, python-dotenv 1.2.2, streamlit 1.67.0 (la 1.55 exigía
  pandas<3 y lo había bajado a 2.3.3; se restauró pandas 3.0.6).
- 2026-11-17 · `.env` + `.env.example` + `.gitignore`; `primera_chamba/config.py` carga las claves con python-dotenv.
- 2026-11-17 · Repo público https://github.com/leocarpio16/primera-chamba (`.env` verificado fuera del repo).
- 2026-11-17 · Dataset descargado con kagglehub (159 MB comprimido, 15 s) en
  `~/.cache/kagglehub/datasets/arshkon/linkedin-job-postings/versions/13/`.

## Pendiente del bloque 0
- [x] Claves de Gemini, JSearch y Adzuna cargadas desde `.env` (verificado sin imprimirlas). Sondeo real hecho.

## Decisiones
- Claves en `.env` vía python-dotenv; en la nube, la variable de entorno tiene prioridad.
- API en vivo: **JSearch como principal** (descripción completa; trae vacantes de LinkedIn, Indeed, Computrabajo… vía
  Google for Jobs, sin scraping) y **Adzuna como respaldo** (descripción recortada, pero a veces trae sueldo).
- Presupuesto de cuota: con 10 vacantes por llamada, unas 20–30 llamadas de JSearch se gastan en precargar la caché
  de la demo; el resto queda para consultas en vivo. Adzuna solo si JSearch falla.

## Hallazgos verificados
### Dataset (`postings.csv`, 493 MB)
- **123,849 vacantes**, 31 columnas. `description` 100 % presente: mediana 477 palabras (p25 298, p75 696, máx 3,400).
  Los modelos truncan (MiniLM a 128 tokens por defecto, e5 a 512): hay que decidir qué parte del texto se embebe.
- `pd.read_csv(engine="pyarrow")` **falla** (hay saltos de línea dentro de celdas); usar el lector por defecto.
  Leer todo, incluida `description`, llegó a 2.1 GB de RSS → en el bloque 1 se convierte una sola vez a parquet.
- `title`: 72,521 títulos distintos (top: Sales Manager 673, Customer Service Representative 373, Project Manager 354)
  → para la etiqueta "mismo puesto" hace falta normalizar títulos.
- `formatted_experience_level` 76.3 % presente (Mid-Senior 41,489; Entry 36,708; Associate 9,826; Director 3,746;
  Internship 1,449; Executive 1,222).
- `formatted_work_type` 100 % (Full-time 98,814; Contract 12,117; Part-time 9,696…).
- `remote_allowed` solo vale 1 (15,246) o nulo; no hay "no remoto" explícito.
- Sueldo (`normalized_salary`, `pay_period`, `currency`) 29.1 % presente; casi todo USD (36,058). YEARLY 20,628, HOURLY 14,741.
- `views` 98.6 %, `applies` 18.8 % → la línea base de popularidad usa `views`.
- `skills_desc` solo 2.0 % → las habilidades finas habrá que sacarlas de `description`.
- `location` 100 %, en EE. UU. (8,125 dicen solo "United States").

### Tablas auxiliares
- `jobs/job_skills.csv`: **35 categorías amplias** (`mappings/skills.csv`, p. ej. ART, DSGN, MRKT, IT, SALE), 1 a 3 por
  vacante (media 1.69). Confirmado: no son habilidades finas.
- `jobs/job_industries.csv`: 422 industrias. Ojo: 126,807 job_id con habilidad y 127,125 con industria, más que las
  123,849 vacantes → en el bloque 1 se mide la cobertura real del cruce.
- También: `jobs/salaries.csv`, `jobs/benefits.csv`, `companies/*`.

### APIs en vivo — sondeo real con México (2026-11-17), respuestas en `cache/sondeo/`
- **JSearch:** `/search` fue retirado (404 "Endpoint '/search' does not exist"); el actual es
  `GET https://jsearch.p.rapidapi.com/search-v2` con encabezados `X-RapidAPI-Key` y `X-RapidAPI-Host`. Con
  `query="analista de datos en Ciudad de México"` y `country="mx"` devolvió **10 vacantes** en `data.jobs`, más un
  `data.cursor` para paginar. La descripción viene **completa** (70–639 palabras). Fuentes: LinkedIn 3, Indeed 3,
  Computrabajo 2, SimplyHired 1, JobLeads 1. `job_city`/`job_country` a veces vienen nulos → usar `job_location`
  ("Ciudad de México, CDMX • a través de LinkedIn"). Sin sueldo en esta muestra. `job_employment_type` en español
  ("Tiempo completo"). Cuota según los encabezados: `X-RateLimit-Requests-Limit: 200`, Remaining 199, reinicio en
  ~30 días. El 404 no consumió cuota.
- **Adzuna:** `GET https://api.adzuna.com/v1/api/jobs/mx/search/1` funciona con México: 20 resultados de un total de
  301 para "analista de datos". La descripción viene recortada (59–80 palabras); 13 de 20 traen `salary_min`.
  Cuota según el usuario: 25 llamadas.

### APIs en vivo (lectura de documentación, 2026-11-17)
- **Adzuna** (docs oficiales): requiere `app_id` + `app_key`; endpoint `/v1/api/jobs/{país}/search/{página}` con
  `what`, `where`, `results_per_page`, `salary_min`…; la **descripción viene recortada** ("snippet"). La documentación
  leída no lista países ni límite gratuito: México **por verificar** con una consulta real.
- **JSearch** (RapidAPI, agrega Google for Jobs): la página de precios no se pudo leer (JavaScript). Fuentes de terceros
  reportan un plan gratuito de 200 solicitudes/mes. Cobertura de México y límite **por verificar**.
