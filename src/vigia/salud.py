"""El chequeo de salud, desde adentro del contenedor.

Docker, Compose y Swarm leen el **código de salida** de este comando: `0` está vivo, `1` no.

## Por qué está en Python y no en `curl`

Porque la imagen **no instala nada**. El núcleo de decisión es stdlib y un test lo impone; meter
`curl` en la imagen sería abrir la puerta a la primera dependencia de un proyecto que se sostiene en
no tenerlas. `urllib` ya viene.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request

from vigia.servidor import puerto_del_entorno

TIEMPO_LIMITE_S = 4
"""Corto a propósito: un chequeo de salud que se cuelga es un chequeo de salud que falla."""


def main() -> int:
    """`0` si el servidor contesta, `1` si no."""
    url = f"http://127.0.0.1:{puerto_del_entorno(os.environ)}/"
    try:
        with urllib.request.urlopen(url, timeout=TIEMPO_LIMITE_S) as respuesta:
            return 0 if respuesta.status == 200 else 1
    except (urllib.error.URLError, OSError):
        return 1


if __name__ == "__main__":
    sys.exit(main())
