# Casos de prueba y validación

Sistema experto para el diagnóstico de fallas en workflows de n8n.
Los casos están definidos en `src/casos_prueba.py` y se ejecutan con `pytest` (`tests/test_motor.py`).

**Resultado: 17 de 17 casos satisfactorios.**

## 1. Tabla de validación

| Caso | Tipo | Descripción | Hechos iniciales | Reglas esperadas | Conclusión esperada | Resultado obtenido | Estado |
|---|---|---|---|---|---|---|---|
| 1 | Funcional | 401 con OAuth2 | ErrorHTTP(401), Autenticacion(OAuth2) | R1 → R4 → R12 | TokenVencido → ReautenticarCredencialOAuth2 | R1 → R4 → R12 · TokenVencido (CF 0.72) | ✅ Satisfactorio |
| 2 | Funcional | 429 con muchos items | ErrorHTTP(429), Contexto(ProcesaMuchosItems) | R2 → R6 → R12 | RafagaDeSolicitudes → UsarLoopOverItemsConWait | R2 → R6 → R12 · RafagaDeSolicitudes (CF 0.85) | ✅ Satisfactorio |
| 3 | Funcional | 503 con timeout | ErrorHTTP(503), Sintoma(TimeoutNodo) | R3 → R7 → R12 | ServicioExternoSaturado → ActivarRetryOnFailConEspera | R3 → R7 → R12 · ServicioExternoSaturado (CF 0.68) | ✅ Satisfactorio |
| 4 | Funcional | Webhook sin ejecuciones, workflow inactivo | Sintoma(WebhookSinEjecuciones), Contexto(WorkflowInactivo) | R8 → R12 | WorkflowDesactivado → ActivarElWorkflow | R8 → R12 · WorkflowDesactivado (CF 0.95) | ✅ Satisfactorio |
| 5 | Funcional | Webhook sin ejecuciones, URL de prueba | Sintoma(WebhookSinEjecuciones), Contexto(UsaURLTest) | R9 → R12 | URLDePruebaEnProduccion → UsarLaURLDeProduccionDelWebhook | R9 → R12 · URLDePruebaEnProduccion (CF 0.90) | ✅ Satisfactorio |
| 6 | Funcional | Datos vacíos tras un filtro | Sintoma(DatosVacios), Contexto(FiltroPrevioDescartaTodo) | R10 → R12 | FiltroDemasiadoRestrictivo → RevisarCondicionesDelFiltro | R10 → R12 · FiltroDemasiadoRestrictivo (CF 0.85) | ✅ Satisfactorio |
| 7 | Funcional | 401 con API Key | ErrorHTTP(401), Autenticacion(ApiKey) | R1 → R5 → R12 | ApiKeyIncorrecta → RegenerarYActualizarApiKey | R1 → R5 → R12 · ApiKeyIncorrecta (CF 0.68) | ✅ Satisfactorio |
| 8 | Funcional | Expresión con campo inexistente | Sintoma(ExpresionInvalida) | R11 → R12 | ReferenciaACampoInexistente → CorregirExpresionYVerificarEstructuraJSON | R11 → R12 · ReferenciaACampoInexistente (CF 0.80) | ✅ Satisfactorio |
| 9 | Funcional | 403 con OAuth2 (ampliación) | ErrorHTTP(403), Autenticacion(OAuth2) | R13 → R14 → R12 | ScopesInsuficientes → ReautorizarCredencialConScopesCorrectos | R13 → R14 → R12 · ScopesInsuficientes (CF 0.72) | ✅ Satisfactorio |
| 10 | Funcional | Timeout con muchos items (ampliación) | Sintoma(TimeoutNodo), Contexto(ProcesaMuchosItems) | R15 → R12 | TimeoutPorVolumen → DividirEnLotesConSplitInBatches | R15 → R12 · TimeoutPorVolumen (CF 0.80) | ✅ Satisfactorio |
| 11 | Multifalla | Workflow con fallas simultáneas (14 de 15 reglas) | 13 hechos (ver código) | (todas las de las 9 causas) | 9 causas raíz, cada una con su recomendación | 22 reglas (14 distintas) · 9 causas | ✅ Satisfactorio |
| 12 | Sin conclusión | Sin hechos de entrada | (ninguno) | ninguna | Ninguna (entrada vacía) | Sin conclusión | ✅ Satisfactorio |
| 13 | Sin conclusión | 404: código fuera del alcance | ErrorHTTP(404) | ninguna | Ninguna (ninguna regla aplica) | Sin conclusión | ✅ Satisfactorio |
| 14 | Borde | 401 sin tipo de autenticación | ErrorHTTP(401) | R1 | Solo CategoriaFalla(CredencialInvalida) | R1 · solo información parcial | ✅ Satisfactorio |
| 15 | Borde | 503 sin timeout | ErrorHTTP(503) | R3 | Solo CategoriaFalla(ErrorServidorExterno) | R3 · solo información parcial | ✅ Satisfactorio |
| 16 | Borde | Hechos duplicados | ErrorHTTP(401), ErrorHTTP(401), Autenticacion(OAuth2) | R1 → R4 → R12 | TokenVencido (igual que el caso 1) | R1 → R4 → R12 · TokenVencido (CF 0.72) | ✅ Satisfactorio |
| 17 | Borde | Base con ciclo A→B→A (no debe colgarse) | A() | RA | Termina; detecta el ciclo | RA · solo información parcial | ✅ Satisfactorio |

> El aviso `WARNING` del caso 17 es esperado: el motor detecta el ciclo A→B→A de la base de juguete.

## 2. Matriz de cobertura

| Regla | Descripción | Casos que la ejercitan |
|---|---|---|
| R1 | Un 401 indica credencial inválida | 1, 7, 11, 14, 16 |
| R2 | Un 429 indica límite de solicitudes excedido | 2, 11 |
| R3 | Un código ≥ 500 indica error del servidor externo | 3, 11, 15 |
| R4 | Credencial inválida con OAuth2: token vencido | 1, 11, 16 |
| R5 | Credencial inválida con API Key: clave incorrecta | 7 |
| R6 | Límite excedido con muchos items: ráfaga de solicitudes | 2, 11 |
| R7 | Error del servidor con timeout: servicio saturado | 3, 11 |
| R8 | Webhook sin ejecuciones con workflow inactivo | 4, 11 |
| R9 | Webhook sin ejecuciones con URL de prueba en uso | 5, 11 |
| R10 | Datos vacíos tras un filtro que descarta todo | 6, 11 |
| R11 | Expresión inválida: referencia a un campo inexistente | 8, 11 |
| R12 | Toda causa raíz con solución en el catálogo genera una recomendación | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16 |
| R13 | Un 403 indica permisos insuficientes | 9, 11 |
| R14 | Permisos insuficientes con OAuth2: scopes insuficientes | 9, 11 |
| R15 | Timeout con muchos items: lote demasiado grande | 10, 11 |

Reglas cubiertas: **15 de 15**.

## 3. Nota sobre el caso 11 (fallas simultáneas)

Los hechos no indican a qué nodo pertenecen, así que el caso 11 representa **un workflow con varias fallas simultáneas**, no varios nodos distintos. Activa 14 de las 15 reglas (R5 no, porque un nodo no puede usar OAuth2 y ApiKey a la vez) y deriva 9 causas:

```
Reglas aplicadas: 22  |  Reglas distintas: 14  |  Iteraciones: 3

CF 0.95  WorkflowDesactivado            → ActivarElWorkflow
CF 0.90  URLDePruebaEnProduccion        → UsarLaURLDeProduccionDelWebhook
CF 0.85  RafagaDeSolicitudes            → UsarLoopOverItemsConWait
CF 0.85  FiltroDemasiadoRestrictivo     → RevisarCondicionesDelFiltro
CF 0.80  ReferenciaACampoInexistente    → CorregirExpresionYVerificarEstructuraJSON
CF 0.80  TimeoutPorVolumen              → DividirEnLotesConSplitInBatches
CF 0.72  TokenVencido                   → ReautenticarCredencialOAuth2
CF 0.72  ScopesInsuficientes            → ReautorizarCredencialConScopesCorrectos
CF 0.68  ServicioExternoSaturado        → ActivarRetryOnFailConEspera
```
