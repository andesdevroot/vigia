"""Tests de lo que se le contesta a la persona (T1.4a)."""

from __future__ import annotations

from vigia.conversacion import componer
from vigia.entrante import MensajeRecibido

ID_NUMERO = "109999999999999"


def recibido(texto: str, *, tiene_media: bool = False) -> MensajeRecibido:
    return MensajeRecibido(
        texto=texto,
        phone_number_id=ID_NUMERO,
        destinatario="56912345678",
        tiene_media=tiene_media,
    )


def test_un_enlace_ajeno_se_avisa() -> None:
    respuesta = componer(recibido("entre a claveunica-gob-cl.xyz"))
    assert "NO es del Estado" in respuesta


def test_un_enlace_del_estado_lo_dice_sin_prometer_seguridad() -> None:
    respuesta = componer(recibido("ingrese a https://claveunica.gob.cl"))
    assert "claveunica.gob.cl" in respuesta
    assert "seguro" not in respuesta.lower()


def test_sin_enlaces_invita_a_pegar_el_mensaje() -> None:
    respuesta = componer(recibido("hola"))
    assert "Pégame" in respuesta


def test_una_imagen_sola_pide_el_texto() -> None:
    """No se puede leer una captura, y callarse sería peor que decirlo."""
    respuesta = componer(recibido("", tiene_media=True))
    assert "imágenes" in respuesta.lower()
    assert "texto" in respuesta.lower()


def test_una_imagen_con_texto_se_evalua_por_el_texto() -> None:
    respuesta = componer(recibido("mira esto claveunica-gob-cl.xyz", tiene_media=True))
    assert "NO es del Estado" in respuesta
    assert "imágenes" in respuesta.lower()
