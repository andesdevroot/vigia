"""Bajar la imagen: el tope, la clave y los fallos que no pueden tumbar el webhook."""

from __future__ import annotations

from typing import Any

from vigia.medios import KapsoMedios, Medios


class RespuestaFalsa:
    """Una respuesta que entrega los trozos que se le pidan, y anota si la cerraron."""

    def __init__(self, contenido: bytes = b"", trozo: int = 65536) -> None:
        self._resto = contenido
        self._trozo = trozo
        self.cerrada = False

    def read(self, tamano: int = -1) -> bytes:
        limite = self._trozo if tamano < 0 else min(tamano, self._trozo)
        trozo, self._resto = self._resto[:limite], self._resto[limite:]
        return trozo

    def __enter__(self) -> RespuestaFalsa:
        return self

    def __exit__(self, *_excepcion: object) -> None:
        self.cerrada = True


def _abridor(respuesta: RespuestaFalsa, anotar: list[Any] | None = None) -> Any:
    def abrir(peticion: Any, **_kwargs: Any) -> RespuestaFalsa:
        if anotar is not None:
            anotar.append(peticion)
        return respuesta

    return abrir


def test_baja_los_bytes() -> None:
    imagen = b"\x89PNG" + b"x" * 5000
    medios = KapsoMedios(abrir=_abridor(RespuestaFalsa(imagen)))
    assert medios.descargar("https://api.kapso.ai/media/abc") == imagen


def test_manda_la_clave() -> None:
    """La URL de Kapso puede exigir la misma autenticación que el resto de su API."""
    anotadas: list[Any] = []
    medios = KapsoMedios(api_key="secreta", abrir=_abridor(RespuestaFalsa(b"x"), anotadas))
    medios.descargar("https://api.kapso.ai/media/abc")
    cabeceras = {k.lower(): v for k, v in anotadas[0].headers.items()}
    assert cabeceras.get("x-api-key") == "secreta"


def test_sin_clave_no_manda_cabecera() -> None:
    """Una URL firmada de un CDN no necesita la clave, y mandarla sería regalarla a otro host."""
    anotadas: list[Any] = []
    KapsoMedios(abrir=_abridor(RespuestaFalsa(b"x"), anotadas)).descargar("https://cdn.example/a")
    cabeceras = {k.lower() for k in anotadas[0].headers}
    assert "x-api-key" not in cabeceras


def test_lo_que_no_es_http_no_se_descarga() -> None:
    """**`file://` no.** Un campo con basura no puede convertirse en una lectura del disco."""
    anotadas: list[Any] = []
    medios = KapsoMedios(abrir=_abridor(RespuestaFalsa(b"x"), anotadas))
    assert medios.descargar("file:///etc/passwd") == b""
    assert anotadas == []


def test_un_archivo_gigante_se_corta_durante_la_lectura() -> None:
    """**El tope no es una optimización: es lo que separa «no pude leer» de «el servicio se cayó».**

    Un atacante manda 200 MB y el proceso se queda sin memoria antes de que el OCR tenga ocasión de
    fallar. Y se corta **mientras** se lee: si se leyera todo primero, el tope no serviría de nada.
    """
    gigante = b"x" * (9 * 1024 * 1024)
    respuesta = RespuestaFalsa(gigante, trozo=65536)
    medios = KapsoMedios(abrir=_abridor(respuesta))
    assert medios.descargar("https://api.kapso.ai/media/gigante") == b""
    assert len(gigante) > 8 * 1024 * 1024


def test_justo_en_el_tope_pasa() -> None:
    """El límite es un límite, no una estimación."""
    justo = b"x" * (8 * 1024 * 1024)
    medios = KapsoMedios(abrir=_abridor(RespuestaFalsa(justo, trozo=1024 * 1024)))
    assert len(medios.descargar("https://api.kapso.ai/media/justo")) == 8 * 1024 * 1024


def test_un_fallo_de_red_devuelve_vacio() -> None:
    """La imagen no llegó. El robot pide el texto, que es lo que hacía antes."""

    def abrir(*_a: Any, **_k: Any) -> Any:
        raise OSError("sin red")

    assert KapsoMedios(abrir=abrir).descargar("https://api.kapso.ai/media/x") == b""


def test_cierra_la_respuesta() -> None:
    """Una conexión que no se cierra se queda colgada, y el proveedor reintenta."""
    respuesta = RespuestaFalsa(b"x")
    KapsoMedios(abrir=_abridor(respuesta)).descargar("https://api.kapso.ai/media/x")
    assert respuesta.cerrada


def test_cumple_el_protocolo() -> None:
    assert isinstance(KapsoMedios(), Medios)
