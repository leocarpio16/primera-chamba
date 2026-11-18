"""CV personalizado para una vacante (PRD §5.3).

Base por reglas, siempre disponible: cada experiencia, logro, habilidad y curso que escribió el usuario se compara con
la vacante con el mismo modelo del ranking (e5, con el texto traducido al inglés como el perfil). Con eso se ordena y,
cuando sobra, se deja fuera lo menos relacionado (límites fijos de abajo). Solo reacomoda texto del usuario, así que no
puede inventar. Lo que queda fuera se le muestra al usuario para que lo regrese si quiere.

Gemini (opcional) solo reescribe la redacción del perfil y de los logros. Su respuesta se rechaza si trae cifras o
habilidades del vocabulario que no estaban en lo que escribió el usuario, o si cambia los encabezados de las
experiencias; en ese caso queda la versión por reglas.

El CV se edita como texto con un formato sencillo (ver `a_texto`) y se exporta a PDF con fpdf2.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from primera_chamba import config
from primera_chamba import habilidades as hab

MAX_LOGROS = 4        # logros por experiencia
MAX_HABILIDADES = 12
MAX_CURSOS = 5
TIPOS_EXPERIENCIA = ["Empleo", "Prácticas", "Servicio social", "Proyecto", "Voluntariado"]
SECCIONES = {"perfil": "Perfil", "experiencia": "Experiencia", "educacion": "Educación", "habilidades": "Habilidades",
             "idiomas": "Idiomas", "cursos": "Cursos y certificaciones", "otros": "Otros"}
FUENTES = Path(__file__).resolve().parent / "fuentes"
SEP = " · "


@dataclass
class Experiencia:
    puesto: str
    organizacion: str = ""
    periodo: str = ""
    tipo: str = "Empleo"
    logros: list[str] = field(default_factory=list)


@dataclass
class Estudio:
    titulo: str
    institucion: str = ""
    periodo: str = ""
    detalle: str = ""


@dataclass
class DatosCV:
    nombre: str = ""
    puesto: str = ""          # titular debajo del nombre (el puesto que busca)
    correo: str = ""
    telefono: str = ""
    ciudad: str = ""
    enlace: str = ""
    resumen: str = ""
    objetivo: str = ""        # "tu empleo ideal"
    habilidades: list[str] = field(default_factory=list)
    experiencias: list[Experiencia] = field(default_factory=list)
    estudios: list[Estudio] = field(default_factory=list)
    idiomas: list[str] = field(default_factory=list)
    cursos: list[str] = field(default_factory=list)
    otros: list[str] = field(default_factory=list)

    def todo_el_texto(self) -> str:
        """Todo lo que escribió el usuario (para saber qué habilidades y cifras son suyas)."""
        partes = [self.puesto, self.resumen, self.objetivo, *self.habilidades, *self.idiomas, *self.cursos, *self.otros]
        for e in self.experiencias:
            partes += [e.puesto, e.organizacion, e.periodo, *e.logros]
        for s in self.estudios:
            partes += [s.titulo, s.institucion, s.periodo, s.detalle]
        return "\n".join(p for p in partes if p)


def lineas(texto: str) -> list[str]:
    """Una entrada por línea; se quitan viñetas que el usuario haya escrito."""
    return [re.sub(r"^[-•*·]\s*", "", l).strip() for l in (texto or "").splitlines() if l.strip(" -•*·")]


def _traducir(textos: list[str]) -> list[str]:
    """Al inglés, como el perfil del ranking; si el traductor falla, el texto original (e5 es multilingüe)."""
    try:
        from primera_chamba.traduccion import traducir
        return traducir(textos, "es", "en")
    except Exception:
        return textos


@dataclass
class CVBase:
    secciones: dict[str, str]                 # sección → texto editable
    encabezado: dict[str, str]                # nombre, titular, contacto
    omitidos: list[str]                       # lo que se dejó fuera por poco relacionado
    habilidades: dict[str, list[str]]         # resultado de habilidades.comparar
    orden_experiencias: list[tuple[str, float]]  # (experiencia, similitud) para mostrar cómo se ordenó


def armar(d: DatosCV, vector_vacante: np.ndarray, texto_vacante: str, vectores) -> CVBase:
    """CV por reglas. `vectores(lista de textos) → matriz normalizada` es el codificador del ranking."""
    v = np.asarray(vector_vacante, dtype=np.float32)
    exps = [e for e in d.experiencias if e.puesto.strip() or e.logros]
    textos_exp = [". ".join([e.puesto, *e.logros]) for e in exps]
    logros = [l for e in exps for l in e.logros]
    items = textos_exp + logros + d.habilidades + d.cursos
    sim = (vectores(_traducir(items)) @ v).tolist() if items else []
    s_exp, sim = sim[:len(exps)], sim[len(exps):]
    s_log, sim = sim[:len(logros)], sim[len(logros):]
    s_hab, s_cur = sim[:len(d.habilidades)], sim[len(d.habilidades):]

    omitidos = []
    bloques, orden = [], []
    k = 0
    por_exp = []
    for e in exps:
        por_exp.append(list(zip(e.logros, s_log[k:k + len(e.logros)])))
        k += len(e.logros)
    for i in sorted(range(len(exps)), key=lambda i: -s_exp[i]):
        e = exps[i]
        orden.append((e.puesto or e.organizacion, s_exp[i]))
        ls = sorted(por_exp[i], key=lambda x: -x[1])
        omitidos += [l for l, _ in ls[MAX_LOGROS:]]
        bloques.append("\n".join([encabezado_experiencia(e), *[f"- {l}" for l, _ in ls[:MAX_LOGROS]]]))

    comparacion = hab.comparar(texto_vacante, d.habilidades, d.todo_el_texto())
    pedidas = set(comparacion["tienes"])
    # Primero las que pide la vacante; después, de la más a la menos parecida.
    clave = {h: (0 if pedidas & set(hab.detectar(h)) or h in pedidas else 1, -s) for h, s in zip(d.habilidades, s_hab)}
    habs = [mayuscula(h) for h in sorted(d.habilidades, key=lambda h: clave[h])]
    omitidos += habs[MAX_HABILIDADES:]
    cursos = [c for c, _ in sorted(zip(d.cursos, s_cur), key=lambda x: -x[1])]
    omitidos += cursos[MAX_CURSOS:]

    estudios = []
    for s in d.estudios:
        if s.titulo.strip() or s.institucion.strip():
            linea = SEP.join(p for p in (s.titulo.strip(), s.institucion.strip(), s.periodo.strip()) if p)
            estudios.append(linea + (f"\n- {s.detalle.strip()}" if s.detalle.strip() else ""))

    secciones = {
        "perfil": "\n\n".join(p.strip() for p in (d.resumen, d.objetivo) if p and p.strip()),
        "experiencia": "\n\n".join(bloques),
        "educacion": "\n\n".join(estudios),
        "habilidades": SEP.join(habs[:MAX_HABILIDADES]),
        "idiomas": SEP.join(d.idiomas),
        "cursos": "\n".join(f"- {c}" for c in cursos[:MAX_CURSOS]),
        "otros": "\n".join(f"- {o}" for o in d.otros),
    }
    contacto = SEP.join(p.strip() for p in (d.correo, d.telefono, d.ciudad, d.enlace) if p and p.strip())
    return CVBase(secciones, {"nombre": d.nombre.strip(), "titular": d.puesto.strip(), "contacto": contacto},
                  omitidos, comparacion, orden)


def mayuscula(h: str) -> str:
    """'estadística' → 'Estadística' (solo formato; 'pandas' y 'scikit-learn' se escriben así)."""
    return h if not h[:1].islower() or h in {"pandas", "scikit-learn"} else h[0].upper() + h[1:]


def encabezado_experiencia(e: Experiencia) -> str:
    puesto = e.puesto.strip() + (f" ({e.tipo})" if e.tipo and e.tipo != "Empleo" else "")
    return SEP.join(p for p in (puesto, e.organizacion.strip(), e.periodo.strip()) if p)


# ---------------- Gemini (opcional) ----------------
# gemini-2.5-flash ya no se ofrece a cuentas nuevas (404, verificado el 2026-11-18); Google recomienda este.
MODELO_GEMINI = config.GEMINI_MODELO

INSTRUCCION = """Eres un corrector de estilo de CV en español de México. Recibes en JSON dos textos que escribió una
persona: "perfil" (párrafos) y "experiencia" (bloques separados por una línea en blanco; la primera línea de cada bloque
es su encabezado y las que empiezan con "- " son logros).

Reglas obligatorias:
1. Mejora solo la redacción: claridad, verbos en pasado al inicio de cada logro, frases breves y profesionales.
2. NO agregues habilidades, herramientas, cifras, fechas, empresas, títulos ni experiencias que no estén en el texto.
   Si una cifra no aparece en el texto original, no la escribas.
3. Copia los encabezados de la experiencia exactamente igual, en el mismo orden.
4. Conserva el mismo número de logros por bloque o menos; no inventes logros nuevos.
5. Responde solo con JSON: {"perfil": "...", "experiencia": "..."}."""


def _cifras(t: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)*", t or ""))


def _encabezados(experiencia: str) -> list[str]:
    return [b.splitlines()[0].strip() for b in experiencia.split("\n\n") if b.strip()]


def validar_redaccion(original: dict[str, str], nueva: dict, texto_usuario: str) -> str | None:
    """None si la redacción nueva es aceptable; si no, el motivo (en lenguaje común)."""
    if not isinstance(nueva, dict) or not all(isinstance(nueva.get(k), str) for k in ("perfil", "experiencia")):
        return "la respuesta no tenía el formato esperado"
    if (original["perfil"].strip() == "") != (nueva["perfil"].strip() == ""):
        return "cambió la sección de perfil"
    texto_nuevo = nueva["perfil"] + "\n" + nueva["experiencia"]
    nuevas_cifras = _cifras(texto_nuevo) - _cifras(texto_usuario) - _cifras(original["experiencia"])
    if nuevas_cifras:
        return f"agregó cifras que no escribiste ({', '.join(sorted(nuevas_cifras))})"
    nuevas_hab = set(hab.detectar(texto_nuevo)) - set(hab.detectar(texto_usuario))
    if nuevas_hab:
        return f"agregó habilidades que no escribiste ({', '.join(sorted(nuevas_hab))})"
    if _encabezados(nueva["experiencia"]) != _encabezados(original["experiencia"]):
        return "cambió los encabezados de tu experiencia"
    for a, b in zip(original["experiencia"].split("\n\n"), nueva["experiencia"].split("\n\n")):
        if b.count("\n- ") > a.count("\n- "):
            return "agregó logros que no escribiste"
    return None


def pulir_con_gemini(secciones: dict[str, str], texto_usuario: str, cliente=None) -> tuple[dict | None, str]:
    """Devuelve ({perfil, experiencia} o None, nota para el usuario). Solo manda perfil y experiencia: nunca nombre ni
    datos de contacto. Cualquier error deja la versión por reglas; el error no se muestra con detalle (no filtrar
    claves ni URLs)."""
    original = {"perfil": secciones.get("perfil", ""), "experiencia": secciones.get("experiencia", "")}
    if not (original["perfil"].strip() or original["experiencia"].strip()):
        return None, "No hay perfil ni experiencia que redactar."
    try:
        if cliente is None:
            if not config.hay_gemini():
                return None, "No hay clave de Gemini configurada."
            from google import genai
            from google.genai import types
            cliente = genai.Client(api_key=config.GEMINI_API_KEY, http_options=types.HttpOptions(timeout=30_000))
        from google.genai import types
        r = cliente.models.generate_content(
            model=MODELO_GEMINI, contents=json.dumps(original, ensure_ascii=False),
            config=types.GenerateContentConfig(system_instruction=INSTRUCCION, temperature=0.2,
                                               response_mime_type="application/json"))
        nueva = json.loads(r.text)
    except Exception as e:  # sin str(e)
        codigo = getattr(e, "code", None)
        if codigo in (429, 503):  # cuota agotada o "alta demanda" (503 visto el 2026-11-18)
            return None, f"La IA está saturada en este momento (código {codigo}); dejamos tu versión. Prueba más tarde."
        return None, f"La IA no respondió ({type(e).__name__}{f', código {codigo}' if codigo else ''}); dejamos tu versión."
    motivo = validar_redaccion(original, nueva, texto_usuario)
    if motivo:
        return None, f"Descartamos la redacción de la IA porque {motivo}. Dejamos tu versión."
    return {"perfil": nueva["perfil"].strip(), "experiencia": nueva["experiencia"].strip()}, \
        "Redacción mejorada con IA. Revísala: puedes editarla o volver a tu versión."


# ---------------- PDF ----------------
def pdf(encabezado: dict[str, str], secciones: dict[str, str]) -> bytes:
    """PDF de una columna (A4). Formato de cada sección: líneas con "- " son viñetas; en experiencia y educación, las
    demás líneas son encabezados ("Puesto · Organización · Periodo": lo primero va en negritas)."""
    from fpdf import FPDF

    doc = FPDF(format="A4")
    doc.set_margins(18, 16, 18)
    doc.set_auto_page_break(True, margin=16)
    doc.add_font("DejaVu", "", FUENTES / "DejaVuSans.ttf")
    doc.add_font("DejaVu", "B", FUENTES / "DejaVuSans-Bold.ttf")
    doc.add_font("DejaVu", "I", FUENTES / "DejaVuSans-Oblique.ttf")
    doc.set_title(f"CV {encabezado.get('nombre', '')}".strip())
    doc.add_page()
    tinta, gris, linea = (20, 20, 22), (95, 95, 102), (205, 205, 200)

    doc.set_text_color(*tinta)
    doc.set_font("DejaVu", "B", 20)
    doc.multi_cell(0, 9, encabezado.get("nombre") or "Tu nombre", new_x="LMARGIN", new_y="NEXT")
    if encabezado.get("titular"):
        doc.set_font("DejaVu", "", 11.5)
        doc.set_text_color(*gris)
        doc.multi_cell(0, 6, encabezado["titular"], new_x="LMARGIN", new_y="NEXT")
    if encabezado.get("contacto"):
        doc.set_font("DejaVu", "", 9)
        doc.set_text_color(*gris)
        doc.multi_cell(0, 5, encabezado["contacto"], new_x="LMARGIN", new_y="NEXT")
    doc.ln(2)

    for clave, titulo in SECCIONES.items():
        texto = (secciones.get(clave) or "").strip()
        if not texto:
            continue
        doc.ln(2.5)
        doc.set_font("DejaVu", "B", 9.5)
        doc.set_text_color(*tinta)
        doc.cell(0, 6, titulo.upper(), new_x="LMARGIN", new_y="NEXT")
        doc.set_draw_color(*linea)
        doc.line(doc.l_margin, doc.get_y(), doc.w - doc.r_margin, doc.get_y())
        doc.ln(1.8)
        for parrafo in texto.split("\n"):
            p = parrafo.strip()
            if not p:
                doc.ln(1.6)
            elif p.startswith(("- ", "• ")):
                doc.set_font("DejaVu", "", 9.5)
                doc.set_text_color(*tinta)
                doc.set_x(doc.l_margin + 2)
                doc.cell(4, 4.9, "•")
                doc.multi_cell(doc.epw - 6, 4.9, p[2:].strip(), align="L", new_x="LMARGIN", new_y="NEXT")
            elif clave in ("experiencia", "educacion"):
                partes = p.split(SEP, 1)
                doc.set_font("DejaVu", "B", 10)
                doc.set_text_color(*tinta)
                doc.multi_cell(0, 5.4, partes[0], new_x="LMARGIN", new_y="NEXT")
                if len(partes) > 1:
                    doc.set_font("DejaVu", "", 9)
                    doc.set_text_color(*gris)
                    doc.multi_cell(0, 4.6, partes[1], new_x="LMARGIN", new_y="NEXT")
                doc.ln(0.6)
            else:
                doc.set_font("DejaVu", "", 9.5)
                doc.set_text_color(*tinta)
                doc.multi_cell(0, 4.9, p, align="L", new_x="LMARGIN", new_y="NEXT")
    return bytes(doc.output())
