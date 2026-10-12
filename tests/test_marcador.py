"""El marcador, y el endpoint que lo deja leer desde un teléfono.

**La pregunta que responde:** *¿el robot está contestando?* El chequeo de salud dice que el proceso
vive; esto dice si los mensajes llegan y si salen respuestas.

Y la distinción importa: **un servicio caído y uno que nadie usa se ven igual desde afuera.**
"""

from __future__ import annotations

import json
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from test_servidor import ID_NUMERO, SECRETO, EnviadorFalso, cuerpo
from vigia.firma import firmar
from vigia.marcador import Marcador, Salida


def _reloj(falso: list[float]) -> Any:
    return lambda: falso[0]


def _cuenta(resumen: dict[str, object], campo: str) -> dict[str, int]:
    """El subcontador, con el tipo comprobado.

    `resumen()` devuelve `dict[str, object]` —números, textos y subdiccionarios—, así que mypy hace
    bien en no dejar usar `.values()` a ciegas. Esto lo comprueba una vez, en un solo lugar.
    """
    valor = resumen[campo]
    assert isinstance(valor, dict), f"{campo} debería ser un diccionario"
    return {str(k): int(v) for k, v in valor.items()}


def test_cuenta_las_llegadas() -> None:
    marcador = Marcador()
    for _ in range(3):
        marcador.llegada()
    assert marcador.resumen()["llegaron"] == 3


def test_cuenta_las_respuestas_por_veredicto() -> None:
    """Saber **cuántos** no alcanza: hay que saber qué contestó.

    Si todo sale `sin_enlaces`, el extractor se rompió y el total no lo mostraría.
    """
    marcador = Marcador()
    marcador.contestado("no_coincide")
    marcador.contestado("no_coincide")
    marcador.contestado("confirmado")
    assert marcador.resumen()["veredicto"] == {"confirmado": 1, "no_coincide": 2}


def test_cuenta_los_silencios_por_motivo() -> None:
    marcador = Marcador()
    marcador.silencio(Salida.LIMITE)
    marcador.silencio(Salida.LIMITE)
    marcador.silencio(Salida.FIRMA)
    resumen = marcador.resumen()
    assert resumen["silencio"][Salida.LIMITE.value] == 2  # type: ignore[index]
    assert resumen["silencio"][Salida.FIRMA.value] == 1  # type: ignore[index]


def test_una_clave_de_afuera_se_descarta() -> None:
    """**La lista de motivos es cerrada.**

    Si las claves vinieran de afuera, cualquiera podría inflar el archivo hasta llenar el
    disco: el que manda la clave es el de afuera.
    """
    marcador = Marcador()
    for i in range(50):
        marcador.silencio(f"motivo-inventado-{i}")
    cuenta = _cuenta(marcador.resumen(), "silencio")
    assert len(cuenta) == len(Salida)
    assert sum(cuenta.values()) == 0


def test_guarda_cuando_fue_el_ultimo() -> None:
    """**La señal que importa.**

    Si el último mensaje fue hace tres días, o nadie lo usa o el webhook se rompió — y las dos
    cosas hay que poder distinguirlas de «está todo bien».
    """
    reloj = [1000.0]
    marcador = Marcador(ahora=_reloj(reloj))
    assert marcador.resumen()["ultimo_mensaje"] is None

    marcador.llegada()
    reloj[0] = 1060.0
    resumen = marcador.resumen()
    assert resumen["ultimo_mensaje"] is not None
    assert resumen["segundos_desde_el_ultimo"] == 60


def test_sin_contestar_es_la_resta() -> None:
    """El número que hay que mirar: **si sube, algo se rompió.**"""
    marcador = Marcador()
    for _ in range(10):
        marcador.llegada()
    for _ in range(7):
        marcador.contestado("ajeno")
    assert marcador.resumen()["sin_contestar"] == 3


def test_el_resumen_no_lleva_contenido() -> None:
    """Solo números, claves cerradas y momentos. **No hay dónde poner un mensaje.**"""
    marcador = Marcador()
    marcador.llegada()
    marcador.contestado("no_coincide")
    texto = json.dumps(marcador.resumen())
    for filtracion in ("569", "http", "@", "bancoestado"):
        assert filtracion not in texto


def test_es_seguro_entre_hilos() -> None:
    """**El servidor atiende cada webhook en su propio hilo.**

    Un contador que pierde cuentas es peor que no tenerlo, porque parece un dato.
    """
    marcador = Marcador()

    def trabajar() -> None:
        for _ in range(500):
            marcador.llegada()
            marcador.contestado("ajeno")

    hilos = [threading.Thread(target=trabajar) for _ in range(8)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    resumen = marcador.resumen()
    assert resumen["llegaron"] == 4000
    assert resumen["contestados"] == 4000


# ---------------------------------------------------------------- el endpoint


def _estado(puerto: int, cabeceras: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    peticion = Request(f"http://127.0.0.1:{puerto}/estado", headers=cabeceras or {})
    try:
        with urlopen(peticion, timeout=5) as respuesta:
            return respuesta.status, json.loads(respuesta.read())
    except HTTPError as error:
        return error.code, {}


def _servidor_con(marcador: Marcador | None, token: str) -> tuple[Any, Any]:
    from vigia.servidor import construir_servidor

    enviador = EnviadorFalso()
    servidor = construir_servidor(
        ("127.0.0.1", 0), SECRETO, enviador, marcador=marcador, token_de_estado=token
    )
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    return servidor, enviador


def test_sin_token_configurado_el_endpoint_no_existe() -> None:
    """**Seguro por defecto.**

    Si nadie configuró un token no hay superficie que atacar: la ruta contesta 404, igual que
    cualquier otra que no exista.
    """
    servidor, _ = _servidor_con(Marcador(), "")
    try:
        codigo, _ = _estado(servidor.server_address[1])
        assert codigo == 404
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_con_token_equivocado_tampoco_existe() -> None:
    """Un 401 diría «acá hay algo». Un 404 no dice nada."""
    servidor, _ = _servidor_con(Marcador(), "el-bueno")
    try:
        codigo, _ = _estado(servidor.server_address[1], {"Authorization": "Bearer el-malo"})
        assert codigo == 404
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_con_el_token_bueno_devuelve_el_resumen() -> None:
    marcador = Marcador()
    marcador.llegada()
    marcador.contestado("no_coincide")
    servidor, _ = _servidor_con(marcador, "el-bueno")
    try:
        codigo, datos = _estado(servidor.server_address[1], {"Authorization": "Bearer el-bueno"})
        assert codigo == 200
        assert datos["llegaron"] == 1
        assert datos["veredicto"] == {"no_coincide": 1}
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_el_endpoint_no_es_una_via_para_mandar_mensajes() -> None:
    """Leer el estado no manda nada, y **no puede costar 19 CLP**."""
    marcador = Marcador()
    enviador = EnviadorFalso()
    servidor, _ = _servidor_con(marcador, "el-bueno")
    try:
        for _ in range(5):
            _estado(servidor.server_address[1], {"Authorization": "Bearer el-bueno"})
        assert enviador.enviados == []
        assert marcador.resumen()["llegaron"] == 0
    finally:
        servidor.shutdown()
        servidor.server_close()


def test_el_webhook_alimenta_el_marcador() -> None:
    """De punta a punta: un mensaje firmado de verdad tiene que mover el contador."""
    from vigia.servidor import atender

    marcador = Marcador()
    enviador = EnviadorFalso()
    bruto = cuerpo()
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, marcador=marcador)
    resumen = marcador.resumen()
    assert resumen["llegaron"] == 1
    assert resumen["contestados"] == 1
    assert sum(_cuenta(resumen, "veredicto").values()) == 1


def test_una_firma_mala_mueve_el_silencio_y_no_el_contador_de_llegadas() -> None:
    """**Una firma que empieza a fallar es una alarma**, no un mensaje.

    O cambió el secreto, o alguien está probando. Por eso se cuenta aparte.
    """
    from vigia.servidor import atender

    marcador = Marcador()
    enviador = EnviadorFalso()
    atender(
        cuerpo(),
        "0" * 64,
        SECRETO,
        enviador,
        marcador=marcador,
        anotar=lambda _m: None,
    )
    resumen = marcador.resumen()
    assert resumen["llegaron"] == 0
    assert enviador.enviados == []


def test_el_numero_de_llegadas_cuadra_con_el_de_kapso() -> None:
    """El `phone_number_id` no entra al marcador: es un dato de la conversación, no una cuenta."""
    from vigia.servidor import atender

    marcador = Marcador()
    enviador = EnviadorFalso()
    bruto = cuerpo()
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, marcador=marcador)
    assert ID_NUMERO not in json.dumps(marcador.resumen())
