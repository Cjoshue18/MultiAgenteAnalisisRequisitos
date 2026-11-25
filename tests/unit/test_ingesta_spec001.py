from pathlib import Path
from unittest.mock import Mock
import pytest
from src.services.ingesta import preparar_ingesta


def _palabras(cantidad: int) -> str:
    return " ".join(f"requisito{i}" for i in range(cantidad))


@pytest.mark.parametrize("entrada", [None, "", "   \n\t  ", "solo quince chars"])
def test_req_01_rechaza_entrada_nula_vacia_o_menor_20_caracteres(entrada: str | None) -> None:
    with pytest.raises(ValueError, match="20"):
        preparar_ingesta(texto=entrada)


def test_req_01_rechaza_extension_invalida_exceso_10mb_o_10000_palabras(tmp_path: Path) -> None:
    archivo_malo = tmp_path / "malware.exe"
    archivo_malo.write_text("contenido suficientemente largo para pruebas", encoding="utf-8")
    with pytest.raises(ValueError, match="formato|extensión"):
        preparar_ingesta(ruta_archivo=archivo_malo)

    archivo_grande = tmp_path / "grande.txt"
    archivo_grande.write_text("El sistema debe validar tamaño máximo permitido.", encoding="utf-8")
    with pytest.raises(ValueError, match="10 MB"):
        preparar_ingesta(ruta_archivo=archivo_grande, tamano_bytes_override=10 * 1024 * 1024 + 1)

    with pytest.raises(ValueError, match="10,000"):
        preparar_ingesta(texto=_palabras(10_001))


def test_req_01_extrae_texto_desde_txt_md_y_pdf_mock(tmp_path: Path, mocker) -> None:
    txt = tmp_path / "req.txt"
    txt.write_text("El usuario debe iniciar sesión con correo institucional.", encoding="utf-8")
    assert preparar_ingesta(ruta_archivo=txt).estrategia == "directa"

    md = tmp_path / "req.md"
    md.write_text("# Requisitos\nEl administrador debe registrar libros en catálogo.", encoding="utf-8")
    assert preparar_ingesta(ruta_archivo=md).estrategia == "directa"

    pdf = tmp_path / "req.pdf"
    pdf.write_bytes(b"%PDF-1.4 mock")
    pagina = Mock()
    pagina.extract_text.return_value = "El alumno debe consultar libros disponibles en biblioteca."
    mocker.patch("src.services.ingesta.PdfReader", return_value=Mock(pages=[pagina]))
    res_pdf = preparar_ingesta(ruta_archivo=pdf)
    assert res_pdf.estrategia == "directa"
    assert "consultar libros disponibles" in res_pdf.texto_limpio


def test_req_02_selecciona_estrategia_directa_menor_1000_palabras() -> None:
    texto = _palabras(200)
    res = preparar_ingesta(texto=texto)
    assert res.estrategia == "directa"
    assert len(res.fragmentos) == 1
    assert res.total_palabras == 200


def test_req_02_selecciona_estrategia_lotes_con_solapamiento_entre_1000_y_10000_palabras() -> None:
    texto = _palabras(2500)
    res = preparar_ingesta(texto=texto)
    assert res.estrategia == "lotes"
    assert res.total_palabras == 2500
    assert len(res.fragmentos) > 1
    ultimas_f0 = res.fragmentos[0].split()[-50:]
    primeras_f1 = res.fragmentos[1].split()[:100]
    assert all(p in primeras_f1 for p in ultimas_f0)
