"""Contador de modalidades para el protocolo `T3.1`. Apagado por defecto.

## Qué mide, y qué no puede guardar

Mide **una sola cosa**: cómo llegó un mensaje reenviado, desde el punto de vista de lo que el motor
alcanza a leer.

| Modalidad | Qué significa |
|---|---|
| `con_enlace` | llegó un enlace que el motor puede juzgar |
| `con_adjunto` | llegó una captura o un audio, sin enlace legible |
| `texto_sin_enlace` | llegó texto, y el enlace no |

**No hay ningún camino por el que el contenido llegue al archivo.** El contador recibe un
`MensajeRecibido` y devuelve una de tres etiquetas: no tiene dónde poner el texto ni el número. Un
instrumento de medición que **no puede** guardar lo que mide es más fuerte que una promesa de no
guardarlo, y hay un test que lo fija — se cuenta un mensaje con una marca secreta y se comprueba que
la marca no aparece en el archivo.

## Por qué existe

La decisión que toma `T3.1` es si el cuello de botella del fraude ciudadano está en la
**clasificación** o en la **modalidad**. Eso no se puede saber mirando el motor: hay que mirar cómo
llegan los mensajes de verdad.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date
from enum import StrEnum
from pathlib import Path
from threading import Lock

from vigia.entrante import MensajeRecibido
from vigia.motor import extraer_enlaces


class Modalidad(StrEnum):
    """Las tres formas en que puede llegar un mensaje reenviado."""

    CON_ENLACE = "con_enlace"
    CON_ADJUNTO = "con_adjunto"
    TEXTO_SIN_ENLACE = "texto_sin_enlace"


def modalidad(mensaje: MensajeRecibido) -> Modalidad:
    """Cómo llegó el mensaje, desde el punto de vista del motor.

    Un adjunto **con** un enlace en el texto cuenta como enlace: la foto no se puede leer, pero el
    texto que la acompaña sí, así que el motor alcanza a responder. Contarlo como adjunto
    exageraría el problema.
    """
    if extraer_enlaces(mensaje.texto):
        return Modalidad.CON_ENLACE
    if mensaje.tiene_media:
        return Modalidad.CON_ADJUNTO
    return Modalidad.TEXTO_SIN_ENLACE


Contar = Callable[[MensajeRecibido], None]


class Contador:
    """Cuenta modalidades por día en un archivo de agregados.

    El archivo tiene esta forma y nada más:

        {"2026-10-10": {"con_enlace": 41, "con_adjunto": 12, "texto_sin_enlace": 7}}
    """

    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta
        self._cerrojo = Lock()

    def __call__(self, mensaje: MensajeRecibido) -> None:
        """Para poder pasarlo como el `contar` del servidor."""
        self.contar(mensaje)

    def contar(self, mensaje: MensajeRecibido) -> None:
        etiqueta = modalidad(mensaje)
        hoy = date.today().isoformat()
        with self._cerrojo:
            datos = self._leer()
            del_dia = datos.setdefault(hoy, {})
            del_dia[etiqueta] = del_dia.get(etiqueta, 0) + 1
            self._ruta.write_text(
                json.dumps(datos, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    def _leer(self) -> dict[str, dict[str, int]]:
        """Lo contado hasta ahora. Un archivo corrupto no puede botar el servidor."""
        if not self._ruta.exists():
            return {}
        try:
            datos = json.loads(self._ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return datos if isinstance(datos, dict) else {}
