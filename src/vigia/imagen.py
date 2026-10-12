"""Leer el texto de una captura de pantalla, **localmente**.

## Por qué local, y no un modelo de visión

Una captura de un banco trae el **nombre de la persona, su saldo y su teléfono**. Mandarla a un
proveedor de visión sería cambiar el único activo que este proyecto tiene —que el mensaje no salga
de
acá— por comodidad de implementación.

Y no hace falta: **en una captura el enlace está escrito.** No hay que entender la imagen, hay que
leerla. `tesseract` lo hace, corre en la misma máquina, y no cuesta por mensaje.

## La forma de leer: por la entrada estándar

La imagen **nunca toca el disco**. No hay archivo temporal que borrar, ni que se quede si el proceso
muere a mitad de camino. `tesseract stdin stdout` existe justamente para esto.

## Y si no está instalado

`leer` **devuelve vacío**, no levanta. Un OCR ausente no puede tumbar el webhook: el robot vuelve a
pedir el texto, que es exactamente lo que hacía antes de que esto existiera.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

BINARIO = "tesseract"
IDIOMA = "spa"
TIEMPO_LIMITE_S = 20
"""Una captura tarda uno o dos segundos. Veinte es holgado, y evita que una imagen enorme deje el
hilo del webhook ocupado mientras el proveedor reintenta."""


@runtime_checkable
class Lector(Protocol):
    """Lo que el servidor necesita de un lector de imágenes. **Recibe bytes, no una URL.**

    La firma es el invariante: si alguien quiere mandar la imagen afuera, tiene que cambiar esto y
    romper un test que dice explícitamente que no.
    """

    def leer(self, imagen: bytes) -> str: ...


class LectorTesseract:
    """OCR con el binario `tesseract`, en la misma máquina."""

    def __init__(
        self,
        binario: str = BINARIO,
        idioma: str = IDIOMA,
        tiempo_limite_s: float = TIEMPO_LIMITE_S,
        ejecutar: Callable[..., Any] | None = None,
    ) -> None:
        self._binario = binario
        self._idioma = idioma
        self._tiempo_limite_s = tiempo_limite_s
        self._ejecutar: Callable[..., Any] = ejecutar or subprocess.run

    def leer(self, imagen: bytes) -> str:
        """El texto de la imagen, o vacío si no se pudo leer. **Nunca levanta.**"""
        if not imagen:
            return ""
        try:
            resultado = self._ejecutar(
                [self._binario, "stdin", "stdout", "-l", self._idioma],
                input=imagen,
                capture_output=True,
                timeout=self._tiempo_limite_s,
            )
        except (OSError, subprocess.SubprocessError):
            # No está instalado, no tiene permiso, o se colgó. Las tres son «no pude leer»: el robot
            # pide el texto y sigue, que es mejor que un webhook roto.
            return ""
        if resultado.returncode != 0:
            return ""
        # El tipo explícito: el ejecutor es inyectable, así que para mypy su salida es `Any`, y
        # devolver `Any` donde se promete `str` es exactamente cómo se cuela un tipo que no es.
        texto: str = resultado.stdout.decode("utf-8", "replace")
        return texto.strip()

    def esta_disponible(self) -> bool:
        """Si el binario está. Se consulta al arrancar, para decidir si vale la pena intentarlo."""
        try:
            resultado = self._ejecutar(
                [self._binario, "--version"], capture_output=True, timeout=5
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return bool(resultado.returncode == 0)
