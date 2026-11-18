# Estado · Primera chamba

**Bloque actual:** 6 cerrado. Siguiente: bloque 7 (presentación + guion de demo).

## Hecho
- 2026-11-17 · Entrevista socrática y PRD v1.0 aprobado.
- 2026-11-17 · Paquetes: fpdf2 2.9.0, google-genai 1.73.1, python-dotenv 1.2.2, streamlit 1.67.0 (la 1.55 exigía
  pandas<3 y lo había bajado a 2.3.3; se restauró pandas 3.0.6).
- 2026-11-17 · `.env` + `.env.example` + `.gitignore`; `primera_chamba/config.py` carga las claves con python-dotenv.
- 2026-11-17 · Repo público https://github.com/leocarpio16/primera-chamba (`.env` verificado fuera del repo).
- 2026-11-17 · Dataset descargado con kagglehub (159 MB comprimido, 15 s) en
  `~/.cache/kagglehub/datasets/arshkon/linkedin-job-postings/versions/13/`.

- 2026-11-17 · Claves de Gemini, JSearch y Adzuna cargadas desde `.env` (verificado sin imprimirlas). Sondeo real hecho.
- 2026-11-17 · **Bloque 1:** `primera_chamba/etl.py` (`python3 -m primera_chamba.etl`, ~25 s, pico de 3.5 GB de RSS)
  → `datos/procesado/vacantes.parquet` (206 MB, 110,928 × 21) + `etl_estadisticas.json`.

- 2026-11-17 · **Bloque 2:** `primera_chamba/embeddings.py` (`python3 -m primera_chamba.embeddings [tfidf] [minilm] [e5]`)
  → `datos/procesado/indice_{tfidf,tfidf_completo}.npz` + `vectorizador_*.pkl`, `indice_{minilm,e5}.npy` (float16),
  `indice_job_ids.npy` (orden de filas = parquet, verificado) y `embeddings_meta.json` (tiempos y memoria).

- 2026-11-17 · La suspensión de la Mac no dañó los índices: 600 filas recalculadas coinciden (coseno ≥ 0.99995).
- 2026-11-17 · **Bloque 3:** `primera_chamba/evaluacion.py` + `notebooks/evaluacion.ipynb` ejecutado (~2 min) →
  `datos/procesado/evaluacion_{tabla,idiomas,traduccion}.csv` y `evaluacion_por_consulta.parquet`. Se instaló
  `sentencepiece` 0.2.3 (MarianMT; sin dependencias, pandas sigue en 3.0.6). **Modelo elegido: e5 + traducción es → en.**

- 2026-11-17 · **Bloque 4:** `primera_chamba/motor.py` (perfil → consulta en inglés → e5 → puntaje con bonos →
  Rocchio), `primera_chamba/traduccion.py` (MarianMT con caché en memoria) y `app.py` (`streamlit run app.py`).
  Verificado con `streamlit.testing.v1.AppTest` (ejemplo → buscar → 👍 → 👎, sin excepciones) y con el servidor local.
- 2026-11-17 · **Diseño de la app** con la plantilla del usuario (formulario por pasos, tarjeta negra sobre página
  clara, JetBrains Mono + Inter; tema en `.streamlit/config.toml`). Ajustes pedidos: votos con texto e íconos
  ("Me interesa" / "No me interesa", sin emojis), explicación para todo público (coincidencia Muy alta/Alta/Media/
  Baja según el lugar por parecido: ≤50, ≤500, ≤5,000; detalle técnico en letra chica) y ubicación con formato
  explícito (el motor entiende estados completos en inglés o español). `?demo=1` abre la demo ya buscada.
  Revisado en Chrome (formulario, resultados, marcar/desmarcar, descartar).
- 2026-11-17 · Más ajustes de la app: la explicación de cada vacante es un resumen en lenguaje común (sin z ni coseno;
  el detalle técnico vive en la barra lateral); "No me interesa" se puede deshacer (aviso en el lugar de la tarjeta) y
  recuperar después ("Vacantes que descartaste"); sección para comparar con vacantes de coincidencia media y baja
  (lugares 1,000 / 2,500 / 5,000 y 20,000 / 60,000 / última); "¿Cómo elegimos?" y la comparación van al final.

## Bloque 5 (cerrado 2026-11-18)
- [x] `primera_chamba/en_vivo.py`: caché vigente 24 h → JSearch → Adzuna → lo último guardado (marcado como tal).
  Caché en `cache/en_vivo/<hash de la consulta>.json`; bitácora de llamadas (sin claves) en `cache/en_vivo/llamadas.jsonl`.
  `PC_SIN_RED=1` impide toda llamada (pruebas). Los errores no incluyen `str(e)`: la URL de Adzuna lleva la clave.
- [x] Puntaje en el mismo ranking (`motor.rankear(..., vivas=..., origen=...)`) y Rocchio con ids mixtos (int / "mx_…").
  Catálogo sin cambios: 9 rankings (3 perfiles × base, Rocchio con exclusiones, comparación) idénticos a `HEAD`.
- [x] App: selector Todas / México, en vivo / Catálogo de EE. UU.; etiqueta "En vivo · México"; aviso de caché vencida;
  interruptor en la barra lateral; en "Detalle técnico": cuota, "Simular que la API no responde" y "Volver a consultar".
- [x] Pruebas sin gastar llamadas (AppTest + Chrome): marcar/descartar/deshacer/recuperar vacantes en vivo, simular
  caída (muestra las guardadas), perfil sin caché (solo catálogo), apagar/encender en vivo. Sin excepciones.
- [x] Llamadas reales con el código nuevo (2026-11-18 00:30, OK del usuario): JSearch "Analista de datos en Ciudad de
  México" → 10 vacantes en CDMX (LinkedIn, Indeed, Computrabajo, Bumeran, JobLeads, Citi Careers), 7.1 s, ninguna con
  sueldo; cuota restante 198 según el encabezado. Adzuna (llamada directa) → 20 vacantes, 18 con sueldo, 2.7 s.
- [x] El perfil de ejemplo y `?demo=1` usan "Ciudad de México" (decisión del usuario); la demo sale de la caché
  (9 de 10 vacantes entran) sin llamadas.
- [ ] **Viernes por la mañana:** precargar la caché de la demo (vence 24 h después; 1 llamada de JSearch) con
  "Volver a consultar la API" en la barra lateral o abriendo `?demo=1` después de que venza.

## Bloque 6 (cerrado 2026-11-18)
- [x] **Encuesta ampliada a 5 pasos** (pedido del usuario: más datos para un CV completo). 1 Tu puesto · 2 Preferencias ·
  3 Sobre ti (nombre, correo, teléfono, enlace, presentación, empleo ideal) · 4 Tu experiencia (hasta 4 entradas: puesto,
  tipo, organización, periodo, logros uno por línea; agregar/quitar) · 5 Educación y más (hasta 3 estudios, idiomas,
  cursos, otros). Solo el paso 1 es obligatorio; del 3 al 5 no cambian el ranking. Ejemplo ampliado (incluye un empleo
  ajeno al puesto para que se vea el reordenamiento).
- [x] `primera_chamba/cv.py`: CV por reglas. Cada experiencia, logro, habilidad y curso se traduce es → en y se compara
  con la vacante con e5 (mismo prefijo de consulta que el perfil). Orden: experiencias y logros por parecido;
  habilidades, primero las que menciona el anuncio. Recorte fijo: 4 logros por experiencia, 12 habilidades, 5 cursos; lo
  que queda fuera se muestra al usuario. Con el ejemplo, la experiencia de ventas queda última en las 3 primeras vacantes
  de "Analista de datos" (similitud 0.75–0.77 contra 0.79–0.82). Tarda 2.4–3.8 s por vacante (RSS máx 1.1 GB en la prueba).
- [x] `primera_chamba/habilidades.py`: vocabulario fijo de 113 habilidades (alias en inglés y español). El dataset solo trae
  categorías amplias (IT, SALE…), que no sirven para avisar faltantes. Medido con 3,000 descripciones del catálogo: 17 ms
  por vacante, mediana de 3 habilidades detectadas, 385 sin ninguna. Se quitaron alias genéricos tras revisar contextos
  reales ("sales", "maintenance", "inventory", "recruiting", "talent acquisition", "english", "rcp"). En la vacante en
  vivo "Analista de Datos Antifraude", "rcp" era "enfoque RCP", no primeros auxilios. Es una heurística: puede fallar
  con frases poco comunes.
- [x] App: botón "Armar mi CV" en cada vacante (catálogo y en vivo). Vista del CV con "Lo que pide esta vacante" (las tienes
  / las mencionas en otro campo / no están en tu perfil: **nunca entran al CV**), editor por secciones (`persist_state=
  "page"`: lo editado se conserva por vacante al ir y volver), "Restablecer", "Editar", "Volver", descarga en PDF y
  "¿Cómo armamos tu CV?".
- [x] PDF con fpdf2 2.9.0 y DejaVu Sans (copiada de matplotlib a `primera_chamba/fuentes/` con su licencia, para acentos,
  «·» y «•» sin depender del sistema). Revisado: 1 página A4 con el ejemplo completo.
- [x] Gemini opcional: solo manda perfil y experiencia (sin nombre ni contacto); se rechaza la respuesta si agrega cifras,
  habilidades del vocabulario, logros o si cambia encabezados (probado con 6 respuestas simuladas: 1 aceptada, 5
  rechazadas). Los errores muestran tipo y código, nunca `str(e)`.
- [x] Prueba con **Gemini apagado** (`GEMINI_API_KEY=` vacío, AppTest sin red): 5 pasos, agregar/quitar entradas, buscar,
  armar CV (catálogo y en vivo), editar, volver, regresar (edición conservada), restablecer, Editar desde el CV. Sin
  excepciones. Revisión visual en Chrome (formulario, vista del CV, tarjeta con el botón).
- [ ] **Gemini real: por verificar.** 5 llamadas el 2026-11-18, ninguna generó texto: `gemini-2.5-flash` → 404 ("no
  longer available to new users"); `gemini-3.8-flash` → 5xx (29 s) y después 503 "high demand"; `gemini-flash-latest` →
  503. La clave sirve (no hubo 401/403). Modelo por defecto: `gemini-3.8-flash` (variable `GEMINI_MODELO`). En todas las
  fallas salió el CV por reglas con la nota discreta. Reintentar antes de la demo, con OK del usuario.
- [x] Las llamadas reales a Gemini se anotan en `cache/en_vivo/llamadas.jsonl` (fuente "Gemini", solo estado) y se cuentan
  por día en "Detalle técnico". `PC_SIN_RED=1` también bloquea Gemini. Las 5 llamadas del 2026-11-18 son anteriores a
  la bitácora y no aparecen en ella.

## Decisiones
- Claves en `.env` vía python-dotenv; en la nube, la variable de entorno tiene prioridad.
- API en vivo: **JSearch como principal** (descripción completa; trae vacantes de LinkedIn, Indeed, Computrabajo… vía
  Google for Jobs, sin scraping) y **Adzuna como respaldo** (descripción recortada, pero a veces trae sueldo).
- Presupuesto de cuota: con 10 vacantes por llamada, unas 20–30 llamadas de JSearch se gastan en precargar la caché
  de la demo; el resto queda para consultas en vivo. Adzuna solo si JSearch falla.

## Hallazgos verificados
### Vacantes en vivo (bloque 5, con las 30 vacantes reales del sondeo, 0 llamadas)
- Lugar implícito en el catálogo (mediana) con tres formas de comparar vacantes en español:

  | perfil | A: perfil es · vacante es | B: perfil traducido · vacante es | C: ambos en inglés |
  |---|---|---|---|
  | Analista de datos (relevante) | 2 | 256 | 250 |
  | Enfermera | 1,201 | 35,434 | 40,123 |
  | Chofer repartidor | 70 | 26,093 | 43,628 |
  | Diseñador gráfico | 196 | 19,633 | 17,562 |
  | Contador | 101 | 9,084 | 10,036 |

  A sube cualquier vacante en español para cualquier perfil (sesgo de idioma) → descartada. B ≈ C → **se elige B**
  (no requiere cargar MarianMT es → en). Umbral de entrada: lugar ≤ 5,000 (coincidencia Media o mejor); con
  "Analista de datos" pasan 26–30 de 30, con "Enfermera" ninguna.
- Con la misma regla, las vacantes en vivo no llegan al top 15 de "Todas": con "Analista de datos · Ciudad de México"
  la mejor queda en el lugar 18 (25 si pide remoto). Por eso el selector "México, en vivo".
- Adzuna: 13 de 20 traen sueldo; anual en pesos (115,200–300,000 → 9,600–25,000 al mes). JSearch: el sondeo no trajo
  sueldo; si llega, se asume MXN (**por verificar**: la respuesta no indica moneda).
- Preparar 30 vacantes en vivo (e5): 0.5 s.

### App (bloque 4)
- Puntaje: solo compiten las 300 vacantes más parecidas; puntaje = z + 0.5 × preferencias cumplidas (ubicación,
  modalidad, sueldo, nivel). Con perfiles de prueba, z ≈ 6.4 en el 1.º lugar y ≈ 3.5 en el 300.º.
- MarianMT traduce "nivel de entrada" como "input level" → solo se traduce el texto libre (puesto y habilidades); el
  nivel se arma en inglés desde la lista fija.
- El catálogo solo marca "remoto permitido" (no hay presencial ni híbrido) → esas preferencias salen como "sin dato".
- Tipo de cambio: FIX de Banxico del 2026-11-17 = 18.4677 MXN/USD (tuit de Banxico reproducido por Milenio); editable.
- Memoria: el motor ocupa ~1.0 GB (e5 + MarianMT es→en + índice float32 + catálogo sin descripciones). Las
  descripciones se leen bajo demanda con un filtro de pyarrow (~0.3 s), porque cargarlas todas costaría 0.48 GB.
- Tras reiniciar el servidor, la primera carga del motor tardó >10 s (hasta ~25 s): **abrir la app antes de presentar**.
- Streamlit recarga `app.py` al guardar, pero no siempre `primera_chamba/*`: reiniciar el servidor tras cambiar el motor.
- Tiempos: carga del motor ~8 s (una vez, con `st.cache_resource`), traducción ~3 s la primera vez, ranking 0.06 s.

### Evaluación (bloque 3) — `notebooks/evaluacion.ipynb`
- 1,000 consultas (684 puestos, máx. 3 por título, sin títulos genéricos, ≥5 relevantes fuera de su grupo). Perfil:
  `titulo_norm. Skills: <categorías>. Experience level: <nivel>.` Relevantes por consulta (mediana): 29 del mismo
  puesto, 814 estructurales.
- nDCG@10 con título [IC 95 %]: TF-IDF 70 palabras 0.442 [0.423, 0.460] · TF-IDF completo 0.407 · MiniLM 0.365 ·
  e5 0.361 · aleatorio 0.008 · popularidad 0.002.
- nDCG@10 solo estructural: e5 0.210 [0.193, 0.228] · MiniLM 0.199 · TF-IDF 0.196 · TF-IDF completo 0.169 · aleatorio
  0.022 · popularidad 0.004. e5 − TF-IDF = +0.014 [+0.000, +0.028] (casi empate).
- La ventaja de TF-IDF con título es en parte circular (el perfil trae el puesto). La etiqueta no une sinónimos ("system
  engineer" ≠ "systems engineer"), lo que castiga a los modelos densos.
- Título + 70 palabras > descripción completa en TF-IDF (+0.034, P = 1.00).
- **Español (200 perfiles traducidos con opus-mt-en-es):** TF-IDF cae 96 % (0.016), MiniLM 75 % (0.094), e5 55 % (0.165).
- **Traducir es → en antes de buscar** (ida y vuelta, optimista; agregado tras ver resultados): e5 0.323, MiniLM 0.315,
  TF-IDF 0.299. e5 (es→en) − e5 directo = +0.158 [+0.126, +0.192].
- Regla de decisión fijada antes de los resultados: mayor nDCG@10 con perfiles en español → **e5** (gana directo y con
  traducción).
- Traducción con MarianMT en `mps`: 200 perfiles en ~20 s (en → es).

### Índices (bloque 2) — medido el 2026-11-17
- **Texto que se representa:** título + primeras 70 palabras de la descripción, máx. 128 tokens, igual para MiniLM y
  e5 (la comparación mide el modelo, no el largo). Ambos modelos usan el tokenizador de XLM-R: 1.56 tokens/palabra,
  descripción mediana de 727 tokens. Con 70 palabras, el 97 % cabe en 128 tokens (con 80 se cortaría el 47 %).
- Prueba con 2,000 vacantes en `mps` (fp32, lote 64): MiniLM 150 vac/s, e5 a 128 tokens 144 vac/s, e5 a 256 tokens
  61 vac/s, e5 a 512 tokens 22 vac/s (≈84 min y 5.6 GB de `mps`) → descartado. fp16 solo sube a 160 vac/s (coseno
  ≥ 0.9995 contra fp32); CPU 88 vac/s.
- Catálogo completo: **e5 721 s (154 vac/s)**, pico de 1.33 GB en `mps`, RSS 0.33 GB. **MiniLM:** el tiempo guardado
  (5,455 s) está inflado porque la Mac se suspendió al cerrar la tapa; la velocidad sin interrupciones es la de la prueba
  (~150 vac/s ≈ 12 min). Pico de 1.41 GB en `mps`. Cada índice ocupa 85 MB (110,928 × 384, float16).
- TF-IDF (unigramas + bigramas, `stop_words="english"`, min_df 3, max_df 0.5, 200 mil términos, sublineal):
  recortado 26 s, 7.7 M no ceros, 40 MB, pico 0.9 GB; con la descripción completa 70 s, 45.9 M no ceros, 252 MB, pico 1.5 GB.
- Verificación: sin NaN, normas = 1, ninguna fila repetida. Consultas en español ("enfermera en hospital",
  "analista de datos, reportes y tableros") dan Registered Nurse / Data Analyst con los dos modelos densos.
- **Cosenos de e5 comprimidos** (top-4 entre 0.86 y 0.89; MiniLM 0.58–0.79) → en el bloque 4, los bonos por
  preferencias no pueden ser absolutos: estandarizar el coseno por consulta (o escalar los bonos) antes de sumarlos.
- TF-IDF no se desploma del todo en español cuando la consulta comparte términos técnicos ("sql", "python") → la
  prueba entre idiomas debe reportar también perfiles sin esos términos.

### ETL (bloque 1) — `datos/procesado/vacantes.parquet`
- 123,849 → **110,928 vacantes**: 12,695 duplicados exactos (misma empresa + título + descripción, ~10 %) y 226 con
  descripción de menos de 20 palabras.
- Columnas: job_id, company_name, title, `titulo_norm`, description, location, `estado` (84.5 %), `remoto` (13,180),
  `tipo_empleo`, `nivel` (75 %), `sueldo_anual` (30.5 %), pay_period, currency, `vistas`, `postulaciones`,
  job_posting_url, listed_time, `skills` (lista de categorías, 98.5 % con al menos una), `industrias` (lista de nombres,
  98.7 %), `palabras`, `grupo_plantilla`.
- `normalized_salary` **sí está anualizado** (mediana por hora 53,560 ≈ 25.75 USD × 2,080 h; anual 100,810). Se
  invalidaron 452 valores fuera de [10 mil, 1 M] USD o en otra moneda (había quincenales de 1.5 M y sueldos de 118).
  Mediana válida: 82,500 USD.
- **Plantillas copiadas:** 5,177 vacantes (4.7 %, 1,789 grupos, el mayor de 61) comparten la descripción exacta con otra,
  con otro título (1,023 grupos) o empresa (283). `grupo_plantilla` las identifica → en la evaluación no cuentan como
  acierto entre sí (sería una fuga).
- `titulo_norm`: minúsculas, sin paréntesis ni sufijos tras " - ", "|" o ",", sin nivel (senior, sr, jr, II…) ni
  jornada (full time, remote, per diem…). Se conserva "contract" (Contract Specialist es un puesto). 72,018 → 44,674
  títulos; el 68.7 % de las vacantes comparte su título normalizado con otra. Limitación: no une sinónimos ("rn" 356
  vs "registered nurse" 1,356), y hay títulos genéricos ("manager" 920, "director" 743) que en la etiqueta de "mismo
  puesto" valen poco → filtrarlos al elegir las consultas del bloque 3.
- Habilidades por vacante: 0 → 1,709; 1 → 49,046; 2 → 47,061; 3 → 13,112. Las más comunes: IT 23,498, MGMT 17,947,
  SALE 17,619, MNFC 15,782, HCPR 15,427.
- `vistas`: mediana 4, p90 25, p99 188 (1,387 nulas) → línea base de popularidad.

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
