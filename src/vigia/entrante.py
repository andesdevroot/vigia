"""Lectura del webhook de Kapso (T1.4a). Módulo puro: solo stdlib.

Convierte el sobre de Kapso en un `MensajeRecibido`. Nada más: acá no se opina sobre el mensaje.

## La regla de este módulo: nunca levantar

Un webhook que responde 500 hace que el proveedor reintente, y reintentar un mensaje que no supimos
leer no lo vuelve legible: solo multiplica el error y el ruido. Por eso `interpretar` devuelve
`None` —no lanza— cuando no hay nada que responder: un acuse de entrega, un evento que no es un
mensaje, un cuerpo que no entendemos.

## El invariante que evita el bucle

**Un mensaje saliente no se procesa.** Si el motor contestara a sus propios mensajes, cada respuesta
generaría otra, para siempre y pagando cada una. Es el único error de este módulo que no se nota en
un test unitario y sí en la factura.

## Lo que no se puede asumir

La propia documentación de Kapso avisa que `phone_number`, `from`, `to` y `wa_id` **no siempre
están**: hay una migración a identificadores por negocio. Así que el destinatario se busca en
orden y puede **no estar**; sin destinatario el mensaje se lee igual, pero no se podrá responder.

## El caso que va a pasar el primer día

La gente manda **capturas de pantalla**, no texto. El motor no lee imágenes. El mensaje se lee igual
y `tiene_media` queda marcado, para que la respuesta pueda decir que no se pudo leer en vez de
callarse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVENTO_MENSAJE = "whatsapp.message.received"

CLAVES_DESTINATARIO = ("phone_number", "wa_id", "from", "business_scoped_user_id", "username")
"""Dónde puede estar a quién hay que responderle, **en orden de preferencia**.

El teléfono va primero porque es lo que esperan los ejemplos de envío; el identificador por negocio
queda de último, como respaldo de la migración que Kapso documenta.
"""


@dataclass(frozen=True, slots=True)
class MensajeRecibido:
    """Un mensaje entrante ya leído. `destinatario` puede ser `None`: ver el módulo."""

    texto: str
    phone_number_id: str
    destinatario: str | None
    tiene_media: bool


def _diccionario(valor: object) -> dict[str, Any]:
    """El valor si es un diccionario, y si no un diccionario vacío.

    Evita una escalera de `isinstance` en cada campo: un webhook con la forma equivocada devuelve
    `None` al final, que es la respuesta correcta.
    """
    return valor if isinstance(valor, dict) else {}


def _texto(valor: object) -> str | None:
    """El valor si es un texto con contenido. Un texto vacío no sirve como dato."""
    if isinstance(valor, str) and valor.strip():
        return valor
    return None


def _campo(mensaje: dict[str, Any], nombre: str) -> object:
    """Busca en `message.kapso` primero y en `message` después.

    Kapso pone lo suyo bajo `kapso` y deja lo de Meta en la raíz del mensaje; el mismo dato puede
    venir en cualquiera de los dos según la configuración, así que se miran los dos.
    """
    for contenedor in (_diccionario(mensaje.get("kapso")), mensaje):
        if nombre in contenedor:
            return contenedor[nombre]
    return None


def _destinatario(cuerpo: dict[str, Any]) -> str | None:
    conversacion = _diccionario(cuerpo.get("conversation"))
    mensaje = _diccionario(cuerpo.get("message"))
    for clave in CLAVES_DESTINATARIO:
        for contenedor in (conversacion, mensaje):
            encontrado = _texto(contenedor.get(clave))
            if encontrado is not None:
                return encontrado
    return None


def interpretar(cuerpo: object) -> MensajeRecibido | None:
    """El mensaje entrante del webhook, o `None` si no hay nada que responder."""
    if not isinstance(cuerpo, dict):
        return None

    evento = cuerpo.get("event")
    if isinstance(evento, str) and evento != EVENTO_MENSAJE:
        return None

    mensaje = cuerpo.get("message")
    if not isinstance(mensaje, dict):
        return None

    # El invariante contra el bucle. Antes de leer nada más.
    if _campo(mensaje, "direction") == "outbound":
        return None

    texto = _texto(_campo(mensaje, "content"))
    if texto is None:
        texto = _texto(_diccionario(mensaje.get("text")).get("body")) or ""
    tiene_media = _campo(mensaje, "has_media") is True

    # Sin texto y sin adjunto no hay nada que contestar: una reacción o una ubicación no se
    # responden. Contestarlas sería ruido, y el ruido hace que la gente deje de usar esto.
    if not texto and not tiene_media:
        return None

    identificador = _texto(cuerpo.get("phone_number_id")) or ""
    return MensajeRecibido(
        texto=texto,
        phone_number_id=identificador,
        destinatario=_destinatario(cuerpo),
        tiene_media=tiene_media,
    )
