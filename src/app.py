"""Interfaz Streamlit para el sistema experto de diagnóstico de n8n."""

import streamlit as st

from base_conocimiento import DOMINIOS, PREDICADOS
from casos_prueba import CASOS_PRUEBA, ejecutar_caso
from motor_inferencia import diagnosticar, porque, validar_hechos


HTTP_KEY = "codigo_http"
OTHER_HTTP_KEY = "otro_codigo_http"
AUTH_KEY = "autenticacion"
SYMPTOMS_KEY = "sintomas"
CONTEXT_KEY = "contexto"
CASE_KEY = "caso_precargado"
ACTIVE_CASE_KEY = "_caso_activo"
RESULT_KEY = "resultado"
RESULT_SOURCE_KEY = "_origen_resultado"
CASE_CHECKS_KEY = "_checks_caso"
WHY_KEY = "_causa_explicada"

CASES_BY_ID = {caso["id"]: caso for caso in CASOS_PRUEBA}
NO_APLICA = "No aplica"
NO_CASE = "Sin caso precargado"
OTHER_HTTP = "Otro código"

HTTP_DESCRIPTIONS = {
    400: "Solicitud incorrecta",
    401: "No autorizado: posible problema de acceso",
    403: "Acceso prohibido: posible falta de permisos",
    404: "No encontrado",
    429: "Demasiadas solicitudes",
    500: "Error interno del servidor",
    502: "Respuesta incorrecta de otro servidor",
    503: "Servicio temporalmente no disponible",
    504: "Tiempo de espera agotado",
}

AUTH_LABELS = {
    "OAuth2": "OAuth 2.0 (autorización mediante una cuenta)",
    "ApiKey": "Clave API (una clave de acceso)",
}

SYMPTOM_LABELS = {
    "WebhookSinEjecuciones": "El webhook no inicia el flujo",
    "DatosVacios": "Un paso del flujo no recibió datos",
    "ExpresionInvalida": "Hay un error en una expresión o referencia a datos",
    "TimeoutNodo": "Un paso tardó demasiado y agotó el tiempo",
}

CONTEXT_LABELS = {
    "ProcesaMuchosItems": "El flujo procesa muchos elementos",
    "WorkflowInactivo": "El flujo está desactivado",
    "UsaURLTest": "El webhook usa una dirección de prueba",
    "FiltroPrevioDescartaTodo": "Un filtro anterior elimina todos los datos",
}

CAUSE_LABELS = {
    "TokenVencido": "La autorización de la cuenta pudo haber vencido",
    "ApiKeyIncorrecta": "La clave API podría ser incorrecta",
    "RafagaDeSolicitudes": "Se enviaron demasiadas solicitudes en poco tiempo",
    "ServicioExternoSaturado": "El servicio conectado pudo estar ocupado",
    "WorkflowDesactivado": "El flujo de trabajo está desactivado",
    "URLDePruebaEnProduccion": "Se está usando una dirección de prueba del webhook",
    "FiltroDemasiadoRestrictivo": "Un filtro podría estar descartando todos los datos",
    "ReferenciaACampoInexistente": "Una expresión menciona un dato que no existe",
    "ScopesInsuficientes": "La cuenta autorizada podría carecer de permisos necesarios",
    "TimeoutPorVolumen": "El volumen de datos pudo exceder el tiempo disponible",
}

RECOMMENDATION_LABELS = {
    "ReautenticarCredencialOAuth2": "Vuelve a conectar la cuenta usada para autorizar el acceso en n8n y prueba de nuevo.",
    "RegenerarYActualizarApiKey": "Revisa la clave API con el servicio conectado y actualízala en la credencial de n8n.",
    "UsarLoopOverItemsConWait": "Procesa los elementos en grupos pequeños y agrega una pausa entre solicitudes.",
    "ActivarRetryOnFailConEspera": "Configura nuevos intentos con una pausa en el paso que consulta el servicio.",
    "ActivarElWorkflow": "Activa el flujo de trabajo en n8n y vuelve a probarlo.",
    "UsarLaURLDeProduccionDelWebhook": "Si el flujo ya está activo, configura el servicio que lo llama con la dirección de producción del webhook.",
    "RevisarCondicionesDelFiltro": "Revisa las condiciones del filtro y confirma que permitan pasar los datos esperados.",
    "CorregirExpresionYVerificarEstructuraJSON": "Revisa la expresión y confirma que el dato mencionado exista en la información recibida.",
    "ReautorizarCredencialConScopesCorrectos": "Vuelve a autorizar la cuenta y concede los permisos que necesita el flujo.",
    "DividirEnLotesConSplitInBatches": "Divide los datos en grupos pequeños y procesa cada grupo por separado.",
}


def _domain_for(predicate):
    domain_key = PREDICADOS[predicate]["argumentos"][0]
    return DOMINIOS[domain_key]


def _http_label(code):
    if code is None:
        return NO_APLICA
    if code == OTHER_HTTP:
        return "Otro código (escribir número)"
    description = HTTP_DESCRIPTIONS.get(code)
    if description is None:
        return f"{code} — Otro código HTTP"
    return f"{code} — {description}"


def _case_label(case_id):
    if case_id is None:
        return NO_CASE
    caso = CASES_BY_ID[case_id]
    return f"Caso {case_id}: {caso['descripcion']}"


def _fact_label(fact):
    predicate, *arguments = fact
    value = arguments[0] if arguments else None
    if predicate == "ErrorHTTP":
        return f"Se observó el código HTTP {_http_label(value)}."
    if predicate == "Autenticacion":
        return f"El tipo de acceso indicado fue {AUTH_LABELS.get(value, value)}."
    if predicate == "Sintoma":
        return SYMPTOM_LABELS.get(value, str(value))
    if predicate == "Contexto":
        return CONTEXT_LABELS.get(value, str(value))
    if predicate == "CategoriaFalla":
        categories = {
            "CredencialInvalida": "un posible problema con la credencial",
            "LimiteRateExcedido": "un posible límite de solicitudes",
            "ErrorServidorExterno": "un posible problema en el servicio conectado",
            "PermisosInsuficientes": "un posible problema de permisos",
        }
        return categories.get(value, str(value))
    if predicate == "CausaRaiz":
        return CAUSE_LABELS.get(value, str(value))
    if predicate == "Recomendar":
        return RECOMMENDATION_LABELS.get(value, str(value))
    if predicate == "Solucion" and len(arguments) == 2:
        causa, recomendacion = arguments
        return (
            f"El catálogo relaciona «{CAUSE_LABELS.get(causa, causa)}» con "
            f"«{RECOMMENDATION_LABELS.get(recomendacion, recomendacion)}»."
        )
    return f"{predicate}({', '.join(str(argument) for argument in arguments)})"


def _rules_for_explanation(causa, resultado):
    explicacion = porque(
        ("CausaRaiz", causa),
        resultado["hechos_iniciales"],
        resultado["reglas_aplicadas"],
    )
    reglas_por_nombre = {
        regla["regla"]: regla for regla in resultado["reglas_aplicadas"]
    }
    reglas_usadas = []
    for linea in explicacion.splitlines():
        if "derivado por " in linea:
            nombre = linea.split("derivado por ", 1)[1].split()[0]
            if nombre in reglas_por_nombre and nombre not in reglas_usadas:
                reglas_usadas.append(nombre)
    return explicacion, [
        reglas_por_nombre[nombre] for nombre in reversed(reglas_usadas)
    ]


def _clear_session():
    for key in (
        HTTP_KEY,
        OTHER_HTTP_KEY,
        AUTH_KEY,
        SYMPTOMS_KEY,
        CONTEXT_KEY,
        CASE_KEY,
        ACTIVE_CASE_KEY,
        RESULT_KEY,
        RESULT_SOURCE_KEY,
        CASE_CHECKS_KEY,
        WHY_KEY,
    ):
        st.session_state.pop(key, None)


def _clear_manual_fields():
    st.session_state[HTTP_KEY] = None
    st.session_state[OTHER_HTTP_KEY] = None
    st.session_state[AUTH_KEY] = NO_APLICA
    st.session_state[SYMPTOMS_KEY] = []
    st.session_state[CONTEXT_KEY] = []


def _load_case_into_form(caso):
    _clear_manual_fields()
    hechos = caso["hechos"]

    codigos = [hecho[1] for hecho in hechos if hecho[0] == "ErrorHTTP"]
    if codigos:
        codigo = codigos[0]
        if codigo in HTTP_DESCRIPTIONS:
            st.session_state[HTTP_KEY] = codigo
        else:
            st.session_state[HTTP_KEY] = OTHER_HTTP
            st.session_state[OTHER_HTTP_KEY] = codigo

    autenticaciones = [
        hecho[1] for hecho in hechos if hecho[0] == "Autenticacion"
    ]
    if autenticaciones:
        st.session_state[AUTH_KEY] = autenticaciones[0]
    st.session_state[SYMPTOMS_KEY] = [
        hecho[1] for hecho in hechos if hecho[0] == "Sintoma"
    ]
    st.session_state[CONTEXT_KEY] = [
        hecho[1] for hecho in hechos if hecho[0] == "Contexto"
    ]


def _case_is_representable_in_form(caso):
    return all(
        hecho[0] in {"ErrorHTTP", "Autenticacion", "Sintoma", "Contexto"}
        for hecho in caso["hechos"]
    )


def _build_facts():
    hechos = []
    codigo = st.session_state[HTTP_KEY]
    if codigo == OTHER_HTTP:
        codigo = st.session_state[OTHER_HTTP_KEY]
    autenticacion = st.session_state[AUTH_KEY]

    if codigo is not None:
        hechos.append(("ErrorHTTP", codigo))
    if autenticacion != NO_APLICA:
        hechos.append(("Autenticacion", autenticacion))
    hechos.extend(("Sintoma", sintoma) for sintoma in st.session_state[SYMPTOMS_KEY])
    hechos.extend(("Contexto", contexto) for contexto in st.session_state[CONTEXT_KEY])
    return hechos


def _show_resultado(resultado):
    estados = {
        "diagnostico_completo": (
            st.success,
            f"El sistema encontró {len(resultado['causas'])} posible(s) causa(s). "
            "Revisa las recomendaciones antes de hacer cambios.",
        ),
        "diagnostico_parcial": (
            st.warning,
            "Encontramos una pista, pero falta información para precisar la causa. "
            "Prueba añadir los datos que conozcas.",
        ),
        "sin_conclusion": (
            st.info,
            "Con estos datos no encontramos una causa en el alcance del sistema. "
            "Puedes añadir síntomas o contexto, o consultar a la persona que administra el flujo.",
        ),
        "entrada_invalida": (st.error, resultado["mensaje"]),
    }
    mostrar_mensaje, mensaje = estados.get(
        resultado["estado"], (st.info, resultado["mensaje"])
    )
    mostrar_mensaje(mensaje)

    for error in resultado["errores"]:
        st.error(error)
    for advertencia in resultado["advertencias"]:
        st.warning(advertencia)
    if resultado["ciclos_reglas"]:
        st.warning(
            "La base de reglas contiene ciclos: "
            + ", ".join(str(ciclo) for ciclo in resultado["ciclos_reglas"])
        )

    checks = st.session_state.get(CASE_CHECKS_KEY)
    if checks is not None:
        case_id = st.session_state[ACTIVE_CASE_KEY]
        if all(checks.values()):
            st.success(f"El caso precargado {case_id} coincide con sus resultados esperados.")
        else:
            st.error(f"El caso precargado {case_id} no coincide con lo esperado: {checks}")

    if resultado["causas"]:
        for index, causa in enumerate(resultado["causas"]):
            with st.container(border=True):
                detalle, certeza = st.columns([3, 1])
                with detalle:
                    st.subheader(CAUSE_LABELS.get(causa["causa"], causa["causa"]))
                with certeza:
                    st.metric(
                        "Confianza estimada",
                        f"{causa['certeza']:.0%}",
                        help="Es una estimación basada en las reglas del sistema, no una garantía.",
                    )

                if st.button("¿Por qué?", key=f"porque_{index}"):
                    st.session_state[WHY_KEY] = causa["causa"]
                if st.session_state.get(WHY_KEY) == causa["causa"]:
                    explicacion, reglas = _rules_for_explanation(
                        causa["causa"], resultado
                    )
                    st.markdown("**Datos que se tomaron en cuenta**")
                    if resultado["hechos_iniciales"]:
                        for hecho in resultado["hechos_iniciales"]:
                            st.markdown(f"- {_fact_label(hecho)}")
                    else:
                        st.write("No se ingresaron observaciones.")
                    st.markdown("**Cómo se relacionan esos datos**")
                    if reglas:
                        for paso, regla in enumerate(reglas, start=1):
                            st.markdown(
                                f"{paso}. **{regla['regla']}:** {regla['descripcion']}"
                            )
                    else:
                        st.write(
                            "No se encontró una regla aplicada que explique esta causa."
                        )
                    st.info(
                        "Por eso, el sistema considera esta causa como una posibilidad; "
                        "no significa que esté confirmada."
                    )
                    with st.expander("Ver detalle técnico de «¿Por qué?»"):
                        st.code(explicacion)

        st.subheader("Recomendaciones para revisar")
        st.caption(
            "Son sugerencias para que las evalúes. El sistema no las aplica ni modifica "
            "tu flujo automáticamente."
        )
        for causa in resultado["causas"]:
            recomendacion = causa["recomendacion"]
            with st.container(border=True):
                st.markdown(
                    f"**Relacionada con:** "
                    f"{CAUSE_LABELS.get(causa['causa'], causa['causa'])}"
                )
                st.write(
                    RECOMMENDATION_LABELS.get(recomendacion, recomendacion)
                    if recomendacion
                    else "No hay una recomendación disponible para esta causa."
                )

    with st.expander("Cómo llegó el sistema a estas conclusiones"):
        reglas_aplicadas = resultado["reglas_aplicadas"]
        if reglas_aplicadas:
            st.write(
                "El sistema compara tus observaciones con sus reglas. En cada paso "
                "puedes ver qué información usó y qué dedujo:"
            )
            for paso, regla in enumerate(reglas_aplicadas, start=1):
                st.markdown(
                    f"**Paso {paso} — {regla['descripcion']}** "
                    f"({regla['regla']})"
                )
                st.write(
                    "**Información considerada:** "
                    + " y ".join(
                        _fact_label(condicion) for condicion in regla["condiciones"]
                    )
                )
                st.write(
                    f"**Conclusión de este paso:** "
                    f"{_fact_label(regla['conclusion'])}"
                )
                st.caption(
                    f"Factor de certeza de este paso: {regla['certeza']:.0%}"
                )
            st.caption(
                "El factor de certeza es una medida interna de las reglas, no una "
                "probabilidad garantizada."
            )
        else:
            st.info(
                "No se activó ninguna regla con las observaciones ingresadas. "
                "Esto puede ocurrir si falta información o si el problema no está "
                "cubierto por el sistema."
            )
        with st.expander("Ver texto técnico original (opcional)"):
            st.caption(
                "Esta versión conserva los nombres y la notación interna del motor. "
                "Para una lectura sencilla, usa los pasos explicados arriba."
            )
            st.code(resultado["explicacion"])


def main():
    st.set_page_config(page_title="Diagnóstico experto de n8n", page_icon="🔎")
    st.title("Ayuda para revisar un flujo de trabajo")
    st.caption(
        "No necesitas conocer n8n: cuéntanos qué pasó y te mostraremos posibles causas "
        "y qué puedes revisar."
    )

    for key, default in (
        (HTTP_KEY, None),
        (OTHER_HTTP_KEY, None),
        (AUTH_KEY, NO_APLICA),
        (SYMPTOMS_KEY, []),
        (CONTEXT_KEY, []),
        (CASE_KEY, None),
        (ACTIVE_CASE_KEY, None),
        (RESULT_KEY, None),
        (RESULT_SOURCE_KEY, None),
        (CASE_CHECKS_KEY, None),
        (WHY_KEY, None),
    ):
        if key not in st.session_state:
            st.session_state[key] = default

    with st.sidebar:
        st.header("Guía y ayuda")
        with st.expander("Qué hace esta página"):
            st.write(
                "n8n conecta aplicaciones para automatizar tareas. Cada automatización "
                "es un **flujo de trabajo**, formado por pasos. Esta página analiza los "
                "datos que selecciones y sugiere posibles causas y recomendaciones."
            )
            st.write(
                "No accede a tu cuenta de n8n, no lee tus flujos y no realiza cambios."
            )
        with st.expander("Cómo funciona"):
            st.markdown(
                "1. Toma los síntomas, el código de error y el contexto que indiques.\n"
                "2. Los compara con un conjunto de reglas de diagnóstico.\n"
                "3. Muestra causas posibles, una estimación de confianza y sugerencias."
            )
        with st.expander("Cómo usarla"):
            st.markdown(
                "1. Revisa el mensaje o registro del paso que falló en n8n.\n"
                "2. Selecciona solo la información que conozcas; no tienes que llenar todo.\n"
                "3. Pulsa **Buscar posibles causas** y revisa cada explicación.\n"
                "4. Decide qué recomendación comprobar. También puedes probar un ejemplo."
            )
        with st.expander("Glosario de convenciones"):
            st.markdown(
                "- **Flujo de trabajo:** automatización que conecta aplicaciones.\n"
                "- **Paso o nodo:** una acción dentro del flujo.\n"
                "- **Webhook:** dirección que permite iniciar un flujo desde otra aplicación.\n"
                "- **Credencial:** cuenta o clave guardada para conectarse a un servicio.\n"
                "- **Síntoma:** lo que observaste que salió mal.\n"
                "- **Contexto:** información adicional que ayuda a entender el problema.\n"
                "- **Causa posible:** explicación sugerida, no confirmación del fallo.\n"
                "- **Confianza (CF):** factor calculado por las reglas; no es una probabilidad garantizada.\n"
                "- **R1, R2…:** nombres de las reglas que relacionan los datos con una conclusión."
            )
        with st.expander("Limitaciones"):
            st.markdown(
                "- Solo analiza los síntomas, códigos, contextos y reglas incluidos en este sistema; "
                "no cubre todos los errores posibles de n8n.\n"
                "- No se conecta a n8n ni inspecciona automáticamente tus flujos o servicios.\n"
                "- Las causas y la confianza son orientativas: verifica el problema antes de cambiar nada.\n"
                "- No escribas contraseñas, tokens ni claves privadas en la página."
            )
        st.divider()
        st.header("Probar un ejemplo")
        st.selectbox(
            "Caso precargado",
            options=[None, *CASES_BY_ID],
            format_func=_case_label,
            key=CASE_KEY,
            help="Elige un ejemplo para ver cómo funciona el diagnóstico. No modifica tu flujo.",
        )
        st.button(
            "Limpiar",
            key="limpiar",
            on_click=_clear_session,
            use_container_width=True,
        )
        if st.session_state[ACTIVE_CASE_KEY] is not None:
            st.caption(
                "El caso se ejecutó con todos sus hechos. Para volver al formulario, "
                "seleccione «Sin caso precargado»."
            )

    selected_case = st.session_state[CASE_KEY]
    if selected_case != st.session_state[ACTIVE_CASE_KEY]:
        st.session_state[ACTIVE_CASE_KEY] = selected_case
        st.session_state[WHY_KEY] = None
        if selected_case is None:
            if st.session_state[RESULT_SOURCE_KEY] == "caso":
                st.session_state[RESULT_KEY] = None
                st.session_state[CASE_CHECKS_KEY] = None
                st.session_state[RESULT_SOURCE_KEY] = None
        else:
            caso = CASES_BY_ID[selected_case]
            _load_case_into_form(caso)
            with st.spinner("Ejecutando el caso precargado..."):
                ejecucion = ejecutar_caso(caso)
            st.session_state[RESULT_KEY] = ejecucion["resultado"]
            st.session_state[CASE_CHECKS_KEY] = ejecucion["checks"]
            st.session_state[RESULT_SOURCE_KEY] = "caso"

    if st.session_state[CASE_KEY] is not None:
        caso = CASES_BY_ID[st.session_state[CASE_KEY]]
        if _case_is_representable_in_form(caso):
            st.info(
                "Se limpiaron los campos anteriores y se cargaron los datos de este "
                "ejemplo. Puedes revisarlos o modificarlos y pulsar "
                "**Buscar posibles causas** para probarlos."
            )
            with st.expander("Ver los datos usados en este ejemplo", expanded=True):
                if caso["hechos"]:
                    for hecho in caso["hechos"]:
                        st.markdown(f"- {_fact_label(hecho)}")
                else:
                    st.write(
                        "Este ejemplo no selecciona ningún dato; deja el formulario "
                        "vacío para probar qué ocurre sin observaciones."
                    )
                codigos = [
                    hecho[1] for hecho in caso["hechos"] if hecho[0] == "ErrorHTTP"
                ]
                if len(codigos) > 1:
                    st.caption(
                        "Este caso usa varios códigos HTTP. El formulario permite "
                        "seleccionar uno; el resultado precargado sí se calculó con "
                        "todos los códigos indicados arriba."
                    )
        else:
            st.info(
                "Este es un caso técnico del motor de inferencia y no corresponde "
                "a una combinación de los campos normales. Se ejecutó usando su "
                "configuración especial."
            )

    st.header("1. Cuéntanos qué ocurrió")
    st.caption(
        "Completa solo lo que sepas. Puedes encontrar detalles en el registro o mensaje "
        "del paso que falló; no hace falta llenar todos los campos."
    )
    http_codes = _domain_for("ErrorHTTP")
    known_http_codes = (400, 401, 403, 404, 429, 500, 502, 503, 504)
    st.selectbox(
        "Código HTTP (opcional)",
        options=[
            None,
            *(code for code in known_http_codes if code in http_codes),
            OTHER_HTTP,
        ],
        format_func=_http_label,
        key=HTTP_KEY,
        help=(
            "Es un número que a veces aparece cuando una aplicación o servicio responde "
            "con un error. Busca el número en el detalle del paso fallido. "
            "Si no está en la lista, selecciona «Otro código» para escribirlo."
        ),
    )
    if st.session_state[HTTP_KEY] == OTHER_HTTP:
        st.number_input(
            "Escribe el código HTTP",
            min_value=100,
            max_value=599,
            step=1,
            value=None,
            placeholder="Por ejemplo, 418",
            key=OTHER_HTTP_KEY,
            help="Debe ser un número entre 100 y 599.",
        )
    with st.form("formulario_diagnostico"):
        st.radio(
            "¿El paso se conecta usando una cuenta o una clave?",
            options=[NO_APLICA, *_domain_for("Autenticacion")],
            format_func=lambda auth: AUTH_LABELS.get(auth, auth),
            key=AUTH_KEY,
            help=(
                "Elige «No aplica» si no lo sabes o si el paso no requiere iniciar sesión. "
                "Una credencial es la cuenta o clave guardada que permite la conexión."
            ),
            horizontal=True,
        )
        st.multiselect(
            "¿Qué observaste? (síntomas)",
            options=_domain_for("Sintoma"),
            format_func=lambda symptom: SYMPTOM_LABELS.get(symptom, symptom),
            key=SYMPTOMS_KEY,
            help="Selecciona una o varias opciones que describan lo ocurrido.",
        )
        st.multiselect(
            "¿Qué más sabes del flujo? (contexto)",
            options=_domain_for("Contexto"),
            format_func=lambda context: CONTEXT_LABELS.get(context, context),
            key=CONTEXT_KEY,
            help="El contexto ayuda a distinguir entre causas parecidas; puedes dejarlo vacío.",
        )
        submitted = st.form_submit_button("Buscar posibles causas", key="diagnosticar")

    if submitted:
        hechos = _build_facts()
        errores, advertencias = validar_hechos(hechos)
        with st.spinner("Calculando el diagnóstico..."):
            resultado = diagnosticar(hechos)
        resultado["errores"] = errores
        resultado["advertencias"] = advertencias
        st.session_state[RESULT_KEY] = resultado
        st.session_state[RESULT_SOURCE_KEY] = "manual"
        st.session_state[CASE_CHECKS_KEY] = None
        st.session_state[WHY_KEY] = None

    st.header("2. Posibles causas")
    with st.expander("¿Qué significan los colores de los resultados?"):
        st.table(
            [
                {
                    "Color": "🟢 Verde",
                    "Significado": "Diagnóstico completo: se encontró una causa probable.",
                    "Qué hacer": "Revisa la recomendación y confirma antes de cambiar el flujo.",
                },
                {
                    "Color": "🟡 Amarillo",
                    "Significado": "Resultado parcial o hay una advertencia.",
                    "Qué hacer": "Lee el mensaje; agrega datos si faltan y revisa la advertencia.",
                },
                {
                    "Color": "🔵 Azul",
                    "Significado": "Sin conclusión: las reglas no identificaron una causa.",
                    "Qué hacer": "Agrega observaciones o consulta las limitaciones en la guía.",
                },
                {
                    "Color": "🔴 Rojo",
                    "Significado": "Entrada inválida: hay datos que deben corregirse.",
                    "Qué hacer": "Lee el error y corrige la información antes de continuar.",
                },
            ]
        )
        st.caption(
            "El color indica el estado del análisis, no la gravedad de la causa. "
            "La confianza de cada causa se muestra por separado."
        )
    if st.session_state[RESULT_KEY] is None:
        st.info(
            "Cuando estés listo, selecciona **Buscar posibles causas**. "
            "También puedes probar un ejemplo desde la barra lateral."
        )
    else:
        _show_resultado(st.session_state[RESULT_KEY])


if __name__ == "__main__":
    main()
