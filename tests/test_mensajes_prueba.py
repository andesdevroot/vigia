"""Tests del instrumento de `T3.1`: los tres mensajes de prueba.

Dos cosas se fijan acá, y las dos importan:

1. **Que ninguno pueda resolver.** Un mensaje de prueba con un dominio vivo sería un ataque real
   mandado a una persona que consintió en un experimento.
2. **Que los tres den el mejor veredicto.** Si un mensaje de prueba recibe una respuesta mala, el
   experimento mediría la modalidad sobre una respuesta que no sirve, y el resultado no diría nada.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from vigia.conversacion import componer
from vigia.entrante import MensajeRecibido
from vigia.motor import Veredicto, evaluar

RAIZ = Path(__file__).resolve().parents[1]
MENSAJES = json.loads((RAIZ / "corpus" / "prueba_t31.json").read_text(encoding="utf-8"))


def test_son_tres_y_estan_completos() -> None:
    assert len(MENSAJES) == 3
    for mensaje in MENSAJES:
        for campo in (
            "letra",
            "institucion",
            "mensaje_para_enviar",
            "fuente_alerta",
            "url_original",
        ):
            assert mensaje[campo], f"falta {campo} en {mensaje.get('letra')}"


def test_ningun_mensaje_de_prueba_puede_resolver() -> None:
    """La garantía de seguridad del experimento, y no una promesa.

    Solo se cambió el TLD, así que el nombre del dominio se conserva y la forma del enlace también;
    pero `.example` es de uso reservado (RFC 2606) y **no puede existir**. Si alguien cambiara el
    saneo por el dominio real, este test lo caza.
    """
    for mensaje in MENSAJES:
        for url in (mensaje["url_de_prueba"], mensaje["mensaje_para_enviar"]):
            assert ".example" in url
        assert urlsplit(mensaje["url_de_prueba"]).netloc.endswith(".example")
        assert ".example" not in urlsplit(mensaje["url_original"]).netloc


def test_los_tres_dan_el_mejor_veredicto() -> None:
    for mensaje in MENSAJES:
        resultado = evaluar(mensaje["mensaje_para_enviar"])
        assert resultado.veredicto is Veredicto.NO_COINCIDE, mensaje["letra"]
        assert resultado.reclamadas, mensaje["letra"]


def test_la_respuesta_a_cada_uno_nombra_la_institucion_y_el_enlace() -> None:
    for mensaje in MENSAJES:
        respuesta = componer(
            MensajeRecibido(
                texto=mensaje["mensaje_para_enviar"],
                phone_number_id="1",
                destinatario="569",
                tiene_media=False,
            )
        )
        assert "dice ser de" in respuesta
        assert urlsplit(mensaje["url_de_prueba"]).netloc in respuesta
        assert "seguro" not in respuesta.lower()
