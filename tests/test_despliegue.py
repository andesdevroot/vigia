"""El contrato del despliegue: lo que tiene que cumplir para vivir fuera de un notebook.

**Por qué existe este archivo.** El robot corría con `python -m vigia.servidor` y un túnel de
`ngrok`, en la máquina del autor. Eso significa que **si se cierra el notebook, el servicio
muere**, y que la URL del webhook cambia en cada arranque. Un número que no contesta destruye
más confianza que no tener número.

Los tests de acá fijan tres cosas que una plataforma necesita y que no existían:

1. **Un chequeo de salud.** Sin él, la plataforma no sabe si el proceso está vivo, y reinicia a
   ciegas —o no reinicia nunca.
2. **El puerto por entorno.** Las PaaS pasan `PORT`, no `VIGIA_PUERTO`.
3. **Que la imagen no instale nada.** El núcleo de decisión es stdlib, y si el despliegue empieza a
   traer dependencias, se pierde la propiedad que hace reproducible el veredicto.
"""

from __future__ import annotations

import pathlib
import threading
from urllib.request import urlopen

import pytest

from test_servidor import SECRETO, EnviadorFalso
from vigia.servidor import construir_servidor, puerto_del_entorno

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def test_el_chequeo_de_salud_contesta_sin_firma() -> None:
    """**La plataforma no puede firmar.** El chequeo de salud no lleva `X-Webhook-Signature`."""
    enviador = EnviadorFalso()
    servidor = construir_servidor(("127.0.0.1", 0), SECRETO, enviador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        with urlopen(f"http://127.0.0.1:{servidor.server_address[1]}/", timeout=5) as respuesta:
            assert respuesta.status == 200
            assert b"ok" in respuesta.read()
        # Un chequeo de salud **no** es un mensaje: no manda nada y no cuesta nada.
        assert enviador.enviados == []
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_el_chequeo_de_salud_no_cuenta_como_mensaje() -> None:
    """No dispara el contador ni el extractor: es barato, y una plataforma lo llama cada pocos
    segundos."""
    contadas: list[object] = []
    enviador = EnviadorFalso()
    servidor = construir_servidor(("127.0.0.1", 0), SECRETO, enviador, contar=contadas.append)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        for _ in range(5):
            with urlopen(f"http://127.0.0.1:{servidor.server_address[1]}/", timeout=5) as r:
                assert r.status == 200
        assert contadas == []
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_el_chequeo_de_salud_no_revela_nada_de_adentro() -> None:
    """Que el servicio esté vivo es un dato público. **Qué versión corre, no.**"""
    enviador = EnviadorFalso()
    servidor = construir_servidor(("127.0.0.1", 0), SECRETO, enviador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        with urlopen(f"http://127.0.0.1:{servidor.server_address[1]}/", timeout=5) as respuesta:
            cuerpo = respuesta.read().decode().lower()
        for filtracion in ("python", "vigia", "3.1", "deepseek", "kapso"):
            assert filtracion not in cuerpo, f"el chequeo de salud no debería nombrar {filtracion}"
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_el_puerto_lo_manda_la_plataforma() -> None:
    """Las PaaS pasan `PORT`. `VIGIA_PUERTO` es el nombre nuestro, y sirve para correr local."""
    assert puerto_del_entorno({"PORT": "9090"}) == 9090
    assert puerto_del_entorno({"VIGIA_PUERTO": "8001"}) == 8001
    assert puerto_del_entorno({}) == 8000


def test_port_gana_sobre_el_nombre_nuestro() -> None:
    """Si están las dos, manda la de la plataforma: es la que ella va a usar para enrutar."""
    assert puerto_del_entorno({"PORT": "9090", "VIGIA_PUERTO": "8001"}) == 9090


def test_un_puerto_absurdo_no_arranca_a_medias() -> None:
    """Mejor fallar al arrancar que escuchar donde nadie va a llamar."""
    with pytest.raises(ValueError):
        puerto_del_entorno({"PORT": "no es un número"})
    with pytest.raises(ValueError):
        puerto_del_entorno({"PORT": "0"})


def test_hay_dockerfile() -> None:
    """Sin imagen no hay despliegue. El archivo tiene que existir."""
    assert (RAIZ / "Dockerfile").is_file()


def _instrucciones() -> str:
    """El Dockerfile **sin los comentarios**.

    Un test que falla por lo que dice un comentario es un test malo. Lo que hay que revisar son las
    instrucciones: la prosa puede nombrar `pip install` justamente para explicar por qué no está.
    """
    lineas = (RAIZ / "Dockerfile").read_text(encoding="utf-8").splitlines()
    return "\n".join(linea for linea in lineas if not linea.lstrip().startswith("#")).lower()


def test_la_imagen_no_instala_dependencias() -> None:
    """**El núcleo de decisión es stdlib, y el despliegue no puede romper eso.**

    Un `pip install` o un `uv sync` en el Dockerfile metería dependencias por la puerta de atrás, y
    la propiedad que hace reproducible el veredicto se pierde sin que ningún test se entere.
    """
    texto = _instrucciones()
    for prohibido in ("pip install", "uv sync", "poetry install", "npm install"):
        assert prohibido not in texto, f"la imagen no debería hacer `{prohibido}`"
    assert "vigia.servidor" in texto, "la imagen tiene que arrancar el servidor"


def test_la_imagen_no_se_lleva_los_secretos() -> None:
    """Un `.env` copiado dentro de una imagen queda en las capas, para siempre."""
    texto = _instrucciones()
    assert ".env" not in texto, "los secretos entran por variables de entorno, nunca por COPY"


def test_la_imagen_trae_el_ocr() -> None:
    """**El OCR tiene que correr adentro.** Una captura de un banco trae el nombre, el saldo y el
    teléfono de la persona: mandarla a un proveedor de visión sería cambiar el único activo que
    tenemos por comodidad.

    Y con el idioma: sin el paquete `-spa`, el OCR de un mensaje chileno inventa palabras.
    """
    texto = _instrucciones()
    assert "tesseract-ocr" in texto, "sin OCR la captura vuelve a ser un callejón sin salida"
    assert "tesseract-ocr-spa" in texto, "sin el idioma, el OCR inventa palabras"


def _flujo() -> str:
    """El archivo de CI, sin comentarios. Igual que con el Dockerfile: se revisan las
    instrucciones, no la prosa."""
    ruta = RAIZ / ".github" / "workflows" / "gate.yml"
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return "\n".join(linea for linea in lineas if not linea.lstrip().startswith("#"))


def test_hay_ci() -> None:
    """**Un repositorio público sin CI no demuestra nada a quien llega.**

    La insignia verde no existe, y la sección de reproducibilidad del paper queda en una promesa.
    """
    assert (RAIZ / ".github" / "workflows" / "gate.yml").is_file()


def test_la_ci_corre_el_mismo_gate_que_uno_a_mano() -> None:
    """**No una versión parecida: el mismo comando.**

    Si la CI corriera los pasos por su cuenta, podría quedar en verde mientras `./gate.sh` está en
    rojo — que es la peor clase de verde.
    """
    assert "./gate.sh" in _flujo()


def test_la_ci_corre_en_cada_push_y_en_cada_pr() -> None:
    flujo = _flujo()
    assert "push" in flujo
    assert "pull_request" in flujo


def test_la_ci_construye_la_imagen_y_la_levanta() -> None:
    """**Es el único modo de saber que la imagen construye.**

    No hay docker en la máquina de desarrollo, así que el primer build real lo hace la CI. Si no lo
    hace nadie, el primer despliegue es la sorpresa — y con `tesseract-ocr` recién agregado, hay
    bastante que puede salir mal.

    Y no alcanza con que construya: **tiene que levantar y contestar el chequeo de salud**.
    """
    flujo = _flujo()
    assert "docker build" in flujo, "la CI tiene que construir la imagen"
    assert "docker run" in flujo, "construir no basta: tiene que levantar"
    assert "8000" in flujo, "y contestar en el puerto del servidor"
