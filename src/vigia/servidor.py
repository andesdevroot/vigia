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
from collections.abc import Callable, Sequence
from http.client import HTTPMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import IO, Any, Protocol
from urllib.request import HTTPRedirectHandler, Request, build_opener

from vigia.conversacion import componer
from vigia.entrante import interpretar
from vigia.firma import es_valida
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
    marcas: Sequence[Marca] = (),
) -> bool:
    """Atiende un webhook y devuelve si se alcanzó a responder.

    La firma se verifica **antes** de parsear: es lo que documenta Kapso y lo único que garantiza
    que el cuerpo no se interpretó antes de saber quién lo mandó.
    """
    if not es_valida(firma, cuerpo, secreto):
        return False
    try:
        sobre = json.loads(cuerpo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

    mensaje = interpretar(sobre)
    if mensaje is None or mensaje.destinatario is None:
        return False

    enviar.responder(
        mensaje.phone_number_id,
        mensaje.destinatario,
        componer(mensaje, marcas),
    )
    return True


class _Manejador(BaseHTTPRequestHandler):
    secreto: str
    enviar: Respondedor
    marcas: tuple[Marca, ...]

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
            )
        except Exception:  # noqa: BLE001 - un webhook nunca contesta 500
            respondido = False

        respuesta = json.dumps({"ok": True, "respondido": respondido}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(respuesta)))
        self.end_headers()
        self.wfile.write(respuesta)


def _manejador(
    secreto: str, enviar: Respondedor, marcas: tuple[Marca, ...]
) -> type[BaseHTTPRequestHandler]:
    """Una subclase con la configuración pegada, que es como `http.server` espera recibirla."""
    campos: dict[str, Any] = {"secreto": secreto, "enviar": enviar, "marcas": marcas}
    return type("Manejador", (_Manejador,), campos)


def construir_servidor(
    direccion: tuple[str, int],
    secreto: str,
    enviar: Respondedor,
    marcas: Sequence[Marca] = (),
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(direccion, _manejador(secreto, enviar, tuple(marcas)))


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
    puerto = int(os.environ.get("VIGIA_PUERTO", "8000"))
    servidor = construir_servidor(("", puerto), secreto, enviar)
    print(f"Escuchando en el puerto {puerto}.")  # noqa: T201 - es la salida del programa
    servidor.serve_forever()


if __name__ == "__main__":
    main()
