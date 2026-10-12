"""Leer una captura de pantalla, **sin que la imagen salga del servidor**.

## El caso que va a pasar el primer día

La gente manda **capturas**, no texto. Hasta ahora el robot contestaba «no puedo leer imágenes,
copia el texto», y **casi nadie lo va a hacer**: la captura ya está ahí, y pedirle a alguien que la
transcriba a mano es pedirle que haga el trabajo del robot.

## Por qué OCR local y no un modelo de visión

**Porque en una captura el enlace está escrito.** No hace falta entender la imagen: hace falta
leerla.
Y la diferencia no es de precio, es de privacidad.

Una captura de pantalla de un banco trae el **nombre de la persona, su saldo, y su teléfono**.
Mandarla
a un proveedor de visión sería el peor intercambio del proyecto: cambiaríamos el único activo que
tenemos —que el mensaje no salga de acá— por comodidad de implementación.

Los tests de acá fijan eso: **este módulo no importa nada de red**, y el lector recibe **bytes**, no
una URL. Si alguien quiere mandar la imagen afuera, va a tener que cambiar la firma y romper un test
que dice explícitamente que no.
"""

from __future__ import annotations

import subprocess

from vigia.imagen import Lector, LectorTesseract


class EjecutorFalso:
    """Anota el comando y devuelve lo que se le pida."""

    def __init__(
        self, salida: bytes = b"", codigo: int = 0, falla: Exception | None = None
    ) -> None:
        self.salida = salida
        self.codigo = codigo
        self.falla = falla
        self.comandos: list[list[str]] = []
        self.entradas: list[bytes] = []

    def __call__(self, comando: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        self.comandos.append(comando)
        self.entradas.append(kwargs.get("input", b""))  # type: ignore[arg-type]
        if self.falla is not None:
            raise self.falla
        return subprocess.CompletedProcess(comando, self.codigo, self.salida, b"")


def test_saca_el_texto_de_la_imagen() -> None:
    """Lo que importa: del PNG sale el texto de la estafa, y el motor lo puede juzgar."""
    ejecutor = EjecutorFalso(b"Su BancoEstado tiene un cargo. Ingrese a bancoestado-login.xyz")
    lector = LectorTesseract(ejecutar=ejecutor)
    texto = lector.leer(b"\x89PNG-falso")
    assert "bancoestado-login.xyz" in texto


def test_la_imagen_entra_por_la_entrada_estandar() -> None:
    """**La imagen nunca toca el disco.** No hay archivo temporal que borrar después, ni que se
    quede si el proceso muere a mitad de camino."""
    ejecutor = EjecutorFalso(b"algo")
    LectorTesseract(ejecutar=ejecutor).leer(b"bytes-de-la-imagen")
    assert ejecutor.entradas == [b"bytes-de-la-imagen"]
    assert "stdin" in ejecutor.comandos[0], "tesseract lee de stdin, no de un archivo"


def test_lee_en_castellano() -> None:
    """El OCR de un mensaje chileno con el idioma equivocado inventa palabras."""
    ejecutor = EjecutorFalso(b"algo")
    LectorTesseract(ejecutar=ejecutor).leer(b"x")
    assert "spa" in ejecutor.comandos[0]


def test_si_el_binario_no_esta_devuelve_vacio() -> None:
    """**Un OCR que no está instalado no puede tumbar el webhook.** Devuelve vacío y el robot pide
    el
    texto, que es lo que hacía antes."""
    lector = LectorTesseract(ejecutar=EjecutorFalso(falla=FileNotFoundError("no está tesseract")))
    assert lector.leer(b"x") == ""


def test_si_el_ocr_se_cuelga_devuelve_vacio() -> None:
    lector = LectorTesseract(ejecutar=EjecutorFalso(falla=subprocess.TimeoutExpired("tesseract",
    1)))
    assert lector.leer(b"x") == ""


def test_un_codigo_de_error_devuelve_vacio() -> None:
    """Una imagen corrupta hace que tesseract salga con error. No es una excepción nuestra."""
    lector = LectorTesseract(ejecutar=EjecutorFalso(b"basura", codigo=1))
    assert lector.leer(b"x") == ""


def test_una_imagen_sin_texto_devuelve_vacio() -> None:
    """Una foto de un paisaje no tiene letras. El robot tiene que pedir el texto, no inventar."""
    lector = LectorTesseract(ejecutar=EjecutorFalso(b"  \n \n  "))
    assert lector.leer(b"x") == ""


def test_el_lector_cumple_el_protocolo() -> None:
    """Se inyecta igual que el extractor y el respondedor: los tests corren sin tesseract."""
    assert isinstance(LectorTesseract(ejecutar=EjecutorFalso()), Lector)


def test_este_modulo_no_toca_la_red() -> None:
    """**El invariante de privacidad, fijado sobre el código fuente.**

    Si alguien quiere mandar la captura a un proveedor de visión, va a tener que importar red acá y
    este test se va a poner rojo. Es exactamente lo que tiene que pasar: la decisión de filtrar una
    captura de pantalla con el nombre y el saldo de alguien no puede entrar por descuido.
    """
    fuente = __import__("pathlib").Path("src/vigia/imagen.py").read_text(encoding="utf-8")
    for prohibido in ("urllib", "http.client", "requests", "socket", "httpx"):
        assert prohibido not in fuente, f"`imagen.py` no puede usar `{prohibido}`: el OCR es local"
