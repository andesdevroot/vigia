"""Tests del contador de `T3.1`.

El test que importa es `test_el_contador_no_puede_guardar_el_contenido`: la garantía de privacidad
del instrumento, fijada donde se puede romper.
"""

from __future__ import annotations

import json
from pathlib import Path

from vigia.entrante import MensajeRecibido
from vigia.medicion import Contador, Modalidad, modalidad


def recibido(texto: str, *, tiene_media: bool = False) -> MensajeRecibido:
    return MensajeRecibido(
        texto=texto, phone_number_id="1", destinatario="56900000000", tiene_media=tiene_media
    )


def test_un_texto_con_enlace_cuenta_como_enlace() -> None:
    assert modalidad(recibido("entre a sitio-falso.example/renovar")) is Modalidad.CON_ENLACE


def test_un_texto_sin_enlace_cuenta_como_texto_sin_enlace() -> None:
    assert modalidad(recibido("me llego esto, es real?")) is Modalidad.TEXTO_SIN_ENLACE


def test_una_captura_sin_texto_cuenta_como_adjunto() -> None:
    assert modalidad(recibido("", tiene_media=True)) is Modalidad.CON_ADJUNTO


def test_una_captura_con_enlace_en_el_texto_cuenta_como_enlace() -> None:
    """La foto no se lee, pero el texto que la acompaña sí: contarlo como adjunto exageraría."""
    assert (
        modalidad(recibido("mira esto sitio-falso.example", tiene_media=True))
        is Modalidad.CON_ENLACE
    )


def test_el_contador_acumula_por_dia(tmp_path: Path) -> None:
    contador = Contador(tmp_path / "conteo.json")
    contador.contar(recibido("entre a sitio-falso.example"))
    contador.contar(recibido("entre a sitio-falso.example"))
    contador.contar(recibido("", tiene_media=True))

    datos = json.loads((tmp_path / "conteo.json").read_text(encoding="utf-8"))
    del_dia = next(iter(datos.values()))
    assert del_dia == {"con_enlace": 2, "con_adjunto": 1}


def test_el_contador_no_puede_guardar_el_contenido(tmp_path: Path) -> None:
    """La garantía de privacidad del instrumento, y no una promesa.

    Se cuenta un mensaje que trae una marca imposible de confundir y se comprueba que **no aparece
    en el archivo**. Si alguien agregara el texto «para depurar», este test lo caza.
    """
    marca = "PISTA-UNICA-QUE-NO-DEBE-APARECER-4f9a1c"
    ruta = tmp_path / "conteo.json"
    contador = Contador(ruta)
    contador.contar(recibido(f"reclame en sitio-falso.example {marca}"))
    contador.contar(recibido(f"me llego {marca}", tiene_media=True))

    crudo = ruta.read_text(encoding="utf-8")
    assert marca not in crudo
    assert "sitio-falso" not in crudo
    assert "56900000000" not in crudo


def test_el_contador_no_revienta_con_un_archivo_corrupto(tmp_path: Path) -> None:
    ruta = tmp_path / "conteo.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    contador = Contador(ruta)
    contador.contar(recibido("entre a sitio-falso.example"))
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert next(iter(datos.values())) == {"con_enlace": 1}


def test_el_contador_se_puede_pasar_como_el_contar_del_servidor(tmp_path: Path) -> None:
    contador = Contador(tmp_path / "conteo.json")
    contador(recibido("entre a sitio-falso.example"))
    assert (tmp_path / "conteo.json").exists()
