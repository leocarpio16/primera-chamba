# PRD · Chambot

**Versión:** 1.0 (borrador para aprobación) · **Fecha:** 2026-11-17 · **Autor:** Leo Carpio
**Materia:** Datos Masivos II — proyecto semestral (requisitos libres; el peso está en el sistema de recomendación)
**Entrega:** viernes 2026-11-20, 19:00 · presentación + demo en vivo · trabajo individual

---

## 1. Problema y propuesta

Quien busca empleo manda el mismo CV genérico a decenas de vacantes y revisa cientos de ofertas que no le
corresponden. **Chambot** recibe el perfil profesional del usuario, le recomienda las vacantes que mejor
coinciden con sus habilidades, ubicación y preferencias, y para cada vacante genera un CV adaptado que **solo usa lo
que el usuario sí tiene**.

Se presenta como producto que se "vende" a la profesora: el argumento de venta es la evidencia de que el motor
funciona sobre un volumen grande de vacantes reales.

## 2. Usuario y flujo

1. El usuario llena un **formulario**: puesto deseado, habilidades, experiencias y logros, educación, ubicación,
   modalidad (presencial / híbrido / remoto), sueldo esperado, nivel de experiencia y una descripción libre de su
   empleo ideal.
2. Ve un **ranking de vacantes** (catálogo del dataset + vacantes en vivo), cada una con su puntuación y una
   explicación de por qué se recomienda (qué preferencias cumple y cuáles no).
3. **Califica** vacantes (👍 / 👎) y el ranking se reajusta (retroalimentación de relevancia, Rocchio).
4. Elige una vacante y obtiene un **CV personalizado**, lo **edita** en la app y lo **descarga en PDF**.
5. Ve un **aviso de habilidades faltantes**: lo que pide la vacante y él no tiene. Esas habilidades **no** entran al CV.

## 3. Alcance por prioridad

El orden lo fijó el usuario. Si el tiempo no alcanza, se recorta desde abajo.

| Prioridad | Pieza | Criterio mínimo de "hecho" |
|---|---|---|
| 1 · (a) | Motor de recomendación evaluado sobre el dataset masivo | Tabla de nDCG@10 y Recall@10 para 3 modelos + 2 líneas base, con prueba entre idiomas, reproducible desde un notebook ejecutado |
| 2 · (f) | Presentación de venta del producto | Diapositivas + guion de demo ensayado |
| 3 · (b) | Vacantes en vivo por API | La app consulta la API, guarda en caché y, si la API falla, muestra lo último en caché marcado como tal |
| 4 · (c) | CV personalizado | Plantilla por reglas + edición + PDF; redacción con Gemini solo si la clave funciona |
| 5 · (e) | App publicada en internet | Streamlit Community Cloud desde el repo público; si no da tiempo, la demo corre local |
| 6 · (d) | Aviso de habilidades faltantes | Lista de habilidades de la vacante que no aparecen en el perfil |

**Fuera de alcance:** scraping de LinkedIn u OCC (sus términos lo prohíben), cuentas de usuario y persistencia entre
sesiones, aplicar a vacantes desde la app, apps nativas (Xcode).

## 4. Restricciones

- **Costo cero.** Nada de servicios de pago. Se descarta la API de Claude, que no tiene nivel gratuito.
- **Hardware:** Mac con 8 GB de RAM, con swap ya ocupado por otras apps. Todo lo pesado (embeddings del dataset) se
  precalcula por lotes, en float16 y con avance visible.
- **Idioma:** la interfaz y el CV van en español; el dataset está en inglés; las vacantes en vivo pueden venir en
  español. Por eso se usan embeddings multilingües.
- **Claves:** ninguna clave va en el código ni en el repo. Se guardan en `.env` (ignorado por git, cargado con python-dotenv)
  y, en la nube, como secretos de Streamlit.
- **Datos:** el dataset crudo no se sube al repo (tamaño y licencia de Kaggle). Se descarga con `kagglehub`.

## 5. Arquitectura

```
                 FUERA DE LÍNEA (Mac, una vez)                       EN LÍNEA (app Streamlit)
 Kaggle LinkedIn ──► ETL ──► vacantes.parquet ──► embeddings ──►  índice (float16)
                                   │                 (TF-IDF,           │
                                   │                  MiniLM-multi,     ▼
                                   │                  e5-small)    formulario ─► vector de perfil
                                   ▼                                    │        + filtros/bonos
                          evaluación fuera de línea                     ▼
                          (nDCG, Recall, líneas base,          ranking ◄── vacantes en vivo (API + caché)
                           prueba entre idiomas)                   │
                                                                   ├─► 👍/👎 ─► Rocchio ─► nuevo ranking
                                                                   └─► vacante elegida ─► CV por reglas
                                                                              └─► (Gemini opcional) ─► edición ─► PDF
```

### 5.1 Puntuación de una vacante
`puntaje = coseno(perfil, vacante) + bonos por preferencias cumplidas (ubicación, modalidad, sueldo, nivel)`.
Los pesos de los bonos se fijan y se documentan; no se ajustan para "verse bien" en la demo. Cada vacante muestra
el desglose del puntaje.

### 5.2 Retroalimentación (Rocchio, por sesión)
`q' = α·q + β·media(👍) − γ·media(👎)`, con valores iniciales α=1, β=0.75, γ=0.15. Vive solo en la sesión.

### 5.3 CV
- **Base, siempre disponible:** se puntúa cada experiencia, logro y habilidad del formulario contra la vacante con el
  mismo modelo de embeddings; se ordenan, se descarta lo irrelevante y se arma una plantilla fija. Solo reacomoda texto
  del usuario, así que no puede inventar.
- **Opcional:** si hay clave de Gemini (nivel gratuito) y responde, reescribe la redacción con una instrucción explícita
  de no agregar habilidades, cifras ni experiencias que no estén en la entrada. Si falla o se agota la cuota, sale la
  versión base sin aviso de error para el usuario (solo una nota discreta).
- Aviso en la interfaz: en el nivel gratuito de Gemini, Google puede usar los datos enviados.
- Exportación a PDF con una librería de Python pura (candidata: `fpdf2`; se confirma en el bloque de la app).

## 6. Datos

- **Catálogo masivo:** *LinkedIn Job Postings 2023-2024* (Kaggle, `arshkon/linkedin-job-postings`), ~124 mil
  vacantes de EE. UU. **Por verificar al descargar:** columnas de sueldo, ubicación, modalidad, nivel, vistas y
  postulaciones, y las tablas de habilidades e industrias por vacante (se cree que las habilidades son ~35 categorías
  amplias, no habilidades finas; eso cambia el diseño de las etiquetas de la sección 7).
- **En vivo:** JSearch (RapidAPI) o Adzuna. **Por verificar en el bloque 0:** cuál cubre México con plan gratuito y su
  límite de solicitudes. Las respuestas se guardan en caché en disco.

## 7. Evaluación (pieza principal)

**Fuera de línea, con etiquetas que el modelo no ve:**
- Se toma una muestra de vacantes y cada una se convierte en un **perfil sintético** (puesto + habilidades + nivel).
  La vacante de origen se excluye de su propio ranking.
- **Relevancia graduada** a partir de campos estructurados, no del texto: 2 = mismo puesto normalizado; 1 = comparte
  categoría de habilidad e industria; 0 = el resto. Se reporta también con etiquetas solo estructurales para medir
  cuánto se beneficia TF-IDF de coincidir con el título.
- **Métricas:** nDCG@10 y Recall@10, con intervalos por bootstrap.
- **Comparación:** TF-IDF, `paraphrase-multilingual-MiniLM-L12-v2` e `intfloat/multilingual-e5-small` (con los
  prefijos `query:` / `passage:`), contra dos líneas base: aleatorio y más populares (por vistas o postulaciones).
- **Prueba entre idiomas:** una muestra de perfiles sintéticos se traduce al español con un traductor local gratuito
  (candidato: `Helsinki-NLP/opus-mt-en-es`) y se mide cuánto cae cada modelo. TF-IDF debería desplomarse; los
  multilingües, no.
- El modelo ganador es el que usa la app.

**En línea, en la demo:** Rocchio con las calificaciones del usuario. Se presenta como función del producto
("aprende de ti"), no como prueba estadística.

## 8. Stack

Python 3.11 · pandas / pyarrow · scikit-learn (TF-IDF) · sentence-transformers 5.2 (instalado) · Streamlit ·
`kagglehub` (funciona) · `google-genai` (opcional) · `fpdf2` · transformers (MarianMT, instalado).
**Paquetes a instalar** (se confirmará antes): `streamlit`, `fpdf2`, `google-genai`.

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Embeddings de 124 mil vacantes saturan la RAM o tardan demasiado | Lotes, texto truncado, float16, avance visible; si no cabe, muestra estratificada documentada |
| Las etiquetas favorecen a TF-IDF (circularidad por títulos) | Se reportan dos versiones de etiquetas (con y sin título) y se discute |
| La API en vivo falla o se agota la cuota en la demo | Caché en disco + catálogo del dataset siempre disponible |
| Gemini falla o inventa | CV base por reglas como respaldo; instrucción de no inventar; la edición queda en manos del usuario |
| Dataset de EE. UU. frente a usuario mexicano | Se declara como limitación; la API en vivo aporta vacantes de México; prueba entre idiomas |
| Streamlit Cloud no aguanta el modelo o el índice | La demo corre local; la publicación es prioridad 5 |
| Se acaba el tiempo | Recorte en el orden d → e → c → b; (a) y (f) no se recortan |

## 10. Plan de bloques

Cada bloque termina con su criterio verificado y `docs/ESTADO.md` actualizado.

| Bloque | Cuándo | Contenido | Hecho cuando |
|---|---|---|---|
| 0 | mar 17 | Arnés (`CLAUDE.md`, `ESTADO.md`), repo público, verificación de APIs en vivo y del dataset | Repo en GitHub; API elegida con su límite documentado; columnas reales del dataset anotadas |
| 1 | mié 18 a.m. | ETL → `vacantes.parquet` + exploración breve | Conteos y nulos verificados; campos de evaluación confirmados |
| 2 | mié 18 | Embeddings de los 3 modelos | Índices guardados; tiempos y memoria medidos |
| 3 | mié 18 p.m. – jue 19 a.m. | Evaluación fuera de línea | Notebook ejecutado con tabla final y modelo elegido |
| 4 | jue 19 | App: formulario, ranking con desglose, Rocchio | Demo local funcional con el catálogo |
| 5 | jue 19 | API en vivo + caché | Vacantes reales de México en el ranking; prueba con la API apagada |
| 6 | jue 19 p.m. | CV por reglas, edición, PDF, Gemini opcional, habilidades faltantes | PDF descargado y revisado; prueba con Gemini apagado |
| 7 | vie 20 a.m. | Presentación + guion de demo | Diapositivas listas; demo ensayada de principio a fin |
| 8 | vie 20 | Publicación en Streamlit Cloud, README, margen | Liga pública funcionando, o decisión explícita de demo local |

## 11. Reglas de trabajo (para el arnés)

- No adivinar: todo dato del dataset, de las APIs o de las métricas se verifica antes de escribirse.
- El CV nunca contiene habilidades, cifras ni experiencias que el usuario no escribió.
- Trabajo por bloques con `docs/ESTADO.md`; se pueden usar subagentes cuando ahorren tiempo.
- Ninguna clave en el repo. No se suben datos crudos.
