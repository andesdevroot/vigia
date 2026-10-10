"""Lo que se le contesta a la persona (T1.4a). Módulo puro: solo stdlib.

Separa **leer** (`entrante`), **decidir** (`motor`) y **decir**. Este módulo es el decir, y ahí se
toman decisiones que no son técnicas:

- La respuesta **no promete seguridad**. Solo puede afirmar algo sobre el enlace.
- Si no hay enlaces, no se contesta «no hay nada»: se le pide el mensaje completo. Un «hola» y una
  estafa sin enlace reciben la misma respuesta, y está bien: en los dos casos falta el dato.
- Si mandó una **captura**, se dice que no se lee. Callarse sería peor que admitirlo.
"""

from __future__ import annotations

from collections.abc import Sequence

from vigia.entrante import MensajeRecibido
from vigia.motor import Veredicto, evaluar
from vigia.suplantacion import Marca

PEDIR_EL_MENSAJE = "Pégame acá el mensaje que te llegó y te digo si su enlace es del Estado."

PEDIR_TEXTO = (
    "No puedo leer imágenes. Mándame el mensaje como texto: mantén apretado el mensaje, elige "
    "Copiar y pégalo acá."
)

ACLARAR_IMAGEN = "Ojo: las imágenes no las puedo leer, esto lo digo por el texto que venía abajo."


def componer(mensaje: MensajeRecibido, marcas: Sequence[Marca] = ()) -> str:
    """El texto que se le manda de vuelta, listo para enviar."""
    if mensaje.tiene_media and not mensaje.texto:
        return PEDIR_TEXTO

    evaluacion = evaluar(mensaje.texto, marcas=marcas)

    partes: list[str] = []
    if mensaje.tiene_media:
        partes.append(ACLARAR_IMAGEN)
    if evaluacion.veredicto is Veredicto.SIN_ENLACES:
        partes.append(PEDIR_EL_MENSAJE)
    partes.append(evaluacion.explicacion)
    return " ".join(partes)
