# Documentación técnica y de implementación

## Sistema experto para el diagnóstico de fallas en workflows de n8n

**Proyecto:** López Narváez — Sistema experto con interfaz web  
**Autores:** Laura Daniela Lopez Santos y Juan Jose Narvaez Ortiz  
**Universidad:** Fundación Universitaria Los Libertadores  
**Asignatura:** Inteligencia Artificial II  

---

## 1. Descripción general

Este proyecto implementa un sistema basado en conocimiento para ayudar a diagnosticar fallas en workflows creados con n8n. n8n es una plataforma de automatización que permite construir flujos mediante nodos conectados a servicios externos, APIs, bases de datos y webhooks.

El usuario introduce hechos observables, como:

- Código HTTP devuelto por un nodo.
- Método de autenticación utilizado.
- Síntomas visibles en el workflow.
- Condiciones o características del contexto de ejecución.

Con esos datos, el sistema aplica reglas de producción y obtiene:

- Una o varias causas raíz probables.
- Un factor de certeza para cada causa.
- Una recomendación correctiva.
- Una explicación de las reglas que se encadenaron.

La arquitectura está separada en tres responsabilidades principales:

1. **Base de conocimiento:** dominios, predicados, catálogo de soluciones y reglas.
2. **Motor de inferencia:** validación, unificación de reglas, encadenamiento hacia adelante y explicación.
3. **Interfaz web:** formulario, casos precargados, resultados y navegación construidos con Streamlit.

```text
Usuario
  │
  ▼
Interfaz Streamlit — src/app.py
  │ construye hechos y muestra resultados
  ▼
Motor de inferencia — src/motor_inferencia.py
  │ valida, encadena reglas y calcula certeza
  ▼
Base de conocimiento — src/base_conocimiento.py
  │ proporciona predicados, soluciones y reglas
  ▼
Casos de prueba — src/casos_prueba.py
```

---

## 2. Estructura del proyecto

```text
lopez-narvaez-sbc/
├── src/
│   ├── base_conocimiento.py
│   ├── motor_inferencia.py
│   ├── casos_prueba.py
│   └── app.py
├── tests/
│   ├── test_motor.py
│   ├── test_app.py
│   └── casos_prueba.md
├── docs/
│   ├── traspaso.md
│   ├── documentacion_tecnica.pdf
│   └── capturas/
├── notebooks/
│   └── Lopez_Narvaez_proyecto_final_sbc.ipynb
├── requirements.txt
├── pytest.ini
├── README.md
└── documentacion.md
```

### 2.1 Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `src/base_conocimiento.py` | Define los universos de discurso, predicados, soluciones y 15 reglas de producción. |
| `src/motor_inferencia.py` | Ejecuta la inferencia, valida hechos, calcula factores de certeza y construye explicaciones. |
| `src/casos_prueba.py` | Contiene 17 casos funcionales, de borde y de robustez. |
| `src/app.py` | Implementa la interfaz web con Streamlit y gestiona el estado de sesión. |
| `tests/test_motor.py` | Comprueba el motor y los casos precargados. |
| `tests/test_app.py` | Comprueba la interfaz, los controles y la integración con el motor. |
| `notebooks/Lopez_Narvaez_proyecto_final_sbc.ipynb` | Conserva la implementación original de desarrollo y validación. |

---

## 3. Tecnologías y dependencias

El proyecto está implementado en Python.

- **Python 3.10 o superior:** lenguaje principal.
- **Streamlit:** construcción de la interfaz web sin un framework JavaScript independiente.
- **pytest:** ejecución de pruebas unitarias e integración.
- **Streamlit Testing:** simulación de widgets y estado de la aplicación en las pruebas.

Las dependencias están declaradas en `requirements.txt`:

```text
streamlit
pytest
```

El archivo `pytest.ini` agrega `src` al `pythonpath`, lo que permite importar módulos como `motor_inferencia` y `base_conocimiento` desde las pruebas.

---

## 4. Instalación y ejecución

### 4.1 Instalación

Desde la carpeta del proyecto:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

En Linux o macOS, la activación del entorno virtual se realiza con:

```bash
source .venv/bin/activate
```

### 4.2 Ejecución de la interfaz

```bash
python -m streamlit run src/app.py
```

Por defecto, Streamlit abre la aplicación en un servidor local. Si el navegador no se abre automáticamente, se puede acceder a la dirección indicada en la terminal, normalmente `http://localhost:8501`.

### 4.3 Ejecución de las pruebas

```bash
python -m pytest -v
```

La suite cubre el motor de inferencia y el funcionamiento integrado de los widgets. El proyecto contiene 38 comprobaciones parametrizadas y específicas.

---

## 5. Base de conocimiento

La base de conocimiento se define en `src/base_conocimiento.py`. Se estructura en dominios, predicados, reglas y hechos estáticos.

### 5.1 Dominios

Un dominio establece los valores válidos para los argumentos de un predicado:

| Nombre | Valores |
|---|---|
| `K` | Códigos HTTP del rango 100 a 599. |
| `T` | `OAuth2`, `ApiKey`. |
| `SIN` | `WebhookSinEjecuciones`, `DatosVacios`, `ExpresionInvalida`, `TimeoutNodo`. |
| `CTX` | `ProcesaMuchosItems`, `WorkflowInactivo`, `UsaURLTest`, `FiltroPrevioDescartaTodo`. |
| `F` | Categorías generales de falla. |
| `C` | Causas raíz específicas. |
| `S` | Acciones correctivas disponibles. |

### 5.2 Predicados

Se implementaron ocho predicados:

| Predicado | Capa | Significado |
|---|---|---|
| `ErrorHTTP(n, c)` | Observación | El nodo `n` respondió con el código HTTP `c`. |
| `Autenticacion(n, t)` | Observación | El nodo `n` usa el mecanismo de autenticación `t`. |
| `Sintoma(x, s)` | Observación | El objeto `x` presenta el síntoma `s`. |
| `Contexto(x, k)` | Observación | El objeto `x` cumple la condición `k`. |
| `CategoriaFalla(n, f)` | Intermedia | La falla del nodo pertenece a la categoría `f`. |
| `CausaRaiz(x, c)` | Diagnóstico | La causa probable es `c`. |
| `Solucion(c, s)` | Catálogo | La acción `s` corrige la causa `c`. |
| `Recomendar(x, s)` | Diagnóstico | Se recomienda aplicar `s` sobre `x`. |

El diseño omite la escritura del nodo `n` o del objeto `x` dentro de los hechos enviados por la interfaz. El diagnóstico se ejecuta sobre un workflow de forma agregada.

### 5.3 Catálogo de soluciones

| Causa raíz | Solución |
|---|---|
| `TokenVencido` | `ReautenticarCredencialOAuth2` |
| `ApiKeyIncorrecta` | `RegenerarYActualizarApiKey` |
| `RafagaDeSolicitudes` | `UsarLoopOverItemsConWait` |
| `ServicioExternoSaturado` | `ActivarRetryOnFailConEspera` |
| `WorkflowDesactivado` | `ActivarElWorkflow` |
| `URLDePruebaEnProduccion` | `UsarLaURLDeProduccionDelWebhook` |
| `FiltroDemasiadoRestrictivo` | `RevisarCondicionesDelFiltro` |
| `ReferenciaACampoInexistente` | `CorregirExpresionYVerificarEstructuraJSON` |
| `ScopesInsuficientes` | `ReautorizarCredencialConScopesCorrectos` |
| `TimeoutPorVolumen` | `DividirEnLotesConSplitInBatches` |

Las soluciones se convierten en hechos estáticos `("Solucion", causa, solucion)`. Así, la regla R12 puede relacionar dinámicamente una causa derivada con su recomendación.

### 5.4 Reglas de producción

Las reglas siguen el formato:

```text
SI condición₁ Y condición₂ Y ... ENTONCES conclusión [CF]
```

| Regla | Condiciones | Conclusión | CF |
|---|---|---|---|
| R1 | `ErrorHTTP(401)` | `CategoriaFalla(CredencialInvalida)` | 0.90 |
| R2 | `ErrorHTTP(429)` | `CategoriaFalla(LimiteRateExcedido)` | 0.95 |
| R3 | `ErrorHTTP(c)` con `c >= 500` | `CategoriaFalla(ErrorServidorExterno)` | 0.90 |
| R4 | Credencial inválida + OAuth2 | `CausaRaiz(TokenVencido)` | 0.80 |
| R5 | Credencial inválida + ApiKey | `CausaRaiz(ApiKeyIncorrecta)` | 0.75 |
| R6 | Límite excedido + procesa muchos items | `CausaRaiz(RafagaDeSolicitudes)` | 0.90 |
| R7 | Error externo + timeout | `CausaRaiz(ServicioExternoSaturado)` | 0.75 |
| R8 | Webhook sin ejecuciones + workflow inactivo | `CausaRaiz(WorkflowDesactivado)` | 0.95 |
| R9 | Webhook sin ejecuciones + URL de prueba | `CausaRaiz(URLDePruebaEnProduccion)` | 0.90 |
| R10 | Datos vacíos + filtro previo restrictivo | `CausaRaiz(FiltroDemasiadoRestrictivo)` | 0.85 |
| R11 | Expresión inválida | `CausaRaiz(ReferenciaACampoInexistente)` | 0.80 |
| R12 | Causa raíz + solución en el catálogo | `Recomendar(solucion)` | 1.00 |
| R13 | `ErrorHTTP(403)` | `CategoriaFalla(PermisosInsuficientes)` | 0.90 |
| R14 | Permisos insuficientes + OAuth2 | `CausaRaiz(ScopesInsuficientes)` | 0.80 |
| R15 | Timeout + procesa muchos items | `CausaRaiz(TimeoutPorVolumen)` | 0.80 |

---

## 6. Motor de inferencia

El motor está implementado en `src/motor_inferencia.py`.

### 6.1 Representación de hechos

Los hechos son tuplas con el nombre del predicado y sus argumentos:

```python
("ErrorHTTP", 401)
("Autenticacion", "OAuth2")
("Sintoma", "TimeoutNodo")
("Contexto", "ProcesaMuchosItems")
```

Los hechos observados reciben un factor de certeza inicial de `1.0`. Los hechos derivados heredan la menor certeza de sus condiciones multiplicada por el factor de certeza de la regla aplicada.

### 6.2 Cálculo del factor de certeza

La fórmula utilizada es:

```text
CF(resultado) = min(CF(condiciones)) × CF(regla)
```

El resultado se redondea a dos decimales.

Ejemplo:

```text
ErrorHTTP(401)                 CF = 1.00
R1 aplica 0.90                 ⇒ CategoriaFalla(CredencialInvalida) CF = 0.90
Autenticacion(OAuth2)          CF = 1.00
R4 aplica 0.80                 ⇒ CausaRaiz(TokenVencido) CF = 0.72
R12 aplica 1.00                ⇒ Recomendar(ReautenticarCredencialOAuth2) CF = 0.72
```

### 6.3 Unificación

Las reglas pueden contener variables, que se representan con textos que empiezan por `?`. Por ejemplo, R3 usa `?c` para aceptar cualquier código HTTP:

```python
("ErrorHTTP", "?c")
```

La función `_unificar` compara un patrón de regla con un hecho. Cuando encuentra una variable, guarda su liga. Las ligas posteriores deben coincidir con el mismo valor.

La función `_buscar_ligas` combina todas las condiciones de una regla y devuelve cada conjunto de hechos que satisface el patrón completo.

Las restricciones permiten aplicar operadores adicionales. R3 usa:

```python
("?c", ">=", 500)
```

De esta forma se pueden derivar códigos como 500, 503 o 599, pero no 404 o 429.

### 6.4 Encadenamiento hacia adelante

El motor ejecuta `encadenamiento_adelante` mediante `_ejecutar`:

1. Agrega los hechos estáticos del catálogo.
2. Agrega los hechos iniciales sin duplicarlos.
3. Recorre todas las reglas.
4. Busca combinaciones que satisfagan sus condiciones.
5. Verifica las restricciones.
6. Calcula el factor de certeza.
7. Agrega cada conclusión nueva.
8. Repite el proceso hasta alcanzar el punto fijo.

La ejecución termina cuando ninguna regla puede derivar conclusiones nuevas.

Para evitar bucles, el motor implementa:

- Una firma de disparo por regla y conjunto de ligas.
- Un máximo configurable de 100 iteraciones.
- Detección previa de ciclos entre predicados.

### 6.5 Estados de diagnóstico

`diagnosticar()` puede devolver los siguientes estados:

| Estado | Significado |
|---|---|
| `diagnostico_completo` | Se obtuvo al menos una causa con recomendación. |
| `diagnostico_parcial` | Se derivaron datos intermedios, pero falta información para una causa raíz completa. |
| `sin_conclusion` | Ninguna regla produjo una conclusión. |
| `entrada_invalida` | El hecho no pertenece al dominio o usa un predicado observable incorrecto. |

### 6.6 Diccionario de retorno

`diagnosticar()` devuelve un diccionario que desacopla el motor de la interfaz:

| Clave | Uso |
|---|---|
| `estado` | Determina el tipo de mensaje mostrado al usuario. |
| `mensaje` | Explica el resultado general. |
| `causas` | Contiene causa, certeza y recomendación. |
| `hechos_iniciales` | Permite reconstruir la explicación desde los datos observados. |
| `hechos_finales` | Contiene hechos iniciales y derivados. |
| `hechos_derivados` | Lista las conclusiones obtenidas. |
| `reglas_aplicadas` | Conserva el orden y los hechos usados por cada regla. |
| `explicacion` | Texto completo de todas las inferencias. |
| `errores` | Errores que impiden el diagnóstico. |
| `advertencias` | Inconsistencias no bloqueantes. |
| `iteraciones` | Número de recorridos realizados. |
| `limite_excedido` | Indica si se alcanzó el límite de seguridad. |
| `ciclos_reglas` | Contiene los ciclos detectados en la base. |

### 6.7 Explicación

El sistema ofrece dos niveles de explicación:

- `explicar_razonamiento()` muestra todas las reglas disparadas en orden.
- `porque()` sigue hacia atrás desde una causa raíz hasta los hechos observados.

Esto permite a la interfaz mostrar no solo el resultado, sino también la cadena lógica utilizada para alcanzarlo.

---

## 7. Validación de entrada

`validar_hechos()` verifica cada hecho recibido:

- El predicado debe existir.
- El predicado debe pertenecer a la capa observable.
- Debe tener el número correcto de argumentos.
- El valor debe pertenecer al dominio correspondiente.
- Los hechos duplicados generan una advertencia.
- OAuth2 y ApiKey simultáneamente generan una advertencia.
- Una lista vacía genera una advertencia informativa.

Ejemplo de llamada directa:

```python
from motor_inferencia import diagnosticar

resultado = diagnosticar([
    ("ErrorHTTP", 401),
    ("Autenticacion", "OAuth2"),
])

print(resultado["estado"])
print(resultado["causas"])
```

Resultado esperado:

```python
{
    "causa": "TokenVencido",
    "certeza": 0.72,
    "recomendacion": "ReautenticarCredencialOAuth2",
}
```

---

## 8. Casos de prueba

Los casos se encuentran en `src/casos_prueba.py`.

### 8.1 Clasificación

Los 17 casos se dividen en:

- 10 casos funcionales normales.
- 1 caso multifalla.
- 6 casos de borde o robustez.

El caso 11 combina varios errores, síntomas y contextos. Activa hasta nueve causas raíz y sirve para comprobar que el motor puede derivar varias conclusiones en una misma ejecución.

### 8.2 Mecanismo de comprobación

`ejecutar_caso(caso)`:

1. Ejecuta `diagnosticar()` con los hechos del caso.
2. Obtiene las reglas aplicadas.
3. Obtiene las causas y sus factores de certeza.
4. Compara los valores obtenidos con los valores esperados.
5. Devuelve el resultado completo y los indicadores de coincidencia.

Las comprobaciones incluyen:

- Reglas obtenidas.
- Causas obtenidas.
- Estado del diagnóstico.
- Detección de ciclos cuando corresponde.

### 8.3 Casos especiales

- Entrada vacía: no se derivan conclusiones.
- Código 404: el dominio admite 404, pero ninguna regla lo utiliza.
- 401 sin autenticación: se deriva la categoría general, pero no la causa específica.
- 503 sin timeout: se deriva el origen externo, pero no se puede confirmar saturación.
- Hechos duplicados: se ignoran durante la inferencia.
- Base con ciclo: se detecta el ciclo y el motor termina sin entrar en bucle.

Las 15 reglas tienen al menos un caso que las ejercita.

---

## 9. Interfaz web con Streamlit

La interfaz está implementada en `src/app.py`. Streamlit ejecuta el archivo completo cuando ocurre una interacción y mantiene datos persistentes en `st.session_state`.

### 9.1 Configuración inicial

La aplicación define:

- Título de página.
- Icono.
- Título principal.
- Texto explicativo.
- Estado inicial de todos los widgets y resultados.

Los valores predeterminados se conservan en la sesión para que al seleccionar una causa o hacer clic en «¿Por qué?» no se pierda el diagnóstico.

### 9.2 Navegación lateral

La barra lateral contiene:

- Un selector de casos precargados.
- Un botón para limpiar toda la entrada y los resultados.
- Una advertencia contextual cuando se está mostrando un caso.

Los casos se cargan desde `CASOS_PRUEBA`. Cada opción se identifica con su número y descripción.

### 9.3 Entrada manual

El formulario contiene:

| Campo | Widget | Datos generados |
|---|---|---|
| Código HTTP | `st.selectbox` | `("ErrorHTTP", codigo)` |
| Autenticación | `st.radio` | `("Autenticacion", tipo)` |
| Síntomas | `st.multiselect` | Uno o varios `("Sintoma", sintoma)` |
| Contexto | `st.multiselect` | Uno o varios `("Contexto", contexto)` |
| Diagnosticar | `st.form_submit_button` | Construye los hechos y llama al motor |

Las opciones se toman directamente de los dominios de la base de conocimiento. Por ello, el formulario y la validación usan las mismas fuentes de valores.

### 9.4 Construcción de hechos

La función `_build_facts()` convierte los widgets en hechos del motor:

```python
hechos = []

if codigo is not None:
    hechos.append(("ErrorHTTP", codigo))

if autenticacion != "No aplica":
    hechos.append(("Autenticacion", autenticacion))

hechos.extend(("Sintoma", sintoma) for sintoma in sintomas)
hechos.extend(("Contexto", contexto) for contexto in contextos)
```

Después la aplicación:

1. Ejecuta `validar_hechos()`.
2. Ejecuta `diagnosticar()`.
3. Inserta los errores y advertencias obtenidos.
4. Guarda el resultado en `st.session_state`.

### 9.5 Caso precargado

Cuando el usuario selecciona un caso:

1. Streamlit establece el caso activo.
2. `ejecutar_caso()` ejecuta todos los hechos del caso.
3. El resultado se guarda con origen `"caso"`.
4. Los indicadores de coincidencia se guardan en la sesión.
5. `_show_resultado()` muestra el estado y comprueba las reglas esperadas.

Cuando el usuario vuelve a «Sin caso precargado», se limpia el resultado generado por el caso. Esto evita que el resultado anterior siga visible después de cambiar de modo.

### 9.6 Visualización de resultados

El estado determina el tipo de mensaje:

- `diagnostico_completo`: `st.success`
- `diagnostico_parcial`: `st.warning`
- `sin_conclusion`: `st.info`
- `entrada_invalida`: `st.error`

Los errores se muestran con `st.error`, las advertencias con `st.warning` y los ciclos con una advertencia específica.

Cada causa se presenta dentro de un contenedor con:

- Nombre de la causa.
- Factor de certeza mediante `st.metric`.
- Recomendación.
- Botón «¿Por qué?».

Al pulsar el botón, se llama a `porque()`. El texto obtenido se muestra con `st.code`.

También existe un desplegable «Explicación del razonamiento» que presenta el resultado completo de `explicar_razonamiento()`.

### 9.7 Estado de sesión

La interfaz mantiene claves separadas para:

- Código HTTP.
- Tipo de autenticación.
- Síntomas seleccionados.
- Contextos seleccionados.
- Caso precargado.
- Caso activo.
- Resultado.
- Origen del resultado.
- Comprobaciones del caso.
- Causa seleccionada para explicar.

Esta separación permite responder a las interacciones de Streamlit sin repetir el diagnóstico ni perder controles seleccionados.

---

## 10. Flujo completo del sistema

### 10.1 Diagnóstico manual

```text
Formulario manual
  → selección de widgets
  → _build_facts()
  → validar_hechos()
  → diagnosticar()
  → _ejecutar()
  → aplicar reglas
  → calcular CF
  → construir causas y recomendaciones
  → guardar resultado en session_state
  → _show_resultado()
  → mostrar tarjetas, explicaciones y mensajes
```

### 10.2 Ejemplo de flujo HTTP 401 con OAuth2

1. El usuario selecciona el código HTTP 401.
2. La interfaz agrega `("ErrorHTTP", 401)`.
3. El usuario selecciona OAuth2.
4. La interfaz agrega `("Autenticacion", "OAuth2")`.
5. R1 detecta el 401 y deriva credencial inválida con CF 0.90.
6. R4 combina credencial inválida y OAuth2 y deriva token vencido con CF 0.72.
7. R12 encuentra la solución asociada y deriva la recomendación.
8. La interfaz muestra la causa, el CF y el botón de explicación.

### 10.3 Ejemplo de resultado

```text
Causa: TokenVencido
Certeza: 0.72
Recomendación: ReautenticarCredencialOAuth2
```

Explicación simplificada:

```text
R1: ErrorHTTP(401) -> CategoriaFalla(CredencialInvalida)
R4: CredencialInvalida + Autenticacion(OAuth2) -> CausaRaiz(TokenVencido)
R12: CausaRaiz(TokenVencido) + Solucion(TokenVencido, ...) -> Recomendacion
```

---

## 11. Pruebas automáticas

### 11.1 Pruebas del motor

`tests/test_motor.py` contiene:

- 17 ejecuciones parametrizadas de los casos precargados.
- Una prueba que verifica exactamente 17 casos.
- Una prueba que confirma el diagnóstico `TokenVencido` con CF 0.72.

### 11.2 Pruebas de interfaz

`tests/test_app.py` utiliza `AppTest` de Streamlit para comprobar:

- Los 17 casos desde el selector lateral.
- El formulario manual.
- El cálculo mostrado por la interfaz.
- El botón «¿Por qué?».
- El botón de limpiar.
- La advertencia por OAuth2 y ApiKey simultáneos.

### 11.3 Ejecución manual de una prueba específica

```bash
python -m pytest tests/test_motor.py -v
python -m pytest tests/test_app.py -v
```

---

## 12. Desarrollo realizado

El proyecto se desarrolló por etapas:

1. **Selección del dominio:** diagnóstico de errores en workflows de n8n.
2. **Identificación de hechos observables:** códigos HTTP, autenticación, síntomas y contexto.
3. **Formalización del conocimiento:** definición de predicados, dominios y categorías.
4. **Diseño de reglas:** escritura de reglas R1 a R15 con factores de certeza.
5. **Implementación del motor:** unificación, encadenamiento hacia adelante y explicación.
6. **Creación de casos:** funcionales, multifalla y casos de borde.
7. **Pruebas automatizadas:** validación del motor y los casos.
8. **Separación en módulos:** paso del desarrollo original del notebook a archivos Python.
9. **Interfaz web:** integración de Streamlit con el motor.
10. **Pruebas de integración:** verificación de formularios, botones y casos precargados.
11. **Documentación:** README, validación de casos, traspaso e este documento técnico.

---

## 13. Ejemplo de uso desde Python

```python
from motor_inferencia import diagnosticar

hechos = [
    ("ErrorHTTP", 429),
    ("Contexto", "ProcesaMuchosItems"),
]

resultado = diagnosticar(hechos)

for causa in resultado["causas"]:
    print(causa["causa"])
    print(causa["certeza"])
    print(causa["recomendacion"])
```

Salida esperada:

```text
RafagaDeSolicitudes
0.85
UsarLoopOverItemsConWait
```

---

## 14. Limitaciones y posibles mejoras

Las principales limitaciones actuales son:

- El diagnóstico no conoce el nombre real del nodo n8n; trabaja sobre el workflow en conjunto.
- La base contiene reglas definidas manualmente.
- Las causas no se ordenan explícitamente por certeza dentro del motor; el orden depende de las reglas y hechos derivados.
- Los factores de certeza se calculan con la fórmula de mínimo, no con otros modelos probabilísticos.
- La interfaz no persiste diagnósticos entre reinicios del servidor.
- No existe una API REST separada; Streamlit consume directamente las funciones Python.

Posibles extensiones futuras:

- Relacionar síntomas con identificadores concretos de nodos.
- Permitir agregar reglas desde una interfaz administrativa.
- Añadir autenticación de usuarios.
- Guardar diagnósticos en una base de datos.
- Exportar reportes PDF o CSV.
- Incorporar una API FastAPI para separar completamente backend y frontend.
- Integrar llamadas a una API de n8n para obtener fallas reales de workflows.

---

## 15. Referencias del repositorio

- [README principal](README.md)
- [Guía de traspaso](docs/traspaso.md)
- [Casos de prueba](tests/casos_prueba.md)
- [Notebook original](notebooks/Lopez_Narvaez_proyecto_final_sbc.ipynb)
- [Backend: base de conocimiento](src/base_conocimiento.py)
- [Backend: motor](src/motor_inferencia.py)
- [Backend: casos](src/casos_prueba.py)
- [Frontend: aplicación Streamlit](src/app.py)
