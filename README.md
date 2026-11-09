# Sistema experto para el diagnóstico de fallas en workflows de n8n

**Fundación Universitaria Los Libertadores** · Ingeniería de Sistemas · Inteligencia Artificial II
**Proyecto final:** Sistema experto con interfaz web

| | |
|---|---|
| **Autores** | Laura Daniela Lopez Santos · Juan Jose Narvaez Ortiz |
| **Docente** | Gonzalo Ricardo Novoa |
| **Estado** | Fase Rol A terminada (backend + pruebas) · etiqueta `v1-backend` |

---

## Contenido

1. [¿Qué hace el sistema?](#1-qué-hace-el-sistema)
2. [Estructura del repositorio](#2-estructura-del-repositorio)
3. [Instalación y ejecución](#3-instalación-y-ejecución)
4. [Paso a paso de lo que se hizo](#4-paso-a-paso-de-lo-que-se-hizo)
5. [Base de conocimiento](#5-base-de-conocimiento)
6. [Motor de inferencia](#6-motor-de-inferencia)
7. [Casos de prueba](#7-casos-de-prueba)
8. [Ejemplo de uso](#8-ejemplo-de-uso)
9. [Pendiente (Rol B)](#9-pendiente-rol-b)

---

## 1. ¿Qué hace el sistema?

n8n es una plataforma de automatización que conecta servicios (APIs, webhooks, bases de datos) mediante *workflows* formados por nodos. Cuando un workflow falla, el usuario indica **qué observa** (códigos HTTP, timeouts, nodos sin datos, webhooks que no disparan) y **en qué contexto** (tipo de autenticación, volumen de datos, workflow inactivo…).

A partir de esos hechos, el sistema:

1. **Deduce la causa raíz probable** usando reglas de producción y encadenamiento hacia adelante.
2. **Asigna un factor de certeza (CF)** a cada conclusión.
3. **Recomienda una acción correctiva.**
4. **Explica qué reglas usó** y por qué llegó a esa conclusión (función `porque()`).

---

## 2. Estructura del repositorio

```
lopez-narvaez-sbc/
│
├── README.md                 # Este archivo
├── requirements.txt          # Dependencias (streamlit, pytest)
├── pytest.ini                # Configuración de pytest (pythonpath = src)
├── .gitignore                # Excluye *.pyc y .pytest_cache/
│
├── src/
│   ├── base_conocimiento.py  # DOMINIOS, PREDICADOS, SOLUCIONES, REGLAS, BASE_CONOCIMIENTO
│   ├── motor_inferencia.py   # Motor, explicación, validación, diagnosticar()
│   └── casos_prueba.py       # CASOS_PRUEBA (17) y ejecutar_caso()
│
├── tests/
│   ├── test_motor.py         # Pruebas automáticas con pytest
│   └── casos_prueba.md       # Tabla de validación, cobertura y nota del caso 11
│
├── docs/
│   ├── traspaso.md           # Guía de traspaso Rol A → Rol B y boceto de interfaz
│   └── capturas/             # Capturas de pantalla para la documentación
│
└── notebooks/
    └── Lopez_Narvaez_proyecto_final_sbc.ipynb   # Notebook original con todo el desarrollo
```

---

## 3. Instalación y ejecución

**Requisitos:** Python 3.10 o superior y Git.

```bash
# 1. Clonar el repositorio
git clone https://github.com/juanjosenarvaezortiz02-design/lopez-narvaez-sbc.git
cd lopez-narvaez-sbc

# 2. Instalar dependencias
python -m pip install -r requirements.txt

# 3. Ejecutar las pruebas
python -m pytest -v
```

Resultado esperado: **`19 passed`** (17 casos de prueba + 2 pruebas adicionales).

---

## 4. Paso a paso de lo que se hizo

### Paso 1. Definición del dominio
Se eligió el **troubleshooting de workflows en n8n** como dominio de diagnóstico técnico. Se delimitó el alcance: errores de autenticación (401), permisos (403), límites de uso (429), fallas del servidor externo (5xx), timeouts por volumen, webhooks que no se activan, nodos sin datos y expresiones inválidas.

### Paso 2. Formalización del conocimiento
- Se definieron los **universos de discurso** (códigos HTTP, tipos de autenticación, síntomas, contextos, categorías, causas y soluciones).
- Se definieron **8 predicados** con su tipo, dominio y rango.
- Se escribieron **15 reglas en lógica de predicados** (R1–R12 de la Actividad 4 y R13–R15 como ampliación).
- Cada regla se tradujo a formato **SI-ENTONCES** y se le asignó un **factor de certeza**.

### Paso 3. Implementación en el notebook
Todo se desarrolló primero en `notebooks/Lopez_Narvaez_proyecto_final_sbc.ipynb`, organizado por módulos (una celda por módulo). La lógica **no imprime nada**: devuelve datos para que el notebook o la interfaz los muestren.

### Paso 4. Creación del repositorio y la estructura de carpetas
Se clonó el repositorio de GitHub y se crearon las carpetas `src/`, `tests/`, `docs/` y `notebooks/`, junto con `requirements.txt` y `pytest.ini`.

### Paso 5. Paso del notebook a módulos de Python
Cada celda del notebook se copió a su archivo en `src/`:

| Celda del notebook | Archivo | Ajuste realizado |
|---|---|---|
| 5.1 Base de conocimiento | `src/base_conocimiento.py` | Ninguno |
| 5.2 Motor de inferencia | `src/motor_inferencia.py` | Se activó el `import` desde `base_conocimiento` |
| 6.1 Casos de prueba | `src/casos_prueba.py` | Se agregaron los `import` del motor y de la base |

### Paso 6. Pruebas automáticas con pytest
Se creó `tests/test_motor.py`, que ejecuta los 17 casos de `CASOS_PRUEBA` y además verifica:
- que existan exactamente 17 casos;
- que un 401 con OAuth2 dé `TokenVencido` con CF = 0.72.

`pytest.ini` agrega `src` al `pythonpath` para que las pruebas encuentren los módulos.

### Paso 7. Documentación de la validación
Se generó `tests/casos_prueba.md` con la tabla de validación de los 17 casos, la matriz de cobertura (15 de 15 reglas) y el análisis del caso 11 (fallas simultáneas).

### Paso 8. Limpieza del repositorio
Se agregó `.gitignore` para no subir archivos generados automáticamente (`*.pyc` y `.pytest_cache/`) y se retiraron del repositorio los que ya se habían subido.

### Paso 9. Traspaso al Rol B
Se escribió `docs/traspaso.md` con lo que devuelve `diagnosticar()`, qué widget de Streamlit corresponde a cada elemento de la interfaz y lo que falta por hacer. La versión se marca con la etiqueta `v1-backend`.

---

## 5. Base de conocimiento

### Predicados (8)

| Capa | Predicado | Significado |
|---|---|---|
| Observación | `ErrorHTTP(n, c)` | El nodo n respondió con el código HTTP c |
| Observación | `Autenticacion(n, t)` | El nodo n usa el mecanismo t (OAuth2 / ApiKey) |
| Observación | `Sintoma(x, s)` | El objeto x presenta el síntoma s |
| Observación | `Contexto(x, k)` | El objeto x cumple la condición de contexto k |
| Intermedio | `CategoriaFalla(n, f)` | La falla del nodo n pertenece a la categoría f |
| Diagnóstico | `CausaRaiz(x, c)` | La causa probable de la falla de x es c |
| Catálogo | `Solucion(c, s)` | La acción s corrige la causa c |
| Diagnóstico | `Recomendar(x, s)` | Se recomienda aplicar la acción s sobre x |

### Reglas (15)

| Regla | SI | ENTONCES | CF |
|---|---|---|---|
| R1 | ErrorHTTP 401 | CategoriaFalla = CredencialInvalida | 0.90 |
| R2 | ErrorHTTP 429 | CategoriaFalla = LimiteRateExcedido | 0.95 |
| R3 | ErrorHTTP ≥ 500 | CategoriaFalla = ErrorServidorExterno | 0.90 |
| R4 | CredencialInvalida + OAuth2 | CausaRaiz = TokenVencido | 0.80 |
| R5 | CredencialInvalida + ApiKey | CausaRaiz = ApiKeyIncorrecta | 0.75 |
| R6 | LimiteRateExcedido + ProcesaMuchosItems | CausaRaiz = RafagaDeSolicitudes | 0.90 |
| R7 | ErrorServidorExterno + TimeoutNodo | CausaRaiz = ServicioExternoSaturado | 0.75 |
| R8 | WebhookSinEjecuciones + WorkflowInactivo | CausaRaiz = WorkflowDesactivado | 0.95 |
| R9 | WebhookSinEjecuciones + UsaURLTest | CausaRaiz = URLDePruebaEnProduccion | 0.90 |
| R10 | DatosVacios + FiltroPrevioDescartaTodo | CausaRaiz = FiltroDemasiadoRestrictivo | 0.85 |
| R11 | ExpresionInvalida | CausaRaiz = ReferenciaACampoInexistente | 0.80 |
| R12 | CausaRaiz ?c + Solucion(?c, ?s) | Recomendar ?s | 1.00 |
| R13 | ErrorHTTP 403 | CategoriaFalla = PermisosInsuficientes | 0.90 |
| R14 | PermisosInsuficientes + OAuth2 | CausaRaiz = ScopesInsuficientes | 0.80 |
| R15 | TimeoutNodo + ProcesaMuchosItems | CausaRaiz = TimeoutPorVolumen | 0.80 |

### Catálogo de soluciones

| Causa raíz | Acción recomendada |
|---|---|
| TokenVencido | ReautenticarCredencialOAuth2 |
| ApiKeyIncorrecta | RegenerarYActualizarApiKey |
| RafagaDeSolicitudes | UsarLoopOverItemsConWait |
| ServicioExternoSaturado | ActivarRetryOnFailConEspera |
| WorkflowDesactivado | ActivarElWorkflow |
| URLDePruebaEnProduccion | UsarLaURLDeProduccionDelWebhook |
| FiltroDemasiadoRestrictivo | RevisarCondicionesDelFiltro |
| ReferenciaACampoInexistente | CorregirExpresionYVerificarEstructuraJSON |
| ScopesInsuficientes | ReautorizarCredencialConScopesCorrectos |
| TimeoutPorVolumen | DividirEnLotesConSplitInBatches |

### Factores de certeza
- Hechos observados: **CF = 1.0**.
- Conclusión de una regla: **CF = min(CF de las condiciones) × CF de la regla**.
- Ejemplo: 401 con OAuth2 → R1 (0.90) × R4 (0.80) = **0.72**.

---

## 6. Motor de inferencia

Encadenamiento **hacia adelante**: aplica las reglas una y otra vez hasta que ya no se puede derivar ningún hecho nuevo (punto fijo).

| Función | Qué hace |
|---|---|
| `encadenamiento_adelante(base, hechos)` | Aplica las reglas hasta el punto fijo. Devuelve `(hechos_finales, reglas_aplicadas)` |
| `explicar_razonamiento(reglas_aplicadas)` | Devuelve el texto con todos los pasos de la inferencia |
| `porque(conclusion, hechos_iniciales, reglas_aplicadas)` | Devuelve la cadena que justifica una conclusión, hasta los hechos observados |
| `validar_hechos(hechos)` | Valida la entrada. Devuelve `(errores, advertencias)` |
| `detectar_ciclos(base)` | Busca ciclos entre predicados en la base de reglas |
| `diagnosticar(hechos)` | Orquesta todo y devuelve un diccionario con el resultado |

**Casos especiales que maneja:** entrada vacía o sin conclusión, entrada inválida, hechos duplicados y bases con ciclos (no se queda colgado).

---

## 7. Casos de prueba

| # | Caso | Tipo |
|---|---|---|
| 1 | 401 con OAuth2 | Funcional |
| 2 | 429 con muchos items | Funcional |
| 3 | 503 con timeout | Funcional |
| 4 | Webhook sin ejecuciones, workflow inactivo | Funcional |
| 5 | Webhook sin ejecuciones, URL de prueba | Funcional |
| 6 | Datos vacíos tras un filtro | Funcional |
| 7 | 401 con API Key | Funcional |
| 8 | Expresión con campo inexistente | Funcional |
| 9 | 403 con OAuth2 (ampliación) | Funcional |
| 10 | Timeout con muchos items (ampliación) | Funcional |
| 11 | Workflow con fallas simultáneas (14 de 15 reglas) | Multifalla |
| 12 | Sin hechos de entrada | Borde |
| 13 | 404: código fuera del alcance | Borde |
| 14 | 401 sin tipo de autenticación | Borde |
| 15 | 503 sin timeout | Borde |
| 16 | Hechos duplicados | Borde |
| 17 | Base con ciclo A→B→A | Robustez |

**Resultado: 17 de 17 casos correctos. Cobertura: 15 de 15 reglas.**
El detalle completo está en [`tests/casos_prueba.md`](tests/casos_prueba.md).

---

## 8. Ejemplo de uso

```python
# Ejecutar desde la carpeta src/
from motor_inferencia import diagnosticar

r = diagnosticar([("ErrorHTTP", 401), ("Autenticacion", "OAuth2")])

print(r["estado"])   # diagnostico_completo
print(r["causas"])
# [{'causa': 'TokenVencido', 'certeza': 0.72,
#   'recomendacion': 'ReautenticarCredencialOAuth2'}]
print(r["explicacion"])
```

`diagnosticar()` devuelve un diccionario con: `estado`, `mensaje`, `causas`, `reglas_aplicadas`, `explicacion`, `errores`, `advertencias` y `hechos_iniciales`.

---

## 9. Pendiente (Rol B)

- [ ] Interfaz web en Streamlit (`src/app.py`), ejecutable con `streamlit run src/app.py`.
- [ ] Documentación técnica: secciones 5 (interfaz) y 7 (manual / despliegue).
- [ ] Manual de usuario con capturas.
- [ ] Enlace al video de demostración.
- [ ] Etiqueta `v2-app` y ZIP final `lopez_narvaez_proyecto_final_sbc.zip`.
