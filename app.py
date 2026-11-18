"""Primera chamba · app Streamlit. Ejecutar con `streamlit run app.py`.

Diseño: página clara con la tarjeta del formulario en negro (formulario por pasos con barra de avance), títulos en
monoespaciada y resultados en tarjetas blancas. El tema base está en `.streamlit/config.toml`; los detalles, en ESTILOS.
"""
from datetime import datetime
from html import escape

import streamlit as st

from primera_chamba import config
from primera_chamba.motor import (BONO, CANDIDATOS, MODALIDADES, NIVEL_ES, NIVELES, TIPO_ES, TIPOS, Motor, Perfil,
                                  coincidencia, consulta_en, descripciones)

st.set_page_config(page_title="Primera chamba", page_icon=":material/work:", layout="centered", initial_sidebar_state="collapsed")
ss = st.session_state
SIN_NIVEL = "(sin preferencia)"

ESTILOS = """
<style>
:root {
  --tinta: #0b0b0c; --tinta-2: #5b5b61; --tinta-3: #8a8a90; --borde: #e4e4e1; --blanco: #ffffff;
  --negro-1: #141416; --negro-2: #1c1c1f; --negro-borde: #2b2b30; --negro-tinta: #ececf0; --negro-tinta-2: #a1a1aa;
}
[data-testid="stDecoration"] { display: none; }
.block-container { padding-top: 4.5rem; max-width: 760px; }

/* Encabezado */
.pc-marca { font-family: "JetBrains Mono", monospace; font-weight: 600; font-size: 2.1rem; letter-spacing: .01em;
            color: var(--tinta); margin: 0; line-height: 1.15; }
.pc-sub { color: var(--tinta-2); margin: .35rem 0 1.6rem; font-size: 1rem; }
.pc-seccion { font-family: "JetBrains Mono", monospace; font-weight: 600; font-size: 1.25rem; color: var(--tinta);
              margin: 2rem 0 .2rem; }

/* Tarjeta oscura del formulario */
.st-key-asistente { background: var(--negro-1); border: 1px solid var(--negro-borde); border-radius: 18px;
                    padding: 0 1.75rem 1.4rem; box-shadow: 0 28px 60px -24px rgba(0,0,0,.45); overflow: hidden; }
.pc-avance { height: 4px; background: var(--negro-borde); margin: 0 -1.75rem 1.4rem; }
.pc-avance > div { height: 100%; background: var(--blanco); border-radius: 0 4px 4px 0; transition: width .3s; }
.pc-paso { font-family: "JetBrains Mono", monospace; font-size: .72rem; color: var(--negro-tinta-2);
           letter-spacing: .08em; text-transform: uppercase; margin-bottom: .3rem; }
.pc-titulo { color: var(--negro-tinta); font-weight: 600; font-size: 1.35rem; margin: 0; }
.pc-desc { color: var(--negro-tinta-2); font-size: .92rem; margin: .1rem 0 .6rem; }
.st-key-asistente label p { color: #d4d4d8 !important; font-size: .82rem; font-weight: 500; }
.st-key-asistente [data-testid="stTextInputRootElement"], .st-key-asistente [data-testid="stTextAreaRootElement"],
.st-key-asistente [data-testid="stNumberInputContainer"], .st-key-asistente [data-testid="stSelectbox"] [role="group"],
.st-key-asistente [data-testid="stMultiSelect"] [role="group"] {
  background: var(--negro-2) !important; border-color: var(--negro-borde) !important; }
.st-key-asistente [data-testid="stTextInputRootElement"]:focus-within, .st-key-asistente [data-testid="stTextAreaRootElement"]:focus-within,
.st-key-asistente [data-testid="stNumberInputContainer"]:focus-within, .st-key-asistente [role="group"]:focus-within {
  border-color: #6b6b73 !important; }
.st-key-asistente input, .st-key-asistente textarea, .st-key-asistente [role="group"] * {
  color: var(--negro-tinta) !important; -webkit-text-fill-color: var(--negro-tinta); }
.st-key-asistente input::placeholder, .st-key-asistente textarea::placeholder {
  color: #6b6b73 !important; -webkit-text-fill-color: #6b6b73; }
.st-key-asistente [data-testid="stIconMaterial"], .st-key-asistente [data-testid="stSelectboxIcon"] * {
  color: #8a8a93 !important; -webkit-text-fill-color: #8a8a93; }
.st-key-asistente [data-testid="stNumberInputStepDown"], .st-key-asistente [data-testid="stNumberInputStepUp"] {
  background: var(--negro-2) !important; color: var(--negro-tinta-2) !important; }
.st-key-asistente [data-baseweb="tag"] { background: #2e2e34 !important; }
.st-key-asistente [data-baseweb="tag"] span { color: var(--negro-tinta) !important; }
.st-key-asistente [data-testid="stTooltipIcon"] svg { color: #6b6b73; }
.st-key-asistente [data-testid="stBaseButton-primary"] {
  background: var(--blanco); color: var(--tinta); border: none; border-radius: 10px; font-weight: 600;
  padding: .45rem 1.15rem; box-shadow: 0 6px 18px -8px rgba(255,255,255,.35); }
.st-key-asistente [data-testid="stBaseButton-primary"]:hover { background: #e7e7ea; color: var(--tinta); }
.st-key-asistente [data-testid="stBaseButton-primary"] p { color: var(--tinta) !important; }
.st-key-asistente [data-testid="stBaseButton-tertiary"] p,
.st-key-asistente [data-testid="stBaseButton-tertiary"] span { color: var(--negro-tinta-2) !important; }
.st-key-asistente [data-testid="stBaseButton-tertiary"]:hover p { color: var(--negro-tinta) !important; }
.st-key-asistente [data-testid="stAlert"] { background: #2a1d1d; }
.st-key-asistente [data-testid="stAlert"] p { color: #fca5a5 !important; }

/* Resumen del perfil y tarjetas de vacantes (claras) */
[class*="st-key-vac_"] { background: var(--blanco); border: 1px solid var(--borde) !important;
  border-radius: 14px; box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px -16px rgba(0,0,0,.18); }
.st-key-resumen { background: var(--negro-1); border: 1px solid var(--negro-borde); border-radius: 14px;
  padding: .9rem 1.1rem; box-shadow: 0 18px 40px -22px rgba(0,0,0,.45); }
.st-key-resumen p { color: var(--negro-tinta-2) !important; }
.st-key-resumen strong { color: var(--negro-tinta) !important; }
.st-key-resumen [data-testid="stBaseButton-secondary"] { background: var(--blanco); border: none; border-radius: 10px; }
.st-key-resumen [data-testid="stBaseButton-secondary"] p,
.st-key-resumen [data-testid="stBaseButton-secondary"] span { color: var(--tinta) !important; font-weight: 600; }
[class*="st-key-vac_"] { padding: 1rem 1.2rem .6rem; }
.pc-vac-titulo { font-weight: 600; font-size: 1.08rem; color: var(--tinta); margin: 0; line-height: 1.3; }
.pc-vac-meta { color: var(--tinta-2); font-size: .86rem; margin: .15rem 0 .5rem; }
.pc-mov { font-family: "JetBrains Mono", monospace; font-size: .75rem; padding: .1rem .4rem; border-radius: 6px;
          margin-left: .4rem; vertical-align: middle; background: #f0f0ee; color: var(--tinta-2); }
.pc-coinc { text-align: right; }
.pc-coinc .l { font-size: .68rem; color: var(--tinta-3); text-transform: uppercase; letter-spacing: .08em; }
.pc-coinc .n { font-family: "JetBrains Mono", monospace; font-weight: 600; font-size: 1.15rem; color: var(--tinta);
               margin: .1rem 0 .35rem; }
.pc-coinc .b { display: inline-flex; gap: 3px; }
.pc-coinc .b span { width: 16px; height: 5px; border-radius: 3px; background: #e4e4e1; }
.pc-coinc .b span.on { background: var(--tinta); }
.pc-nota { color: var(--negro-tinta-2); font-size: .8rem; line-height: 1.45; margin: -.5rem 0 .2rem; }
.pc-nota b { color: var(--negro-tinta); font-weight: 600; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) { background: #ececea; border: 1px solid var(--borde); }
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] * { color: var(--tinta) !important; }
[class*="st-key-acc_"] { border-top: 1px solid var(--borde); padding-top: .55rem; margin-top: .1rem; }
[class*="st-key-acc_"] [data-testid="stBaseButton-secondary"] { border-radius: 9px; font-size: .88rem; }
[class*="st-key-acc_"] [data-testid="stBaseButton-primary"] { border-radius: 9px; font-size: .88rem; }
.pc-pos { font-family: "JetBrains Mono", monospace; color: var(--tinta-3); font-size: .8rem; }
[class*="st-key-vac_"] [data-testid="stExpander"] details { border-color: var(--borde); }
</style>
"""

EJEMPLO = {
    "puesto": "Analista de datos",
    "nivel": "Sin experiencia / recién egresado",
    "habilidades": "SQL, Python, Excel, Power BI, estadística, visualización de datos",
    "ubicacion": "",
    "modalidad": "Remoto",
    "sueldo": 25000,
    "tipos": ["Tiempo completo"],
    "experiencias": "Servicio social en el IIMAS: limpié y analicé una base de 50 mil registros con Python.\n"
                    "Proyecto escolar: tablero en Power BI con indicadores de ventas.",
    "educacion": "Licenciatura en Ciencia de Datos, UNAM (2022–2026)",
    "descripcion": "Quiero empezar en un equipo de datos donde pueda aprender y trabajar con SQL y Python.",
}
VACIO = {"puesto": "", "nivel": SIN_NIVEL, "habilidades": "", "ubicacion": "", "modalidad": MODALIDADES[0],
         "sueldo": 0, "tipos": [], "experiencias": "", "educacion": "", "descripcion": ""}
PASOS = {
    1: ("Tu puesto", "Empecemos por lo básico.", ["puesto", "nivel", "habilidades"]),
    2: ("Preferencias", "¿Dónde y cómo quieres trabajar?", ["ubicacion", "modalidad", "sueldo", "tipos"]),
    3: ("Para tu CV", "Cuéntanos de ti. Esto no cambia el ranking: se usa para armar tu CV.",
        ["experiencias", "educacion", "descripcion"]),
}


@st.cache_resource(show_spinner="Cargando el motor: modelo e5 e índice de 110,928 vacantes…")
def motor() -> Motor:
    return Motor()


@st.cache_data(show_spinner=False, max_entries=20)
def textos(ids: tuple[int, ...]) -> dict[int, str]:
    return descripciones(list(ids))


# ---------------- estado ----------------
for k, v in {"gustan": [], "no_gustan": [], "lugares_previos": {}, "paso": 1, "datos": dict(VACIO),
             "editando": True}.items():
    ss.setdefault(k, v)


def guardar_paso():
    """Copia los campos visibles a `datos` (Streamlit borra el estado de los campos que dejan de mostrarse)."""
    for campo in PASOS[ss.paso][2]:
        if f"w_{campo}" in ss:
            ss.datos[campo] = ss[f"w_{campo}"]


def ir_a(paso: int):
    guardar_paso()
    ss.error_paso = None
    if paso > ss.paso == 1 and (not ss.datos["puesto"].strip() or not ss.datos["habilidades"].strip()):
        ss.error_paso = "Escribe el puesto que buscas y al menos una habilidad."
        return
    ss.paso = paso
    cargar_paso(paso)


def cargar_paso(paso: int):
    for campo in PASOS[paso][2]:
        ss[f"w_{campo}"] = ss.datos[campo]


def llenar_ejemplo():
    ss.datos = dict(EJEMPLO)
    for campo, valor in EJEMPLO.items():
        ss[f"w_{campo}"] = valor


def calificar(idx: int, gusta: bool):
    ss.lugares_previos = dict(ss.get("lugares_actuales", {}))
    ss.gustan = [i for i in ss.gustan if i != idx]
    ss.no_gustan = [i for i in ss.no_gustan if i != idx]
    (ss.gustan if gusta else ss.no_gustan).append(idx)


def quitar_interes(idx: int):
    ss.lugares_previos = dict(ss.get("lugares_actuales", {}))
    ss.gustan = [i for i in ss.gustan if i != idx]


def reiniciar_calificaciones():
    ss.gustan, ss.no_gustan, ss.lugares_previos = [], [], {}


def editar_perfil():
    ss.editando, ss.paso = True, 1
    cargar_paso(1)


def buscar():
    guardar_paso()
    d = ss.datos
    perfil = Perfil(
        puesto=d["puesto"], habilidades=[h.strip() for h in d["habilidades"].split(",") if h.strip()],
        nivel=None if d["nivel"] == SIN_NIVEL else d["nivel"], ubicacion=d["ubicacion"], modalidad=d["modalidad"],
        sueldo_mxn_mensual=float(d["sueldo"]) or None, tipos_empleo=d["tipos"],
        experiencias=d["experiencias"], educacion=d["educacion"], descripcion=d["descripcion"])
    consulta, traducido = consulta_en(perfil)
    ss.q0 = motor().vector(consulta)
    ss.mi_perfil, ss.consulta, ss.traducido = perfil, consulta, traducido
    reiniciar_calificaciones()
    ss.lugares_actuales, ss.editando = {}, False


# `?demo=1` abre la app con el perfil de ejemplo ya buscado (respaldo para la presentación).
if st.query_params.get("demo") == "1" and "q0" not in ss:
    llenar_ejemplo()
    with st.spinner("Cargando la demo…"):
        buscar()

# ---------------- barra lateral ----------------
with st.sidebar:
    st.markdown("### Ajustes")
    tipo_cambio = st.number_input("Tipo de cambio (MXN por USD)", value=config.TIPO_CAMBIO_MXN_USD, step=0.1,
                                  format="%.4f", help="FIX de Banxico del 17/11/2026. Solo se usa para comparar tu "
                                                      "sueldo esperado con los sueldos del catálogo (USD al año).")
    n_mostrar = st.slider("Vacantes a mostrar", 5, 50, 15, step=5)
    if ss.gustan or ss.no_gustan:
        st.button("Borrar mis calificaciones", on_click=reiniciar_calificaciones)
    st.divider()
    st.caption("**Catálogo:** 110,928 vacantes reales de LinkedIn (EE. UU., 2023–2024).  \n"
               "**Modelo:** multilingual-e5-small con tu perfil traducido al inglés. Se eligió en una evaluación "
               "fuera de línea con 1,000 perfiles contra TF-IDF, MiniLM, azar y popularidad.")

# ---------------- encabezado ----------------
st.html(ESTILOS)
st.html('<p class="pc-marca">Primera chamba</p>'
        '<p class="pc-sub">Dinos qué buscas y te recomendamos las vacantes que mejor encajan contigo. '
        'Marca las que te interesan y la lista se ajusta a ti.</p>')

# ---------------- formulario por pasos ----------------
if ss.editando or "q0" not in ss:
    paso = ss.paso
    titulo, desc, campos = PASOS[paso]
    for campo in campos:  # restaura lo escrito antes de volver a este paso
        ss.setdefault(f"w_{campo}", ss.datos[campo])
    with st.container(key="asistente"):
        st.html(f'<div class="pc-avance"><div style="width:{100 * paso / len(PASOS):.0f}%"></div></div>'
                f'<div class="pc-paso">Paso {paso} de {len(PASOS)}</div>'
                f'<p class="pc-titulo">{titulo}</p><p class="pc-desc">{desc}</p>')
        if paso == 1:
            st.text_input("Puesto que buscas", key="w_puesto", placeholder="Analista de datos", icon=":material/work:")
            st.selectbox("Nivel de experiencia", [SIN_NIVEL, *NIVELES], key="w_nivel",
                         icon=":material/signal_cellular_alt:")
            st.text_area("Habilidades, separadas por comas", key="w_habilidades", height=96,
                         placeholder="SQL, Python, Excel, atención a clientes…")
        elif paso == 2:
            st.text_input("Ubicación", key="w_ubicacion", placeholder="Ej. Austin, Texas",
                          icon=":material/location_on:")
            st.html('<p class="pc-nota">Escribe la ciudad, el estado o ambos, separados por coma. El estado puede ir '
                    'completo o abreviado: <b>Texas</b> o <b>TX</b>, <b>Nueva York</b> o <b>NY</b>. '
                    'Por ahora el catálogo es de vacantes en EE. UU.</p>')
            st.selectbox("Modalidad", MODALIDADES, key="w_modalidad", icon=":material/home_work:")
            st.number_input("Sueldo mensual esperado (MXN)", min_value=0, step=1000, key="w_sueldo",
                            icon=":material/payments:", help="0 = sin preferencia")
            st.multiselect("Tipo de empleo", list(TIPOS), key="w_tipos", placeholder="Todos")
        else:
            st.text_area("Experiencias y logros", key="w_experiencias", height=110,
                         placeholder="Servicio social, proyectos, trabajos… con cifras si las tienes.")
            c1, c2 = st.columns(2)
            c1.text_area("Educación", key="w_educacion", height=90, placeholder="Licenciatura en…")
            c2.text_area("Tu empleo ideal", key="w_descripcion", height=90, placeholder="Algo breve sobre ti…")
        if ss.get("error_paso"):
            st.error(ss.error_paso, icon=":material/error:")

        izq, der = st.columns(2, vertical_alignment="center")
        if paso > 1:
            izq.button("Atrás", type="tertiary", icon=":material/chevron_left:", on_click=ir_a, args=(paso - 1,))
        else:
            izq.button("Usar un perfil de ejemplo", type="tertiary", icon=":material/auto_awesome:",
                       on_click=llenar_ejemplo)
        with der.container(horizontal=True, horizontal_alignment="right"):
            if paso < len(PASOS):
                st.button("Continuar", type="primary", icon=":material/chevron_right:", icon_position="right",
                          on_click=ir_a, args=(paso + 1,))
            elif st.button("Buscar vacantes", type="primary", icon=":material/chevron_right:",
                           icon_position="right"):
                with st.spinner("Traduciendo tu perfil y buscando entre 110,928 vacantes…"):
                    buscar()
                st.rerun()

# ---------------- resultados ----------------
ICONO = {"✓": ":material/check:", "✗": ":material/close:", "–": ":material/remove:"}
COLOR = {"✓": "green", "✗": "orange", "–": "gray"}


def ordinal(n: int) -> str:
    return f"{n:,}.ª"


if "q0" in ss and not ss.editando:
    m, perfil = motor(), ss.mi_perfil
    calificadas = len(ss.gustan) + len(ss.no_gustan)
    q = m.rocchio(ss.q0, ss.gustan, ss.no_gustan) if calificadas else ss.q0
    r = m.rankear(q, perfil, excluir=ss.no_gustan, n=n_mostrar, tipo_cambio=tipo_cambio)
    desc = textos(tuple(int(j) for j in r["job_id"]))

    with st.container(key="resumen"):
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        partes = [f"**{perfil.puesto}**", ", ".join(perfil.habilidades[:4]) + ("…" if len(perfil.habilidades) > 4 else "")]
        if perfil.nivel:
            partes.append(perfil.nivel)
        if perfil.modalidad != "Me da igual":
            partes.append(perfil.modalidad)
        if perfil.ubicacion.strip():
            partes.append(perfil.ubicacion.strip())
        c1.markdown(" · ".join(partes))
        c2.button("Editar", icon=":material/edit:", on_click=editar_perfil, width="stretch")

    st.html('<p class="pc-seccion">Vacantes recomendadas</p>')
    with st.expander("¿Cómo elegimos estas vacantes?"):
        st.markdown(
            "1. **Leemos tu perfil.** Las vacantes del catálogo están en inglés, así que traducimos al inglés lo que "
            "escribiste.\n"
            "2. **Comparamos el significado, no solo las palabras.** Un modelo de lenguaje compara tu perfil con "
            "cada una de las 110,928 vacantes y entiende, por ejemplo, que *analista de datos* y *data analyst* son "
            "el mismo puesto. La **coincidencia** dice qué tanto se parece cada vacante a tu perfil.\n"
            f"3. **Subimos las que cumplen tus preferencias.** De las {CANDIDATOS} vacantes que más se parecen a tu "
            "perfil, ganan lugares las que cumplen lo que pediste: ubicación, modalidad, sueldo y experiencia.\n"
            "4. **Aprendemos de ti.** Cuando marcas *Me interesa*, buscamos más vacantes parecidas a esa; cuando "
            "marcas *No me interesa*, la quitamos y nos alejamos de las que se le parecen.")
        st.caption(f"Detalle técnico: modelo multilingual-e5-small; tu perfil se busca como «{ss.consulta}»"
                   f"{'' if ss.traducido else ' (sin traducir: el traductor no respondió)'}. Puntaje = similitud "
                   f"coseno estandarizada (z) + {BONO} por preferencia cumplida; retroalimentación con Rocchio "
                   f"(α = 1, β = 0.75, γ = 0.15).")
    if calificadas:
        st.info(f"Ajustamos la lista con lo que marcaste: {len(ss.gustan)} te interesan y {len(ss.no_gustan)} no. "
                "Las flechas indican cuántos lugares subió o bajó cada vacante.", icon=":material/tune:")

    previos = ss.lugares_previos
    ss.lugares_actuales = {int(j): i for i, j in enumerate(r["job_id"])}
    for i, f in r.iterrows():
        jid, idx = int(f["job_id"]), int(f["idx"])
        mov = ""
        if calificadas and previos:
            antes = previos.get(jid)
            mov = ("nueva" if antes is None else f"↑ {antes - i}" if antes > i else f"↓ {i - antes}" if antes < i
                   else "")
        interesa = idx in ss.gustan
        etiqueta, nivel_c = coincidencia(int(f["lugar_similitud"]))
        detalles = [f["company_name"] if isinstance(f["company_name"], str) else "Empresa no indicada",
                    f["location"], TIPO_ES.get(f["tipo_empleo"], f["tipo_empleo"])]
        if f["nivel"] in NIVEL_ES:
            detalles.append(NIVEL_ES[f["nivel"]])
        with st.container(key=f"vac_{jid}"):
            c1, c2 = st.columns([5, 1.3])
            with c1:
                st.html(f'<span class="pc-pos">#{i + 1}</span>'
                        f'{f"<span class=pc-mov>{mov}</span>" if mov else ""}'
                        f'{"<span class=pc-mov>Te interesa</span>" if interesa else ""}'
                        f'<p class="pc-vac-titulo">{escape(f["title"])}</p>'
                        f'<p class="pc-vac-meta">{escape(" · ".join(str(d) for d in detalles))}</p>')
                st.markdown(" ".join(f":{COLOR[e]}-badge[{ICONO[e]} {pref}]" for e, pref, _ in f["desglose"]))
            with c2:
                barras = "".join(f'<span class="{"on" if k < nivel_c else ""}"></span>' for k in range(4))
                st.html(f'<div class="pc-coinc"><div class="l">Coincidencia</div><div class="n">{etiqueta}</div>'
                        f'<div class="b">{barras}</div></div>')
            with st.expander("¿Por qué te la recomendamos?"):
                lugar = int(f["lugar_similitud"])
                parecido = ("Es la vacante que **más se parece a tu perfil** de las 110,928." if lugar == 1 else
                            f"De las 110,928 vacantes, es la **{ordinal(lugar)} que más se parece a tu perfil**.")
                lineas = [f"**Coincidencia {etiqueta.lower()}.** {parecido}", "", "**Lo que pediste:**"]
                for e, pref, texto in f["desglose"]:
                    lineas.append(f"- :{COLOR[e]}[{ICONO[e]}] **{pref}:** {texto}")
                st.markdown("\n".join(lineas))
                palabras = desc.get(jid, "").split()
                if palabras:
                    st.markdown("**Del anuncio:**")
                    st.caption(" ".join(palabras[:90]) + (" …" if len(palabras) > 90 else ""))
                fecha = datetime.fromtimestamp(f["listed_time"] / 1000).strftime("%d/%m/%Y")
                st.caption(f"Publicada el {fecha}. Detalle técnico: z = {f['z']:.2f}, coseno = {f['coseno']:.3f}, "
                           f"preferencias cumplidas = {f['cumplidas']}, puntaje = {f['puntaje']:.2f}.")
            with st.container(horizontal=True, vertical_alignment="center", key=f"acc_{jid}"):
                st.link_button("Ver anuncio", f["job_posting_url"], type="tertiary", icon=":material/open_in_new:",
                               icon_position="right")
                st.space("stretch")
                st.button("Te interesa" if interesa else "Me interesa", key=f"si_{jid}",
                          type="primary" if interesa else "secondary",
                          icon=":material/check_circle:" if interesa else ":material/check:",
                          on_click=quitar_interes if interesa else calificar,
                          args=(idx,) if interesa else (idx, True),
                          help="Quitar de las que te interesan" if interesa else
                          "Te mostraremos más vacantes parecidas a esta")
                st.button("No me interesa", key=f"no_{jid}", icon=":material/close:", on_click=calificar,
                          args=(idx, False), help="La quitamos de la lista y nos alejamos de las que se le parecen")
