"""Registra o actualiza el webhook en Kapso con la URL del túnel actual.

## El problema que resuelve

`ngrok` da una URL **distinta cada vez**. Si el webhook queda apuntando a la anterior, los mensajes
dejan de llegar **sin ningún error visible**: el teléfono se queda callado y uno culpa al motor. Acá
la URL se reescribe en cada arranque, así que ese modo de fallar no existe.

Si el webhook todavía no existe, lo crea y guarda el `secret_key` en `.env` — es la **única** vez
que se puede leer. Si ya existe, le cambia la URL y lo reactiva. Con `--apagar` lo deja inactivo,
para no dejar un webhook huérfano apuntando a un túnel muerto.

No imprime secretos. Nunca.
"""

from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ENV = RAIZ / ".env"
EVENTO = "whatsapp.message.received"


def leer_env() -> dict[str, str]:
    valores: dict[str, str] = {}
    for linea in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, _, valor = linea.partition("=")
            valores[clave.strip()] = valor.strip()
    return valores


def guardar_env(clave: str, valor: str) -> None:
    """Escribe o reemplaza una variable, sin tocar el resto del archivo."""
    texto = ENV.read_text(encoding="utf-8")
    lineas = [
        f"{clave}={valor}" if linea.startswith(f"{clave}=") else linea
        for linea in texto.splitlines()
    ]
    if not any(linea.startswith(f"{clave}=") for linea in lineas):
        lineas.append(f"{clave}={valor}")
    ENV.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def pedir(raiz: str, api_key: str, metodo: str, ruta: str, cuerpo: object = None) -> object:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(
        raiz + ruta,
        data=datos,
        method=metodo,
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            return json.loads(respuesta.read() or b"{}")
    except urllib.error.HTTPError as error:
        detalle = error.read().decode(errors="replace")[:200]
        raise SystemExit(f"Kapso contestó HTTP {error.code}: {detalle}") from error


def primer_numero(raiz: str, api_key: str) -> str:
    respuesta = pedir(raiz, api_key, "GET", "/platform/v1/whatsapp/phone_numbers")
    numeros = respuesta.get("data", []) if isinstance(respuesta, dict) else []
    if not numeros:
        raise SystemExit("No hay ningún número conectado en el proyecto.")
    return str(numeros[0]["id"])


def main() -> None:
    apagar = "--apagar" in sys.argv
    url = next((a for a in sys.argv[1:] if a.startswith("http")), None)

    env = leer_env()
    api_key = env.get("KAPSO_API_KEY")
    if not api_key:
        raise SystemExit("Falta KAPSO_API_KEY en .env")
    raiz = env.get("KAPSO_API_BASE_URL", "https://api.kapso.ai").rstrip("/")
    webhook_id = env.get("VIGIA_WEBHOOK_ID", "")

    if apagar:
        if not webhook_id:
            return
        pedir(raiz, api_key, "PATCH", f"/platform/v1/whatsapp/webhooks/{webhook_id}",
              {"whatsapp_webhook": {"active": False}})
        print("  webhook apagado (no queda apuntando a un túnel muerto)")
        return

    if not url:
        raise SystemExit("Falta la URL del túnel.")
    destino = url.rstrip("/") + "/webhook"
    cuerpo = {
        "whatsapp_webhook": {
            "url": destino,
            "events": [EVENTO],
            "payload_version": "v2",
            "kind": "kapso",
            "active": True,
        }
    }

    if webhook_id:
        respuesta = pedir(raiz, api_key, "PATCH",
                          f"/platform/v1/whatsapp/webhooks/{webhook_id}", cuerpo)
        print(f"  webhook actualizado: {destino}")
    else:
        cuerpo["whatsapp_webhook"]["phone_number_id"] = primer_numero(raiz, api_key)
        respuesta = pedir(raiz, api_key, "POST", "/platform/v1/whatsapp/webhooks", cuerpo)
        creado = respuesta.get("data", {}) if isinstance(respuesta, dict) else {}
        secreto = creado.get("secret_key")
        if not secreto:
            raise SystemExit("Kapso no devolvió secret_key: no se puede verificar la firma.")
        guardar_env("VIGIA_WEBHOOK_ID", str(creado["id"]))
        guardar_env("VIGIA_WEBHOOK_SECRET", str(secreto))
        print(f"  webhook creado: {destino}")
        print("  id y secreto guardados en .env (el secreto no se muestra)")

    datos = respuesta.get("data", {}) if isinstance(respuesta, dict) else {}
    if isinstance(datos, dict):
        print(f"  activo={datos.get('active')}  evento={datos.get('events')}  "
              f"version={datos.get('payload_version')}")


if __name__ == "__main__":
    main()
