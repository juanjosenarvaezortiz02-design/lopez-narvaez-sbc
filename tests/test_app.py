from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from casos_prueba import CASOS_PRUEBA
from motor_inferencia import validar_hechos


APP_PATH = Path(__file__).parents[1] / "src" / "app.py"
SCREENSHOTS_DIR = Path(__file__).parents[1] / "docs" / "capturas"


def _form_app():
    app = AppTest.from_file(str(APP_PATH))
    app.session_state["pagina"] = "Probar diagnóstico"
    return app.run(timeout=10)


def test_guia_inicial_y_navegacion_al_formulario():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=20)

    assert app.session_state["pagina"] == "Conoce n8n"
    assert any("Una guía sencilla para entender n8n" in item.value for item in app.title)
    assert all(
        (SCREENSHOTS_DIR / filename).is_file()
        for filename in (
            "05_interfaz.png",
            "06_flujo.png",
            "07_nodos.png",
            "08_flujo_nodos.png",
            "09_salida_request_401.png",
            "10_salida_capturar_error.png",
            "11_logs.png",
        )
    )
    assert any("HTTP Request" in item.value for item in app.markdown)

    app.button(key="ir_a_diagnostico_desde_guia").click().run(timeout=10)

    assert app.session_state["pagina"] == "Probar diagnóstico"
    assert any("Cuéntanos qué ocurrió" in item.value for item in app.header)
    assert app.selectbox(key="codigo_http")

    app.sidebar.button(key="navegar_guia").click().run(timeout=10)
    assert app.session_state["pagina"] == "Conoce n8n"

    app.sidebar.button(key="navegar_diagnostico").click().run(timeout=10)
    assert app.session_state["pagina"] == "Probar diagnóstico"


@pytest.mark.parametrize("caso", CASOS_PRUEBA, ids=lambda caso: f"caso_{caso['id']}")
def test_caso_precargado_desde_streamlit(caso):
    app = _form_app()

    app.sidebar.selectbox(key="caso_precargado").select(caso["id"]).run()

    ejecucion = app.session_state["resultado"]
    assert app.session_state["_checks_caso"] == {
        "reglas": True,
        "causas": True,
        "estado": True,
        "ciclo": True,
    }
    assert ejecucion["hechos_iniciales"] == caso["hechos"]
    assert ejecucion["estado"] == caso["estado"] or caso["estado"] is None
    formulario_representable = all(
        hecho[0] in {"ErrorHTTP", "Autenticacion", "Sintoma", "Contexto"}
        for hecho in caso["hechos"]
    )
    if formulario_representable:
        codigos = [hecho[1] for hecho in caso["hechos"] if hecho[0] == "ErrorHTTP"]
        autenticaciones = [
            hecho[1] for hecho in caso["hechos"] if hecho[0] == "Autenticacion"
        ]
        assert app.session_state["codigo_http"] == (
            codigos[0] if codigos and codigos[0] in (400, 401, 403, 404, 429, 500, 502, 503, 504)
            else "Otro código" if codigos else None
        )
        assert app.session_state["autenticacion"] == (
            autenticaciones[0] if autenticaciones else "No aplica"
        )
        assert app.session_state["sintomas"] == [
            hecho[1] for hecho in caso["hechos"] if hecho[0] == "Sintoma"
        ]
        assert app.session_state["contexto"] == [
            hecho[1] for hecho in caso["hechos"] if hecho[0] == "Contexto"
        ]
        assert any("Se limpiaron los campos anteriores" in item.value for item in app.info)
    else:
        assert app.session_state["codigo_http"] is None
        assert any("caso técnico del motor" in item.value for item in app.info)


def test_cambiar_ejemplo_limpia_y_precarga_el_formulario():
    app = _form_app()
    selector = app.sidebar.selectbox(key="caso_precargado")
    selector.select(1).run()
    app.sidebar.selectbox(key="caso_precargado").select(8).run()

    assert app.session_state["codigo_http"] is None
    assert app.session_state["autenticacion"] == "No aplica"
    assert app.session_state["sintomas"] == ["ExpresionInvalida"]
    assert app.session_state["contexto"] == []


def test_entrada_vacia_desde_el_formulario():
    app = _form_app()
    app.button(key="diagnosticar").click().run()

    resultado = app.session_state["resultado"]
    assert resultado["estado"] == "sin_conclusion"
    assert resultado["causas"] == []
    assert any("No se ingresó ningún hecho" in aviso for aviso in resultado["advertencias"])
    assert any("No se ingresó ningún hecho" in aviso.value for aviso in app.warning)


def test_codigo_404_desde_el_formulario():
    app = _form_app()
    app.selectbox(key="codigo_http").select(404)
    app.button(key="diagnosticar").click().run()

    resultado = app.session_state["resultado"]
    assert resultado["hechos_iniciales"] == [("ErrorHTTP", 404)]
    assert resultado["estado"] == "sin_conclusion"
    assert resultado["causas"] == []
    assert any("no encontramos una causa" in aviso.value for aviso in app.info)


def test_hechos_repetidos_muestran_advertencia_en_interfaz():
    app = _form_app()
    app.sidebar.selectbox(key="caso_precargado").select(16).run()

    assert any(
        "Hecho repetido" in aviso for aviso in app.session_state["resultado"]["advertencias"]
    )
    assert any("Hecho repetido" in aviso.value for aviso in app.warning)


def test_formulario_manual_explica_y_limpia():
    app = _form_app()
    assert {
        "Qué hace esta página",
        "Cómo funciona",
        "Cómo usarla",
        "Glosario de convenciones",
        "Limitaciones",
        "¿Qué significan los colores de los resultados?",
    }.issubset({expander.label for expander in app.expander})
    assert len(app.table) == 1
    assert set(app.table[0].value["Color"]) == {
        "🟢 Verde",
        "🟡 Amarillo",
        "🔵 Azul",
        "🔴 Rojo",
    }

    app.selectbox(key="codigo_http").select(401)
    app.radio(key="autenticacion").set_value("OAuth2")
    app.button(key="diagnosticar").click().run()

    assert app.session_state["resultado"]["causas"][0]["causa"] == "TokenVencido"
    assert app.session_state["resultado"]["causas"][0]["certeza"] == 0.72

    app.button(key="porque_0").click().run()
    assert any("Datos que se tomaron en cuenta" in item.value for item in app.markdown)
    assert any("Un 401 indica credencial inválida" in item.value for item in app.markdown)
    assert any(
        "Recomendaciones para revisar" in item.value for item in app.subheader
    )
    assert any(
        "Conclusión de este paso:" in item.value for item in app.markdown
    )
    assert "Ver cómo se conectan los pasos" in {
        expander.label for expander in app.expander
    }
    assert any("¿Por qué CausaRaiz(TokenVencido)?" in code.value for code in app.code)

    app.sidebar.button(key="limpiar").click().run()
    assert app.session_state["resultado"] is None
    assert app.session_state["codigo_http"] is None


def test_formulario_acepta_otro_codigo_http():
    app = _form_app()
    app.selectbox(key="codigo_http").select("Otro código").run()
    app.number_input(key="otro_codigo_http").set_value(418)
    app.button(key="diagnosticar").click().run()

    assert app.session_state["resultado"]["hechos_iniciales"] == [("ErrorHTTP", 418)]
    assert app.session_state["resultado"]["estado"] == "sin_conclusion"


def test_autenticaciones_simultaneas_muestran_advertencia():
    app = _form_app()
    errores, advertencias = validar_hechos(
        [("Autenticacion", "OAuth2"), ("Autenticacion", "ApiKey")]
    )

    assert set(app.radio(key="autenticacion").options) == {
        "No aplica",
        "OAuth 2.0 (autorización mediante una cuenta)",
        "Clave API (una clave de acceso)",
    }
    assert errores == []
    assert any("OAuth2 y ApiKey a la vez" in advertencia for advertencia in advertencias)
