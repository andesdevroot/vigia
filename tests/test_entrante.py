"""Tests de la lectura del webhook de Kapso (T1.4a)."""

from __future__ import annotations

from typing import Any

from vigia.entrante import EVENTO_MENSAJE, MensajeRecibido, interpretar

ID_NUMERO = "109999999999999"
TEXTO = "Su ClaveUnica sera bloqueada, entre a claveunica-gob-cl.xyz"


def payload(
    *,
    event: Any = "whatsapp.message.received",
    message: Any = None,
    conversation: Any = None,
    con_phone_number_id: bool = True,
) -> dict[str, Any]:
    """Un webhook v2 con la forma que documenta Kapso. Cada test cambia una pieza."""
    if message is None:
        message = {
            "id": "wamid.ABC",
            "timestamp": "1760000000",
            "kapso": {"direction": "inbound", "has_media": False, "content": TEXTO},
        }
    if conversation is None:
        conversation = {"id": "conv-1", "phone_number": "56912345678"}
    cuerpo: dict[str, Any] = {"event": event, "message": message, "conversation": conversation}
    if con_phone_number_id:
        cuerpo["phone_number_id"] = ID_NUMERO
    return cuerpo


def test_lee_un_mensaje_entrante() -> None:
    leido = interpretar(payload())
    assert leido == MensajeRecibido(
        texto=TEXTO,
        phone_number_id=ID_NUMERO,
        destinatario="56912345678",
        tiene_media=False,
    )


def test_el_texto_tambien_se_lee_del_formato_de_meta() -> None:
    """Sin `kapso.content` queda el formato crudo de Meta, y ahí el texto va en `text.body`."""
    leido = interpretar(payload(message={"text": {"body": TEXTO}}))
    assert leido is not None
    assert leido.texto == TEXTO


def test_un_evento_que_no_es_un_mensaje_no_se_procesa() -> None:
    for evento in ("whatsapp.message.delivered", "whatsapp.conversation.created"):
        assert interpretar(payload(event=evento)) is None


def test_un_mensaje_saliente_no_se_procesa() -> None:
    """**El invariante que evita el bucle.**

    Si el motor contestara a sus propios mensajes, cada respuesta generaría otra respuesta, para
    siempre y pagando cada una. Es el único error de este módulo que no se nota en un test unitario
    y sí en la factura.
    """
    saliente = {
        "id": "wamid.XYZ",
        "kapso": {"direction": "outbound", "content": "El enlace NO es del Estado."},
    }
    assert interpretar(payload(message=saliente)) is None


def test_sin_destinatario_se_lee_igual_pero_no_se_podra_responder() -> None:
    """Kapso avisa que `phone_number` no siempre viene. Se lee; responder es otra cosa."""
    leido = interpretar(payload(conversation={"id": "conv-1"}))
    assert leido is not None
    assert leido.texto == TEXTO
    assert leido.destinatario is None


def test_el_destinatario_cae_al_identificador_por_negocio() -> None:
    leido = interpretar(payload(conversation={"id": "c", "business_scoped_user_id": "BSUID-1"}))
    assert leido is not None
    assert leido.destinatario == "BSUID-1"


def test_una_captura_de_pantalla_se_reconoce() -> None:
    """La gente manda capturas. El motor no lee imágenes, pero el mensaje hay que verlo igual."""
    captura = {"id": "wamid.IMG", "kapso": {"direction": "inbound", "has_media": True}}
    leido = interpretar(payload(message=captura))
    assert leido is not None
    assert leido.tiene_media
    assert leido.texto == ""


def test_una_reaccion_no_genera_nada() -> None:
    """Sin texto y sin adjunto no hay nada que contestar, y contestar sería ruido."""
    reaccion = {"id": "wamid.R", "kapso": {"direction": "inbound", "has_media": False}}
    assert interpretar(payload(message=reaccion)) is None


def test_un_cuerpo_que_no_es_un_diccionario_no_revienta() -> None:
    """El webhook nunca levanta: un 500 hace que el proveedor reintente lo que no supimos leer."""
    basuras: tuple[object, ...] = ("no soy json", [], None, 42, {"event": EVENTO_MENSAJE})
    for basura in basuras:
        assert interpretar(basura) is None
