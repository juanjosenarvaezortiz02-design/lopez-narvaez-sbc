# Base de conocimiento del sistema experto

## 1. Objetivo de este documento

Este documento explica cómo está diseñada la base de conocimiento ubicada en [src/base_conocimiento.py](C:\Users\juanj\OneDrive\Documentos\Universidad FULL\SEMESTRE IX\Inteligencia_artificial\Proyecto-final-Sistema-experto-con-interfaz-web\lopez-narvaez-sbc\src\base_conocimiento.py).

Su propósito no es solo enumerar reglas. También describe:

- Qué problema representa la base.
- Qué conocimiento se decidió almacenar.
- Por qué se separó el conocimiento en dominios, predicados, reglas y soluciones.
- Qué significa cada regla.
- Qué factores de certeza se utilizaron.
- Qué comportamiento cumple el sistema.
- Qué decisiones limitan el conocimiento actual.

La implementación corresponde a un sistema experto basado en reglas de producción y encadenamiento hacia adelante.

---

## 2. Qué es la base de conocimiento

La base de conocimiento contiene el conocimiento declarativo que permite diagnosticar fallas en workflows de n8n.

No contiene directamente el proceso de inferencia. Las responsabilidades están separadas así:

| Componente | Responsabilidad |
|---|---|
| [src/base_conocimiento.py](C:\Users\juanj\OneDrive\Documentos\Universidad FULL\SEMESTRE IX\Inteligencia_artificial\Proyecto-final-Sistema-experto-con-interfaz-web\lopez-narvaez-sbc\src\base_conocimiento.py) | Almacena dominios, predicados, hechos estáticos y reglas. |
| [src/motor_inferencia.py](C:\Users\juanj\OneDrive\Documentos\Universidad FULL\SEMESTRE IX\Inteligencia_artificial\Proyecto-final-Sistema-experto-con-interfaz-web\lopez-narvaez-sbc\src\motor_inferencia.py) | Aplica las reglas, valida los datos y explica el razonamiento. |
| [src/casos_prueba.py](C:\Users\juanj\OneDrive\Documentos\Universidad FULL\SEMESTRE IX\Inteligencia_artificial\Proyecto-final-Sistema-experto-con-interfaz-web\lopez-narvaez-sbc\src\casos_prueba.py) | Proporciona casos observables para comprobar el conocimiento. |

Esta separación permite modificar reglas sin modificar el algoritmo que las ejecuta.

---

## 3. Dominio resuelto

Se eligió el diagnóstico de fallas en workflows de n8n. n8n puede presentar problemas relacionados con credenciales, permisos, límites de solicitudes, servicios externos, webhooks, filtros, expresiones y volumen de datos.

El conocimiento se decidió limitar a hechos que pueden ser identificados por un usuario o capturados visualmente desde una ejecución:

- Códigos HTTP.
- Tipo de autenticación.
- Síntomas observables.
- Condiciones de contexto.

Se excluyeron de esta primera versión:

- Diagnósticos basados en registros completos del sistema.
- Acceso directo a servicios externos.
- Ejecución automática de acciones correctivas.
- Aprendizaje de nuevas reglas desde la experiencia.

Esta limitación se hizo porque el proyecto requiere un sistema experto comprensible y evaluable. El usuario introduce hechos observables y recibe una conclusión explicada.

---

## 4. Universos de discurso

Los dominios se representan en el diccionario `DOMINIOS`.

### 4.1 `K`: códigos HTTP

```python
"K": range(100, 600)
```

Incluye valores enteros del 100 al 599. Esto permite validar errores que pertenecen al rango estándar de códigos HTTP.

Se eligió un rango amplio para que el motor pueda distinguir códigos válidos de valores inválidos. Sin embargo, no todas las respuestas HTTP tienen una regla asociada. Por ejemplo, 404 es un código válido, pero no activa ninguna conclusión porque no fue incluido en el alcance diagnóstico.

### 4.2 `T`: autenticación

```python
"T": ["OAuth2", "ApiKey"]
```

Son los dos mecanismos de autenticación considerados por las reglas actuales.

Se incluyó este dominio porque 401 puede tener diferentes causas según el tipo de credencial y 403 puede requerir un diagnóstico distinto.

### 4.3 `SIN`: síntomas

```python
"SIN": [
    "WebhookSinEjecuciones",
    "DatosVacios",
    "ExpresionInvalida",
    "TimeoutNodo",
]
```

Los síntomas representan lo que el usuario observa directamente. Se separaron de los códigos HTTP porque existen fallas que no producen necesariamente un código de error.

### 4.4 `CTX`: contexto

```python
"CTX": [
    "ProcesaMuchosItems",
    "WorkflowInactivo",
    "UsaURLTest",
    "FiltroPrevioDescartaTodo",
]
```

El contexto incluye condiciones adicionales que ayudan a distinguir una causa probable de otra.

Se agregó este dominio porque dos workflows pueden presentar el mismo síntoma por causas diferentes.

### 4.5 `F`: categorías de falla

Agrupa diagnósticos genéricos:

- `CredencialInvalida`
- `LimiteRateExcedido`
- `ErrorServidorExterno`
- `PermisosInsuficientes`

Estas categorías permiten encadenar el conocimiento por niveles:

```text
Síntoma o código HTTP
        ↓
Categoría general
        ↓
Causa específica
        ↓
Recomendación
```

### 4.6 `C`: causas raíz

Contiene diez causas específicas que el sistema puede concluir.

Una causa raíz describe el problema probable con mayor precisión que una categoría general. Por ejemplo:

```text
CategoriaFalla(CredencialInvalida)
        ↓
CausaRaiz(TokenVencido)
```

### 4.7 `S`: soluciones

Contiene las acciones correctivas disponibles. Las soluciones están expresadas con nombres descriptivos para mantener consistencia con el resto de los hechos.

---

## 5. Predicados

Se definieron ocho predicados en el diccionario `PREDICADOS`. Se utilizaron predicados y no variables sueltas para que cada hecho tenga significado, dominio y capa conocidos.

### 5.1 Predicados observables

| Predicado | Hecho producido | Razón de su existencia |
|---|---|---|
| `ErrorHTTP(n, c)` | `("ErrorHTTP", 401)` | Representa el código HTTP observado en un nodo. |
| `Autenticacion(n, t)` | `("Autenticacion", "OAuth2")` | Permite distinguir tipos de credencial. |
| `Sintoma(x, s)` | `("Sintoma", "TimeoutNodo")` | Representa problemas visibles sin código HTTP. |
| `Contexto(x, k)` | `("Contexto", "ProcesaMuchosItems")` | Añade condiciones que modifican el diagnóstico. |

Solo estos cuatro predicados pueden ingresarse directamente desde el usuario. La interfaz construye hechos utilizando únicamente esta capa observable.

### 5.2 Predicados intermedios

`CategoriaFalla(n, f)` representa una clasificación general derivada principalmente de un código HTTP.

El sistema no presenta esta clasificación como causa final. Se utiliza como escalón necesario para concluir una causa más específica.

### 5.3 Predicados de diagnóstico

| Predicado | Significado |
|---|---|
| `CausaRaiz(x, c)` | Indica la causa probable del problema. |
| `Recomendar(x, s)` | Indica una acción correctiva asociada a la causa. |

Estos predicados no se aceptan como entrada. Solo pueden ser derivados por las reglas.

### 5.4 Predicado de catálogo

`Solucion(c, s)` relaciona una causa con una acción correctiva. Su catálogo se convierte en hechos estáticos:

```python
("Solucion", causa, solucion)
```

Esto permite mantener las soluciones como conocimiento separado y no repetirlas dentro de cada regla.

---

## 6. Catálogo de soluciones

El diccionario `SOLUCIONES` relaciona cada causa raíz con una sola solución principal.

| Causa | Solución | Problema que pretende resolver |
|---|---|---|
| `TokenVencido` | `ReautenticarCredencialOAuth2` | Renovar o recuperar una credencial OAuth2 vencida. |
| `ApiKeyIncorrecta` | `RegenerarYActualizarApiKey` | Corregir una clave API inválida o desactualizada. |
| `RafagaDeSolicitudes` | `UsarLoopOverItemsConWait` | Evitar exceder el límite de solicitudes. |
| `ServicioExternoSaturado` | `ActivarRetryOnFailConEspera` | Reintentar temporalmente ante saturación del servicio. |
| `WorkflowDesactivado` | `ActivarElWorkflow` | Permitir que el webhook se ejecute. |
| `URLDePruebaEnProduccion` | `UsarLaURLDeProduccionDelWebhook` | Usar la dirección correspondiente al entorno activo. |
| `FiltroDemasiadoRestrictivo` | `RevisarCondicionesDelFiltro` | Permitir que los datos pasen por una condición válida. |
| `ReferenciaACampoInexistente` | `CorregirExpresionYVerificarEstructuraJSON` | Evitar referencias a campos que no existen. |
| `ScopesInsuficientes` | `ReautorizarCredencialConScopesCorrectos` | Otorgar permisos OAuth2 necesarios. |
| `TimeoutPorVolumen` | `DividirEnLotesConSplitInBatches` | Reducir el tamaño de la carga procesada. |

Se utilizó una relación causa–solución porque permite que R12 derive recomendaciones de forma genérica sin incluir un catálogo completo dentro de cada causa.

---

## 7. Reglas de producción

Las reglas se construyen mediante `crear_regla()` y tienen la estructura:

```python
{
    "nombre",
    "descripcion",
    "grupo",
    "condiciones",
    "restricciones",
    "conclusion",
    "certeza",
}
```

Las condiciones son patrones. Un valor que comienza con `?` representa una variable.

Por ejemplo:

```python
[("ErrorHTTP", "?c")]
```

representa cualquier código HTTP. La restricción posterior determina cuáles códigos cumplen la regla:

```python
[("?c", ">=", 500)]
```

### 7.1 R1: credencial inválida por 401

- Hecho: `ErrorHTTP(401)`
- Conclusión: `CategoriaFalla(CredencialInvalida)`
- CF: `0.90`

Se utiliza un 401 porque una respuesta HTTP no autorizada suele indicar que la credencial no fue aceptada.

### 7.2 R2: límite excedido por 429

- Hecho: `ErrorHTTP(429)`
- Conclusión: `CategoriaFalla(LimiteRateExcedido)`
- CF: `0.95`

El 429 tiene un significado de límite de solicitudes más específico que otros errores. Por eso conserva una certeza alta.

### 7.3 R3: error externo por códigos 5xx

- Hecho: código mayor o igual a 500
- Conclusión: `CategoriaFalla(ErrorServidorExterno)`
- CF: `0.90`

Se utiliza una variable y una restricción para admitir varios códigos 5xx sin escribir una regla por cada uno.

### 7.4 R4 y R5: clasificación de credenciales

Si existe una credencial inválida:

- OAuth2 deriva `TokenVencido` con CF 0.80.
- API Key deriva `ApiKeyIncorrecta` con CF 0.75.

Se separaron las reglas porque el método de autenticación modifica directamente la acción correctiva.

### 7.5 R6: ráfaga por muchos items

Combina:

- `CategoriaFalla(LimiteRateExcedido)`
- `Contexto(ProcesaMuchosItems)`

Esta combinación deriva `RafagaDeSolicitudes` con CF 0.90.

Una sola condición no permite determinar el volumen. El contexto hace que la causa sea más precisa.

### 7.6 R7: servicio externo saturado

Combina:

- `CategoriaFalla(ErrorServidorExterno)`
- `Sintoma(TimeoutNodo)`

La conclusión es `ServicioExternoSaturado` con CF 0.75.

Se utiliza una certeza menor porque un timeout puede tener causas adicionales, no necesariamente saturación del servicio.

### 7.7 R8 y R9: webhook sin ejecuciones

El síntoma `WebhookSinEjecuciones` puede tener al menos dos causas:

- Workflow inactivo: `WorkflowDesactivado`.
- Uso de URL de prueba: `URLDePruebaEnProduccion`.

La condición de contexto evita concluir una única causa a partir del síntoma general.

### 7.8 R10: filtro demasiado restrictivo

Combina datos vacíos con un filtro que descarta todos los registros.

Conclusión:

```text
CausaRaiz(FiltroDemasiadoRestrictivo)
CF = 0.85
```

Sin el contexto, los datos vacíos podrían deberse a otras fuentes.

### 7.9 R11: expresión inválida

Una expresión inválida deriva directamente una referencia a un campo inexistente.

Esta regla tiene CF 0.80 porque una expresión puede ser inválida por diferentes motivos.

### 7.10 R12: generación de recomendaciones

R12 relaciona una causa raíz con su solución:

```text
CausaRaiz(?c) + Solucion(?c, ?s)
        ↓
Recomendar(?s)
CF = 1.00
```

Esta regla aplica el mismo mecanismo a todas las causas. Su certeza es 1.00 porque representa una relación de catálogo definida previamente, no una inferencia probabilística adicional.

### 7.11 R13 y R14: permisos insuficientes

R13 convierte un 403 en la categoría `PermisosInsuficientes`.

R14 combina esta categoría con OAuth2 y deriva `ScopesInsuficientes`.

No existe una conclusión equivalente con API Key en esta versión. La regla R14 está limitada a OAuth2 porque los alcances de permisos son propios de ese tipo de credencial.

### 7.12 R15: timeout por volumen

Combina timeout con procesamiento de muchos items.

Conclusión:

```text
CausaRaiz(TimeoutPorVolumen)
CF = 0.80
```

La certeza no es máxima porque el volumen es una causa probable, pero no la única fuente de timeout.

---

## 8. Factores de certeza

Los hechos observados tienen CF inicial de `1.00`.

Las conclusiones utilizan la fórmula:

```text
CF(conclusion) =
    min(CF de las condiciones) × CF de la regla
```

El resultado se redondea a dos decimales.

### Ejemplo: OAuth2 con 401

```text
ErrorHTTP(401)                 CF 1.00
R1                             CF 0.90
Categoría credencial inválida  CF 0.90

CategoriaFalla(...) + OAuth2  CF 0.90
R4                             CF 0.80
Causa TokenVencido             CF 0.72

R12                            CF 1.00
Recomendación                  CF 0.72
```

Por esto el caso de 401 con OAuth2 devuelve:

```text
TokenVencido
CF = 0.72
ReautenticarCredencialOAuth2
```

El uso de la regla R12 no reduce el resultado porque su certeza es 1.00.

---

## 9. Hechos estáticos

Las relaciones `Solucion(c, s)` se generan automáticamente desde `SOLUCIONES`:

```python
HECHOS_ESTATICOS = [
    ("Solucion", c, s)
    for c, s in SOLUCIONES.items()
]
```

Son hechos estáticos porque representan conocimiento definido por el experto y no datos observados por el usuario.

Su factor de certeza es 1.00. Esto permite que R12 derive una recomendación sin introducir incertidumbre adicional por el catálogo.

---

## 10. Construcción de la base

`crear_base_conocimiento()` reúne:

```python
{
    "reglas": REGLAS,
    "hechos_estaticos": HECHOS_ESTATICOS,
}
```

`BASE_CONOCIMIENTO` contiene la base final que utiliza el motor por defecto.

Esta estructura facilita crear bases alternativas para pruebas. Por ejemplo, el caso 17 utiliza una base con reglas `A -> B -> A` para comprobar que el motor detecta ciclos.

---

## 11. Por qué se organizó así

La organización fue diseñada para cumplir varios objetivos académicos y técnicos.

### 11.1 Representación formal

Los predicados imitan expresiones de lógica de predicados:

```text
ErrorHTTP(n, c)
Autenticacion(n, t)
Sintoma(x, s)
CausaRaiz(x, c)
Solucion(c, s)
```

Esto permite relacionar hechos reales con el contenido formal de la asignatura.

### 11.2 Encadenamiento hacia adelante

Las reglas siguen una estructura que el motor puede ejecutar:

```text
condiciones -> conclusión
```

El encadenamiento comienza con hechos observables y avanza hacia categorías, causas y soluciones.

### 11.3 Separación entre conocimiento y algoritmo

Las reglas están declaradas como datos. El motor no contiene una instrucción `if/elif` para cada diagnóstico.

De este modo, una regla puede modificarse o agregarse sin reescribir por completo el motor.

### 11.4 Explicación

Cada regla incluye una descripción legible y conserva las condiciones utilizadas.

Esto permite reconstruir:

- Qué regla se aplicó.
- Qué hechos la hicieron aplicable.
- Qué conclusión produjo.
- Qué certeza obtuvo.

### 11.5 Validación

Los dominios permiten que el motor rechace hechos fuera del conocimiento. Por ejemplo:

- Un predicado desconocido genera un error.
- Un código que no sea entero genera un error.
- Un tipo de autenticación distinto de OAuth2 o API Key genera un error.
- Un hecho derivado usado como entrada genera un error.

### 11.6 Capacidad de crecimiento

El proyecto puede ampliar su base agregando:

- Nuevos predicados observables.
- Nuevos dominios.
- Nuevas causas.
- Nuevas soluciones.
- Nuevas reglas.
- Nuevos casos de prueba.

Toda modificación debe mantener su coherencia con el motor y los dominios.

---

## 12. Qué funciona actualmente

La base de conocimiento actual cumple las siguientes funciones verificadas:

- Define ocho predicados.
- Define cuatro predicados observables utilizables por el usuario.
- Define seis niveles de catálogo y dominios.
- Contiene 15 reglas de producción.
- Contiene 10 causas raíz.
- Contiene 10 soluciones.
- Convierte el catálogo de soluciones en hechos estáticos.
- Permite encadenar reglas hasta alcanzar una recomendación.
- Permite derivar varias causas desde hechos simultáneos.
- Permite informar falta de datos mediante diagnóstico parcial.
- Permite rechazar hechos fuera del dominio.
- Permite conservar el factor de certeza de cada causa.
- Permite explicar qué reglas produjeron una conclusión.
- Permite cubrir las 15 reglas mediante casos de prueba.

La cobertura y la validación están documentadas en [tests/casos_prueba.md](C:\Users\juanj\OneDrive\Documentos\Universidad FULL\SEMESTRE IX\Inteligencia_artificial\Proyecto-final-Sistema-experto-con-interfaz-web\lopez-narvaez-sbc\tests\casos_prueba.md).

---

## 13. Comportamientos comprobados

Los casos principales que verifican la base son:

| Hechos | Reglas esperadas | Resultado |
|---|---|---|
| 401 + OAuth2 | R1, R4, R12 | `TokenVencido`, CF 0.72 |
| 429 + muchos items | R2, R6, R12 | `RafagaDeSolicitudes`, CF 0.85 |
| 503 + timeout | R3, R7, R12 | `ServicioExternoSaturado`, CF 0.68 |
| Webhook sin ejecuciones + workflow inactivo | R8, R12 | `WorkflowDesactivado`, CF 0.95 |
| Datos vacíos + filtro restrictivo | R10, R12 | `FiltroDemasiadoRestrictivo`, CF 0.85 |
| Expresión inválida | R11, R12 | `ReferenciaACampoInexistente`, CF 0.80 |
| 403 + OAuth2 | R13, R14, R12 | `ScopesInsuficientes`, CF 0.72 |
| Timeout + muchos items | R15, R12 | `TimeoutPorVolumen`, CF 0.80 |

Los casos de borde comprueban entrada vacía, código 404, ausencia de autenticación, duplicados y ciclos.

---

## 14. Limitaciones conocidas

La base no representa actualmente:

- Nombres individuales de nodos n8n.
- Evidencia adicional procedente de logs.
- Dependencias temporales entre acciones.
- Varias soluciones alternativas para una causa.
- Diagnósticos probabilísticos distintos del mínimo de certeza.
- Confianza independiente para categorías derivadas.
- Aprendizaje o actualización automática de reglas.
- Reglas específicas por proveedor o integración.

También existe una limitación semántica: un conjunto de hechos puede activar varias causas y presentarlas simultáneamente. Esto representa una multifalla, pero no confirma que todas sean independientes ni determina cuál debe corregirse primero.

---

## 15. Relación con los requisitos académicos

La base de conocimiento implementa los elementos principales de un sistema basado en conocimiento:

1. Universos de discurso.
2. Predicados y hechos.
3. Reglas de producción.
4. Hechos observables.
5. Hechos derivados.
6. Encadenamiento hacia adelante.
7. Factores de certeza.
8. Explicación del razonamiento.
9. Validación de entradas.
10. Casos de prueba.

Las reglas no son simples respuestas escritas en el frontend. Se almacenan en la base de conocimiento y son interpretadas por el motor de inferencia.

Esta estructura permite demostrar que el proyecto no solo muestra resultados definidos previamente, sino que aplica las reglas sobre hechos ingresados por el usuario.

---

## 16. Conclusión

La base de conocimiento fue diseñada en capas:

```text
Hechos observables
    ↓
Categorías generales
    ↓
Causas raíz específicas
    ↓
Acciones correctivas
```

Se hizo así para reflejar la forma en que se diagnostican fallas: primero se observa un síntoma o código, luego se clasifica el problema y finalmente se determina una causa probable y una acción.

El diseño cumple su objetivo actual porque permite representar el dominio, validar datos, aplicar inferencia hacia adelante, calcular certeza, generar recomendaciones y explicar los resultados. Las reglas están separadas del algoritmo y pueden ampliarse mediante nuevos predicados, dominios, hechos estáticos y casos de prueba.
