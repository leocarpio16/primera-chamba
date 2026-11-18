"""Primera chamba · app Streamlit. Ejecutar con `streamlit run app.py`."""
from datetime import datetime

import streamlit as st

from primera_chamba import config
from primera_chamba.motor import (BONO, CANDIDATOS, MODALIDADES, NIVEL_ES, NIVELES, TIPO_ES, TIPOS, Motor, Perfil,
                                  consulta_en, descripciones)

st.set_page_config(page_title="Primera chamba", page_icon="💼", layout="wide")
ss = st.session_state
SIN_NIVEL = "(sin preferencia)"

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


@st.cache_resource(show_spinner="Cargando el motor: modelo e5 e índice de 110,928 vacantes…")
def motor() -> Motor:
    return Motor()


@st.cache_data(show_spinner=False, max_entries=20)
def textos(ids: tuple[int, ...]) -> dict[int, str]:
    return descripciones(list(ids))


def llenar_ejemplo():
    for k, v in EJEMPLO.items():
        ss[f"f_{k}"] = v


def calificar(idx: int, gusta: bool):
    ss.lugares_previos = dict(ss.get("lugares_actuales", {}))
    ss.gustan = [i for i in ss.gustan if i != idx]
    ss.no_gustan = [i for i in ss.no_gustan if i != idx]
    (ss.gustan if gusta else ss.no_gustan).append(idx)


def reiniciar_calificaciones():
    ss.gustan, ss.no_gustan, ss.lugares_previos = [], [], {}


for k, v in {"gustan": [], "no_gustan": [], "lugares_previos": {}}.items():
    ss.setdefault(k, v)

# ---------------- barra lateral ----------------
with st.sidebar:
    st.header("Ajustes")
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

# ---------------- encabezado y formulario ----------------
st.title("💼 Primera chamba")
st.markdown("Dinos qué buscas y te recomendamos las vacantes que mejor encajan contigo. Califícalas con 👍 / 👎 "
            "y el ranking aprende de ti.")

with st.expander("**1 · Tu perfil**", expanded="q0" not in ss):
    st.button("Llenar con un perfil de ejemplo", on_click=llenar_ejemplo)
    with st.form("perfil"):
        c1, c2 = st.columns(2)
        c1.text_input("Puesto que buscas *", key="f_puesto", placeholder="Ej. analista de datos")
        c2.selectbox("Nivel de experiencia", [SIN_NIVEL, *NIVELES], key="f_nivel")
        st.text_area("Habilidades, separadas por comas *", key="f_habilidades",
                     placeholder="Ej. SQL, Python, Excel, atención a clientes")
        c3, c4, c5 = st.columns(3)
        c3.text_input("Ubicación", key="f_ubicacion", placeholder="Ciudad o estado",
                      help="El catálogo histórico es de EE. UU.; escribe una ciudad (p. ej. Austin) o estado (TX).")
        c4.selectbox("Modalidad", MODALIDADES, key="f_modalidad")
        c5.number_input("Sueldo mensual esperado (MXN)", min_value=0, step=1000, key="f_sueldo",
                        help="0 = sin preferencia")
        st.multiselect("Tipo de empleo (vacío = todos)", list(TIPOS), key="f_tipos")
        st.markdown("**Para tu CV** · no cambia el ranking")
        st.text_area("Experiencias y logros", key="f_experiencias")
        c6, c7 = st.columns(2)
        c6.text_area("Educación", key="f_educacion")
        c7.text_area("Describe tu empleo ideal", key="f_descripcion")
        enviado = st.form_submit_button("Buscar vacantes", type="primary")

if enviado:
    habilidades = [h.strip() for h in ss.get("f_habilidades", "").split(",") if h.strip()]
    if not ss.get("f_puesto", "").strip() or not habilidades:
        st.error("Escribe al menos el puesto que buscas y una habilidad.")
    else:
        perfil = Perfil(
            puesto=ss.f_puesto, habilidades=habilidades,
            nivel=None if ss.f_nivel == SIN_NIVEL else ss.f_nivel, ubicacion=ss.f_ubicacion,
            modalidad=ss.f_modalidad, sueldo_mxn_mensual=float(ss.f_sueldo) or None, tipos_empleo=ss.f_tipos,
            experiencias=ss.f_experiencias, educacion=ss.f_educacion, descripcion=ss.f_descripcion)
        m = motor()
        with st.spinner("Traduciendo tu perfil y buscando entre 110,928 vacantes…"):
            consulta, traducido = consulta_en(perfil)
            ss.q0 = m.vector(consulta)
        ss.mi_perfil, ss.consulta, ss.traducido = perfil, consulta, traducido
        reiniciar_calificaciones()
        ss.lugares_actuales = {}
        st.rerun()

# ---------------- resultados ----------------
if "q0" in ss:
    m, perfil = motor(), ss.mi_perfil
    calificadas = len(ss.gustan) + len(ss.no_gustan)
    q = m.rocchio(ss.q0, ss.gustan, ss.no_gustan) if calificadas else ss.q0
    r = m.rankear(q, perfil, excluir=ss.no_gustan, n=n_mostrar, tipo_cambio=tipo_cambio)
    desc = textos(tuple(int(j) for j in r["job_id"]))

    st.subheader("2 · Vacantes recomendadas")
    with st.expander("¿Cómo se calcula el puntaje?"):
        st.markdown(
            f"- **Tu perfil, como lo busca el motor** "
            f"({'traducido al inglés' if ss.traducido else 'sin traducir: el traductor no respondió'}): "
            f"`{ss.consulta}`\n"
            f"- **Similitud:** coseno entre tu perfil y cada vacante con *multilingual-e5-small*, estandarizado "
            f"contra las 110,928 vacantes (z = cuántas desviaciones estándar está por encima del promedio).\n"
            f"- Solo compiten las **{CANDIDATOS} vacantes más parecidas** a tu perfil; entre ellas, cada preferencia "
            f"cumplida (ubicación, modalidad, sueldo, nivel) suma **+{BONO}**.\n"
            f"- **Puntaje = z + {BONO} × preferencias cumplidas.** ✓ cumple · ✗ no cumple · – sin preferencia o "
            f"sin dato (no suma ni resta).\n"
            f"- **Aprende de ti (Rocchio):** perfil nuevo = perfil + 0.75 × promedio de 👍 − 0.15 × promedio de 👎. "
            f"Las vacantes con 👎 salen de la lista.")
    if calificadas:
        st.info(f"Ranking ajustado con tus {calificadas} calificaciones: {len(ss.gustan)} 👍 y "
                f"{len(ss.no_gustan)} 👎. Las flechas muestran cuántos lugares se movió cada vacante.")

    previos = ss.lugares_previos
    ss.lugares_actuales = {int(j): i for i, j in enumerate(r["job_id"])}
    colores = {"✓": "green", "✗": "orange", "–": "gray"}
    for i, f in r.iterrows():
        jid, idx = int(f["job_id"]), int(f["idx"])
        if calificadas and previos:
            antes = previos.get(jid)
            mov = (" · 🆕 nueva" if antes is None else f" · ⬆️ {antes - i}" if antes > i
                   else f" · ⬇️ {i - antes}" if antes < i else "")
        else:
            mov = ""
        gusta = idx in ss.gustan
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            detalles = [f["company_name"] if isinstance(f["company_name"], str) else "Empresa no indicada",
                        f["location"], TIPO_ES.get(f["tipo_empleo"], f["tipo_empleo"])]
            if f["remoto"]:
                detalles.append("permite remoto")
            if f["nivel"] in NIVEL_ES:
                detalles.append(NIVEL_ES[f["nivel"]])
            c1.markdown(f"#### {i + 1}. {f['title']}{' · 👍' if gusta else ''}{mov}")
            c1.caption(" · ".join(str(d) for d in detalles))
            c1.markdown(" ".join(f":{colores[e]}-badge[{e} {pref}]" for e, pref, _ in f["desglose"]))
            c2.metric("Puntaje", f"{f['puntaje']:.2f}")
            b1, b2 = c2.columns(2)
            b1.button("👍", key=f"si_{jid}", on_click=calificar, args=(idx, True), disabled=gusta,
                      help="Me interesa: el ranking se acerca a vacantes como esta")
            b2.button("👎", key=f"no_{jid}", on_click=calificar, args=(idx, False),
                      help="No me interesa: sale de la lista y el ranking se aleja de ella")
            with c1.expander("¿Por qué te la recomendamos?"):
                lineas = [f"- **Similitud con tu perfil:** z = {f['z']:.2f} (coseno {f['coseno']:.3f}); es la "
                          f"**#{int(f['lugar_similitud']):,}** más parecida de 110,928."]
                for e, pref, det in f["desglose"]:
                    lineas.append(f"- {e} **{pref}:** {det} → {'+' + str(BONO) if e == '✓' else '+0'}")
                lineas.append(f"\n**Puntaje** = {f['z']:.2f} + {BONO} × {f['cumplidas']} = **{f['puntaje']:.2f}**")
                if f["sueldo_anual"] == f["sueldo_anual"]:  # no es NaN
                    lineas.append(f"\n**Sueldo publicado:** US${f['sueldo_anual']:,.0f} al año "
                                  f"(≈ ${f['sueldo_anual'] * tipo_cambio / 12:,.0f} MXN al mes)")
                st.markdown("\n".join(lineas))
                texto = desc.get(jid, "")
                palabras = texto.split()
                st.caption(" ".join(palabras[:120]) + (" …" if len(palabras) > 120 else ""))
                fecha = datetime.fromtimestamp(f["listed_time"] / 1000).strftime("%d/%m/%Y")
                st.markdown(f"Publicada el {fecha} · [Ver anuncio original]({f['job_posting_url']})")
