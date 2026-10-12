"""Tests del servidor del webhook (T1.4b)."""

from __future__ import annotations

import json
import threading
from http.client import HTTPMessage
from io import BytesIO
from typing import Any
from urllib.request import Request, urlopen

from vigia.firma import firmar
from vigia.memoria import Memoria
from vigia.servidor import (
    KapsoRespondedor,
    _SinRedirecciones,
    atender,
    construir_servidor,
)

SECRETO = "s3cr3t0"
ID_NUMERO = "109999999999999"


class EnviadorFalso:
    """Anota lo que se le pidió enviar, sin tocar la red."""

    def __init__(self) -> None:
        self.enviados: list[tuple[str, str, str]] = []

    def responder(self, phone_number_id: str, destinatario: str, texto: str) -> None:
        self.enviados.append((phone_number_id, destinatario, texto))


def cuerpo(**cambios: Any) -> bytes:
    base: dict[str, Any] = {
        "event": "whatsapp.message.received",
        "phone_number_id": ID_NUMERO,
        "message": {
            "id": "wamid.ABC",
            "kapso": {
                "direction": "inbound",
                "has_media": False,
                "content": "Su ClaveUnica sera bloqueada, entre a claveunica-gob-cl.xyz",
            },
        },
        "conversation": {"id": "conv-1", "phone_number": "56912345678"},
    }
    base.update(cambios)
    return json.dumps(base).encode()


def test_sin_firma_no_responde() -> None:
    enviador = EnviadorFalso()
    assert not atender(cuerpo(), None, SECRETO, enviador)
    assert enviador.enviados == []


def test_una_firma_mala_no_responde() -> None:
    enviador = EnviadorFalso()
    assert not atender(cuerpo(), "0" * 64, SECRETO, enviador)
    assert enviador.enviados == []


def test_un_mensaje_con_enlace_ajeno_se_responde() -> None:
    enviador = EnviadorFalso()
    bruto = cuerpo()
    assert atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    assert len(enviador.enviados) == 1
    id_numero, destinatario, texto = enviador.enviados[0]
    assert id_numero == ID_NUMERO
    assert destinatario == "56912345678"
    assert "no es de ClaveÚnica" in texto


def test_un_acuse_de_entrega_no_responde() -> None:
    enviador = EnviadorFalso()
    bruto = cuerpo(event="whatsapp.message.delivered")
    assert not atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    assert enviador.enviados == []


def test_sin_destinatario_no_se_responde() -> None:
    enviador = EnviadorFalso()
    bruto = cuerpo(conversation={"id": "conv-1"})
    assert not atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    assert enviador.enviados == []


def test_un_cuerpo_ilegible_no_revienta() -> None:
    enviador = EnviadorFalso()
    bruto = b"no soy json"
    assert not atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    assert enviador.enviados == []


def test_el_envio_no_sigue_redirecciones() -> None:
    """`urlopen` sigue las redirecciones por defecto y **reenvía las cabeceras**, incluida la clave
    de API, al host de destino: bastaría un 302 para llevársela. `REQ-12`."""
    manejador = _SinRedirecciones()
    respuesta = manejador.redirect_request(
        Request("https://api.kapso.ai/x"),
        BytesIO(b""),
        302,
        "Found",
        HTTPMessage(),
        "https://otro.example/",
    )
    assert respuesta is None


def test_el_envio_arma_la_peticion_que_documenta_kapso() -> None:
    """Fija la forma de la petición, que es lo único que no salió de un ejemplo literal.

    Kapso la documenta en su referencia de la API de WhatsApp; queda clavada acá para que un cambio
    se note, y se confirma con un envío real la primera vez que haya credenciales.
    """
    capturadas: list[Any] = []

    def abrir(peticion: Any) -> Any:
        capturadas.append(peticion)
        return None

    enviador = KapsoRespondedor(base="https://api.kapso.ai", api_key="clave", abrir=abrir)
    enviador.responder(ID_NUMERO, "56912345678", "hola")

    assert len(capturadas) == 1
    peticion = capturadas[0]
    assert peticion.full_url == f"https://api.kapso.ai/meta/whatsapp/v24.0/{ID_NUMERO}/messages"
    assert peticion.get_header("X-api-key") == "clave"
    assert json.loads(peticion.data) == {
        "messaging_product": "whatsapp",
        "to": "56912345678",
        "type": "text",
        "text": {"body": "hola"},
    }


def test_el_servidor_cuenta_la_modalidad_cuando_se_le_pide() -> None:
    """El contador de `T3.1`, enchufado. Sin él, nada se cuenta: está apagado por defecto."""
    contadas: list[object] = []
    enviador = EnviadorFalso()
    bruto = cuerpo()
    assert atender(
        bruto, firmar(bruto, SECRETO), SECRETO, enviador, contar=contadas.append
    )
    assert len(contadas) == 1
    assert "ClaveUnica" in str(contadas[0])


def test_el_servidor_no_cuenta_nada_si_no_se_le_pide() -> None:
    enviador = EnviadorFalso()
    bruto = cuerpo()
    assert atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)


def test_el_servidor_usa_el_catalogo_por_defecto() -> None:
    """El catálogo tiene que llegar hasta producción.

    `atender` y `construir_servidor` traían la lista **vacía** por defecto y `main` no pasaba
    ninguna, así que el servidor corría el motor sin catálogo: un mensaje legítimo del SERNAC se
    habría leído como ajeno, que es justo el error que `T1.3` vino a evitar.

    Se descubrió comparando la respuesta que llegó a un teléfono real con la que daba el mismo
    texto en local. Los tests unitarios no lo veían porque **todos** pasaban el catálogo a mano.
    """
    enviador = EnviadorFalso()
    bruto = json.dumps(
        {
            "event": "whatsapp.message.received",
            "phone_number_id": ID_NUMERO,
            "message": {
                "id": "wamid.CAT",
                "kapso": {
                    "direction": "inbound",
                    "has_media": False,
                    "content": "SERNAC le devuelve dinero. Reclame en https://www.sernac.cl/reclamo",
                },
            },
            "conversation": {"id": "conv-cat", "phone_number": "56912345678"},
        }
    ).encode()
    assert atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    # Con el catálogo vacío el texto diría «El enlace sernac.cl NO es del Estado», que es
    # exactamente la acusación falsa que se estaba colando en producción.
    assert "SERNAC" in enviador.enviados[0][2]


def test_el_servidor_contesta_200_aunque_la_firma_sea_mala() -> None:
    """Un error nuestro no puede hacer que Kapso reintente: siempre 200."""
    enviador = EnviadorFalso()
    servidor = construir_servidor(("127.0.0.1", 0), SECRETO, enviador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        puerto = servidor.server_address[1]
        peticion = Request(
            f"http://127.0.0.1:{puerto}/webhook",
            data=cuerpo(),
            headers={"X-Webhook-Signature": "0" * 64},
            method="POST",
        )
        with urlopen(peticion, timeout=5) as respuesta:
            assert respuesta.status == 200
        assert enviador.enviados == []
    finally:
        servidor.shutdown()
        servidor.server_close()


class ExtractorFalso:
    """Un extractor de mentira, para probar el cableado sin red."""

    def __init__(self, pide: tuple[Any, ...] = ()) -> None:
        self.pide = pide

    def extraer(self, texto: str, dice_ser: str | None) -> Any:
        from vigia.peticion import Peticion

        return Peticion(dice_ser=dice_ser, pide=self.pide)


def test_un_mensaje_sin_enlace_que_pide_la_clave_ya_no_queda_mudo() -> None:
    """**El extractor conectado al robot.** Antes del cableado esto daba `SIN_ENLACES`."""
    from vigia.peticion import PeticionDe

    enviador = EnviadorFalso()
    bruto = json.dumps(
        {
            "event": "whatsapp.message.received",
            "phone_number_id": ID_NUMERO,
            "message": {
                "id": "wamid.PET",
                "kapso": {
                    "direction": "inbound",
                    "has_media": False,
                    "content": "Su ClaveUnica sera bloqueada. Responda con su clave y su RUT.",
                },
            },
            "conversation": {"id": "c-pet", "phone_number": "56912345678"},
        }
    ).encode()
    assert atender(
        bruto,
        firmar(bruto, SECRETO),
        SECRETO,
        enviador,
        extraer=ExtractorFalso((PeticionDe.CLAVE, PeticionDe.DATOS_PERSONALES)),
    )
    texto = enviador.enviados[0][2]
    assert "ClaveÚnica" in texto
    assert "clave" in texto
    assert "seguro" not in texto.lower()


def test_sin_extractor_el_motor_se_comporta_como_antes() -> None:
    enviador = EnviadorFalso()
    bruto = json.dumps(
        {
            "event": "whatsapp.message.received",
            "phone_number_id": ID_NUMERO,
            "message": {
                "id": "wamid.MUDO",
                "kapso": {
                    "direction": "inbound",
                    "has_media": False,
                    "content": "Su ClaveUnica sera bloqueada",
                },
            },
            "conversation": {"id": "c-mudo", "phone_number": "56912345678"},
        }
    ).encode()
    assert atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    assert "Pégame" in enviador.enviados[0][2]


def test_el_limite_corta_los_mensajes_y_ahorra_dinero() -> None:
    """**Cada respuesta cuesta ≈ 19 CLP.** El que se pasa recibe un aviso y después silencio."""
    memoria = Memoria(maximo=2, ventana_s=3600, ahora=lambda: 0.0)
    enviador = EnviadorFalso()
    for i in range(4):
        bruto = cuerpo(conversation={"id": "c", "phone_number": "56912345678"}, message={
            "id": f"wamid.{i}",
            "kapso": {"direction": "inbound", "has_media": False, "content": "hola"},
        })
        atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, memoria=memoria)

    # El tercero cruza el límite y todavía se contesta para poder avisar; el cuarto ya no.
    assert len(enviador.enviados) == 3, "el cuarto mensaje no se contesta: costaría 19 CLP"
    assert "muchos mensajes" in enviador.enviados[2][2].lower()


def test_el_aviso_de_privacidad_viaja_en_la_primera_respuesta() -> None:
    """La decisión de `doc/14-GAP.md` §5.1, cumplida: se avisa que se usa un modelo."""
    memoria = Memoria(maximo=10, ventana_s=3600, ahora=lambda: 0.0)
    enviador = EnviadorFalso()
    bruto = cuerpo()
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, memoria=memoria)
    primera = enviador.enviados[0][2]
    assert "modelo" in primera.lower()
    assert "no lo guardamos" in primera.lower() or "no se guarda" in primera.lower()

    bruto2 = cuerpo(message={
        "id": "wamid.DOS",
        "kapso": {"direction": "inbound", "has_media": False, "content": "otra vez"},
    })
    atender(bruto2, firmar(bruto2, SECRETO), SECRETO, enviador, memoria=memoria)
    assert "modelo" not in enviador.enviados[1][2].lower(), "no se repite: sería ruido"


def test_sin_memoria_nada_cambia() -> None:
    """La memoria es opcional, como todo lo demás: sin ella el robot se comporta como antes."""
    enviador = EnviadorFalso()
    bruto = cuerpo()
    assert atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador)
    assert len(enviador.enviados) == 1


def test_el_servidor_anota_por_que_no_respondio() -> None:
    """**Un envío que falla no puede verse igual que un mensaje sin nada que responder.**

    Es el modo de fallo que ya nos dejó ciegos una vez: en la prueba real hubo que ir a la API de
    Kapso para saber si la respuesta había salido, porque el registro solo tenía el código HTTP.
    """
    anotaciones: list[str] = []
    enviador = EnviadorFalso()

    atender(b"{}", "mala", SECRETO, enviador, anotar=anotaciones.append)
    assert anotaciones and not anotaciones[0].startswith("respondido")

    anotaciones.clear()
    bruto = cuerpo()
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, anotar=anotaciones.append)
    assert anotaciones[-1].startswith("respondido")
