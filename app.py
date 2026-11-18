"""Primera chamba · app Streamlit. Ejecutar con `streamlit run app.py`.

Diseño: página clara con la tarjeta del formulario en negro (formulario por pasos con barra de avance), títulos en
monoespaciada y resultados en tarjetas blancas. El tema base está en `.streamlit/config.toml`; los detalles, en ESTILOS.
"""
import re
from datetime import datetime
from html import escape

import streamlit as st

from primera_chamba import config, cv, en_vivo
from primera_chamba import habilidades as hab
from primera_chamba.motor import (BONO, CANDIDATOS, LUGAR_MAX_VIVAS, MODALIDADES, NIVEL_ES, NIVELES, TIPO_ES, TIPOS,
                                  Motor, Perfil, coincidencia, consulta_en, descripciones)

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
[class*="st-key-exp_"], [class*="st-key-edu_"] { background: #19191c; border: 1px solid var(--negro-borde);
  border-radius: 12px; padding: .75rem .9rem .2rem; }

/* Resumen del perfil y tarjetas de vacantes (claras) */
[class*="st-key-vac_"] { background: var(--blanco); border: 1px solid var(--borde) !important;
  border-radius: 14px; box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px -16px rgba(0,0,0,.18); }
.st-key-resumen { background: var(--negro-1); border: 1px solid var(--negro-borde); border-radius: 14px;
  padding: .9rem 1.1rem; box-shadow: 0 18px 40px -22px rgba(0,0,0,.45); }
.st-key-resumen p { color: var(--negro-tinta-2) !important; }
.st-key-cvcab { background: var(--negro-1); border: 1px solid var(--negro-borde); border-radius: 14px;
  padding: .9rem 1.1rem; box-shadow: 0 18px 40px -22px rgba(0,0,0,.45); }
.st-key-cvcab .pc-cv-l { color: var(--negro-tinta-2); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em;
  font-family: "JetBrains Mono", monospace; margin: 0; }
.st-key-cvcab .pc-cv-t { color: var(--negro-tinta); font-weight: 600; font-size: 1.05rem; margin: .1rem 0 0; }
.st-key-cvcab .pc-cv-m { color: var(--negro-tinta-2); font-size: .86rem; margin: 0; }
.st-key-cvcab [data-testid="stBaseButton-secondary"] { background: var(--blanco); border: none; border-radius: 10px; }
.st-key-cvcab [data-testid="stBaseButton-secondary"] p,
.st-key-cvcab [data-testid="stBaseButton-secondary"] span { color: var(--tinta) !important; font-weight: 600; }
.st-key-cveditor { background: var(--blanco); border: 1px solid var(--borde); border-radius: 14px; padding: 1rem 1.2rem .4rem;
  box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px -16px rgba(0,0,0,.18); }
.st-key-resumen strong { color: var(--negro-tinta) !important; }
.st-key-resumen [data-testid="stBaseButton-secondary"] { background: var(--blanco); border: none; border-radius: 10px; }
.st-key-resumen [data-testid="stBaseButton-secondary"] p,
.st-key-resumen [data-testid="stBaseButton-secondary"] span { color: var(--tinta) !important; font-weight: 600; }
[class*="st-key-vac_"] { padding: 1rem 1.2rem .6rem; }
.pc-vac-titulo { font-weight: 600; font-size: 1.08rem; color: var(--tinta); margin: 0; line-height: 1.3; }
.pc-vac-meta { color: var(--tinta-2); font-size: .86rem; margin: .15rem 0 .5rem; }
.pc-mov { font-family: "JetBrains Mono", monospace; font-size: .75rem; padding: .1rem .4rem; border-radius: 6px;
          margin-left: .4rem; vertical-align: middle; background: #f0f0ee; color: var(--tinta-2); }
.pc-vivo { font-family: "JetBrains Mono", monospace; font-size: .72rem; padding: .12rem .45rem; border-radius: 6px;
           margin-left: .4rem; vertical-align: middle; background: var(--negro-1); color: var(--negro-tinta); }
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
.st-key-deshacer { background: #ececea; border: 1px dashed #c9c9c5; border-radius: 14px; padding: .55rem .6rem .55rem 1.1rem; }
.pc-deshacer { margin: 0; color: var(--tinta-2); font-size: .92rem; }
.pc-deshacer b { color: var(--tinta); font-weight: 600; }
[class*="st-key-cmp_"] { background: #fbfbfa; border: 1px solid var(--borde); border-radius: 12px; padding: .8rem 1rem .4rem; }
[class*="st-key-desc_"] { border-bottom: 1px solid var(--borde); padding: .35rem 0; }
[class*="st-key-acc_"] { border-top: 1px solid var(--borde); padding-top: .55rem; margin-top: .1rem; }
[class*="st-key-acc_"] [data-testid="stBaseButton-secondary"] { border-radius: 9px; font-size: .88rem; }
[class*="st-key-acc_"] [data-testid="stBaseButton-primary"] { border-radius: 9px; font-size: .88rem; }
.pc-pos { font-family: "JetBrains Mono", monospace; color: var(--tinta-3); font-size: .8rem; }
[class*="st-key-vac_"] [data-testid="stExpander"] details { border-color: var(--borde); }
</style>
"""

MAX_EXP, MAX_EDU = 4, 3
CAMPOS_EXP = ["puesto", "tipo", "org", "periodo", "logros"]
CAMPOS_EDU = ["titulo", "inst", "periodo", "detalle"]
EJEMPLO = {
    "puesto": "Analista de datos",
    "nivel": "Sin experiencia / recién egresado",
    "habilidades": "SQL, Python, Excel, Power BI, estadística, visualización de datos, trabajo en equipo",
    "ubicacion": "Ciudad de México",
    "modalidad": "Remoto",
    "sueldo": 25000,
    "tipos": ["Tiempo completo"],
    "nombre": "Ana López Hernández", "correo": "ana.lopez@example.com", "telefono": "55 1234 5678",
    "enlace": "portafolio.example.com/ana",
    "resumen": "Recién egresada de Ciencia de Datos. Me gusta encontrar patrones en los datos y explicarlos de "
               "forma sencilla.",
    "descripcion": "Quiero empezar en un equipo de datos donde pueda aprender y trabajar con SQL y Python.",
    "n_exp": 3,
    "exp0_puesto": "Vendedora de medio tiempo", "exp0_tipo": "Empleo", "exp0_org": "Tienda departamental",
    "exp0_periodo": "2022 – 2023", "exp0_logros": "Atendí a clientes en piso de venta.\nCuadré la caja al cierre del turno.",
    "exp1_puesto": "Apoyo en análisis de datos", "exp1_tipo": "Servicio social", "exp1_org": "IIMAS, UNAM",
    "exp1_periodo": "ene 2025 – jun 2025",
    "exp1_logros": "Presenté los resultados al equipo de investigación.\n"
                   "Limpié y analicé una base de 50 mil registros con Python.\n"
                   "Automaticé en Excel un reporte semanal que antes se hacía a mano.",
    "exp2_puesto": "Tablero de indicadores de ventas", "exp2_tipo": "Proyecto", "exp2_org": "Proyecto escolar, UNAM",
    "exp2_periodo": "2024", "exp2_logros": "Diseñé un tablero en Power BI con indicadores de ventas.\n"
                                           "Escribí las consultas en SQL que alimentan el tablero.",
    "n_edu": 1,
    "edu0_titulo": "Licenciatura en Ciencia de Datos", "edu0_inst": "UNAM", "edu0_periodo": "2022 – 2026",
    "edu0_detalle": "Promedio 9.1. Materias: estadística, bases de datos y aprendizaje automático.",
    "idiomas": "Español: nativo\nInglés: intermedio (B2)",
    "cursos": "Curso de SQL para análisis de datos (en línea, 2024)",
    "otros": "Voluntariado: asesorías de matemáticas a estudiantes de secundaria (2023)",
}
VACIO = {"puesto": "", "nivel": SIN_NIVEL, "habilidades": "", "ubicacion": "", "modalidad": MODALIDADES[0],
         "sueldo": 0, "tipos": [], "nombre": "", "correo": "", "telefono": "", "enlace": "", "resumen": "",
         "descripcion": "", "n_exp": 1, "n_edu": 1, "idiomas": "", "cursos": "", "otros": ""}
VACIO |= {f"exp{i}_{c}": ("Empleo" if c == "tipo" else "") for i in range(MAX_EXP) for c in CAMPOS_EXP}
VACIO |= {f"edu{i}_{c}": "" for i in range(MAX_EDU) for c in CAMPOS_EDU}
EJEMPLO = VACIO | EJEMPLO
PASOS = {
    1: ("Tu puesto", "Empecemos por lo básico.", ["puesto", "nivel", "habilidades"]),
    2: ("Preferencias", "¿Dónde y cómo quieres trabajar?", ["ubicacion", "modalidad", "sueldo", "tipos"]),
    3: ("Sobre ti", "Desde aquí todo es para tu CV y es opcional: no cambia el ranking.",
        ["nombre", "correo", "telefono", "enlace", "resumen", "descripcion"]),
    4: ("Tu experiencia", "Empleos, prácticas, servicio social, proyectos escolares o voluntariado. Cuenta qué hiciste "
                          "y qué lograste, con cifras si las tienes.", []),
    5: ("Educación y más", "Lo último: estudios, idiomas y cursos.", ["idiomas", "cursos", "otros"]),
}


def campos(paso: int) -> list[str]:
    """Campos visibles del paso (las experiencias y los estudios cambian según cuántos agregó el usuario)."""
    if paso == 4:
        return [f"exp{i}_{c}" for i in range(ss.datos["n_exp"]) for c in CAMPOS_EXP]
    if paso == 5:
        return [f"edu{i}_{c}" for i in range(ss.datos["n_edu"]) for c in CAMPOS_EDU] + PASOS[5][2]
    return PASOS[paso][2]


@st.cache_resource(show_spinner="Cargando el motor: modelo e5 e índice de 110,928 vacantes…")
def motor() -> Motor:
    return Motor()


@st.cache_data(show_spinner=False, max_entries=20)
def textos(ids: tuple[int, ...]) -> dict[int, str]:
    return descripciones(list(ids))


# ---------------- estado ----------------
for k, v in {"gustan": [], "no_gustan": [], "lugares_previos": {}, "ultimo_descarte": None, "paso": 1, "datos": dict(VACIO),
             "editando": True, "vivo_res": None, "vivas": None, "vec_vivas": {}, "cv_para": None, "cv_bases": {},
             "cv_notas": {}, "cv_mia": {}}.items():
    ss.setdefault(k, v)


def guardar_paso():
    """Copia los campos visibles a `datos` (Streamlit borra el estado de los campos que dejan de mostrarse)."""
    for campo in campos(ss.paso):
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
    for campo in campos(paso):
        ss[f"w_{campo}"] = ss.datos[campo]


def agregar(grupo: str):
    """Agrega una experiencia ("exp") o un estudio ("edu") al paso actual."""
    guardar_paso()
    ss.datos[f"n_{grupo}"] += 1
    cargar_paso(ss.paso)


def quitar(grupo: str, i: int):
    """Quita la entrada i y recorre las siguientes; si es la única, solo la vacía."""
    guardar_paso()
    cs, n = (CAMPOS_EXP, ss.datos["n_exp"]) if grupo == "exp" else (CAMPOS_EDU, ss.datos["n_edu"])
    for j in range(i, n - 1):
        for c in cs:
            ss.datos[f"{grupo}{j}_{c}"] = ss.datos[f"{grupo}{j + 1}_{c}"]
    for c in cs:
        ss.datos[f"{grupo}{n - 1}_{c}"] = VACIO[f"{grupo}{n - 1}_{c}"]
    ss.datos[f"n_{grupo}"] = max(1, n - 1)
    cargar_paso(ss.paso)


def llenar_ejemplo():
    ss.datos = dict(EJEMPLO)
    cargar_paso(ss.paso)


def calificar(idx: int, gusta: bool):
    ss.lugares_previos = dict(ss.get("lugares_actuales", {}))
    ss.gustan = [i for i in ss.gustan if i != idx]
    ss.no_gustan = [i for i in ss.no_gustan if i != idx]
    (ss.gustan if gusta else ss.no_gustan).append(idx)
    ss.ultimo_descarte = None if gusta else idx


def quitar_interes(idx: int):
    ss.lugares_previos = dict(ss.get("lugares_actuales", {}))
    ss.gustan = [i for i in ss.gustan if i != idx]
    ss.ultimo_descarte = None


def recuperar(idx: int):
    """Devuelve a la lista una vacante descartada (por error o por cambio de opinión)."""
    ss.lugares_previos = dict(ss.get("lugares_actuales", {}))
    ss.no_gustan = [i for i in ss.no_gustan if i != idx]
    ss.ultimo_descarte = None


def reiniciar_calificaciones():
    ss.gustan, ss.no_gustan, ss.lugares_previos, ss.ultimo_descarte = [], [], {}, None


def editar_perfil():
    ss.editando, ss.paso = True, 1
    cargar_paso(1)


def buscar():
    guardar_paso()
    d = ss.datos
    perfil = Perfil(
        puesto=d["puesto"], habilidades=[h.strip() for h in d["habilidades"].split(",") if h.strip()],
        nivel=None if d["nivel"] == SIN_NIVEL else d["nivel"], ubicacion=d["ubicacion"], modalidad=d["modalidad"],
        sueldo_mxn_mensual=float(d["sueldo"]) or None, tipos_empleo=d["tipos"])
    consulta, traducido = consulta_en(perfil)
    ss.q0 = motor().vector(consulta)
    ss.mi_perfil, ss.consulta, ss.traducido = perfil, consulta, traducido
    reiniciar_calificaciones()
    ss.lugares_actuales, ss.editando = {}, False
    ss.vivo_res, ss.vivas, ss.vec_vivas = None, None, {}
    ss.cv_para, ss.cv_bases, ss.cv_notas, ss.cv_mia = None, {}, {}, {}
    for k in [k for k in ss if str(k).startswith("cv_t_")]:  # textos editados del CV de la búsqueda anterior
        del ss[k]
    if ss.get("incluir_vivo", True):
        cargar_vivas()


def datos_cv() -> cv.DatosCV:
    """Lo que escribió el usuario, ya separado por entradas, para armar el CV."""
    d = ss.datos
    exps = [cv.Experiencia(d[f"exp{i}_puesto"].strip(), d[f"exp{i}_org"].strip(), d[f"exp{i}_periodo"].strip(),
                           d[f"exp{i}_tipo"], cv.lineas(d[f"exp{i}_logros"])) for i in range(d["n_exp"])]
    edus = [cv.Estudio(d[f"edu{i}_titulo"].strip(), d[f"edu{i}_inst"].strip(), d[f"edu{i}_periodo"].strip(),
                       d[f"edu{i}_detalle"].strip()) for i in range(d["n_edu"])]
    return cv.DatosCV(
        nombre=d["nombre"], puesto=d["puesto"].strip(), correo=d["correo"], telefono=d["telefono"],
        ciudad=d["ubicacion"].strip(), enlace=d["enlace"], resumen=d["resumen"], objetivo=d["descripcion"],
        habilidades=[h.strip() for h in d["habilidades"].split(",") if h.strip()],
        experiencias=[e for e in exps if e.puesto or e.organizacion or e.logros],
        estudios=[e for e in edus if e.titulo or e.institucion], idiomas=cv.lineas(d["idiomas"]),
        cursos=cv.lineas(d["cursos"]), otros=cv.lineas(d["otros"]))


def cargar_vivas(forzar: bool = False):
    """Vacantes en vivo de México para el perfil buscado (caché → JSearch → Adzuna → lo último guardado)."""
    if "mi_perfil" not in ss:
        return
    p = ss.mi_perfil
    ss.vivo_res = en_vivo.buscar(p.puesto, p.ubicacion, sin_red=ss.get("simular_caida", False), forzar=forzar)
    ss.vivas, ss.vec_vivas = motor().preparar_vivas(ss.vivo_res.vacantes)


def ficha(idx) -> tuple[str, str, str]:
    """(título, empresa, ubicación) de una vacante del catálogo (int) o en vivo (str)."""
    if isinstance(idx, str):
        v = ss.vivas[ss.vivas["idx"] == idx] if ss.vivas is not None and len(ss.vivas) else []
        if not len(v):
            return "Vacante en vivo", "", "México"
        v = v.iloc[0]
    else:
        v = motor().cat.iloc[idx]
    empresa = v["company_name"] if isinstance(v["company_name"], str) else "Empresa no indicada"
    return v["title"], empresa, v["location"]


def jid_de(idx):
    return idx if isinstance(idx, str) else int(motor().cat["job_id"].iloc[idx])


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
    st.toggle("Buscar también vacantes en vivo de México", value=True, key="incluir_vivo")
    if ss.gustan or ss.no_gustan:
        st.button("Borrar mis calificaciones", on_click=reiniciar_calificaciones)
    st.divider()
    st.caption("**Catálogo:** 110,928 vacantes reales de LinkedIn (EE. UU., 2023–2024).  \n"
               "**En vivo:** vacantes de México de LinkedIn, Indeed, Computrabajo y otras bolsas (JSearch; Adzuna "
               f"si falla). Se guardan {en_vivo.VIGENCIA_H} h para no gastar consultas.  \n"
               "**Modelo:** multilingual-e5-small con tu perfil traducido al inglés. Se eligió en una evaluación "
               "fuera de línea con 1,000 perfiles contra TF-IDF, MiniLM, azar y popularidad.")
    with st.expander("Detalle técnico"):
        st.caption(f"Puntaje = similitud coseno estandarizada contra el catálogo (z) + {BONO} por preferencia "
                   f"cumplida, entre las {CANDIDATOS} vacantes más parecidas. Coincidencia: Muy alta = top 50 por "
                   "similitud, Alta = top 500, Media = top 5,000. Retroalimentación con Rocchio (α = 1, β = 0.75, "
                   "γ = 0.15).")
        if "consulta" in ss:
            st.caption(f"Tu perfil se busca como: «{ss.consulta}»"
                       f"{'' if ss.traducido else ' (sin traducir: el traductor no respondió)'}.")
        st.caption("**En vivo:** cada vacante se compara con la misma consulta y se estandariza con el catálogo, así "
                   f"queda en la misma escala; entran las que estarían en el top {LUGAR_MAX_VIVAS:,} por similitud.")
        c = en_vivo.cuota()
        st.caption(f"Consultas a las APIs registradas: {c['total']}. JSearch: "
                   f"{'quedan ' + str(c['JSearch']) + ' de 200 este mes' if c['JSearch'] is not None else 'sin dato de cuota aún'}"
                   f"; Adzuna: {c['Adzuna']} este mes; Gemini: {c['Gemini']} hoy.")
        st.checkbox("Simular que la API no responde", key="simular_caida", on_change=cargar_vivas,
                    help="Prueba del respaldo: se muestran las vacantes en vivo guardadas la última vez.")
        if "mi_perfil" in ss and ss.get("incluir_vivo", True):
            st.button("Volver a consultar la API (gasta 1 consulta)", icon=":material/refresh:",
                      on_click=cargar_vivas, kwargs={"forzar": True})
        if ss.vivo_res is not None and ss.vivo_res.errores:
            st.caption("Último error: " + "; ".join(ss.vivo_res.errores))

# ---------------- encabezado ----------------
st.html(ESTILOS)
st.html('<p class="pc-marca">Primera chamba</p>'
        '<p class="pc-sub">Dinos qué buscas y te recomendamos las vacantes que mejor encajan contigo. '
        'Marca las que te interesan y la lista se ajusta a ti.</p>')

# ---------------- formulario por pasos ----------------
if ss.editando or "q0" not in ss:
    paso = ss.paso
    titulo, desc, _ = PASOS[paso]
    for campo in campos(paso):  # restaura lo escrito antes de volver a este paso
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
            st.text_input("Ubicación", key="w_ubicacion", placeholder="Ej. Ciudad de México o Austin, Texas",
                          icon=":material/location_on:")
            st.html('<p class="pc-nota">Escribe la ciudad, el estado o ambos, separados por coma. Buscamos en vivo '
                    'vacantes de México (<b>Ciudad de México</b>, <b>CDMX</b>, <b>Monterrey</b>…) y en un catálogo '
                    'de EE. UU., donde el estado puede ir completo o abreviado: <b>Texas</b> o <b>TX</b>.</p>')
            st.selectbox("Modalidad", MODALIDADES, key="w_modalidad", icon=":material/home_work:")
            st.number_input("Sueldo mensual esperado (MXN)", min_value=0, step=1000, key="w_sueldo",
                            icon=":material/payments:", help="0 = sin preferencia")
            st.multiselect("Tipo de empleo", list(TIPOS), key="w_tipos", placeholder="Todos")
        elif paso == 3:
            st.text_input("Nombre completo", key="w_nombre", placeholder="Como quieres que aparezca en tu CV",
                          icon=":material/person:")
            c1, c2 = st.columns(2)
            c1.text_input("Correo", key="w_correo", placeholder="nombre@correo.com", icon=":material/mail:")
            c2.text_input("Teléfono", key="w_telefono", placeholder="55 1234 5678", icon=":material/call:")
            st.text_input("LinkedIn, portafolio o GitHub", key="w_enlace", placeholder="linkedin.com/in/…",
                          icon=":material/link:")
            st.text_area("Preséntate en dos o tres frases", key="w_resumen", height=80,
                         placeholder="Qué estudiaste o a qué te dedicas y qué se te da bien.")
            st.text_area("Tu empleo ideal", key="w_descripcion", height=80,
                         placeholder="Qué tipo de trabajo buscas y qué quieres aprender.")
        elif paso == 4:
            n = ss.datos["n_exp"]
            for i in range(n):
                with st.container(key=f"exp_{i}"):
                    c1, c2 = st.columns([3, 2])
                    c1.text_input("Puesto o nombre del proyecto", key=f"w_exp{i}_puesto",
                                  placeholder="Practicante de análisis de datos")
                    c2.selectbox("Tipo", cv.TIPOS_EXPERIENCIA, key=f"w_exp{i}_tipo")
                    c1, c2 = st.columns([3, 2])
                    c1.text_input("Empresa, escuela u organización", key=f"w_exp{i}_org", placeholder="IIMAS, UNAM")
                    c2.text_input("Periodo", key=f"w_exp{i}_periodo", placeholder="ene 2025 – jun 2025")
                    st.text_area("Qué hiciste y qué lograste (uno por línea)", key=f"w_exp{i}_logros", height=96,
                                 placeholder="Limpié y analicé una base de 50 mil registros con Python.\n"
                                             "Presenté los resultados al equipo.")
                    st.button("Quitar esta experiencia", key=f"quitar_exp{i}", type="tertiary",
                              icon=":material/delete:", on_click=quitar, args=("exp", i))
            if n < MAX_EXP:
                st.button("Agregar otra experiencia", type="tertiary", icon=":material/add:", on_click=agregar,
                          args=("exp",))
        else:
            n = ss.datos["n_edu"]
            for i in range(n):
                with st.container(key=f"edu_{i}"):
                    c1, c2 = st.columns([3, 2])
                    c1.text_input("Carrera, bachillerato o certificado", key=f"w_edu{i}_titulo",
                                  placeholder="Licenciatura en Ciencia de Datos")
                    c2.text_input("Periodo", key=f"w_edu{i}_periodo", placeholder="2022 – 2026")
                    st.text_input("Escuela", key=f"w_edu{i}_inst", placeholder="UNAM")
                    st.text_input("Detalle (opcional)", key=f"w_edu{i}_detalle",
                                  placeholder="Promedio, materias relevantes, tesis, reconocimientos…")
                    if n > 1:
                        st.button("Quitar estos estudios", key=f"quitar_edu{i}", type="tertiary",
                                  icon=":material/delete:", on_click=quitar, args=("edu", i))
            if n < MAX_EDU:
                st.button("Agregar otros estudios", type="tertiary", icon=":material/add:", on_click=agregar,
                          args=("edu",))
            c1, c2 = st.columns(2)
            c1.text_area("Idiomas (uno por línea)", key="w_idiomas", height=90, placeholder="Inglés: intermedio (B2)")
            c2.text_area("Cursos y certificaciones (uno por línea)", key="w_cursos", height=90,
                         placeholder="Curso de SQL (en línea, 2024)")
            st.text_area("Otros: voluntariado, premios, actividades (uno por línea)", key="w_otros", height=70)
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


PARECIDO = {"Muy alta": "Se parece mucho a lo que buscas", "Alta": "Se parece bastante a lo que buscas",
            "Media": "Se parece en parte a lo que buscas", "Baja": "Se parece poco a lo que buscas"}


def lista(nombres: list[str], conj: str = "y") -> str:
    nombres = [f"tu {n.lower()}" for n in nombres]
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + f" {conj} " + nombres[-1]


def resumen(desglose, etiqueta: str, lugar: int, en_lista: bool = True, viva: bool = False) -> str:
    """Interpretación en dos frases: qué tanto se parece y qué cumple de lo que pediste."""
    cumple = [p for e, p, _ in desglose if e == "✓"]
    no_cumple = [p for e, p, _ in desglose if e == "✗"]
    pidio = [p for e, p, t in desglose if not t.startswith("No indicaste")]
    lugar_txt = ("es la más parecida" if lugar == 1 else "es la menos parecida" if lugar >= 110928
                 else f"es la {ordinal(lugar)} más parecida")
    frases = [f"{PARECIDO[etiqueta]}: {lugar_txt} de las 110,928 vacantes."]
    if viva:  # no es parte del catálogo: se dice a qué altura del catálogo quedaría
        frases = [f"{PARECIDO[etiqueta]}: quedaría como la {ordinal(lugar)} más parecida entre las 110,928 vacantes "
                  "del catálogo."]
    if cumple and no_cumple:
        frases.append(f"Cumple con {lista(cumple)}, pero no con {lista(no_cumple, 'ni')}.")
    elif cumple:
        frases.append(f"Cumple con {lista(cumple)}.")
    elif no_cumple:
        frases.append(f"No cumple con {lista(no_cumple, 'ni')}.")
    elif pidio:
        frases.append("El anuncio no da datos para comparar tus preferencias.")
    if en_lista and etiqueta == "Baja" and cumple:
        frases.append("Aparece en tu lista porque cumple con lo que pediste.")
    return f"**En resumen:** {' '.join(frases)}"


# ---------------- CV para una vacante ----------------
def abrir_cv(idx):
    ss.cv_para = idx


def cerrar_cv():
    ss.cv_para = None


def clave_cv(jid, campo: str) -> str:
    return f"cv_t_{jid}_{campo}"


def texto_y_vector(idx) -> tuple[str, object]:
    """Descripción completa y vector de la vacante (catálogo o en vivo) para ordenar el CV y buscar habilidades."""
    m = motor()
    if isinstance(idx, str):
        f = ss.vivas[ss.vivas["idx"] == idx].iloc[0]
        return f"{f['title']}. {f['descripcion']}", ss.vec_vivas[idx]
    jid = int(m.cat["job_id"].iloc[idx])
    return f"{m.cat['title'].iloc[idx]}. {textos((jid,)).get(jid, '')}", m.E[idx]


def textos_cv(jid) -> tuple[dict[str, str], dict[str, str]]:
    enc = {k: ss.get(clave_cv(jid, k), "") for k in ("nombre", "titular", "contacto")}
    return enc, {k: ss.get(clave_cv(jid, k), "") for k in cv.SECCIONES}


def restablecer_cv(jid):
    base = ss.cv_bases[jid]
    for k, t in (base.encabezado | base.secciones).items():
        ss[clave_cv(jid, k)] = t
    ss.cv_mia.pop(jid, None)
    ss.cv_notas[jid] = "Volvimos al CV armado automáticamente."


def pulir(jid):
    _, sec = textos_cv(jid)
    tuyo = datos_cv().todo_el_texto() + "\n" + "\n".join(sec.values())  # lo editado también es del usuario
    with st.spinner("La IA está mejorando la redacción…"):
        nueva, nota = cv.pulir_con_gemini(sec, tuyo)
    ss.cv_notas[jid] = nota
    if nueva:
        ss.cv_mia[jid] = {k: sec[k] for k in nueva}
        for k, t in nueva.items():
            ss[clave_cv(jid, k)] = t


def volver_a_mi_version(jid):
    for k, t in ss.cv_mia.pop(jid, {}).items():
        ss[clave_cv(jid, k)] = t
    ss.cv_notas[jid] = "Volvimos a tu versión."


def insignias(nombres: list[str], color: str, icono: str) -> str:
    return " ".join(f":{color}-badge[{icono} {n}]" for n in nombres)


AYUDA_CV = {
    "experiencia": "Cada experiencia: una línea «Puesto · Organización · Periodo» y debajo sus logros, cada uno con "
                   "«- ». Deja una línea en blanco entre experiencias.",
    "educacion": "Cada estudio: una línea «Carrera · Escuela · Periodo» y, si quieres, un detalle con «- ».",
}
ALTURA_CV = {"perfil": 136, "experiencia": 330, "educacion": 110, "habilidades": 76, "idiomas": 68, "cursos": 90,
             "otros": 76}

if "q0" in ss and not ss.editando and ss.get("cv_para") is not None:
    idx = ss.cv_para
    if isinstance(idx, str) and (ss.vivas is None or not ss.vivas["idx"].eq(idx).any()):
        ss.cv_para = None  # la vacante en vivo ya no está (p. ej., se volvió a consultar la API)
        st.rerun()
    jid = jid_de(idx)
    titulo, empresa, ubic = ficha(idx)
    if jid not in ss.cv_bases:
        with st.spinner("Armando tu CV para esta vacante…"):
            texto, vec = texto_y_vector(idx)
            ss.cv_bases[jid] = cv.armar(datos_cv(), vec, texto, motor().vectores)
    base = ss.cv_bases[jid]
    for k, t in (base.encabezado | base.secciones).items():
        ss.setdefault(clave_cv(jid, k), t)

    with st.container(key="cvcab"):
        c1, c2 = st.columns([3, 2], vertical_alignment="center")
        c1.html(f'<p class="pc-cv-l">Tu CV para</p><p class="pc-cv-t">{escape(titulo)}</p>'
                f'<p class="pc-cv-m">{escape(empresa)} · {escape(str(ubic))}</p>')
        with c2.container(horizontal=True, horizontal_alignment="right"):
            st.button("Editar", icon=":material/edit:", on_click=editar_perfil, help="Cambiar lo que escribiste")
            st.button("Volver", icon=":material/arrow_back:", on_click=cerrar_cv, help="Volver a las vacantes")

    st.html('<p class="pc-seccion">Lo que pide esta vacante</p>')
    h = base.habilidades
    if not any(h.values()):
        st.caption("El anuncio no menciona ninguna de las habilidades que sabemos reconocer, así que no hay nada que "
                   "comparar.")
    if h["tienes"]:
        st.markdown("**Las tienes y van en tu CV:** " + insignias(h["tienes"], "green", ":material/check:"))
    if h["en_tu_texto"]:
        st.markdown("**Las mencionas en tu experiencia o tus estudios:** "
                    + insignias(h["en_tu_texto"], "blue", ":material/info:"))
        st.caption("Ya aparecen donde las escribiste. Si las dominas, agrégalas a tus habilidades en «Editar».")
    if h["faltan"]:
        faltan = sorted(h["faltan"], key=lambda n: hab.tipo_de(n) != hab.TECNICA)
        st.markdown("**No están en tu perfil:** " + insignias(faltan, "orange", ":material/close:"))
        st.caption("No las pusimos en tu CV porque no las escribiste. Si sí las tienes, agrégalas en «Editar»; si "
                   "no, pueden ser lo siguiente que aprendas.")

    st.html('<p class="pc-seccion">Tu CV</p>')
    st.caption("Lo armamos solo con lo que escribiste, ordenado según lo que pide la vacante. Cámbialo como quieras "
               "antes de descargarlo; si dejas una sección vacía, no sale en el PDF.")
    with st.container(key="cveditor"):
        c1, c2 = st.columns(2)
        c1.text_input("Nombre", key=clave_cv(jid, "nombre"), persist_state="page")
        c2.text_input("Titular", key=clave_cv(jid, "titular"), persist_state="page", help="Va debajo de tu nombre.")
        st.text_input("Contacto", key=clave_cv(jid, "contacto"), persist_state="page")
        for sec, titulo_sec in cv.SECCIONES.items():
            st.text_area(titulo_sec, key=clave_cv(jid, sec), height=ALTURA_CV[sec], persist_state="page",
                         help=AYUDA_CV.get(sec))

    if config.hay_gemini():
        with st.container(horizontal=True, vertical_alignment="center"):
            st.button("Mejorar la redacción con IA", icon=":material/auto_fix_high:", on_click=pulir, args=(jid,))
            if jid in ss.cv_mia:
                st.button("Volver a mi versión", type="tertiary", icon=":material/undo:", on_click=volver_a_mi_version,
                          args=(jid,))
        st.caption("Opcional. Solo mandamos a Gemini (Google) tu perfil y tu experiencia, sin tu nombre ni tu "
                   "contacto. En el nivel gratuito, Google puede usar estos datos para mejorar sus productos. Si la "
                   "IA agrega cifras o habilidades que no escribiste, descartamos su versión.")
    if ss.cv_notas.get(jid):
        st.caption(ss.cv_notas[jid])

    enc, sec = textos_cv(jid)
    archivo = "_".join(re.findall(r"\w+", f"CV {enc['nombre'] or ''} {empresa}"))[:70] + ".pdf"
    with st.container(horizontal=True, vertical_alignment="center"):
        st.download_button("Descargar PDF", cv.pdf(enc, sec), file_name=archivo, mime="application/pdf",
                           type="primary", icon=":material/download:", on_click="ignore")
        st.space("stretch")
        st.button("Restablecer", type="tertiary", icon=":material/restart_alt:", on_click=restablecer_cv, args=(jid,),
                  help="Vuelve al CV armado automáticamente. Pierdes los cambios que hiciste aquí.")

    with st.expander("¿Cómo armamos tu CV?", icon=":material/help_outline:"):
        st.markdown(
            "1. **Solo usamos lo que escribiste.** No agregamos habilidades, cifras ni experiencias.\n"
            "2. **Ordenamos según la vacante.** Comparamos cada experiencia, logro, habilidad y curso con el anuncio "
            "usando el mismo modelo de lenguaje que el ranking, y ponemos primero lo que más se parece. En "
            "habilidades, primero van las que el anuncio menciona.\n"
            f"3. **Recortamos si sobra.** Hasta {cv.MAX_LOGROS} logros por experiencia, {cv.MAX_HABILIDADES} "
            f"habilidades y {cv.MAX_CURSOS} cursos. "
            + ("Lo demás queda fuera, pero te lo mostramos aquí abajo." if base.omitidos else
               "Esta vez no quedó nada fuera."))
        if base.orden_experiencias:
            st.markdown("**Orden de tu experiencia para esta vacante:** "
                        + " → ".join(escape(n) for n, _ in base.orden_experiencias))
        if base.omitidos:
            st.markdown("**Lo que dejamos fuera:**\n" + "\n".join(f"- {escape(o)}" for o in base.omitidos))
            st.caption("Si quieres alguno, cópialo a la sección que corresponde.")
    st.stop()

if "q0" in ss and not ss.editando:
    m, perfil = motor(), ss.mi_perfil
    if ss.incluir_vivo and ss.vivo_res is None:  # se activó después de buscar
        with st.spinner("Buscando vacantes en vivo de México…"):
            cargar_vivas()
    vivas = ss.vivas if ss.incluir_vivo else None
    calificadas = len(ss.gustan) + len(ss.no_gustan)
    q = m.rocchio(ss.q0, ss.gustan, ss.no_gustan, ss.vec_vivas) if calificadas else ss.q0

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
    ORIGENES = {"Todas": "todas", "México, en vivo": "vivo", "Catálogo de EE. UU.": "catalogo"}
    cuando = ""
    if ss.incluir_vivo:
        eleccion = st.segmented_control("Mostrar", list(ORIGENES), default="Todas", key="origen",
                                        label_visibility="collapsed")
        origen = ORIGENES.get(eleccion or "Todas")
        res = ss.vivo_res
        cuando = datetime.fromisoformat(res.consultada).strftime("el %d/%m/%Y a las %H:%M") if res.consultada else ""
        n_vivas = len(m.rankear(q, perfil, excluir=ss.no_gustan, n=10_000, tipo_cambio=tipo_cambio, vivas=vivas,
                                vectores_vivas=ss.vec_vivas, origen="vivo")) if vivas is not None and len(vivas) else 0
        if res.vencida:
            st.info(f"No pudimos consultar las vacantes en vivo en este momento. Te mostramos las que guardamos "
                    f"{cuando}.", icon=":material/cloud_off:")
        elif not res.vacantes:
            st.info("No pudimos consultar vacantes en vivo de México y no tenemos guardadas para esta búsqueda. "
                    "Te mostramos solo el catálogo.", icon=":material/cloud_off:")
        else:
            st.caption(f"En vivo: {n_vivas} de {len(res.vacantes)} vacantes de México se parecen lo suficiente a tu "
                       f"perfil y entran a la lista (consultadas {cuando}).")
    else:
        origen = "catalogo"
    r = m.rankear(q, perfil, excluir=ss.no_gustan, n=n_mostrar, tipo_cambio=tipo_cambio, vivas=vivas,
                  vectores_vivas=ss.vec_vivas, origen=origen)
    es_cat = r["origen"].eq("catalogo") if len(r) else []
    desc = textos(tuple(int(j) for j in r.loc[es_cat, "job_id"])) if len(r) else {}
    if not len(r):
        st.info("Ninguna vacante en vivo se parece lo suficiente a tu perfil. Prueba con «Todas».",
                icon=":material/search_off:")
    if calificadas:
        st.info(f"Ajustamos la lista con lo que marcaste: {len(ss.gustan)} te interesan y {len(ss.no_gustan)} no. "
                "Las flechas indican cuántos lugares subió o bajó cada vacante.", icon=":material/tune:")

    def aviso_deshacer(idx):
        with st.container(horizontal=True, vertical_alignment="center", key="deshacer"):
            st.html(f'<p class="pc-deshacer">Quitaste <b>{escape(ficha(idx)[0])}</b> de tu lista.</p>')
            st.space("stretch")
            st.button("Deshacer", icon=":material/undo:", on_click=recuperar, args=(idx,), key="btn_deshacer")

    previos = ss.lugares_previos
    descarte = ss.ultimo_descarte
    lugar_descarte = previos.get(jid_de(descarte)) if descarte is not None else None
    ss.lugares_actuales = {jid_de(j): i for i, j in enumerate(r["idx"])} if len(r) else {}
    for i, f in r.iterrows():
        viva = f["origen"] == "vivo"
        idx = f["idx"] if viva else int(f["idx"])
        jid = jid_de(idx)
        if lugar_descarte is not None and i == lugar_descarte:
            aviso_deshacer(descarte)
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
        if viva and f["publicador"]:
            detalles.append(f"vía {f['publicador']}")
        detalles = [d for d in detalles if isinstance(d, str) and d]
        with st.container(key=f"vac_{jid}"):
            c1, c2 = st.columns([5, 1.3])
            with c1:
                st.html(f'<span class="pc-pos">#{i + 1}</span>'
                        f'{f"<span class=pc-mov>{mov}</span>" if mov else ""}'
                        f'{"<span class=pc-vivo>En vivo · México</span>" if viva else ""}'
                        f'{"<span class=pc-mov>Te interesa</span>" if interesa else ""}'
                        f'<p class="pc-vac-titulo">{escape(f["title"])}</p>'
                        f'<p class="pc-vac-meta">{escape(" · ".join(str(d) for d in detalles))}</p>')
                st.markdown(" ".join(f":{COLOR[e]}-badge[{ICONO[e]} {pref}]" for e, pref, _ in f["desglose"]))
            with c2:
                barras = "".join(f'<span class="{"on" if k < nivel_c else ""}"></span>' for k in range(4))
                st.html(f'<div class="pc-coinc"><div class="l">Coincidencia</div><div class="n">{etiqueta}</div>'
                        f'<div class="b">{barras}</div></div>')
            with st.expander("¿Por qué te la recomendamos?"):
                st.markdown(resumen(f["desglose"], etiqueta, int(f["lugar_similitud"]), viva=viva))
                st.markdown("**Lo que pediste:**\n" + "\n".join(
                    f"- :{COLOR[e]}[{ICONO[e]}] **{pref}:** {texto}" for e, pref, texto in f["desglose"]))
                palabras = (f["descripcion"] if viva else desc.get(jid, "")).split()
                if palabras:
                    st.markdown("**Del anuncio:**")
                    st.caption(" ".join(palabras[:90]) + (" …" if len(palabras) > 90 else ""))
                if viva:
                    st.caption(f"Publicada {f['publicada'] or 'sin fecha'} · consultada {cuando}." if f["publicada"]
                               else f"Consultada {cuando}.")
                else:
                    fecha = datetime.fromtimestamp(f["listed_time"] / 1000).strftime("%d/%m/%Y")
                    st.caption(f"Publicada el {fecha}.")
            with st.container(horizontal=True, vertical_alignment="center", key=f"acc_{jid}"):
                if isinstance(f["job_posting_url"], str) and f["job_posting_url"]:
                    st.link_button("Ver anuncio", f["job_posting_url"], type="tertiary",
                                   icon=":material/open_in_new:", icon_position="right")
                st.button("Armar mi CV", key=f"armar_{jid}", type="tertiary", icon=":material/description:",
                          on_click=abrir_cv, args=(idx,), help="Un CV con lo que escribiste, ordenado para esta vacante")
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
    if lugar_descarte is not None and lugar_descarte >= len(r):
        aviso_deshacer(descarte)

    with st.expander("¿Cómo elegimos estas vacantes?", icon=":material/help_outline:"):
        st.markdown(
            "1. **Leemos tu perfil.** Las vacantes del catálogo están en inglés, así que traducimos al inglés lo que "
            "escribiste.\n"
            "2. **Comparamos el significado, no solo las palabras.** Un modelo de lenguaje compara tu perfil con "
            "cada una de las 110,928 vacantes y entiende, por ejemplo, que *analista de datos* y *data analyst* son "
            "el mismo puesto. La **coincidencia** dice qué tanto se parece cada vacante a tu perfil.\n"
            f"3. **Subimos las que cumplen tus preferencias.** De las {CANDIDATOS} vacantes que más se parecen a tu "
            "perfil, ganan lugares las que cumplen lo que pediste: ubicación, modalidad, sueldo y experiencia.\n"
            "4. **Aprendemos de ti.** Cuando marcas *Me interesa*, buscamos más vacantes parecidas a esa; cuando "
            "marcas *No me interesa*, la quitamos y nos alejamos de las que se le parecen.\n"
            "5. **Sumamos vacantes de México en vivo.** Consultamos bolsas de trabajo en línea con tu puesto y tu "
            "ubicación, y las medimos con la misma regla que el catálogo. Si la consulta falla, usamos las últimas "
            "que guardamos.")
    with st.expander("¿Y las que no coinciden? Compara con vacantes de coincidencia media y baja",
                     icon=":material/compare_arrows:"):
        st.caption("Estas vacantes quedan lejos de tu perfil y por eso no aparecen en tu lista. Te las mostramos "
                   "para que compares con tus recomendaciones.")
        lugares = {"Coincidencia media": [1000, 2500, 5000], "Coincidencia baja": [20000, 60000, len(m.cat)]}
        for titulo, lugs in lugares.items():
            st.markdown(f"**{titulo}**")
            for _, g in m.por_lugar(q, perfil, lugs, excluir=ss.no_gustan, tipo_cambio=tipo_cambio).iterrows():
                etq, niv = coincidencia(int(g["lugar_similitud"]))
                empresa = g["company_name"] if isinstance(g["company_name"], str) else "Empresa no indicada"
                meta = f"{empresa} · {g['location']}"
                barras = "".join(f'<span class="{"on" if k < niv else ""}"></span>' for k in range(4))
                with st.container(key=f"cmp_{int(g['job_id'])}"):
                    c1, c2 = st.columns([5, 1.3])
                    c1.html(f'<p class="pc-vac-titulo">{escape(g["title"])}</p>'
                            f'<p class="pc-vac-meta">{escape(meta)}</p>')
                    c2.html(f'<div class="pc-coinc"><div class="l">Coincidencia</div><div class="n">{etq}</div>'
                            f'<div class="b">{barras}</div></div>')
                    st.markdown(resumen(g["desglose"], etq, int(g["lugar_similitud"]), en_lista=False))

    if ss.no_gustan:
        with st.expander(f"Vacantes que descartaste ({len(ss.no_gustan)})", icon=":material/visibility_off:"):
            st.caption("Si quitaste alguna por error, recupérala y volverá a tu lista.")
            for idx in reversed(ss.no_gustan):
                titulo, empresa, ubic = ficha(idx)
                with st.container(horizontal=True, vertical_alignment="center", key=f"desc_{idx}"):
                    st.markdown(f"**{titulo}**  \n:gray[{empresa} · {ubic}]")
                    st.space("stretch")
                    st.button("Recuperar", icon=":material/undo:", key=f"rec_{idx}", on_click=recuperar, args=(idx,))
