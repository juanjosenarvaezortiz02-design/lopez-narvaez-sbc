# ============================================================
# MÓDULO: base_conocimiento.py
# Predicados, dominios, reglas de producción y catálogo de soluciones
# ============================================================

# --- Dominios (universos de discurso) usados para validar la entrada ---
DOMINIOS = {
    "K": range(100, 600),                                   # códigos HTTP
    "T": ["OAuth2", "ApiKey"],                              # tipos de autenticación
    "SIN": ["WebhookSinEjecuciones", "DatosVacios", "ExpresionInvalida", "TimeoutNodo"],
    "CTX": ["ProcesaMuchosItems", "WorkflowInactivo", "UsaURLTest", "FiltroPrevioDescartaTodo"],
    "F": ["CredencialInvalida", "LimiteRateExcedido", "ErrorServidorExterno", "PermisosInsuficientes"],
    "C": ["TokenVencido", "ApiKeyIncorrecta", "RafagaDeSolicitudes", "ServicioExternoSaturado",
          "WorkflowDesactivado", "URLDePruebaEnProduccion", "FiltroDemasiadoRestrictivo",
          "ReferenciaACampoInexistente", "ScopesInsuficientes", "TimeoutPorVolumen"],
    "S": ["ReautenticarCredencialOAuth2", "RegenerarYActualizarApiKey", "UsarLoopOverItemsConWait",
          "ActivarRetryOnFailConEspera", "ActivarElWorkflow", "UsarLaURLDeProduccionDelWebhook",
          "RevisarCondicionesDelFiltro", "CorregirExpresionYVerificarEstructuraJSON",
          "ReautorizarCredencialConScopesCorrectos", "DividirEnLotesConSplitInBatches"],
}

# --- Predicados: 8 en total. "argumentos" = dominios de los argumentos que aparecen
#     en los hechos (el objeto n/x diagnosticado se omite: se diagnostica uno a la vez).
PREDICADOS = {
    "ErrorHTTP":      {"formal": "ErrorHTTP(n, c)",      "argumentos": ["K"],        "capa": "observacion",
                       "descripcion": "El nodo n respondió con el código de error HTTP c"},
    "Autenticacion":  {"formal": "Autenticacion(n, t)",  "argumentos": ["T"],        "capa": "observacion",
                       "descripcion": "El nodo n se autentica mediante el mecanismo t"},
    "Sintoma":        {"formal": "Sintoma(x, s)",        "argumentos": ["SIN"],      "capa": "observacion",
                       "descripcion": "El objeto x presenta el síntoma s"},
    "Contexto":       {"formal": "Contexto(x, k)",       "argumentos": ["CTX"],      "capa": "observacion",
                       "descripcion": "El objeto x cumple la condición de contexto k"},
    "CategoriaFalla": {"formal": "CategoriaFalla(n, f)", "argumentos": ["F"],        "capa": "intermedio",
                       "descripcion": "La falla del nodo n pertenece a la categoría general f"},
    "CausaRaiz":      {"formal": "CausaRaiz(x, c)",      "argumentos": ["C"],        "capa": "diagnostico",
                       "descripcion": "La causa probable de la falla del objeto x es c"},
    "Solucion":       {"formal": "Solucion(c, s)",       "argumentos": ["C", "S"],   "capa": "catalogo",
                       "descripcion": "La acción s corrige la causa c (catálogo fijo)"},
    "Recomendar":     {"formal": "Recomendar(x, s)",     "argumentos": ["S"],        "capa": "diagnostico",
                       "descripcion": "Se recomienda aplicar la acción s sobre el objeto x"},
}

# --- Catálogo Solucion(c, s) ---
SOLUCIONES = {
    "TokenVencido":                "ReautenticarCredencialOAuth2",
    "ApiKeyIncorrecta":            "RegenerarYActualizarApiKey",
    "RafagaDeSolicitudes":         "UsarLoopOverItemsConWait",
    "ServicioExternoSaturado":     "ActivarRetryOnFailConEspera",
    "WorkflowDesactivado":         "ActivarElWorkflow",
    "URLDePruebaEnProduccion":     "UsarLaURLDeProduccionDelWebhook",
    "FiltroDemasiadoRestrictivo":  "RevisarCondicionesDelFiltro",
    "ReferenciaACampoInexistente": "CorregirExpresionYVerificarEstructuraJSON",
    "ScopesInsuficientes":         "ReautorizarCredencialConScopesCorrectos",
    "TimeoutPorVolumen":           "DividirEnLotesConSplitInBatches",
}


def crear_regla(nombre, descripcion, grupo, condiciones, conclusion, certeza=1.0, restricciones=None):
    """
    Crea una regla de producción.

    condiciones:   lista de patrones (predicado, arg, ...). Un texto que empieza con "?"
                   es una variable (equivale al cuantificador ∀ de la lógica de predicados).
    restricciones: lista de (variable, operador, valor), p. ej. ("?c", ">=", 500).
    """
    return {
        "nombre": nombre, "descripcion": descripcion, "grupo": grupo,
        "condiciones": list(condiciones), "restricciones": list(restricciones or []),
        "conclusion": conclusion, "certeza": certeza,
    }


G1, G2, G3, G4 = ("Síntoma → categoría", "Categoría/contexto → causa raíz",
                  "Síntoma → causa raíz", "Recomendación")

REGLAS = [
    crear_regla("R1", "Un 401 indica credencial inválida", G1,
                [("ErrorHTTP", 401)], ("CategoriaFalla", "CredencialInvalida"), 0.90),
    crear_regla("R2", "Un 429 indica límite de solicitudes excedido", G1,
                [("ErrorHTTP", 429)], ("CategoriaFalla", "LimiteRateExcedido"), 0.95),
    crear_regla("R3", "Un código ≥ 500 indica error del servidor externo", G1,
                [("ErrorHTTP", "?c")], ("CategoriaFalla", "ErrorServidorExterno"), 0.90,
                restricciones=[("?c", ">=", 500)]),
    crear_regla("R4", "Credencial inválida con OAuth2: token vencido", G2,
                [("CategoriaFalla", "CredencialInvalida"), ("Autenticacion", "OAuth2")],
                ("CausaRaiz", "TokenVencido"), 0.80),
    crear_regla("R5", "Credencial inválida con API Key: clave incorrecta", G2,
                [("CategoriaFalla", "CredencialInvalida"), ("Autenticacion", "ApiKey")],
                ("CausaRaiz", "ApiKeyIncorrecta"), 0.75),
    crear_regla("R6", "Límite excedido con muchos items: ráfaga de solicitudes", G2,
                [("CategoriaFalla", "LimiteRateExcedido"), ("Contexto", "ProcesaMuchosItems")],
                ("CausaRaiz", "RafagaDeSolicitudes"), 0.90),
    crear_regla("R7", "Error del servidor con timeout: servicio saturado", G2,
                [("CategoriaFalla", "ErrorServidorExterno"), ("Sintoma", "TimeoutNodo")],
                ("CausaRaiz", "ServicioExternoSaturado"), 0.75),
    crear_regla("R8", "Webhook sin ejecuciones con workflow inactivo", G3,
                [("Sintoma", "WebhookSinEjecuciones"), ("Contexto", "WorkflowInactivo")],
                ("CausaRaiz", "WorkflowDesactivado"), 0.95),
    crear_regla("R9", "Webhook sin ejecuciones con URL de prueba en uso", G3,
                [("Sintoma", "WebhookSinEjecuciones"), ("Contexto", "UsaURLTest")],
                ("CausaRaiz", "URLDePruebaEnProduccion"), 0.90),
    crear_regla("R10", "Datos vacíos tras un filtro que descarta todo", G3,
                [("Sintoma", "DatosVacios"), ("Contexto", "FiltroPrevioDescartaTodo")],
                ("CausaRaiz", "FiltroDemasiadoRestrictivo"), 0.85),
    crear_regla("R11", "Expresión inválida: referencia a un campo inexistente", G3,
                [("Sintoma", "ExpresionInvalida")],
                ("CausaRaiz", "ReferenciaACampoInexistente"), 0.80),
    crear_regla("R12", "Toda causa raíz con solución en el catálogo genera una recomendación", G4,
                [("CausaRaiz", "?c"), ("Solucion", "?c", "?s")],
                ("Recomendar", "?s"), 1.00),
    # --- Ampliación respecto a la Actividad 4 ---
    crear_regla("R13", "Un 403 indica permisos insuficientes", G1,
                [("ErrorHTTP", 403)], ("CategoriaFalla", "PermisosInsuficientes"), 0.90),
    crear_regla("R14", "Permisos insuficientes con OAuth2: scopes insuficientes", G2,
                [("CategoriaFalla", "PermisosInsuficientes"), ("Autenticacion", "OAuth2")],
                ("CausaRaiz", "ScopesInsuficientes"), 0.80),
    crear_regla("R15", "Timeout con muchos items: lote demasiado grande", G3,
                [("Sintoma", "TimeoutNodo"), ("Contexto", "ProcesaMuchosItems")],
                ("CausaRaiz", "TimeoutPorVolumen"), 0.80),
]

# Hechos estáticos: el catálogo Solucion(c, s) entra al motor como hechos con CF = 1.0
HECHOS_ESTATICOS = [("Solucion", c, s) for c, s in SOLUCIONES.items()]


def crear_base_conocimiento():
    """Retorna la base de conocimiento lista para el motor de inferencia."""
    return {"reglas": REGLAS, "hechos_estaticos": HECHOS_ESTATICOS}


BASE_CONOCIMIENTO = crear_base_conocimiento()
