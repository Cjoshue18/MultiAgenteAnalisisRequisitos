import pytest
from src.services.ingesta import validar_modalidad_modelado


@pytest.mark.parametrize("modalidad", [None, "", "OTRO", "cus"])
def test_req_01_rechaza_modalidad_nula_o_invalida(modalidad: str | None) -> None:
    with pytest.raises(ValueError, match="CUS, HU o AMBOS"):
        validar_modalidad_modelado(modalidad)


@pytest.mark.parametrize("modalidad", ["CUS", "HU"])
def test_req_01_cus_y_hu_emiten_advertencia_de_modalidad_fija(modalidad: str) -> None:
    elegida, advertencias = validar_modalidad_modelado(modalidad)
    assert elegida == modalidad
    assert len(advertencias) == 1
    assert "fija" in advertencias[0].lower()


def test_req_01_ambos_emite_advertencia_fija_y_mayor_demora() -> None:
    elegida, advertencias = validar_modalidad_modelado("AMBOS")
    assert elegida == "AMBOS"
    assert len(advertencias) == 2
    texto = " ".join(advertencias).lower()
    assert "fija" in texto
    assert "demorará más" in texto
