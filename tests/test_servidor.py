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


class LectorFalso:
    """Un OCR de mentira: devuelve lo que se le diga, y anota qué imágenes vio."""

    def __init__(self, texto: str = "") -> None:
        self.texto = texto
        self.vistas: list[bytes] = []

    def leer(self, imagen: bytes) -> str:
        self.vistas.append(imagen)
        return self.texto


class MediosFalsos:
    """Un descargador de mentira: anota las URLs y devuelve bytes."""

    def __init__(self, contenido: bytes = b"imagen") -> None:
        self.contenido = contenido
        self.pedidas: list[str] = []

    def descargar(self, url: str) -> bytes:
        self.pedidas.append(url)
        return self.contenido


def _sobre_imagen(url: str = "https://api.kapso.ai/media/abc", **extra: Any) -> bytes:
    return json.dumps(
        {
            "event": "whatsapp.message.received",
            "phone_number_id": ID_NUMERO,
            "message": {
                "id": "wamid.FOTO",
                "kapso": {
                    "direction": "inbound",
                    "has_media": True,
                    "content": "",
                    "media_url": url,
                    **extra,
                },
            },
            "conversation": {"id": "c-foto", "phone_number": "56912345678"},
        }
    ).encode()


def test_una_captura_se_lee_y_se_juzga() -> None:
    """**El caso que va a pasar el primer día.** La gente manda capturas, no texto.

    Con el OCR local, el enlace que está escrito en la imagen llega al motor y el veredicto sale.
    """
    lector = LectorFalso("Su BancoEstado tiene un cargo. Ingrese a bancoestado-chile-login.xyz")
    medios = MediosFalsos(b"\x89PNG")
    enviador = EnviadorFalso()
    bruto = _sobre_imagen()
    assert atender(
        bruto, firmar(bruto, SECRETO), SECRETO, enviador, lector=lector, medios=medios
    )
    assert medios.pedidas == ["https://api.kapso.ai/media/abc"]
    assert lector.vistas == [b"\x89PNG"]
    respuesta = enviador.enviados[0][2]
    assert "bancoestado-chile-login.xyz" in respuesta
    assert "BancoEstado" in respuesta


def test_a_la_captura_legible_no_se_le_dice_que_no_se_puede_leer() -> None:
    """Leerla y después avisar que no se lee sería contradecirse en la misma respuesta."""
    lector = LectorFalso("entre a bancoestado-chile-login.xyz")
    enviador = EnviadorFalso()
    bruto = _sobre_imagen()
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, lector=lector, medios=MediosFalsos())
    assert "no las puedo leer" not in enviador.enviados[0][2]
    assert "no puedo leer" not in enviador.enviados[0][2].lower()


def test_una_captura_ilegible_pide_el_texto() -> None:
    """Una foto de un paisaje no tiene letras.

    **Se degrada a lo que hacía antes**, no se inventa.
    """
    lector = LectorFalso("")
    enviador = EnviadorFalso()
    bruto = _sobre_imagen()
    assert atender(
        bruto, firmar(bruto, SECRETO), SECRETO, enviador, lector=lector, medios=MediosFalsos()
    )
    assert "Copiar" in enviador.enviados[0][2]


def test_sin_lector_no_se_baja_la_imagen() -> None:
    """Sin OCR instalado no tiene sentido gastar una descarga: se pide el texto de una."""
    medios = MediosFalsos()
    enviador = EnviadorFalso()
    bruto = _sobre_imagen()
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, medios=medios)
    assert medios.pedidas == [], "sin lector no se baja nada"
    assert "Copiar" in enviador.enviados[0][2]


def test_un_fallo_al_bajar_la_imagen_no_tumba_el_webhook() -> None:
    """Si la descarga falla, el ciudadano recibe algo. **Un webhook nunca contesta 500.**"""

    class MediosRotos:
        def descargar(self, url: str) -> bytes:
            return b""

    enviador = EnviadorFalso()
    bruto = _sobre_imagen()
    assert atender(
        bruto,
        firmar(bruto, SECRETO),
        SECRETO,
        enviador,
        lector=LectorFalso("texto"),
        medios=MediosRotos(),
    )
    assert "Copiar" in enviador.enviados[0][2]


def test_el_audio_lo_transcribe_kapso_y_se_usa() -> None:
    """**Kapso ya transcribe los audios.** No hay que bajar nada: el texto viene en el sobre."""
    medios = MediosFalsos()
    enviador = EnviadorFalso()
    # El campo del sobre de Kapso se llama `transcript`, no `transcripcion`: ese es el nombre
    # nuestro una vez leido.
    dicho = "me llego un mensaje de bancoestado que dice que entre a bancoestado-chile-login.xyz"
    bruto = _sobre_imagen(transcript=dicho)
    atender(bruto, firmar(bruto, SECRETO), SECRETO, enviador, medios=medios)
    assert medios.pedidas == [], "el audio ya viene transcrito: no hay nada que bajar"
    respuesta = enviador.enviados[0][2]
    assert "bancoestado-chile-login.xyz" in respuesta, "el veredicto usa lo que dijo el audio"
    assert "no puedo leer" not in respuesta.lower(), "el audio no es una imagen ilegible"


def test_el_texto_escrito_gana_sobre_la_imagen() -> None:
    """Si el ciudadano escribió algo, eso manda. La imagen no se baja."""
    medios = MediosFalsos()
    enviador = EnviadorFalso()
    bruto = json.dumps(
        {
            "event": "whatsapp.message.received",
            "phone_number_id": ID_NUMERO,
            "message": {
                "id": "wamid.MIXTO",
                "kapso": {
                    "direction": "inbound",
                    "has_media": True,
                    "content": "mire, me llego esto: entre a bancoestado-chile-login.xyz",
                    "media_url": "https://api.kapso.ai/media/abc",
                },
            },
            "conversation": {"id": "c-mix", "phone_number": "56912345678"},
        }
    ).encode()
    atender(
        bruto, firmar(bruto, SECRETO), SECRETO, enviador, lector=LectorFalso("x"), medios=medios
    )
    assert medios.pedidas == []
    assert "bancoestado-chile-login.xyz" in enviador.enviados[0][2]
