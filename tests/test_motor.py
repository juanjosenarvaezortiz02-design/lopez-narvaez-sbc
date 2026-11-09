import pytest

from casos_prueba import CASOS_PRUEBA, ejecutar_caso
from motor_inferencia import diagnosticar


@pytest.mark.parametrize("caso", CASOS_PRUEBA, ids=lambda c: f"caso_{c['id']}")
def test_caso(caso):
    e = ejecutar_caso(caso)
    assert e["ok"], f"Caso {caso['id']} ({caso['descripcion']}) falló: {e['checks']}"


def test_hay_17_casos():
    assert len(CASOS_PRUEBA) == 17


def test_token_vencido_cf_072():
    r = diagnosticar([("ErrorHTTP", 401), ("Autenticacion", "OAuth2")])
    assert r["causas"][0]["causa"] == "TokenVencido"
    assert r["causas"][0]["certeza"] == 0.72
