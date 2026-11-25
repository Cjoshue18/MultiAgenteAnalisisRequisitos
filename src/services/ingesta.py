from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, cast
from pypdf import PdfReader
from src.schemas.contracts import ModalidadModelado
from src.services.seguridad import validar_seguridad_entrada

MIN_CARACTERES = 20
MAX_BYTES = 10 * 1024 * 1024
UMBRAL_PALABRAS_LOTES = 1000
MAX_PALABRAS = 10_000
EXTENSIONES_PERMITIDAS = {".txt", ".md", ".pdf"}
MODALIDADES_PERMITIDAS = {"CUS", "HU", "AMBOS"}


def validar_modalidad_modelado(modalidad: str | None) -> tuple[ModalidadModelado, list[str]]:
    """Valida la modalidad elegida antes del envío y emite las advertencias obligatorias."""
    if modalidad not in MODALIDADES_PERMITIDAS:
        raise ValueError("Debe seleccionar una modalidad válida antes de enviar: CUS, HU o AMBOS")
    advertencias = [
        "La modalidad seleccionada quedará fija para toda la corrida y no podrá cambiarse en revisión ni al regenerar."
    ]
    if modalidad == "AMBOS":
        advertencias.append(
            "Al seleccionar AMBOS el proceso demorará más al generar Casos de Uso e Historias de Usuario."
        )
    return cast(ModalidadModelado, modalidad), advertencias


@dataclass(frozen=True)
class ResultadoIngesta:
    texto_limpio: str
    total_palabras: int
    tamano_bytes: int
    estrategia: Literal["directa", "lotes"]
    fragmentos: list[str]


class EstrategiaProcesamiento(Protocol):
    nombre: Literal["directa", "lotes"]

    def segmentar(self, texto: str) -> list[str]:
        ...


class EstrategiaDirecta:
    nombre: Literal["directa"] = "directa"

    def segmentar(self, texto: str) -> list[str]:
        return [texto]


class EstrategiaSegmentacion:
    nombre: Literal["lotes"] = "lotes"

    def __init__(self, tamano_lote: int = 800, solapamiento: int = 100) -> None:
        if solapamiento >= tamano_lote:
            raise ValueError("El solapamiento debe ser menor que el tamaño del lote")
        self.tamano_lote = tamano_lote
        self.solapamiento = solapamiento

    def segmentar(self, texto: str) -> list[str]:
        palabras = texto.split()
        paso = self.tamano_lote - self.solapamiento
        fragmentos: list[str] = []
        inicio = 0
        while inicio < len(palabras):
            fin = inicio + self.tamano_lote
            fragmentos.append(" ".join(palabras[inicio:fin]))
            if fin >= len(palabras):
                break
            inicio += paso
        return fragmentos


def _leer_archivo(ruta: Path, tamano_bytes_override: int | None) -> tuple[str, int]:
    if not ruta.exists() or not ruta.is_file():
        raise ValueError(f"El archivo no existe: {ruta}")
    extension = ruta.suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(f"Formato o extensión no permitida ({extension}). Válidos: .txt, .md, .pdf")
    tamano = tamano_bytes_override if tamano_bytes_override is not None else ruta.stat().st_size
    if tamano > MAX_BYTES:
        raise ValueError("El archivo supera el límite máximo permitido de 10 MB")
    if extension == ".pdf":
        lector = PdfReader(str(ruta))
        texto = "\n".join((p.extract_text() or "") for p in lector.pages)
        return texto, tamano
    return ruta.read_text(encoding="utf-8"), tamano


def preparar_ingesta(
    texto: str | None = None,
    ruta_archivo: str | Path | None = None,
    tamano_bytes_override: int | None = None,
) -> ResultadoIngesta:
    """Valida entrada (RN01/RN02) y aplica estrategia directa o por lotes (Sección 9.5)."""
    if ruta_archivo is not None:
        contenido, tamano = _leer_archivo(Path(ruta_archivo), tamano_bytes_override)
    else:
        contenido = texto or ""
        tamano = tamano_bytes_override if tamano_bytes_override is not None else len(contenido.encode("utf-8"))
        if tamano > MAX_BYTES:
            raise ValueError("La entrada supera el límite máximo permitido de 10 MB")

    texto_limpio = " ".join(contenido.split())
    if len(texto_limpio) < MIN_CARACTERES:
        raise ValueError("La descripción debe contener al menos 20 caracteres significativos")
    validar_seguridad_entrada(texto_limpio)

    palabras = texto_limpio.split()
    total_palabras = len(palabras)
    if total_palabras > MAX_PALABRAS:
        raise ValueError("La solicitud supera el límite máximo permitido de 10,000 palabras")

    estrategia: EstrategiaProcesamiento = (
        EstrategiaDirecta() if total_palabras < UMBRAL_PALABRAS_LOTES else EstrategiaSegmentacion()
    )
    return ResultadoIngesta(
        texto_limpio=texto_limpio,
        total_palabras=total_palabras,
        tamano_bytes=tamano,
        estrategia=estrategia.nombre,
        fragmentos=estrategia.segmentar(texto_limpio),
    )
