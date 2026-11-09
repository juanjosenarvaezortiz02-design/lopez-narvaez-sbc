# Traspaso Rol A → Rol B (etiqueta `v1-backend`)

## 1. Cómo empezar
```bash
git clone <URL del repositorio>
cd <carpeta del repositorio>
git checkout v1-backend
pip install -r requirements.txt
pytest            # debe mostrar 19 passed (17 casos + 2 pruebas extra)
```

## 2. Lo que ya funciona
- `src/base_conocimiento.py`: `DOMINIOS`, `PREDICADOS`, `SOLUCIONES`, `REGLAS` (15), `BASE_CONOCIMIENTO`.
- `src/motor_inferencia.py`: `encadenamiento_adelante()`, `explicar_razonamiento()`, `porque()`, `validar_hechos()`, `detectar_ciclos()`, `diagnosticar()`.
- `src/casos_prueba.py`: `CASOS_PRUEBA` (17 casos) y `ejecutar_caso()`.
- `tests/test_motor.py`: 17 de 17 casos en verde.
- `tests/casos_prueba.md`: tabla de validación, cobertura y nota del caso 11.
- `docs/documentacion_tecnica.pdf`: secciones 1, 2, 3, 4 y 6.

## 3. Qué devuelve `diagnosticar(hechos)`
Un diccionario (no imprime nada):

| Clave | Contenido | Uso en la interfaz |
|---|---|---|
| `estado` | `diagnostico_completo`, `diagnostico_parcial`, `sin_conclusion`, `entrada_invalida` | Color del mensaje (`st.success`, `st.warning`, `st.info`, `st.error`) |
| `mensaje` | Texto para el usuario | Mensaje principal |
| `causas` | Lista de `{causa, certeza, recomendacion}` | Tarjetas / `st.metric` con el CF |
| `reglas_aplicadas` | Lista de `{regla, descripcion, condiciones, conclusion, certeza}` | Tabla de reglas en orden |
| `explicacion` | Texto con todos los pasos | `st.code` o `st.expander` |
| `errores`, `advertencias` | Listas de textos | `st.error` / `st.warning` |
| `hechos_iniciales` | Hechos de entrada | Necesario para llamar a `porque()` |

Botón «¿Por qué?»: `porque(("Recomendar", rec), r["hechos_iniciales"], r["reglas_aplicadas"])`.

## 4. Boceto de la interfaz (widget por elemento)

| Sección | Elemento | Widget de Streamlit | Fuente en el backend |
|---|---|---|---|
| Entrada | Códigos HTTP | `st.multiselect` (401, 403, 429, 500, 502, 503, 504, 404…) | `DOMINIOS["K"]` → `("ErrorHTTP", c)` |
| Entrada | Tipo de autenticación | `st.radio` (Ninguna / OAuth2 / ApiKey) | `DOMINIOS["T"]` → `("Autenticacion", t)` |
| Entrada | Síntomas | `st.checkbox` por valor | `DOMINIOS["SIN"]` → `("Sintoma", s)` |
| Entrada | Contexto | `st.checkbox` por valor | `DOMINIOS["CTX"]` → `("Contexto", k)` |
| Entrada | Botón diagnosticar | `st.button` dentro de `st.form` | `validar_hechos()` + `diagnosticar()` |
| Resultados | Estado y mensaje | `st.success` / `st.warning` / `st.info` / `st.error` | `estado`, `mensaje` |
| Resultados | Causas y recomendación | `st.metric` o tarjetas, ordenadas por CF | `causas` |
| Explicación | Reglas en orden | `st.dataframe` o `st.table` | `reglas_aplicadas` |
| Explicación | Razonamiento completo | `st.expander` + `st.code` | `explicacion` |
| Explicación | «¿Por qué?» | `st.button` por causa | `porque()` |
| Navegación | Casos precargados | `st.selectbox` en `st.sidebar` | `CASOS_PRUEBA` |
| Navegación | Limpiar | `st.button` que reinicia `st.session_state` | — |

## 5. Lo que falta (Rol B)
- `src/app.py` en Streamlit (`streamlit run src/app.py`).
- Integración y prueba con los casos 1, 11 y 13.
- Documentación técnica secciones 5 y 7, manual de usuario con capturas, README final, ZIP `lopez_narvaez_proyecto_final_sbc.zip`. Etiqueta `v2-app`.
