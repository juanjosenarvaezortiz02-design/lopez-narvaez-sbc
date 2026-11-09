# ============================================================
# MÓDULO: motor_inferencia.py
# Encadenamiento hacia adelante con factores de certeza y explicación
# ============================================================
import logging

# En src/motor_inferencia.py descomentar la siguiente línea (en el notebook las celdas comparten espacio de nombres):
from base_conocimiento import PREDICADOS, DOMINIOS, BASE_CONOCIMIENTO

logger = logging.getLogger("sbc.motor")

OPERADORES = {
    ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
    ">":  lambda a, b: a > b,  "<":  lambda a, b: a < b,
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
}


# ---------- Utilidades de representación ----------
def formatear_hecho(hecho):
    """('ErrorHTTP', 401) -> 'ErrorHTTP(401)'"""
    nombre, *args = hecho
    return f"{nombre}({', '.join(str(a) for a in args)})"


def calcular_certeza(certeza_condiciones, certeza_regla):
    """CF(conclusión) = min(CF de las condiciones) × CF(regla), redondeado a 2 decimales."""
    return round(certeza_condiciones * certeza_regla, 2)


# ---------- Unificación de patrones (implementa el ∀ de las reglas) ----------
def _es_variable(x):
    return isinstance(x, str) and x.startswith("?")


def _unificar(patron, hecho, ligas):
    """Intenta ajustar un patrón a un hecho; retorna las ligas ampliadas o None."""
    if len(patron) != len(hecho):
        return None
    nuevas = dict(ligas)
    for p, h in zip(patron, hecho):
        if _es_variable(p):
            if p in nuevas and nuevas[p] != h:
                return None
            nuevas[p] = h
        elif p != h:
            return None
    return nuevas


def _buscar_ligas(condiciones, hechos, ligas=None):
    """Genera (ligas, hechos_usados) para cada forma de satisfacer TODAS las condiciones."""
    ligas = ligas or {}
    if not condiciones:
        yield ligas, []
        return
    primera, *resto = condiciones
    for hecho in hechos:
        nuevas = _unificar(primera, hecho, ligas)
        if nuevas is not None:
            for l, usados in _buscar_ligas(resto, hechos, nuevas):
                yield l, [hecho] + usados


def _cumple_restricciones(restricciones, ligas):
    for variable, operador, valor in restricciones:
        try:
            if not OPERADORES[operador](ligas[variable], valor):
                return False
        except TypeError:          # p. ej. comparar un texto con un número
            return False
    return True


def _instanciar(patron, ligas):
    return tuple(ligas.get(x, x) if _es_variable(x) else x for x in patron)


# ---------- Detección de ciclos en la base de reglas ----------
def detectar_ciclos(base_conocimiento):
    """
    Busca ciclos entre predicados (A → B → A) en la base de reglas.
    Retorna una lista de ciclos, cada uno como lista de nombres de predicado.
    """
    grafo = {}
    for regla in base_conocimiento["reglas"]:
        destino = regla["conclusion"][0]
        for condicion in regla["condiciones"]:
            grafo.setdefault(condicion[0], set()).add(destino)

    ciclos, estado, pila = [], {}, []

    def visitar(nodo):
        estado[nodo] = 1
        pila.append(nodo)
        for vecino in sorted(grafo.get(nodo, ())):
            if estado.get(vecino, 0) == 0:
                visitar(vecino)
            elif estado[vecino] == 1:
                ciclos.append(pila[pila.index(vecino):] + [vecino])
        pila.pop()
        estado[nodo] = 2

    for nodo in sorted(grafo):
        if estado.get(nodo, 0) == 0:
            visitar(nodo)
    return ciclos


# ---------- Motor de inferencia ----------
def _ejecutar(base_conocimiento, hechos_iniciales, max_iteraciones=100):
    hechos, certezas, aplicadas, disparos = [], {}, [], set()

    for h in list(base_conocimiento.get("hechos_estaticos", [])) + [tuple(h) for h in hechos_iniciales]:
        if h not in certezas:                       # hechos duplicados se ignoran
            hechos.append(h)
            certezas[h] = 1.0

    ciclos_reglas = detectar_ciclos(base_conocimiento)
    if ciclos_reglas:
        logger.warning("La base de reglas contiene ciclos entre predicados: %s", ciclos_reglas)
    logger.info("Inicio de inferencia con %d hechos iniciales", len(hechos_iniciales))

    iteraciones, limite_excedido, cambio = 0, False, True
    while cambio:
        iteraciones += 1
        if iteraciones > max_iteraciones:           # protección contra ciclos infinitos
            limite_excedido = True
            logger.warning("Se alcanzó el límite de %d iteraciones; inferencia detenida", max_iteraciones)
            break
        cambio = False
        for regla in base_conocimiento["reglas"]:
            for ligas, usados in list(_buscar_ligas(regla["condiciones"], list(hechos))):
                if not _cumple_restricciones(regla["restricciones"], ligas):
                    continue
                firma = (regla["nombre"], tuple(sorted(ligas.items())))
                if firma in disparos:               # una regla no se dispara dos veces con lo mismo
                    continue
                disparos.add(firma)
                conclusion = _instanciar(regla["conclusion"], ligas)
                if conclusion in certezas:
                    logger.debug("%s: %s ya estaba derivada; se conserva su CF", regla["nombre"],
                                 formatear_hecho(conclusion))
                    continue
                cf = calcular_certeza(min([certezas[u] for u in usados] or [1.0]), regla["certeza"])
                hechos.append(conclusion)
                certezas[conclusion] = cf
                aplicadas.append({"regla": regla["nombre"], "descripcion": regla["descripcion"],
                                  "condiciones": usados, "conclusion": conclusion, "certeza": cf})
                logger.info("Iteración %d | %s: %s ⇒ %s [CF %.2f]", iteraciones, regla["nombre"],
                            " ∧ ".join(formatear_hecho(u) for u in usados), formatear_hecho(conclusion), cf)
                cambio = True

    logger.info("Fin de inferencia: %d reglas aplicadas en %d iteraciones", len(aplicadas), iteraciones)
    return {"hechos": hechos, "certezas": certezas, "reglas_aplicadas": aplicadas,
            "iteraciones": iteraciones, "limite_excedido": limite_excedido, "ciclos_reglas": ciclos_reglas}


def encadenamiento_adelante(base_conocimiento, hechos_iniciales, max_iteraciones=100):
    """
    Aplica encadenamiento hacia adelante hasta el punto fijo.
    Returns: (hechos_finales, reglas_aplicadas)
    """
    r = _ejecutar(base_conocimiento, hechos_iniciales, max_iteraciones)
    return r["hechos"], r["reglas_aplicadas"]


# ---------- Explicación ----------
def explicar_razonamiento(reglas_aplicadas):
    """Genera la explicación legible de todo el razonamiento. Returns: texto."""
    if not reglas_aplicadas:
        return ("No se aplicó ninguna regla: con los hechos ingresados no es posible "
                "derivar conclusiones.")
    lineas = ["EXPLICACIÓN DEL RAZONAMIENTO"]
    for i, r in enumerate(reglas_aplicadas, start=1):
        lineas += [f"\nPaso {i} · {r['regla']}: {r['descripcion']}",
                   "   SI        " + "  Y  ".join(formatear_hecho(c) for c in r["condiciones"]),
                   f"   ENTONCES  {formatear_hecho(r['conclusion'])}   [CF = {r['certeza']:.2f}]"]
    return "\n".join(lineas)


def porque(conclusion, hechos_iniciales, reglas_aplicadas):
    """Explica por qué se llegó a una conclusión, recorriendo la cadena hasta los hechos observados."""
    conclusion = tuple(conclusion)
    iniciales = {tuple(h) for h in hechos_iniciales}
    por_conclusion = {r["conclusion"]: r for r in reglas_aplicadas}

    if conclusion not in por_conclusion:
        if conclusion in iniciales:
            return f"{formatear_hecho(conclusion)} es un hecho observado (dato de entrada); no fue derivado."
        return f"No se derivó {formatear_hecho(conclusion)} con los hechos ingresados."

    lineas = []

    def expandir(hecho, nivel, visitados):
        sangria = "    " * nivel
        if hecho in por_conclusion and hecho not in visitados:
            r = por_conclusion[hecho]
            lineas.append(f"{sangria}• {formatear_hecho(hecho)}  → derivado por {r['regla']} [CF {r['certeza']:.2f}]")
            for cond in r["condiciones"]:
                expandir(cond, nivel + 1, visitados | {hecho})
        elif hecho in iniciales:
            lineas.append(f"{sangria}• {formatear_hecho(hecho)}  → hecho observado")
        else:
            lineas.append(f"{sangria}• {formatear_hecho(hecho)}  → conocimiento de la base (catálogo)")

    r = por_conclusion[conclusion]
    lineas.append(f"¿Por qué {formatear_hecho(conclusion)}?  (se aplicó {r['regla']}: {r['descripcion']})")
    for cond in r["condiciones"]:
        expandir(cond, 1, {conclusion})
    return "\n".join(lineas)


# ---------- Validación de entrada ----------
def validar_hechos(hechos, predicados=None, dominios=None):
    """
    Validación básica de los hechos de entrada.
    Returns: (errores, advertencias)
    """
    predicados = PREDICADOS if predicados is None else predicados
    dominios = DOMINIOS if dominios is None else dominios
    errores, advertencias, vistos = [], [], set()

    if not hechos:
        advertencias.append("No se ingresó ningún hecho: el sistema no podrá derivar conclusiones.")
    for h in hechos:
        h = tuple(h)
        if not h:
            errores.append("Se recibió un hecho vacío.")
            continue
        nombre, *args = h
        if nombre not in predicados:
            errores.append(f"Predicado desconocido: «{nombre}».")
            continue
        info = predicados[nombre]
        if info["capa"] != "observacion":
            errores.append(f"«{nombre}» no es un dato observable: lo deriva el sistema.")
            continue
        if len(args) != len(info["argumentos"]):
            errores.append(f"{nombre} espera {len(info['argumentos'])} argumento(s) y recibió {len(args)}.")
            continue
        for arg, dom in zip(args, info["argumentos"]):
            valido = (isinstance(arg, int) and not isinstance(arg, bool) and arg in dominios[dom]) \
                if dom == "K" else arg in dominios[dom]
            if not valido:
                errores.append(f"Valor no válido para {nombre}: {arg!r} (dominio {dom}).")
        if h in vistos:
            advertencias.append(f"Hecho repetido: {formatear_hecho(h)} (se considera una sola vez).")
        vistos.add(h)

    if ("Autenticacion", "OAuth2") in vistos and ("Autenticacion", "ApiKey") in vistos:
        advertencias.append("Se indicaron OAuth2 y ApiKey a la vez; un mismo nodo usa un solo mecanismo.")
    return errores, advertencias


# ---------- Diagnóstico completo (lo que consumirá la interfaz web) ----------
def diagnosticar(hechos_iniciales, base_conocimiento=None, max_iteraciones=100, validar=True):
    """
    Ejecuta el diagnóstico completo. No imprime nada: retorna un diccionario
    que la interfaz web (Streamlit) puede mostrar directamente.
    """
    base = BASE_CONOCIMIENTO if base_conocimiento is None else base_conocimiento
    hechos_iniciales = [tuple(h) for h in hechos_iniciales]
    errores, advertencias = validar_hechos(hechos_iniciales) if validar else ([], [])

    resultado = {"hechos_iniciales": hechos_iniciales, "errores": errores, "advertencias": advertencias,
                 "hechos_finales": [], "hechos_derivados": [], "reglas_aplicadas": [], "causas": [],
                 "iteraciones": 0, "limite_excedido": False, "ciclos_reglas": [],
                 "explicacion": "", "estado": "entrada_invalida", "mensaje": ""}
    if errores:
        resultado["mensaje"] = "La entrada contiene errores: " + " ".join(errores)
        return resultado

    r = _ejecutar(base, hechos_iniciales, max_iteraciones)
    aplicadas, certezas = r["reglas_aplicadas"], r["certezas"]
    derivados = [a["conclusion"] for a in aplicadas]

    causas = []
    for h in derivados:
        if h[0] == "CausaRaiz":
            rec = next((a["conclusion"][1] for a in aplicadas
                        if a["conclusion"][0] == "Recomendar" and h in a["condiciones"]), None)
            causas.append({"causa": h[1], "certeza": certezas[h], "recomendacion": rec})

    if causas and all(c["recomendacion"] for c in causas):
        estado, mensaje = "diagnostico_completo", f"Se identificaron {len(causas)} causa(s) probable(s) con su acción recomendada."
    elif aplicadas:
        estado = "diagnostico_parcial"
        mensaje = ("Se pudo derivar información parcial (" + ", ".join(formatear_hecho(d) for d in derivados) +
                   "), pero no hay datos suficientes para determinar la causa raíz. "
                   "Agregue el tipo de autenticación, síntomas o factores de contexto.")
    else:
        estado = "sin_conclusion"
        mensaje = ("Con los hechos ingresados no se pudo derivar ninguna conclusión. Puede que el caso esté "
                   "fuera del alcance del sistema (p. ej. códigos 400 o 404) o que falten datos.")

    resultado.update({"hechos_finales": r["hechos"], "hechos_derivados": derivados, "reglas_aplicadas": aplicadas,
                      "causas": causas, "iteraciones": r["iteraciones"], "limite_excedido": r["limite_excedido"],
                      "ciclos_reglas": r["ciclos_reglas"], "explicacion": explicar_razonamiento(aplicadas),
                      "estado": estado, "mensaje": mensaje})
    return resultado
