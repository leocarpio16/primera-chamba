# Chambot

Proyecto semestral de Datos Masivos II (individual). Recomendador de vacantes + CV personalizado, en Streamlit.
**Entrega: viernes 2026-11-20, 19:00** (presentación + demo en vivo).

- Especificación: `docs/PRD.md`. Estado y bloque actual: `docs/ESTADO.md`. **Leer ESTADO.md al iniciar cada sesión.**
- Todo en español: interfaz, CV, comentarios, notebooks y documentación.

## Reglas

1. **No adivinar.** Columnas del dataset, respuestas de las APIs, límites, tiempos y métricas se verifican ejecutando
   antes de escribirlos en código, docs o diapositivas. Lo no verificado se marca "por verificar".
2. **El CV nunca inventa.** Solo usa habilidades, cifras y experiencias que el usuario escribió. Las habilidades que
   faltan se avisan en la interfaz, nunca entran al CV. Gemini es opcional; sin él, el CV por reglas debe salir igual.
3. **Costo cero.** Ningún servicio de pago.
4. **Secretos:** las claves viven solo en `.env` (ignorado). Se leen con `primera_chamba.config`. Nunca imprimir,
   registrar ni subir una clave. No leer el contenido de `.env`.
5. **Datos:** el dataset crudo y los derivados van en `datos/` y `cache/` (ignorados). No se suben al repo.
6. **Memoria (Mac de 8 GB con swap ocupado):** procesar por lotes, float16 para embeddings, mostrar avance, no cargar
   más de lo necesario.
7. **Trabajo por bloques** (PRD §10). Al cerrar un bloque: verificar su criterio de "hecho", actualizar `ESTADO.md`
   y hacer commit. Prioridades si falta tiempo: recortar d → e → c → b; (a) motor y (f) presentación no se recortan.
8. Subagentes permitidos cuando ahorren tiempo (búsquedas, verificaciones en paralelo).

## Estructura

- `primera_chamba/` — paquete (config, ETL, motor, CV…)
- `notebooks/` — evaluación fuera de línea (se entrega ejecutada)
- `app.py` — app Streamlit (bloque 4)
- `docs/` — PRD, ESTADO
- Entorno: Python 3.11 global (`python3`); dependencias en `requirements.txt`.
