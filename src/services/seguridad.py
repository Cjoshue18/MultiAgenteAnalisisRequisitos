import re
import unicodedata

_PATRONES_INYECCION = (
    re.compile(r"ignora\w*\s+(?:todas?\s+)?(?:las\s+)?instrucciones\s+(?:anteriores|previas)"),
    re.compile(r"(?:ignore|forget|disregard)\s+(?:all\s+)?(?:previous|prior)\s+instructions"),
    re.compile(r"olvida\s+(?:todas?\s+)?tus\s+(?:reglas|instrucciones)"),
    re.compile(r"actua\s+como\s+(?:administrador|sistema|desarrollador|root)\b"),
    re.compile(r"\b(?:system\s+prompt|revela\w*\s+tus\s+instrucciones|jailbreak)\b"),
)


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.split())


def validar_seguridad_entrada(texto: str) -> str:
    """Rechaza entradas con patrones de Prompt Injection conforme a RNF02."""
    normalizado = _normalizar(texto)
    for patron in _PATRONES_INYECCION:
        if patron.search(normalizado):
            raise ValueError("Solicitud rechazada por posible inyección de instrucciones.")
    return texto


def delimitar_documento(texto: str) -> str:
    """Aísla el documento del usuario como datos pasivos de lectura."""
    return f"<documento_usuario>\n{texto}\n</documento_usuario>"
