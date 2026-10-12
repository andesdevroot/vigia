"""Lo que el servidor recuerda de cada persona, y **nada más**.

## Las tres promesas que sostiene

1. **No dejarse drenar.** Cada respuesta cuesta ≈ 19 CLP. Sin límite, cualquiera que encuentre el
   número puede vaciar el presupuesto de un servicio público, y no hace falta malicia: alcanza con
   reenviar. El límite es por **persona** y por **ventana**, no global, para que un spammer no deje
   sin servicio a todos los demás.
2. **No quedarse en silencio.** Al que cruza el límite se le dice **una vez** que frene, y recién
   después no se le contesta. Callar de golpe es el modo de fallo que este proyecto persigue en
   todas partes: un fallo que se disfraza de éxito.
3. **Decir la verdad sobre la privacidad.** La primera vez que alguien escribe se le avisa que su
   mensaje se analiza con un modelo. La decisión estaba tomada en `doc/14-GAP.md` §5.1 y no estaba
   implementada: era una promesa escrita y no cumplida.

## Lo que **no** guarda

**El mensaje no está.** No hay campo donde ponerlo, y eso es a propósito: la memoria lleva números y
ventanas, nada más. Si mañana alguien quiere guardar texto acá, va a tener que agregar un campo y
romper un test que dice explícitamente que no existe.

Tampoco crece sin límite. Una memoria que se llena con cada número que escribe es una fuga en un
servicio público, así que al llegar al tope se descarta la entrada más vieja.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

MENSAJES_POR_VENTANA = 20
"""Suficiente para una persona que reenvía varios mensajes, corto para un drenaje."""

VENTANA_S = 3600.0
"""Una hora. La ventana se renueva sola, así que nadie queda bloqueado para siempre."""

TOPE_DE_NUMEROS = 4096
"""Cuántas personas se recuerdan a la vez. Al llegar, se descarta la más vieja."""


@dataclass(frozen=True, slots=True)
class Decision:
    """Qué hacer con un mensaje entrante. **Los tres campos son promesas distintas.**"""

    responder: bool
    avisar_privacidad: bool = False
    avisar_limite: bool = False


@dataclass(slots=True)
class _Estado:
    """Lo que se recuerda de una persona. **Números y banderas: nunca texto.**"""

    desde: float
    cuenta: int = 0
    aviso_privacidad: bool = False
    aviso_limite: bool = False


@dataclass(slots=True)
class Memoria:
    """El límite y los avisos, por persona y por ventana."""

    maximo: int = MENSAJES_POR_VENTANA
    ventana_s: float = VENTANA_S
    ahora: Callable[[], float] = time.monotonic
    tope_de_numeros: int = TOPE_DE_NUMEROS
    _estados: dict[str, _Estado] = field(default_factory=dict, repr=False)

    def decidir(self, quien: str) -> Decision:
        """Cuenta el mensaje y devuelve qué corresponde hacer con él."""
        momento = self.ahora()
        estado = self._estados.get(quien)
        if estado is None or momento - estado.desde >= self.ventana_s:
            self._hacer_sitio()
            estado = _Estado(desde=momento)
            self._estados[quien] = estado

        estado.cuenta += 1
        privacidad = not estado.aviso_privacidad
        estado.aviso_privacidad = True

        if estado.cuenta <= self.maximo:
            return Decision(responder=True, avisar_privacidad=privacidad)

        if not estado.aviso_limite:
            # Se contesta **una** vez más, y solo para poder avisar. Después, silencio.
            estado.aviso_limite = True
            return Decision(responder=True, avisar_privacidad=privacidad, avisar_limite=True)

        return Decision(responder=False, avisar_privacidad=privacidad)

    def cuantos(self) -> int:
        """Cuántas personas se están recordando. Para tests y para vigilar la memoria."""
        return len(self._estados)

    def _hacer_sitio(self) -> None:
        """Descarta lo vencido; y si igual no cabe, la entrada más vieja."""
        if len(self._estados) < self.tope_de_numeros:
            return
        momento = self.ahora()
        vencidos = [
            quien
            for quien, estado in self._estados.items()
            if momento - estado.desde >= self.ventana_s
        ]
        for quien in vencidos:
            del self._estados[quien]
        if len(self._estados) >= self.tope_de_numeros:
            mas_viejo = min(self._estados, key=lambda quien: self._estados[quien].desde)
            del self._estados[mas_viejo]
