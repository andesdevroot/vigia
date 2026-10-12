"""Bajar la imagen que mandó el ciudadano. Módulo de red, aislado como el respondedor.

## Lo que resuelve

El webhook trae una **URL**, no los bytes. Sin bajarla no hay nada que leer, y el robot vuelve a
contestar «cópialo a mano».

## El tope de tamaño, y por qué existe

Un ciudadano manda una captura de 200 KB. Un atacante puede mandar un archivo de 200 MB, y el
proceso
se queda sin memoria **antes** de que el OCR tenga ocasión de fallar. El tope no es una
optimización:
es lo que separa «no pude leer esto» de «el servicio se cayó».

## Por qué no es `stdlib` puro, y está bien

Este módulo **sí toca la red**, igual que `KapsoRespondedor`. La regla del proyecto no es que nada
toque la red: es que **el núcleo de decisión no la toque**, para que un veredicto se pueda
reproducir sin internet. Bajar una imagen es entrada, no decisión.
"""

from __future__ import annotations

import subprocess
from typing import Any, Protocol, runtime_checkable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TIEMPO_LIMITE_S = 20
TOPE_BYTES = 8 * 1024 * 1024
"""8 MB. Una captura de pantalla no llega ni cerca; un archivo que lo pase no es una captura."""


@runtime_checkable
class Medios(Protocol):
    """Bajar una imagen por su URL. **Devuelve bytes, nunca levanta.**"""

    def descargar(self, url: str) -> bytes: ...


class KapsoMedios:
    """Baja la imagen desde la URL que vino en el webhook."""

    def __init__(
        self,
        api_key: str = "",
        tiempo_limite_s: float = TIEMPO_LIMITE_S,
        tope_bytes: int = TOPE_BYTES,
        abrir: Any = None,
    ) -> None:
        self._api_key = api_key
        self._tiempo_limite_s = tiempo_limite_s
        self._tope_bytes = tope_bytes
        self._abrir = abrir or urlopen

    def descargar(self, url: str) -> bytes:
        """Los bytes de la imagen, o vacío. **Nunca levanta**: un fallo acá no puede tumbar el
        webhook, porque el robot siempre tiene algo que decir."""
        if not url.startswith(("http://", "https://")):
            return b""
        cabeceras = {"X-API-Key": self._api_key} if self._api_key else {}
        peticion = Request(url, headers=cabeceras)
        try:
            with self._abrir(peticion, timeout=self._tiempo_limite_s) as respuesta:
                return self._leer_con_tope(respuesta)
        except (HTTPError, URLError, OSError, subprocess.SubprocessError, ValueError):
            return b""

    def _leer_con_tope(self, respuesta: Any) -> bytes:
        """Lee a lo más `tope_bytes`. Se corta **durante** la lectura, no después: si se leyera todo
        primero, el tope no serviría de nada."""
        trozos: list[bytes] = []
        leidos = 0
        while True:
            trozo = respuesta.read(65536)
            if not trozo:
                break
            leidos += len(trozo)
            if leidos > self._tope_bytes:
                return b""
            trozos.append(trozo)
        return b"".join(trozos)
