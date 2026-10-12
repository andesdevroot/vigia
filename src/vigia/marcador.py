"""Saber si el robot está vivo **de verdad**, y no solo si el proceso responde.

## El hueco que cierra

El chequeo de salud dice que el proceso contesta un `GET`. **No dice si los mensajes están llegando
o si se están contestando.** Y esas dos cosas se ven igual:

> Un servicio caído y un servicio que nadie usa **son indistinguibles desde afuera**.

Eso ya nos pasó una vez: en la prueba real hubo que ir a la API de Kapso para saber si una respuesta
había salido, porque el registro solo tenía el código HTTP.

## Lo que se cuenta, y lo que no se puede contar

| | |
|---|---|
| **Llegaron** | Un mensaje entrante, con la firma verificada |
| **Contestados** | Uno por veredicto del motor |
| **Silencios** | Uno por motivo, de una **lista cerrada** |
| **El último** | Cuándo fue, en segundos desde ahora |

**No hay dónde poner el contenido.** El marcador recibe un veredicto o un motivo, y los dos
son vocabularios cerrados: uno que no esté en la lista **no se cuenta**. Igual que el extractor,
y por la misma razón: un contador con claves libres crece sin límite, y el que manda la clave
es el de afuera.

## Por qué la lista de motivos es cerrada

Si las claves vinieran del mensaje, cualquiera podría inflar el archivo hasta llenar el disco. Con
una lista cerrada, lo que no está **se descarta**, y eso es un test.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from enum import StrEnum


class Salida(StrEnum):
    """Por qué NO se contestó. **Lista cerrada**, y a propósito."""

    FIRMA = "firma_invalida"
    ILEGIBLE = "cuerpo_ilegible"
    SIN_DESTINATARIO = "sin_destinatario"
    LIMITE = "limite"


class Marcador:
    """Cuenta llegadas, respuestas y silencios. **Nunca contenido.**

    Es seguro entre hilos: el servidor atiende cada webhook en su propio hilo, y dos mensajes que
    llegan a la vez podrían pisarse el contador. Un contador que pierde cuentas es peor que no
    tenerlo, porque parece un dato.
    """

    def __init__(self, ahora: Callable[[], float] = time.time) -> None:
        self._ahora = ahora
        self._desde = ahora()
        self._llegaron = 0
        self._contestados = 0
        self._silencios: dict[str, int] = {clave.value: 0 for clave in Salida}
        self._veredictos: dict[str, int] = {}
        self._ultimo: float | None = None
        self._cerrojo = threading.Lock()

    def llegada(self) -> None:
        """Un mensaje entrante, con la firma ya verificada."""
        with self._cerrojo:
            self._llegaron += 1
            self._ultimo = self._ahora()

    def contestado(self, veredicto: str) -> None:
        """Se mandó una respuesta, y con qué veredicto del motor."""
        with self._cerrojo:
            self._contestados += 1
            self._veredictos[veredicto] = self._veredictos.get(veredicto, 0) + 1

    def silencio(self, motivo: object) -> None:
        """No se contestó, y por qué.

        **Lo que no está en la lista se descarta.** Si las claves vinieran de afuera, cualquiera
        podría inflar el archivo hasta llenar el disco.
        """
        clave = motivo.value if isinstance(motivo, Salida) else str(motivo)
        with self._cerrojo:
            if clave in self._silencios:
                self._silencios[clave] += 1

    def resumen(self) -> dict[str, object]:
        """Todo lo que se sabe, y nada más. Para leer desde un teléfono."""
        with self._cerrojo:
            momento = self._ahora()
            return {
                "desde": _en_iso(self._desde),
                "ahora": _en_iso(momento),
                "llegaron": self._llegaron,
                "contestados": self._contestados,
                "sin_contestar": self._llegaron - self._contestados,
                "silencio": dict(self._silencios),
                "veredicto": dict(sorted(self._veredictos.items())),
                "ultimo_mensaje": _en_iso(self._ultimo) if self._ultimo else None,
                "segundos_desde_el_ultimo": (
                    int(momento - self._ultimo) if self._ultimo else None
                ),
            }


def _en_iso(marca: float | None) -> str | None:
    """El momento, en un formato que se lee de un vistazo."""
    if marca is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(marca))
