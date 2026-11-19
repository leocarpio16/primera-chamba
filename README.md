# Chambot

Recomendador de vacantes para quien busca su primer empleo. A partir de tu perfil, te sugiere las ofertas que mejor
te quedan y te arma un CV adaptado a cada una, usando solo lo que tú escribiste.

Proyecto semestral de Datos Masivos II (individual). Especificación en [`docs/PRD.md`](docs/PRD.md); estado y
hallazgos en [`docs/ESTADO.md`](docs/ESTADO.md).

- **Presentación:** https://claude.ai/artifact/CXHAyrNFEFwyG22H2hS4oz
- **Guion de la demo:** [`docs/GUION_DEMO.md`](docs/GUION_DEMO.md)
- **Evaluación fuera de línea (ejecutada):** [`notebooks/evaluacion.ipynb`](notebooks/evaluacion.ipynb)

## Qué hace

1. **Encuesta de 5 pasos, para cualquier carrera.** Solo el paso 1 (puesto y habilidades) es obligatorio. Al elegir
   tu área, los ejemplos de cada campo se adaptan y hay un perfil de ejemplo por área (salud, derecho, educación,
   diseño, contaduría, psicología y tecnología). Los pasos 1–2 alimentan el ranking; los pasos 3–5 solo sirven para
   el CV.
2. **Ranking.** El perfil se traduce al inglés (MarianMT, local) y se compara con e5 (`multilingual-e5-small`) contra
   110,928 vacantes del catálogo de LinkedIn. Las preferencias cumplidas suben el puntaje.
3. **Aprende de ti.** «Me interesa» y «No me interesa» reordenan la lista (Rocchio).
4. **Vacantes en vivo de México** (JSearch, con Adzuna de respaldo), medidas con la misma regla que el catálogo.
   Se guardan en caché 24 h; si la API no responde, se muestran las últimas guardadas, marcadas como tales.
5. **CV a la medida.** Ordena tu experiencia, tus logros y tus habilidades según la vacante, y se descarga en PDF.
   Avisa qué habilidades pide la vacante y no aparecen en tu perfil, pero **nunca las agrega al CV**. Gemini puede
   pulir la redacción (opcional); si su respuesta agrega cifras, habilidades o logros, se descarta.

## Resultados de la evaluación

Perfiles sintéticos sacados del catálogo; la relevancia sale de campos que el modelo no ve (mismo puesto normalizado,
categoría de habilidad e industria). Detalle e intervalos de confianza en el notebook.

Con 1,000 perfiles en inglés, el nDCG@10 (etiqueta «con título») fue: TF-IDF 0.442, MiniLM 0.365, e5 0.361,
aleatorio 0.008. Pero los usuarios escriben en español. Con 200 de esos perfiles traducidos al español:

| Método | En inglés | En español | Español → inglés antes de buscar* |
|---|---|---|---|
| TF-IDF (70 palabras) | 0.432 | 0.016 | 0.299 |
| MiniLM multilingüe | 0.376 | 0.094 | 0.315 |
| **e5-small multilingüe** | 0.368 | 0.165 | **0.323** |
| Aleatorio | 0.008 | 0.008 | — |

\* Ida y vuelta en → es → en, así que el resultado es optimista.

TF-IDF se desploma en español. La regla se fijó antes de ver resultados (gana el mayor nDCG@10 en español), así que se
eligió **e5**, traduciendo el perfil al inglés antes de buscar.

## Cómo correrla (demo local)

Se probó en una Mac de 8 GB con Python 3.11. La app no se publicó en Streamlit Cloud: el catálogo y los índices
(`datos/`, 664 MB) no se suben al repo, y sin ellos la app no arranca.

### 1. Instalar

```bash
pip install -r requirements.txt
cp .env.example .env   # claves opcionales; ver «Claves»
```

### 2. Construir los datos (una sola vez)

```bash
python3 -m primera_chamba.etl            # descarga el dataset de Kaggle y escribe datos/procesado/vacantes.parquet (~25 s)
python3 -m primera_chamba.embeddings e5  # índice que usa la app (~12 min en una Mac con GPU mps)
```

El dataset es [`arshkon/linkedin-job-postings`](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings)
(se descarga con `kagglehub`). Para reproducir el notebook completo hacen falta los tres índices:
`python3 -m primera_chamba.embeddings` sin argumentos (TF-IDF, MiniLM y e5).

### 3. Abrir la app

```bash
streamlit run app.py
```

- http://localhost:8501: la app normal. La primera búsqueda tarda ~15 s, porque se cargan los modelos.
- http://localhost:8501/?demo=1: abre el perfil de ejemplo ya buscado (respaldo para la presentación).

### Claves (todas opcionales y gratuitas)

Viven solo en `.env`, que git ignora (plantilla en [`.env.example`](.env.example)).

| Variable | Para qué | Sin ella |
|---|---|---|
| `JSEARCH_API_KEY` | Vacantes en vivo de México | Se usa Adzuna |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Respaldo de vacantes en vivo | Solo catálogo (o caché) |
| `GEMINI_API_KEY` | Pulir la redacción del CV | El CV por reglas sale completo |
| `GEMINI_MODELO` | Modelo de Gemini (por omisión `gemini-3.8-flash`) | — |

### Modo sin red (pruebas)

```bash
PC_SIN_RED=1 GEMINI_API_KEY= streamlit run app.py
```

`PC_SIN_RED=1` bloquea toda llamada a JSearch, Adzuna y Gemini: las vacantes en vivo salen solo de la caché
(`cache/en_vivo/`). Sirve para probar sin gastar cuota. Cada llamada real queda en `cache/en_vivo/llamadas.jsonl`,
sin claves.

## Estructura

```
app.py                     app Streamlit
primera_chamba/
  config.py                rutas y claves (.env)
  etl.py                   CSV de Kaggle → vacantes.parquet
  embeddings.py            índices TF-IDF, MiniLM y e5 (float16)
  evaluacion.py            métricas fuera de línea (las usa el notebook)
  traduccion.py            MarianMT es ↔ en, local
  motor.py                 perfil → ranking con preferencias y Rocchio
  en_vivo.py               JSearch / Adzuna con caché y respaldo
  habilidades.py           vocabulario fijo de 113 habilidades (aviso de faltantes)
  cv.py                    CV por reglas, Gemini opcional y PDF (fpdf2 + DejaVu Sans)
  encuesta.py              ejemplos de la encuesta y perfiles de ejemplo por área
notebooks/evaluacion.ipynb evaluación ejecutada
docs/                      PRD, estado, guion de la demo
```

Todo es de costo cero: modelos locales de Hugging Face y planes gratuitos de las APIs.
