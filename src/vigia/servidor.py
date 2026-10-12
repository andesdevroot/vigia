"""Servidor del webhook (T1.4b). Solo stdlib: `http.server` y `urllib.request`.

Junta las piezas: verifica la firma, lee el mensaje, compone la respuesta y la manda. Es el único
módulo que toca la red, y por eso todo lo demás se puede probar sin ella.

## El servidor siempre contesta 200

Si contestara 500, Kapso reintentaría — y reintentar un mensaje que no supimos leer no lo vuelve
legible: solo multiplica el error. Un fallo nuestro se registra y se pierde; el ciudadano que
reenvió el mensaje no recibe respuesta, que es malo, pero peor es un bucle de reintentos.

## Lo que no se guarda

El cuerpo del mensaje se lee, se pasa por el motor y se descarta. **No se escribe en disco y no se
registra.** El registro por defecto de `http.server` escribe solo la línea de la petición —método,
ruta y versión—, nunca el cuerpo. La promesa «no guardamos lo que nos mandas» se cumple acá o no se
cumple en ninguna parte.

## Por qué no se siguen las redirecciones

`urlopen` las sigue por defecto y **reenvía las cabeceras**, incluida la clave de API, al host de
destino. Bastaría un 302 para llevarse la clave a otro sitio. Por eso el abridor propio las corta.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from hmac import compare_digest
from http.client import HTTPMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import IO, Any, Protocol
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from vigia.conversacion import AVISO_PRIVACIDAD, ESPERA, componer
from vigia.entrante import MensajeRecibido, interpretar
from vigia.extractor import CacheDeExtraccion, Extractor, ExtractorLLM
from vigia.firma import es_valida
from vigia.imagen import Lector, LectorTesseract
from vigia.marcador import Marcador, Salida
from vigia.marcas import MARCAS
from vigia.medicion import Contador, Contar
from vigia.medios import KapsoMedios, Medios
from vigia.memoria import MENSAJES_POR_VENTANA, VENTANA_S, Decision, Memoria
from vigia.motor import evaluar
from vigia.suplantacion import Marca

TIEMPO_LIMITE_S = 10
"""Cuánto se espera a la API de Kapso antes de darse por vencido.

Sin límite, una llamada colgada deja el hilo del webhook ocupado y el proveedor reintenta por
tiempo agotado, con lo que el problema se multiplica solo.
"""


class Respondedor(Protocol):
    """Lo que el servidor necesita para contestar. Se inyecta, y por eso se puede probar sin red."""

    def responder(self, phone_number_id: str, destinatario: str, texto: str) -> None: ...


Abridor = Callable[[Request], Any]


class _SinRedirecciones(HTTPRedirectHandler):
    """Corta las redirecciones. Devolver `None` es la forma de decir «no sigas»."""

    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> Request | None:
        return None


_ABRIDOR = build_opener(_SinRedirecciones())


class KapsoRespondedor:
    """Manda la respuesta por la API de WhatsApp de Kapso.

    La forma de la petición —ruta, cabecera de autenticación y cuerpo— es la que documenta Kapso en
    su referencia de la API de WhatsApp, y hay un test que la fija para que un cambio se note.
    """

    def __init__(
        self,
        base: str,
        api_key: str,
        version: str = "v24.0",
        abrir: Abridor | None = None,
    ) -> None:
        self._base = base.rstrip("/")
        self._api_key = api_key
        self._version = version
        self._abrir: Abridor = abrir or _abrir_con_limite

    def responder(self, phone_number_id: str, destinatario: str, texto: str) -> None:
        url = f"{self._base}/meta/whatsapp/{self._version}/{phone_number_id}/messages"
        cuerpo = {
            "messaging_product": "whatsapp",
            "to": destinatario,
            "type": "text",
            "text": {"body": texto},
        }
        peticion = Request(
            url,
            data=json.dumps(cuerpo).encode(),
            headers={"X-API-Key": self._api_key, "Content-Type": "application/json"},
            method="POST",
        )
        self._abrir(peticion)


def _abrir_con_limite(peticion: Request) -> Any:
    return _ABRIDOR.open(peticion, timeout=TIEMPO_LIMITE_S)


def atender(
    cuerpo: bytes,
    firma: str | None,
    secreto: str,
    enviar: Respondedor,
    marcas: Sequence[Marca] = MARCAS,
    contar: Contar | None = None,
    extraer: Extractor | None = None,
    memoria: Memoria | None = None,
    anotar: Callable[[str], None] | None = None,
    lector: Lector | None = None,
    medios: Medios | None = None,
    marcador: Marcador | None = None,
) -> bool:
    """Atiende un webhook y devuelve si se alcanzó a responder.

    La firma se verifica **antes** de parsear: es lo que documenta Kapso y lo único que garantiza
    que el cuerpo no se interpretó antes de saber quién lo mandó.

    Con `memoria` se aplica el límite por persona y se avisa de la privacidad la primera vez. Con
    `anotar` queda registrado **por qué** no se respondió: sin eso, un envío que falla se ve
    exactamente igual que un mensaje sin nada que responder, y ya nos dejó ciegos una vez.
    """
    if not es_valida(firma, cuerpo, secreto):
        # **Una firma que empieza a fallar es una alarma**, no un mensaje: o cambio el secreto, o
        # alguien esta probando. Por eso se cuenta aparte de las llegadas.
        _silencio(marcador, Salida.FIRMA)
        _anota(anotar, "firma invalida")
        return False
    try:
        sobre = json.loads(cuerpo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        _silencio(marcador, Salida.ILEGIBLE)
        _anota(anotar, "cuerpo ilegible")
        return False

    mensaje = interpretar(sobre)
    if mensaje is not None:
        mensaje = _con_el_texto_del_adjunto(mensaje, lector, medios, anotar)
    if mensaje is None or mensaje.destinatario is None:
        # Un mensaje saliente, o un sobre con la forma equivocada. No se contesta y no es un error.
        _silencio(marcador, Salida.SIN_DESTINATARIO)
        _anota(anotar, "sin destinatario")
        return False

    # Se cuenta **antes** de enviar, a propósito: si el envío falla, el mensaje igual llegó, y para
    # medir modalidades lo que importa es cómo llegó, no si alcanzamos a contestar.
    # Llegó de verdad: firma verificada y destinatario conocido. Se cuenta acá y no antes, porque
    # un mensaje sin destinatario no es una llegada: es un sobre que no supimos leer.
    if marcador is not None:
        marcador.llegada()

    if contar is not None:
        contar(mensaje)

    decision = Decision(responder=True)
    if memoria is not None:
        decision = memoria.decidir(mensaje.destinatario)
        if not decision.responder:
            # **Acá es donde se ahorra el dinero.** Cada respuesta cuesta ≈ 19 CLP, y esta no sale.
            _silencio(marcador, Salida.LIMITE)
            _anota(anotar, "limite alcanzado, sin respuesta")
            return False

    # **Una sola vez.** `componer` con extractor llama al modelo, y llamarlo dos veces pagaría
    # DeepSeek dos veces por el mismo mensaje.
    partes = [componer(mensaje, marcas, extraer)]
    if decision.avisar_limite:
        partes.append(ESPERA)
    if decision.avisar_privacidad:
        partes.append(AVISO_PRIVACIDAD)

    enviar.responder(mensaje.phone_number_id, mensaje.destinatario, " ".join(partes))
    # El veredicto del **enlace**, que es local y gratis, y se rotula como tal: con extractor el
    # veredicto final puede ser otro, y el registro no debería insinuar que es el mismo.
    enlace = evaluar(mensaje.texto, marcas=marcas).veredicto.value
    if marcador is not None:
        marcador.contestado(enlace)
    _anota(anotar, f"respondido (enlace {enlace})")
    return True


def _con_el_texto_del_adjunto(
    mensaje: MensajeRecibido,
    lector: Lector | None,
    medios: Medios | None,
    anotar: Callable[[str], None] | None = None,
) -> MensajeRecibido:
    """El mensaje con el texto que se va a juzgar, leyendo el adjunto si hace falta.

    **El orden importa, y es de lo más barato a lo más caro:**

    1. Si el ciudadano escribió algo, eso manda. No se baja nada.
    2. El audio ya viene transcrito por Kapso: no hay nada que hacer.
    3. La captura se baja y **se lee acá adentro**. La imagen no sale del servidor.

    Si nada de eso da texto, el mensaje vuelve como vino y el robot pide el texto a mano, que es
    exactamente lo que hacía antes de que esto existiera.
    """
    if mensaje.texto.strip():
        return mensaje
    if mensaje.transcripcion and mensaje.transcripcion.strip():
        _anota(anotar, "audio transcrito por Kapso")
        return replace(mensaje, texto=mensaje.transcripcion, de_adjunto=True)
    if not mensaje.media_url or lector is None or medios is None:
        return mensaje

    imagen = medios.descargar(mensaje.media_url)
    if not imagen:
        _anota(anotar, "no se pudo bajar el adjunto")
        return mensaje
    texto = lector.leer(imagen)
    if not texto:
        _anota(anotar, "el adjunto no tenia texto legible")
        return mensaje
    _anota(anotar, "captura leida con OCR local")
    return replace(mensaje, texto=texto, de_adjunto=True)


def _silencio(marcador: Marcador | None, motivo: Salida) -> None:
    """Deja constancia de que no se contestó, y por qué. **Vocabulario cerrado.**"""
    if marcador is not None:
        marcador.silencio(motivo)


def _anota(anotar: Callable[[str], None] | None, motivo: str) -> None:
    """Deja constancia de un motivo. **Nunca del contenido.**"""
    if anotar is not None:
        anotar(motivo)


def _motivo(error: BaseException) -> str:
    """Cómo se nombra un fallo en el registro.

    El código HTTP y no el mensaje completo: la respuesta de Kapso puede nombrar al destinatario, y
    el registro de este servidor no es lugar para datos de nadie.
    """
    if isinstance(error, HTTPError):
        return f"HTTP {error.code}"
    return type(error).__name__


class _Manejador(BaseHTTPRequestHandler):
    secreto: str
    enviar: Respondedor
    marcas: tuple[Marca, ...]
    contar: Contar | None
    extraer: Extractor | None
    memoria: Memoria | None
    lector: Lector | None
    medios: Medios | None
    marcador: Marcador | None
    token_de_estado: str

    def do_GET(self) -> None:  # noqa: N802 - lo impone la clase base
        """El chequeo de salud, y el estado.

        El chequeo de salud va **sin firma, porque la plataforma no puede firmar**. Y no dice
        nada de adentro: que el servicio esté vivo es un dato público; qué versión corre, no.

        No dispara el contador ni el extractor. Una plataforma llama a esto cada pocos segundos, y
        no puede costar lo que cuesta un mensaje.
        """
        if self.path.split("?", 1)[0].rstrip("/") == "/estado":
            self._estado()
            return
        self._json(200, {"ok": True})

    def _estado(self) -> None:
        """Cuántos mensajes llegaron, cuántos se contestaron y cuándo fue el último.

        **Cerrado por defecto.** Sin `VIGIA_ESTADO_TOKEN` configurado, esta ruta no existe: no hay
        superficie que atacar. Y con un token equivocado contesta **404, no 401** — un 401 diría
        «acá hay algo».

        La comparación es de tiempo constante. Comparar con `==` filtra, por el tiempo que tarda, en
        qué prefijo se equivocó el que prueba.
        """
        esperado = f"Bearer {self.token_de_estado}" if self.token_de_estado else ""
        recibido = self.headers.get("Authorization", "")
        if not esperado or not compare_digest(recibido, esperado) or self.marcador is None:
            self._json(404, {"ok": False})
            return
        self._json(200, self.marcador.resumen())

    def _json(self, codigo: int, datos: dict[str, Any]) -> None:
        respuesta = json.dumps(datos, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(respuesta)))
        self.end_headers()
        self.wfile.write(respuesta)

    def do_POST(self) -> None:  # noqa: N802 - lo impone la clase base
        respondido = False
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            respondido = atender(
                self.rfile.read(largo),
                self.headers.get("X-Webhook-Signature"),
                self.secreto,
                self.enviar,
                self.marcas,
                self.contar,
                self.extraer,
                self.memoria,
                lambda motivo: self.log_message("%s", motivo),
                self.lector,
                self.medios,
            )
        except Exception as error:  # noqa: BLE001 - un webhook nunca contesta 500
            # Se registra el **motivo**, nunca el contenido. Sin esto, un envío que falla se ve
            # exactamente igual que un mensaje sin nada que responder, y depurar es adivinar: pasó
            # la primera vez que se probó contra el sandbox, con un 403 que no dejó rastro.
            self.log_error("no se pudo responder: %s", _motivo(error))
            respondido = False

        respuesta = json.dumps({"ok": True, "respondido": respondido}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(respuesta)))
        self.end_headers()
        self.wfile.write(respuesta)


def _manejador(
    secreto: str,
    enviar: Respondedor,
    marcas: tuple[Marca, ...],
    contar: Contar | None,
    extraer: Extractor | None,
    memoria: Memoria | None = None,
    lector: Lector | None = None,
    medios: Medios | None = None,
    marcador: Marcador | None = None,
    token_de_estado: str = "",
) -> type[BaseHTTPRequestHandler]:
    """Una subclase con la configuración pegada, que es como `http.server` espera recibirla."""
    campos: dict[str, Any] = {
        "secreto": secreto,
        "enviar": enviar,
        "marcas": marcas,
        "contar": contar,
        "extraer": extraer,
        "memoria": memoria,
        "lector": lector,
        "medios": medios,
        "marcador": marcador,
        "token_de_estado": token_de_estado,
    }
    return type("Manejador", (_Manejador,), campos)


def construir_servidor(
    direccion: tuple[str, int],
    secreto: str,
    enviar: Respondedor,
    marcas: Sequence[Marca] = MARCAS,
    contar: Contar | None = None,
    extraer: Extractor | None = None,
    memoria: Memoria | None = None,
    lector: Lector | None = None,
    medios: Medios | None = None,
    marcador: Marcador | None = None,
    token_de_estado: str = "",
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        direccion,
        _manejador(
            secreto,
            enviar,
            tuple(marcas),
            contar,
            extraer,
            memoria,
            lector,
            medios,
            marcador,
            token_de_estado,
        ),
    )


def puerto_del_entorno(entorno: Mapping[str, str]) -> int:
    """El puerto donde escuchar, sacado del entorno.

    **`PORT` primero**: es la convención de las plataformas, y es la que ellas van a usar para
    enrutar. `VIGIA_PUERTO` es el nombre nuestro y sirve para correr local.

    Un puerto inválido **falla al arrancar**, a propósito: mejor no levantar que escuchar donde
    nadie va a llamar.
    """
    crudo = entorno.get("PORT") or entorno.get("VIGIA_PUERTO") or "8000"
    try:
        puerto = int(crudo)
    except ValueError as error:
        raise ValueError(f"el puerto {crudo!r} no es un número") from error
    if not 1 <= puerto <= 65535:
        raise ValueError(f"el puerto {puerto} está fuera de rango")
    return puerto


def main() -> None:
    """Levanta el webhook. `python -m vigia.servidor`."""
    secreto = os.environ.get("VIGIA_WEBHOOK_SECRET")
    api_key = os.environ.get("KAPSO_API_KEY")
    if not secreto or not api_key:
        raise SystemExit("Faltan VIGIA_WEBHOOK_SECRET y/o KAPSO_API_KEY en el entorno.")

    enviar = KapsoRespondedor(
        base=os.environ.get("KAPSO_API_BASE_URL", "https://api.kapso.ai"),
        api_key=api_key,
    )
    # El contador de `T3.1` está **apagado por defecto**: solo existe si alguien lo pide.
    contar: Contar | None = None
    if os.environ.get("VIGIA_CONTAR"):
        contar = Contador(Path(os.environ.get("VIGIA_CONTADOR", "conteo.json")))

    # El extractor, si hay clave. Se envuelve en la caché para no pagar dos veces el mismo mensaje.
    extraer: Extractor | None = None
    clave_deepseek = os.environ.get("DEEPSEEK_API_KEY")
    if clave_deepseek:
        extraer = CacheDeExtraccion(
            ExtractorLLM(
                base=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                api_key=clave_deepseek,
                modelo=os.environ.get("DEEPSEEK_MODELO", "deepseek-chat"),
            )
        )

    # El límite **no es opcional**: cada respuesta cuesta ≈ 19 CLP, y sin él cualquiera que
    # encuentre el número puede vaciar el presupuesto de un servicio público.
    memoria = Memoria(
        maximo=int(os.environ.get("VIGIA_MAXIMO", str(MENSAJES_POR_VENTANA))),
        ventana_s=float(os.environ.get("VIGIA_VENTANA_S", str(VENTANA_S))),
    )

    # El OCR es **local**: la captura no sale del servidor. Si el binario no está, no se activa y el
    # robot vuelve a pedir el texto, que es lo que hacía antes.
    lector: Lector | None = None
    if LectorTesseract().esta_disponible():
        lector = LectorTesseract()

    # El marcador **no es opcional**: sin el, un servicio caido se ve igual que nadie usandolo.
    marcador = Marcador()

    puerto = puerto_del_entorno(os.environ)
    servidor = construir_servidor(
        ("", puerto),
        secreto,
        enviar,
        contar=contar,
        extraer=extraer,
        memoria=memoria,
        lector=lector,
        medios=KapsoMedios(api_key=api_key),
        marcador=marcador,
        token_de_estado=os.environ.get("VIGIA_ESTADO_TOKEN", ""),
    )
    print(f"Escuchando en el puerto {puerto}.")  # noqa: T201 - es la salida del programa
    servidor.serve_forever()


if __name__ == "__main__":
    main()
