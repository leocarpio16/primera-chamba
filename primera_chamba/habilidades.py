"""Vocabulario de habilidades para el aviso de "habilidades faltantes" (PRD §2, paso 5).

El dataset solo trae categorías amplias de habilidades por vacante (IT, SALE, MRKT…), que no sirven para decirle al
usuario qué le falta. Por eso se busca un vocabulario fijo en el texto de la vacante (inglés en el catálogo, español
en las vacantes en vivo) y en lo que escribió el usuario. Faltantes = las que menciona la vacante y no aparecen en
ningún campo del usuario. Nunca entran al CV: solo se avisan.

Cada entrada: (nombre en español, tipo, alias). Los alias se buscan como palabra completa sobre el texto sin acentos y
en minúsculas. Un alias que empieza con "=" se busca respetando mayúsculas (para "R", "Go" o "Excel", que en minúscula
son palabras comunes en inglés).
"""
import re
import unicodedata

TECNICA, BLANDA, IDIOMA = "técnica", "blanda", "idioma"

VOCABULARIO = [
    # Datos y programación
    ("SQL", TECNICA, ["sql", "t-sql", "pl/sql"]),
    ("Python", TECNICA, ["python"]),
    ("R", TECNICA, ["=RStudio", "=R programming", "=R language", "=R, ", "=R and Python", "=Python and R",
                    "=Python, R", "=Python or R", "=R or Python", "=SQL, R", "lenguaje r", "programacion en r"]),
    ("Excel", TECNICA, ["=Excel(?! (?:in|at|as)\\b)", "ms excel", "microsoft excel", "hojas de calculo", "spreadsheets"]),
    ("VBA", TECNICA, ["vba", "macros"]),
    ("Power BI", TECNICA, ["power bi", "powerbi"]),
    ("Tableau", TECNICA, ["tableau"]),
    ("Looker", TECNICA, ["looker"]),
    ("Estadística", TECNICA, ["statistics", "statistical", "estadistica", "estadisticas"]),
    ("Análisis de datos", TECNICA, ["data analysis", "data analytics", "analisis de datos"]),
    ("Visualización de datos", TECNICA, ["data visualization", "visualizacion de datos", "dashboards", "tableros"]),
    ("Machine learning", TECNICA, ["machine learning", "aprendizaje automatico", "aprendizaje de maquina"]),
    ("Deep learning", TECNICA, ["deep learning", "aprendizaje profundo", "redes neuronales", "neural networks"]),
    ("pandas", TECNICA, ["pandas"]),
    ("NumPy", TECNICA, ["numpy"]),
    ("scikit-learn", TECNICA, ["scikit-learn", "sklearn"]),
    ("TensorFlow", TECNICA, ["tensorflow"]),
    ("PyTorch", TECNICA, ["pytorch"]),
    ("Spark", TECNICA, ["spark", "pyspark"]),
    ("Hadoop", TECNICA, ["hadoop"]),
    ("ETL", TECNICA, ["etl"]),
    ("Airflow", TECNICA, ["airflow"]),
    ("Snowflake", TECNICA, ["snowflake"]),
    ("Databricks", TECNICA, ["databricks"]),
    ("SAS", TECNICA, ["=SAS"]),
    ("SPSS", TECNICA, ["spss"]),
    ("Stata", TECNICA, ["stata"]),
    ("MATLAB", TECNICA, ["matlab"]),
    ("Java", TECNICA, ["java"]),
    ("JavaScript", TECNICA, ["javascript"]),
    ("TypeScript", TECNICA, ["typescript"]),
    ("C++", TECNICA, ["c\\+\\+"]),
    ("C#", TECNICA, ["c#"]),
    (".NET", TECNICA, ["\\.net", "asp\\.net"]),
    ("PHP", TECNICA, ["php"]),
    ("Go", TECNICA, ["=Golang", "=Go(?= programming| developer|,)"]),
    ("HTML", TECNICA, ["html"]),
    ("CSS", TECNICA, ["css"]),
    ("React", TECNICA, ["react", "react\\.js", "reactjs"]),
    ("Node.js", TECNICA, ["node\\.js", "nodejs"]),
    ("APIs REST", TECNICA, ["rest api", "restful", "apis rest", "api rest"]),
    ("Git", TECNICA, ["git", "github", "gitlab"]),
    ("Linux", TECNICA, ["linux", "unix"]),
    ("Docker", TECNICA, ["docker"]),
    ("Kubernetes", TECNICA, ["kubernetes"]),
    ("AWS", TECNICA, ["aws", "amazon web services"]),
    ("Azure", TECNICA, ["azure"]),
    ("Google Cloud", TECNICA, ["google cloud", "gcp"]),
    ("Bases de datos", TECNICA, ["databases", "database", "bases de datos", "base de datos"]),
    ("PostgreSQL", TECNICA, ["postgresql", "postgres"]),
    ("MySQL", TECNICA, ["mysql"]),
    ("MongoDB", TECNICA, ["mongodb"]),
    ("Oracle", TECNICA, ["oracle"]),
    ("Ciberseguridad", TECNICA, ["cybersecurity", "information security", "ciberseguridad", "seguridad informatica"]),
    ("Redes", TECNICA, ["networking", "tcp/ip", "redes de computo"]),
    ("Soporte técnico", TECNICA, ["technical support", "help desk", "helpdesk", "soporte tecnico", "mesa de ayuda"]),
    ("Jira", TECNICA, ["jira"]),
    ("Metodologías ágiles", TECNICA, ["agile", "scrum", "kanban", "metodologias agiles", "metodologia agil"]),
    # Oficina, negocio y finanzas
    ("Microsoft Office", TECNICA, ["microsoft office", "ms office", "office 365", "microsoft 365", "paqueteria office"]),
    ("Word", TECNICA, ["=Word(?= ,|,| and| y| documents)", "microsoft word", "ms word"]),
    ("PowerPoint", TECNICA, ["powerpoint"]),
    ("Google Workspace", TECNICA, ["google workspace", "g suite", "google sheets", "hojas de calculo de google"]),
    ("SAP", TECNICA, ["=SAP"]),
    ("Salesforce", TECNICA, ["salesforce"]),
    ("CRM", TECNICA, ["crm"]),
    ("QuickBooks", TECNICA, ["quickbooks"]),
    ("Contabilidad", TECNICA, ["accounting experience", "accounting principles", "accounting software",
                                  "bookkeeping", "gaap", "contabilidad", "contable"]),
    ("Auditoría", TECNICA, ["auditing", "audit", "auditoria"]),
    ("Finanzas", TECNICA, ["financial analysis", "financial modeling", "analisis financiero", "finanzas"]),
    ("Presupuestos", TECNICA, ["budgeting", "budgets", "presupuestos", "presupuesto"]),
    ("Nómina", TECNICA, ["payroll", "nomina"]),
    ("Impuestos", TECNICA, ["tax preparation", "taxes", "impuestos", "fiscal"]),
    ("Facturación", TECNICA, ["billing", "invoicing", "facturacion"]),
    ("Gestión de proyectos", TECNICA, ["project management", "gestion de proyectos", "administracion de proyectos"]),
    ("Ventas", TECNICA, ["sales experience", "sales skills", "selling", "experiencia en ventas", "ventas"]),
    ("Marketing digital", TECNICA, ["digital marketing", "marketing digital"]),
    ("Redes sociales", TECNICA, ["social media", "redes sociales"]),
    ("SEO", TECNICA, ["seo"]),
    ("Google Analytics", TECNICA, ["google analytics"]),
    ("Recursos humanos", TECNICA, ["human resources", "recursos humanos"]),
    ("Reclutamiento", TECNICA, ["full-cycle recruiting", "full cycle recruiting", "recruiting experience",
                                    "sourcing candidates", "reclutamiento", "seleccion de personal"]),
    ("Lean / Six Sigma", TECNICA, ["lean", "six sigma", "kaizen"]),
    ("Control de calidad", TECNICA, ["quality control", "quality assurance", "control de calidad"]),
    ("Logística", TECNICA, ["logistics", "logistica"]),
    ("Inventarios", TECNICA, ["inventory management", "inventory control", "cycle count", "cycle counts",
                                "control de inventarios", "manejo de inventarios", "inventarios"]),
    ("Cadena de suministro", TECNICA, ["supply chain", "cadena de suministro"]),
    ("Compras", TECNICA, ["purchasing", "procurement", "compras"]),
    # Diseño e ingeniería
    ("Photoshop", TECNICA, ["photoshop"]),
    ("Illustrator", TECNICA, ["illustrator"]),
    ("InDesign", TECNICA, ["indesign"]),
    ("Figma", TECNICA, ["figma"]),
    ("Adobe Creative Suite", TECNICA, ["adobe creative suite", "adobe creative cloud", "adobe suite"]),
    ("AutoCAD", TECNICA, ["autocad"]),
    ("SolidWorks", TECNICA, ["solidworks"]),
    ("Revit", TECNICA, ["revit"]),
    # Salud, operación y oficios
    ("RCP / primeros auxilios", TECNICA, ["=CPR", "=BLS", "=ACLS", "first aid", "primeros auxilios",
                                                "reanimacion cardiopulmonar"]),
    ("Expediente clínico electrónico", TECNICA, ["electronic health records", "electronic medical records", "ehr",
                                                 "emr", "expediente clinico"]),
    ("Licencia de manejo", TECNICA, ["driver's license", "drivers license", "driver license", "licencia de manejo",
                                     "licencia de conducir"]),
    ("Montacargas", TECNICA, ["forklift", "montacargas"]),
    ("Mantenimiento", TECNICA, ["preventive maintenance", "preventative maintenance", "equipment maintenance",
                                  "mantenimiento preventivo", "mantenimiento correctivo"]),
    ("Soldadura", TECNICA, ["welding", "soldadura"]),
    # Habilidades blandas
    ("Atención a clientes", BLANDA, ["customer service", "customer support", "atencion a clientes",
                                     "atencion al cliente", "servicio al cliente", "atencion a cliente"]),
    ("Comunicación", BLANDA, ["communication skills", "comunicacion", "comunicacion efectiva"]),
    ("Trabajo en equipo", BLANDA, ["teamwork", "team player", "trabajo en equipo"]),
    ("Liderazgo", BLANDA, ["leadership", "liderazgo"]),
    ("Resolución de problemas", BLANDA, ["problem solving", "problem-solving", "resolucion de problemas",
                                         "solucion de problemas"]),
    ("Negociación", BLANDA, ["negotiation", "negociacion"]),
    ("Organización", BLANDA, ["organizational skills", "time management", "organizacion", "administracion del tiempo"]),
    ("Pensamiento analítico", BLANDA, ["analytical skills", "analytical thinking", "pensamiento analitico",
                                       "capacidad analitica"]),
    # Idiomas
    ("Inglés", IDIOMA, ["fluent in english", "english proficiency", "proficient in english", "written and spoken english",
                          "spoken and written english", "english and spanish", "ingles"]),
    ("Español", IDIOMA, ["fluent in spanish", "spanish speaking", "spanish-speaking", "english and spanish",
                            "bilingual spanish", "espanol"]),
    ("Francés", IDIOMA, ["french", "frances"]),
    ("Portugués", IDIOMA, ["portuguese", "portugues"]),
]


def sin_acentos(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()


def _patron(alias: list[str]) -> tuple[re.Pattern | None, re.Pattern | None]:
    """(patrón sin distinguir mayúsculas, patrón que sí distingue). Un alias con "\\" o "(" ya es expresión regular."""
    def frag(a):
        return a if "\\" in a or "(" in a else re.escape(a)

    def unir(xs):
        return re.compile("|".join(rf"(?<![\w+#.-])(?:{frag(a)})(?![\w+#-])" for a in xs)) if xs else None
    return unir([a for a in alias if not a.startswith("=")]), unir([a[1:] for a in alias if a.startswith("=")])


_PATRONES = [(nombre, tipo, *_patron(alias)) for nombre, tipo, alias in VOCABULARIO]


def detectar(texto: str) -> list[str]:
    """Habilidades del vocabulario que aparecen en el texto, en el orden del vocabulario."""
    crudo = sin_acentos(texto)
    bajo = crudo.lower()
    return [n for n, _, p, s in _PATRONES if (p is not None and p.search(bajo)) or (s is not None and s.search(crudo))]


def tipo_de(nombre: str) -> str:
    return next(t for n, t, _ in VOCABULARIO if n == nombre)


def comparar(texto_vacante: str, habilidades_usuario: list[str], resto_usuario: str = "") -> dict[str, list[str]]:
    """{'tienes': las que pide la vacante y están entre tus habilidades,
        'en_tu_texto': las que pide y aparecen en otro campo tuyo (experiencias, cursos, idiomas…), no en habilidades,
        'faltan': las que pide y no aparecen en nada de lo que escribiste}.
    Una habilidad del usuario cuenta si su texto coincide con un alias o con el nombre de la entrada."""
    pide = detectar(texto_vacante)
    propias = set(detectar(" , ".join(habilidades_usuario)))
    nombres = {sin_acentos(h).lower().strip() for h in habilidades_usuario}
    propias |= {n for n in pide if sin_acentos(n).lower() in nombres}
    en_texto = set(detectar(resto_usuario)) - propias
    return {"tienes": [n for n in pide if n in propias],
            "en_tu_texto": [n for n in pide if n in en_texto],
            "faltan": [n for n in pide if n not in propias and n not in en_texto]}
