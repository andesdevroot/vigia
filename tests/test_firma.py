"""Tests de la firma del webhook (T1.4a)."""

from __future__ import annotations

import json

from vigia.firma import es_valida, firmar

SECRETO = "s3cr3t0-de-prueba"
CUERPO = b'{"event":"whatsapp.message.received","phone_number_id":"123"}'


def test_una_firma_correcta_pasa() -> None:
    assert es_valida(firmar(CUERPO, SECRETO), CUERPO, SECRETO)


def test_sin_firma_no_pasa() -> None:
    assert not es_valida(None, CUERPO, SECRETO)


def test_otro_secreto_no_pasa() -> None:
    assert not es_valida(firmar(CUERPO, "otro-secreto"), CUERPO, SECRETO)


def test_un_byte_distinto_no_pasa() -> None:
    alterado = CUERPO.replace(b'"123"', b'"124"')
    assert alterado != CUERPO
    assert not es_valida(firmar(CUERPO, SECRETO), alterado, SECRETO)


def test_una_firma_de_largo_equivocado_no_pasa() -> None:
    correcta = firmar(CUERPO, SECRETO)
    assert not es_valida("abc", CUERPO, SECRETO)
    assert not es_valida(correcta + "0", CUERPO, SECRETO)
    assert not es_valida(correcta[:-1], CUERPO, SECRETO)


def test_una_firma_que_no_es_hexadecimal_no_pasa() -> None:
    assert not es_valida("z" * 64, CUERPO, SECRETO)


def test_una_firma_en_mayusculas_pasa() -> None:
    """La comparación es sobre el valor, no sobre cómo se escribió."""
    assert es_valida(firmar(CUERPO, SECRETO).upper(), CUERPO, SECRETO)


def test_la_firma_es_sobre_los_bytes_crudos_y_no_sobre_el_json() -> None:
    """Parsear y volver a serializar **rompe** la firma.

    Es la razón de verificar antes de parsear: `json.dumps` cambia el espaciado y con él cambia el
    HMAC, así que un servidor que firmara el objeto ya parseado rechazaría todas las peticiones
    legítimas — y el arreglo natural, aflojar la comparación, es el que abre la puerta.
    """
    reserializado = json.dumps(json.loads(CUERPO)).encode()
    assert reserializado != CUERPO
    assert not es_valida(firmar(CUERPO, SECRETO), reserializado, SECRETO)
