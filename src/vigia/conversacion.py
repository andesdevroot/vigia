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
from vigia.extractor import Extractor
from vigia.marcas import MARCAS
from vigia.motor import Veredicto, evaluar
from vigia.suplantacion import Marca

PEDIR_EL_MENSAJE = "Pégame acá el mensaje que te llegó y te digo si su enlace es del Estado."

PEDIR_TEXTO = (
    "No puedo leer imágenes. Mándame el mensaje como texto: mantén apretado el mensaje, elige "
    "Copiar y pégalo acá."
)

ACLARAR_IMAGEN = "Ojo: las imágenes no las puedo leer, esto lo digo por el texto que venía abajo."


def componer(
    mensaje: MensajeRecibido,
    marcas: Sequence[Marca] = MARCAS,
    extraer: Extractor | None = None,
) -> str:
    """El texto que se le manda de vuelta, listo para enviar.

    Con `extraer`, el veredicto cubre además **lo que el mensaje pide**, que es lo único que se
    puede decir cuando no trae enlace. Sin él, el motor se comporta como antes.
    """
    if mensaje.tiene_media and not mensaje.texto:
        return PEDIR_TEXTO

    evaluacion = evaluar(mensaje.texto, marcas=marcas)
    if extraer is not None:
        # Se evalúa dos veces a propósito: la primera dice de quién dice ser, y eso es lo que el
        # extractor necesita para que la regla de la petición tenga sus dos condiciones. Las dos
        # evaluaciones son deterministas y locales.
        dice_ser = evaluacion.reclamadas[0] if evaluacion.reclamadas else None
        evaluacion = evaluar(
            mensaje.texto, marcas=marcas, peticion=extraer.extraer(mensaje.texto, dice_ser)
        )

    partes: list[str] = []
    if mensaje.tiene_media:
        partes.append(ACLARAR_IMAGEN)
    if evaluacion.veredicto is Veredicto.SIN_ENLACES:
        partes.append(PEDIR_EL_MENSAJE)
    partes.append(evaluacion.explicacion)
    return " ".join(partes)
