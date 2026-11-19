# Guion de demo · Chambot

Duración objetivo de la demo: **5–6 min** (dentro de la presentación, diapositiva 12 «Demo»).
Presentación: https://claude.ai/artifact/CXHAyrNFEFwyG22H2hS4oz (privada: compartirla desde *Share* si alguien más debe abrirla).

## Antes de presentar (viernes)
- [ ] **En la mañana:** precargar la caché de la demo (1 llamada de JSearch, con OK): abrir `http://localhost:8501/?demo=1`
      o usar «Volver a consultar la API» en la barra lateral. La caché dura 24 h.
- [ ] (Opcional, con OK) Probar una vez «Mejorar la redacción con IA». Si Gemini da 503, **no usarlo en la demo**.
- [ ] 10 min antes: `streamlit run app.py` y abrir la app una vez (el motor tarda 10–25 s en frío).
- [ ] Dos pestañas: `http://localhost:8501` (demo normal) y `http://localhost:8501/?demo=1` (respaldo, ya buscado).
- [ ] Mac con corriente y la tapa abierta (si se cierra, se suspende). Zoom del navegador al 110–125 % para el proyector.

## Recorrido

| # | Acción | Qué decir | Tiempo |
|---|---|---|---|
| 1 | Paso 1 → **Usar un perfil de ejemplo** | «Una recién egresada de Ciencia de Datos busca su primer trabajo como analista de datos.» | 20 s |
| 2 | **Continuar** por los pasos 2 a 5 sin detenerse mucho | «Preferencias para el ranking; del paso 3 en adelante, todo es para el CV. Fíjense: tiene un empleo de vendedora que no tiene que ver con datos.» | 40 s |
| 3 | **Buscar vacantes** (≈12–15 s) | Mientras carga: «Traduce el perfil al inglés, lo convierte en vector con e5 y lo compara contra 110,928 vacantes.» | 15 s |
| 4 | Vacante #1: insignias y **¿Por qué te la recomendamos?** | «No muestra números técnicos: coincidencia muy alta y qué preferencias cumple.» | 40 s |
| 5 | **Me interesa** en una vacante y **No me interesa** en otra → **Deshacer** | «La lista se reajusta: las flechas dicen cuántos lugares subió o bajó cada una (Rocchio).» | 45 s |
| 6 | Selector **México, en vivo** | «Vacantes reales de la Ciudad de México, de LinkedIn, Indeed, Computrabajo…, medidas con la misma regla.» | 30 s |
| 7 | **Armar mi CV** en una vacante (catálogo #2 «Data Analyst» o una en vivo) | «Lo que pide la vacante: lo que tiene, lo que menciona en otro lado y lo que le falta. Lo que falta no entra al CV.» | 45 s |
| 8 | Bajar al CV: la experiencia de ventas queda al final → **Descargar PDF** y abrirlo | «Solo usa lo que ella escribió, ordenado para esta vacante. PDF de una página.» | 45 s |
| 9 | (Si hay tiempo) Barra lateral → **Detalle técnico** → **Simular que la API no responde** | «Si la API cae, la app muestra lo último guardado y lo marca.» | 30 s |
| 10 | Volver a la presentación (diapositiva 13) | — | — |

## Si algo falla
| Problema | Qué hacer |
|---|---|
| El motor tarda o la búsqueda se congela | Cambiar a la pestaña `?demo=1` (ya buscada). |
| La API en vivo no responde o no hay cuota | Seguir: la app muestra lo guardado («No pudimos consultar… te mostramos las que guardamos el …»). |
| Sin internet | El catálogo y el CV funcionan locales; las vacantes en vivo salen de la caché, marcadas como guardadas. |
| Gemini da error | Es opcional; el CV por reglas ya está completo. No usarlo en vivo si no respondió en la mañana. |
| La descarga del PDF no abre | Mostrar el CV en el editor; el PDF se puede abrir después desde Descargas. |

## Ensayo
- 2026-11-18, ensayo técnico en Chrome con `PC_SIN_RED=1` (0 llamadas), servidor recién arrancado: pasos 1→5 al
  instante (0.2 s cada uno); **buscar 15.1 s** (en frío); Me interesa 0.6 s; No me interesa 0.6 s; Deshacer 0.2 s;
  «México, en vivo» 0.2 s (9 de 10 vacantes de CDMX, de la caché); **Armar mi CV 4.6 s** (vacante en vivo: tiene SQL,
  Python y Visualización de datos; le falta R); Volver 0.2 s; simular caída 0.6 s (muestra el aviso de guardadas);
  `?demo=1` carga ya buscado en menos de 8 s. Sin errores. La descarga del PDF no se probó en el navegador (el PDF
  se genera con la misma función revisada en el bloque 6).
- [ ] Ensayo del usuario de principio a fin, con cronómetro (presentación + demo).
