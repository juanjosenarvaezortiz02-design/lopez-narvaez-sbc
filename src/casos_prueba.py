from base_conocimiento import crear_regla
from motor_inferencia import diagnosticar, formatear_hecho

# ============================================================
# MÓDULO: casos_prueba.py  — datos de los casos de prueba
# En src/casos_prueba.py agregar:
#   from base_conocimiento import crear_regla
#   from motor_inferencia import diagnosticar, formatear_hecho
# ============================================================
TOY_CICLO = {   # base de juguete con un ciclo A → B → A, para probar la protección del motor
    "reglas": [crear_regla("RA", "A implica B", "prueba", [("A",)], ("B",)),
               crear_regla("RB", "B implica A", "prueba", [("B",)], ("A",))],
    "hechos_estaticos": [],
}

TODAS_LAS_CAUSAS_MULTIFALLA = {
    "TokenVencido": 0.72, "RafagaDeSolicitudes": 0.85, "ServicioExternoSaturado": 0.68,
    "WorkflowDesactivado": 0.95, "URLDePruebaEnProduccion": 0.90, "FiltroDemasiadoRestrictivo": 0.85,
    "ReferenciaACampoInexistente": 0.80, "ScopesInsuficientes": 0.72, "TimeoutPorVolumen": 0.80,
}

CASOS_PRUEBA = [
    # ---------- Casos funcionales (cada uno ejercita una ruta distinta) ----------
    dict(id=1, tipo="Funcional", descripcion="401 con OAuth2",
         hechos=[("ErrorHTTP", 401), ("Autenticacion", "OAuth2")],
         reglas=["R1", "R4", "R12"], causas={"TokenVencido": 0.72}, estado="diagnostico_completo",
         conclusion="TokenVencido → ReautenticarCredencialOAuth2"),
    dict(id=2, tipo="Funcional", descripcion="429 con muchos items",
         hechos=[("ErrorHTTP", 429), ("Contexto", "ProcesaMuchosItems")],
         reglas=["R2", "R6", "R12"], causas={"RafagaDeSolicitudes": 0.85}, estado="diagnostico_completo",
         conclusion="RafagaDeSolicitudes → UsarLoopOverItemsConWait"),
    dict(id=3, tipo="Funcional", descripcion="503 con timeout",
         hechos=[("ErrorHTTP", 503), ("Sintoma", "TimeoutNodo")],
         reglas=["R3", "R7", "R12"], causas={"ServicioExternoSaturado": 0.68}, estado="diagnostico_completo",
         conclusion="ServicioExternoSaturado → ActivarRetryOnFailConEspera"),
    dict(id=4, tipo="Funcional", descripcion="Webhook sin ejecuciones, workflow inactivo",
         hechos=[("Sintoma", "WebhookSinEjecuciones"), ("Contexto", "WorkflowInactivo")],
         reglas=["R8", "R12"], causas={"WorkflowDesactivado": 0.95}, estado="diagnostico_completo",
         conclusion="WorkflowDesactivado → ActivarElWorkflow"),
    dict(id=5, tipo="Funcional", descripcion="Webhook sin ejecuciones, URL de prueba",
         hechos=[("Sintoma", "WebhookSinEjecuciones"), ("Contexto", "UsaURLTest")],
         reglas=["R9", "R12"], causas={"URLDePruebaEnProduccion": 0.90}, estado="diagnostico_completo",
         conclusion="URLDePruebaEnProduccion → UsarLaURLDeProduccionDelWebhook"),
    dict(id=6, tipo="Funcional", descripcion="Datos vacíos tras un filtro",
         hechos=[("Sintoma", "DatosVacios"), ("Contexto", "FiltroPrevioDescartaTodo")],
         reglas=["R10", "R12"], causas={"FiltroDemasiadoRestrictivo": 0.85}, estado="diagnostico_completo",
         conclusion="FiltroDemasiadoRestrictivo → RevisarCondicionesDelFiltro"),
    dict(id=7, tipo="Funcional", descripcion="401 con API Key",
         hechos=[("ErrorHTTP", 401), ("Autenticacion", "ApiKey")],
         reglas=["R1", "R5", "R12"], causas={"ApiKeyIncorrecta": 0.68}, estado="diagnostico_completo",
         conclusion="ApiKeyIncorrecta → RegenerarYActualizarApiKey"),
    dict(id=8, tipo="Funcional", descripcion="Expresión con campo inexistente",
         hechos=[("Sintoma", "ExpresionInvalida")],
         reglas=["R11", "R12"], causas={"ReferenciaACampoInexistente": 0.80}, estado="diagnostico_completo",
         conclusion="ReferenciaACampoInexistente → CorregirExpresionYVerificarEstructuraJSON"),
    dict(id=9, tipo="Funcional", descripcion="403 con OAuth2 (ampliación)",
         hechos=[("ErrorHTTP", 403), ("Autenticacion", "OAuth2")],
         reglas=["R13", "R14", "R12"], causas={"ScopesInsuficientes": 0.72}, estado="diagnostico_completo",
         conclusion="ScopesInsuficientes → ReautorizarCredencialConScopesCorrectos"),
    dict(id=10, tipo="Funcional", descripcion="Timeout con muchos items (ampliación)",
         hechos=[("Sintoma", "TimeoutNodo"), ("Contexto", "ProcesaMuchosItems")],
         reglas=["R15", "R12"], causas={"TimeoutPorVolumen": 0.80}, estado="diagnostico_completo",
         conclusion="TimeoutPorVolumen → DividirEnLotesConSplitInBatches"),
    # ---------- Caso que activa la mayoría de las reglas ----------
    dict(id=11, tipo="Multifalla", descripcion="Workflow con fallas simultáneas (14 de 15 reglas)",
         hechos=[("ErrorHTTP", 401), ("ErrorHTTP", 403), ("ErrorHTTP", 429), ("ErrorHTTP", 503),
                 ("Autenticacion", "OAuth2"), ("Sintoma", "TimeoutNodo"), ("Contexto", "ProcesaMuchosItems"),
                 ("Sintoma", "WebhookSinEjecuciones"), ("Contexto", "WorkflowInactivo"), ("Contexto", "UsaURLTest"),
                 ("Sintoma", "DatosVacios"), ("Contexto", "FiltroPrevioDescartaTodo"), ("Sintoma", "ExpresionInvalida")],
         reglas=None, causas=TODAS_LAS_CAUSAS_MULTIFALLA, estado="diagnostico_completo",
         conclusion="9 causas raíz, cada una con su recomendación"),
    # ---------- Casos de borde ----------
    dict(id=12, tipo="Sin conclusión", descripcion="Sin hechos de entrada",
         hechos=[], reglas=[], causas={}, estado="sin_conclusion",
         conclusion="Ninguna (entrada vacía)"),
    dict(id=13, tipo="Sin conclusión", descripcion="404: código fuera del alcance",
         hechos=[("ErrorHTTP", 404)], reglas=[], causas={}, estado="sin_conclusion",
         conclusion="Ninguna (ninguna regla aplica)"),
    dict(id=14, tipo="Borde", descripcion="401 sin tipo de autenticación",
         hechos=[("ErrorHTTP", 401)], reglas=["R1"], causas={}, estado="diagnostico_parcial",
         conclusion="Solo CategoriaFalla(CredencialInvalida)"),
    dict(id=15, tipo="Borde", descripcion="503 sin timeout",
         hechos=[("ErrorHTTP", 503)], reglas=["R3"], causas={}, estado="diagnostico_parcial",
         conclusion="Solo CategoriaFalla(ErrorServidorExterno)"),
    dict(id=16, tipo="Borde", descripcion="Hechos duplicados",
         hechos=[("ErrorHTTP", 401), ("ErrorHTTP", 401), ("Autenticacion", "OAuth2")],
         reglas=["R1", "R4", "R12"], causas={"TokenVencido": 0.72}, estado="diagnostico_completo",
         conclusion="TokenVencido (igual que el caso 1)"),
    dict(id=17, tipo="Borde", descripcion="Base con ciclo A→B→A (no debe colgarse)",
         hechos=[("A",)], base=TOY_CICLO, validar=False, ciclo=True,
         reglas=["RA"], causas={}, estado=None,
         conclusion="Termina; detecta el ciclo"),
]


def ejecutar_caso(caso):
    """Ejecuta un caso y compara lo esperado con lo obtenido."""
    r = diagnosticar(caso["hechos"], base_conocimiento=caso.get("base"), validar=caso.get("validar", True))
    reglas_obt = [a["regla"] for a in r["reglas_aplicadas"]]
    causas_obt = {c["causa"]: c["certeza"] for c in r["causas"]}
    checks = {
        "reglas": caso["reglas"] is None or reglas_obt == caso["reglas"],
        "causas": causas_obt == caso["causas"],
        "estado": caso["estado"] is None or r["estado"] == caso["estado"],
        "ciclo": (not caso.get("ciclo")) or bool(r["ciclos_reglas"]),
    }
    return {"resultado": r, "reglas_obtenidas": reglas_obt, "causas_obtenidas": causas_obt,
            "checks": checks, "ok": all(checks.values())}
