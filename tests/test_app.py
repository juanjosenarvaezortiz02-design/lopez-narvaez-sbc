from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from casos_prueba import CASOS_PRUEBA
from motor_inferencia import validar_hechos


APP_PATH = Path(__file__).parents[1] / "src" / "app.py"


@pytest.mark.parametrize("caso", CASOS_PRUEBA, ids=lambda caso: f"caso_{caso['id']}")
def test_caso_precargado_desde_streamlit(caso):
    app = AppTest.from_file(str(APP_PATH)).run()

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


def test_formulario_manual_explica_y_limpia():
    app = AppTest.from_file(str(APP_PATH)).run()
    assert {
        "Qué hace esta página",
        "Cómo funciona",
        "Cómo usarla",
        "Glosario de convenciones",
        "Limitaciones",
    }.issubset({expander.label for expander in app.expander})

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
    assert any("¿Por qué CausaRaiz(TokenVencido)?" in code.value for code in app.code)

    app.sidebar.button(key="limpiar").click().run()
    assert app.session_state["resultado"] is None
    assert app.session_state["codigo_http"] is None


def test_formulario_acepta_otro_codigo_http():
    app = AppTest.from_file(str(APP_PATH)).run()
    app.selectbox(key="codigo_http").select("Otro código").run()
    app.number_input(key="otro_codigo_http").set_value(418)
    app.button(key="diagnosticar").click().run()

    assert app.session_state["resultado"]["hechos_iniciales"] == [("ErrorHTTP", 418)]
    assert app.session_state["resultado"]["estado"] == "sin_conclusion"


def test_autenticaciones_simultaneas_muestran_advertencia():
    errores, advertencias = validar_hechos(
        [("Autenticacion", "OAuth2"), ("Autenticacion", "ApiKey")]
    )

    assert errores == []
    assert any("OAuth2 y ApiKey a la vez" in advertencia for advertencia in advertencias)
