"""Textos de la encuesta por área: los ejemplos de cada campo y un perfil de ejemplo completo por área.

El área solo cambia lo que se muestra en la encuesta (para que no parezca hecha solo para STEM); no entra al ranking.
Cada perfil de ejemplo se probó con el motor (2026-11-18): sus primeras vacantes son del área.
"""

SIN_AREA = "Otra o prefiero no elegir"

# Ejemplos de texto de los campos cuando no se eligió área: mezclan varias áreas.
PISTAS_GENERALES = {
    "puesto": "Ej. Auxiliar administrativo, Enfermera, Diseñador gráfico",
    "habilidades": "Atención a clientes, Excel, redacción, trabajo en equipo…",
    "exp_puesto": "Practicante, auxiliar, voluntario…",
    "exp_org": "Hospital, despacho, escuela, tienda…",
    "exp_logros": "Atendí a 40 personas por semana en ventanilla.\nOrganicé el archivo de 2 mil expedientes.",
    "edu_titulo": "Licenciatura, carrera técnica, bachillerato…",
    "edu_inst": "UNAM",
    "cursos": "Curso de Excel (en línea, 2024)",
}

PISTAS = {
    "Ciencias sociales y humanidades": {
        "puesto": "Psicóloga clínica",
        "habilidades": "Entrevista clínica, evaluación psicológica, redacción de informes…",
        "exp_puesto": "Prácticas en orientación psicológica",
        "exp_org": "Centro comunitario de salud mental",
        "exp_logros": "Apliqué pruebas psicológicas a 30 estudiantes.\nRedacté los informes de evaluación del semestre.",
        "edu_titulo": "Licenciatura en Psicología",
        "cursos": "Diplomado en terapia cognitivo-conductual (2025)",
    },
    "Salud": {
        "puesto": "Enfermera general",
        "habilidades": "Atención a pacientes, toma de signos vitales, curaciones…",
        "exp_puesto": "Enfermera pasante",
        "exp_org": "Hospital General de zona",
        "exp_logros": "Tomé signos vitales de 20 pacientes por turno.\nAdministré medicamentos con indicación médica.",
        "edu_titulo": "Licenciatura en Enfermería",
        "cursos": "Soporte vital básico (BLS), 2024",
    },
    "Administración, contaduría y negocios": {
        "puesto": "Auxiliar contable",
        "habilidades": "Contabilidad, conciliaciones bancarias, facturación, Excel…",
        "exp_puesto": "Auxiliar contable (prácticas)",
        "exp_org": "Despacho contable",
        "exp_logros": "Registré las pólizas de 12 clientes.\nHice las conciliaciones bancarias mensuales.",
        "edu_titulo": "Licenciatura en Contaduría",
        "cursos": "CONTPAQi Contabilidad (2024)",
    },
    "Derecho": {
        "puesto": "Asistente jurídico",
        "habilidades": "Redacción de contratos, investigación jurídica, manejo de expedientes…",
        "exp_puesto": "Pasante",
        "exp_org": "Despacho de derecho laboral",
        "exp_logros": "Redacté borradores de contratos.\nDi seguimiento a 25 expedientes ante el tribunal laboral.",
        "edu_titulo": "Licenciatura en Derecho",
        "cursos": "Diplomado en derecho laboral (2025)",
    },
    "Educación": {
        "puesto": "Maestra de preescolar",
        "habilidades": "Planeación de clases, manejo de grupo, educación inclusiva…",
        "exp_puesto": "Práctica docente",
        "exp_org": "Jardín de niños público",
        "exp_logros": "Planeé y di clases a un grupo de 25 niños.\nOrganicé juntas mensuales con padres de familia.",
        "edu_titulo": "Licenciatura en Educación Preescolar",
        "cursos": "Lengua de Señas Mexicana, nivel 1 (2024)",
    },
    "Arte, diseño y comunicación": {
        "puesto": "Diseñador gráfico",
        "habilidades": "Photoshop, Illustrator, identidad de marca, tipografía…",
        "exp_puesto": "Practicante de diseño",
        "exp_org": "Agencia de publicidad",
        "exp_logros": "Diseñé la identidad de marca de 4 negocios locales.\nPreparé archivos finales para imprenta.",
        "edu_titulo": "Licenciatura en Diseño y Comunicación Visual",
        "cursos": "Motion graphics con After Effects (en línea, 2024)",
    },
    "Ciencias, ingeniería y tecnología": {
        "puesto": "Analista de datos",
        "habilidades": "SQL, Python, Excel, atención a clientes…",
        "exp_puesto": "Practicante de análisis de datos",
        "exp_org": "IIMAS, UNAM",
        "exp_logros": "Limpié y analicé una base de 50 mil registros con Python.\nPresenté los resultados al equipo.",
        "edu_titulo": "Licenciatura en Ciencia de Datos",
        "cursos": "Curso de SQL (en línea, 2024)",
    },
}
AREAS = [SIN_AREA, *PISTAS]


def pista(area: str | None, campo: str) -> str:
    """Ejemplo de texto de un campo para el área elegida (o el general si no hay área)."""
    return PISTAS.get(area, {}).get(campo, PISTAS_GENERALES[campo])


def _exp(puesto, tipo, org, periodo, logros):
    return {"puesto": puesto, "tipo": tipo, "org": org, "periodo": periodo, "logros": "\n".join(logros)}


def _perfil(area, puesto, habilidades, modalidad, sueldo, nombre, correo, telefono, enlace, resumen, descripcion,
            exps, edu, idiomas, cursos, otros):
    """Perfil de ejemplo en el formato de `ss.datos` de la app (sin los campos vacíos, que la app completa)."""
    d = {"area": area, "puesto": puesto, "nivel": "Sin experiencia / recién egresado", "habilidades": habilidades,
         "ubicacion": "Ciudad de México", "modalidad": modalidad, "sueldo": sueldo, "tipos": ["Tiempo completo"],
         "nombre": nombre, "correo": correo, "telefono": telefono, "enlace": enlace, "resumen": resumen,
         "descripcion": descripcion, "n_exp": len(exps), "n_edu": 1,
         "edu0_titulo": edu[0], "edu0_inst": edu[1], "edu0_periodo": edu[2], "edu0_detalle": edu[3],
         "idiomas": "\n".join(idiomas), "cursos": "\n".join(cursos), "otros": "\n".join(otros)}
    for i, e in enumerate(exps):
        d |= {f"exp{i}_{c}": v for c, v in e.items()}
    return d


# El de Ciencias, ingeniería y tecnología es el de la demo (`?demo=1`, caché en vivo de CDMX, guion y diapositivas).
EJEMPLOS = {
    "Ciencias, ingeniería y tecnología": _perfil(
        "Ciencias, ingeniería y tecnología", "Analista de datos",
        "SQL, Python, Excel, Power BI, estadística, visualización de datos, trabajo en equipo", "Remoto", 25000,
        "Ana López Hernández", "ana.lopez@example.com", "55 1234 5678", "portafolio.example.com/ana",
        "Recién egresada de Ciencia de Datos. Me gusta encontrar patrones en los datos y explicarlos de forma sencilla.",
        "Quiero empezar en un equipo de datos donde pueda aprender y trabajar con SQL y Python.",
        [_exp("Vendedora de medio tiempo", "Empleo", "Tienda departamental", "2022 – 2023",
              ["Atendí a clientes en piso de venta.", "Cuadré la caja al cierre del turno."]),
         _exp("Apoyo en análisis de datos", "Servicio social", "IIMAS, UNAM", "ene 2025 – jun 2025",
              ["Presenté los resultados al equipo de investigación.",
               "Limpié y analicé una base de 50 mil registros con Python.",
               "Automaticé en Excel un reporte semanal que antes se hacía a mano."]),
         _exp("Tablero de indicadores de ventas", "Proyecto", "Proyecto escolar, UNAM", "2024",
              ["Diseñé un tablero en Power BI con indicadores de ventas.",
               "Escribí las consultas en SQL que alimentan el tablero."])],
        ("Licenciatura en Ciencia de Datos", "UNAM", "2022 – 2026",
         "Promedio 9.1. Materias: estadística, bases de datos y aprendizaje automático."),
        ["Español: nativo", "Inglés: intermedio (B2)"], ["Curso de SQL para análisis de datos (en línea, 2024)"],
        ["Voluntariado: asesorías de matemáticas a estudiantes de secundaria (2023)"]),

    "Ciencias sociales y humanidades": _perfil(
        "Ciencias sociales y humanidades", "Psicóloga clínica",
        "Evaluación psicológica, entrevista clínica, terapia cognitivo-conductual, aplicación de pruebas psicológicas, "
        "redacción de informes, empatía", "Presencial", 15000,
        "Mariana Torres Ruiz", "mariana.torres@example.com", "55 2345 6789", "linkedin.com/in/mariana-torres-ejemplo",
        "Recién egresada de Psicología con prácticas en evaluación y orientación. Escucho con atención y explico con "
        "claridad.",
        "Quiero trabajar en atención clínica o psicoeducativa, con supervisión, y seguir formándome en terapia "
        "cognitivo-conductual.",
        [_exp("Cajera", "Empleo", "Cafetería", "2021 – 2022",
              ["Atendí a clientes en caja.", "Capacité a dos compañeras nuevas."]),
         _exp("Prácticas en evaluación psicológica", "Prácticas", "Clínica universitaria de atención psicológica",
              "ago 2024 – jun 2025",
              ["Apliqué y califiqué pruebas psicológicas a 30 pacientes, con supervisión.",
               "Redacté informes de evaluación para el equipo clínico.",
               "Coordiné la agenda de primeras entrevistas."]),
         _exp("Talleres de manejo del estrés", "Servicio social", "Preparatoria pública", "2024",
              ["Diseñé e impartí 6 talleres para 120 estudiantes.",
               "Canalicé a orientación los casos que lo requerían."])],
        ("Licenciatura en Psicología", "UNAM", "2021 – 2025",
         "Área clínica. Tesis sobre ansiedad en estudiantes universitarios."),
        ["Español: nativo", "Inglés: intermedio (B1)"],
        ["Diplomado en terapia cognitivo-conductual (2025)", "Intervención en crisis (en línea, 2024)"],
        ["Voluntariado en una línea de apoyo emocional (2023)"]),

    "Salud": _perfil(
        "Salud", "Enfermera general",
        "Atención a pacientes, toma de signos vitales, administración de medicamentos, curaciones, expediente clínico, "
        "trabajo en equipo", "Presencial", 14000,
        "Daniela Ramírez Soto", "daniela.ramirez@example.com", "55 3456 7890", "",
        "Licenciada en Enfermería con servicio social en un hospital de segundo nivel. Trabajo con calma bajo presión.",
        "Busco un puesto de enfermera general en un hospital o clínica, con turnos fijos y la oportunidad de "
        "especializarme.",
        [_exp("Recepcionista de medio tiempo", "Empleo", "Consultorio dental", "2021 – 2022",
              ["Agendé citas y atendí a pacientes en recepción."]),
         _exp("Enfermera pasante", "Servicio social", "Hospital General de zona", "ago 2024 – jul 2025",
              ["Tomé signos vitales y registré la evolución de 20 pacientes por turno.",
               "Preparé y administré medicamentos con indicación médica.",
               "Realicé curaciones y apoyé en procedimientos de urgencias."]),
         _exp("Prácticas clínicas", "Prácticas", "Centro de salud comunitario", "2023",
              ["Apoyé en campañas de vacunación con más de 500 dosis aplicadas.",
               "Di pláticas de prevención a pacientes con diabetes."])],
        ("Licenciatura en Enfermería", "UNAM", "2020 – 2024", "Promedio 9.0."),
        ["Español: nativo", "Inglés: básico (A2)"],
        ["Soporte vital básico (BLS), 2024", "Manejo de residuos peligrosos biológico-infecciosos (2023)"],
        ["Brigadista de protección civil en la facultad (2022 – 2024)"]),

    "Administración, contaduría y negocios": _perfil(
        "Administración, contaduría y negocios", "Auxiliar contable",
        "Contabilidad, conciliaciones bancarias, cuentas por pagar, facturación, Excel, CONTPAQi", "Híbrido", 13000,
        "Luis Hernández Gómez", "luis.hernandez@example.com", "55 4567 8901", "linkedin.com/in/luis-hernandez-ejemplo",
        "Egresado de Contaduría con prácticas en un despacho contable. Ordenado y cuidadoso con los números.",
        "Quiero empezar como auxiliar contable en una empresa donde pueda aprender impuestos y cierre contable.",
        [_exp("Ayudante general", "Empleo", "Tienda de abarrotes familiar", "2020 – 2022",
              ["Surtí el inventario y atendí a clientes."]),
         _exp("Auxiliar contable (prácticas)", "Prácticas", "Despacho contable", "feb 2025 – jul 2025",
              ["Registré pólizas de ingresos y egresos de 12 clientes.",
               "Hice las conciliaciones bancarias mensuales.",
               "Emití y validé facturas electrónicas (CFDI)."]),
         _exp("Plan de negocios para una cafetería", "Proyecto", "Proyecto escolar, UNAM", "2024",
              ["Armé las proyecciones financieras a tres años en Excel.",
               "Presenté el plan ante un jurado de profesores."])],
        ("Licenciatura en Contaduría", "UNAM", "2021 – 2025",
         "Materias: contabilidad financiera, impuestos y auditoría."),
        ["Español: nativo", "Inglés: intermedio (B1)"],
        ["CONTPAQi Contabilidad (2024)", "Excel intermedio (en línea, 2023)"],
        ["Voluntariado: asesoría para declaraciones anuales en la facultad (2025)"]),

    "Derecho": _perfil(
        "Derecho", "Asistente jurídico",
        "Redacción de contratos, investigación jurídica, derecho laboral, manejo de expedientes, atención a clientes, "
        "Word", "Presencial", 12000,
        "Sofía Mendoza Cruz", "sofia.mendoza@example.com", "55 5678 9012", "linkedin.com/in/sofia-mendoza-ejemplo",
        "Pasante de Derecho con experiencia en un despacho laboral. Redacto con precisión y me organizo bien.",
        "Busco empezar como asistente jurídico en un despacho o área legal, en derecho laboral o corporativo.",
        [_exp("Mesera", "Empleo", "Restaurante", "2021 – 2023", ["Atendí mesas en turnos de fin de semana."]),
         _exp("Pasante", "Prácticas", "Despacho de derecho laboral", "ene 2025 – jul 2025",
              ["Redacté borradores de contratos y demandas laborales.",
               "Di seguimiento a 25 expedientes ante el tribunal laboral.",
               "Atendí a clientes en primeras consultas."]),
         _exp("Apoyo en asesoría jurídica gratuita", "Servicio social", "Bufete jurídico universitario", "2024",
              ["Investigué jurisprudencia para casos de pensión alimenticia.",
               "Organicé el archivo de expedientes del bufete."])],
        ("Licenciatura en Derecho", "UNAM", "2020 – 2025", "Promedio 8.9. Seminario de derecho del trabajo."),
        ["Español: nativo", "Inglés: intermedio (B1)"], ["Diplomado en derecho laboral (2025)"],
        ["Concurso universitario de debate jurídico: segundo lugar (2023)"]),

    "Educación": _perfil(
        "Educación", "Maestra de preescolar",
        "Planeación de clases, manejo de grupo, educación inclusiva, comunicación con padres, actividades lúdicas, "
        "evaluación del aprendizaje", "Presencial", 11000,
        "Valeria Castillo Pérez", "valeria.castillo@example.com", "55 6789 0123", "",
        "Licenciada en Educación Preescolar. Me gusta diseñar actividades para que los niños aprendan jugando.",
        "Busco un grupo de preescolar en una escuela que trabaje con educación inclusiva.",
        [_exp("Vendedora", "Empleo", "Papelería", "2020 – 2022", ["Atendí a clientes y acomodé mercancía."]),
         _exp("Práctica docente", "Prácticas", "Jardín de niños público", "ago 2024 – jun 2025",
              ["Planeé y di clases a un grupo de 25 niños de segundo grado.",
               "Adapté actividades para dos alumnos con necesidades educativas especiales.",
               "Organicé juntas mensuales con padres de familia."]),
         _exp("Taller de lectura", "Voluntariado", "Biblioteca pública", "2023",
              ["Coordiné un taller de lectura los sábados para 15 niños."])],
        ("Licenciatura en Educación Preescolar", "Escuela Normal de Educación Preescolar", "2021 – 2025",
         "Titulación con un ensayo sobre el juego simbólico."),
        ["Español: nativo", "Inglés: básico (A2)"], ["Lengua de Señas Mexicana, nivel 1 (2024)"], []),

    "Arte, diseño y comunicación": _perfil(
        "Arte, diseño y comunicación", "Diseñador gráfico",
        "Photoshop, Illustrator, InDesign, identidad de marca, diseño para redes sociales, tipografía", "Remoto", 15000,
        "Diego Morales Vega", "diego.morales@example.com", "55 7890 1234", "behance.net/diego-morales-ejemplo",
        "Diseñador gráfico recién egresado, enfocado en identidad de marca y contenido para redes sociales.",
        "Quiero entrar a una agencia o a un equipo de marketing donde pueda crecer en diseño de marca.",
        [_exp("Barista", "Empleo", "Cafetería", "2021 – 2023", ["Preparé bebidas y atendí a clientes."]),
         _exp("Diseñador gráfico", "Trabajo independiente", "Clientes independientes", "2024 – 2025",
              ["Diseñé la identidad de marca de 4 negocios locales.",
               "Creé plantillas para redes sociales con Illustrator y Photoshop.",
               "Entregué los manuales de marca en InDesign."]),
         _exp("Practicante de diseño", "Prácticas", "Agencia de publicidad", "ene 2025 – jun 2025",
              ["Adapté piezas de campañas a formatos impresos y digitales.",
               "Preparé archivos finales para imprenta."])],
        ("Licenciatura en Diseño y Comunicación Visual", "UNAM", "2021 – 2025",
         "Proyecto final: identidad visual para un museo comunitario."),
        ["Español: nativo", "Inglés: intermedio (B2)"], ["Motion graphics con After Effects (en línea, 2024)"],
        ["Exposición colectiva de carteles en la facultad (2024)"]),
}
EJEMPLO_DEMO = EJEMPLOS["Ciencias, ingeniería y tecnología"]
