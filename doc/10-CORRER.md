# 10 — Cómo se corre

## Las piezas

| Módulo | Qué hace | Toca la red |
|---|---|---|
| `firma.py` | Verifica el HMAC de `X-Webhook-Signature` | No |
| `entrante.py` | Lee el sobre de Kapso | No |
| `motor.py` | El veredicto sobre el enlace | No |
| `conversacion.py` | Lo que se le contesta a la persona | No |
| `servidor.py` | HTTP y envío | **Sí, y es el único** |

**Todo menos el servidor se prueba sin red.** Es la razón de que los 74 tests corran en menos de un
segundo.

## Con lo que ya está, sin cuenta de nada

```bash
uv run pytest
```

## Levantar el webhook

```bash
export VIGIA_WEBHOOK_SECRET='<secret_key del webhook en Kapso>'
export KAPSO_API_KEY='<api key del proyecto>'
export KAPSO_API_BASE_URL='https://api.kapso.ai'
export VIGIA_PUERTO=8000
uv run python -m vigia.servidor
```

Tres cosas que este servidor **no** hace: no escribe en disco, no registra el cuerpo, y contesta 200
aunque falle. Lo primero y lo segundo son la promesa de privacidad; lo tercero evita que Kapso
reintente un mensaje que no supimos leer.

## En un solo comando

```bash
cp .env.example .env     # y pega los valores ahí
./scripts/probar_local.sh
```

El script levanta el webhook, abre un túnel con `ngrok` y **dice qué URL pegar en Kapso**. No imprime
ni copia ningún secreto.

## Enganchar Kapso, paso a paso

1. **El número.** Para probar, el número que Kapso da **gratis y ya verificado** en «Instant
   setup» alcanza, y su país por defecto es **Estados Unidos**. **Tu teléfono personal no se toca:**
   tú le escribes al robot desde tu WhatsApp, y el número dedicado es el del robot, no el tuyo.

   Que sea **+56** importa para producción, no para probar. Y sale barato: un chip prepago chileno
   nuevo —nunca registrado antes en WhatsApp— se conecta con «Bring your own SIM». Traer un número
   local por Kapso cuesta **USD 400 al mes** de add-on, así que no es el camino.
2. **Exponer el servidor.** Lo hace `probar_local.sh` con `ngrok`.
3. **Crear el webhook** contra el número, desde el panel de Kapso: el evento
   `whatsapp.message.received`, `payload_version` **v2**, y la URL `<túnel>/webhook`.
4. **Guardar el `secret_key`.** Kapso lo muestra **una sola vez**, y es `VIGIA_WEBHOOK_SECRET`.
5. **Escribirle al número** desde tu WhatsApp y ver la respuesta.

## Probar sin Kapso

El webhook se puede probar entero sin cuenta y sin túnel: firma el cuerpo a mano y mándalo al
servidor local. El comando está más abajo.

## Probar la firma a mano

Sin firma válida el servidor no responde nada, y eso es correcto. Para probarlo de verdad:

```bash
uv run python -c "
import json, urllib.request
from vigia.firma import firmar

secreto = '<secret_key>'
cuerpo = json.dumps({
    'event': 'whatsapp.message.received',
    'phone_number_id': '<PHONE_NUMBER_ID>',
    'message': {'id': 'wamid.TEST', 'kapso': {'direction': 'inbound', 'has_media': False,
                'content': 'Su ClaveUnica sera bloqueada: http://claveunica-gob-cl.xyz'}},
    'conversation': {'id': 'c1', 'phone_number': '56900000000'},
}).encode()
peticion = urllib.request.Request(
    'http://127.0.0.1:8000/webhook', data=cuerpo, method='POST',
    headers={'X-Webhook-Signature': firmar(cuerpo, secreto), 'Content-Type': 'application/json'},
)
print(urllib.request.urlopen(peticion).read())
"
```

## El sandbox, que es lo que hay conectado

El proyecto trae un número **Sandbox** (`kind: sandbox`, id `597907523413541`) que se crea solo con
el proyecto. No es un número de producción y **solo le puede escribir un destinatario: el que
registres**.

1. Kapso → **WhatsApp → Sandbox → Add Test Number** → tu número de WhatsApp.
2. Te da un **código de 6 caracteres**; mándalo desde tu WhatsApp al número del sandbox.
3. El código **vence a los 15 minutos**; si se pasa, se crea otra sesión.

Con la sesión activa, le escribes al sandbox desde tu teléfono y el webhook recibe el mensaje.

| | Sandbox | Producción |
|---|---|---|
| Texto | sí | sí |
| Plantillas | **no** | sí |
| Varios destinatarios | **no** | sí |

**Tu teléfono personal no se toca.** Registrarlo en el sandbox lo convierte en *remitente
autorizado*, que es lo contrario de cederlo.

## Crear el webhook por API

Lo que se midió, y no es lo que sugiere la documentación:

| Intento | Resultado |
|---|---|
| `POST /platform/v1/whatsapp/phone_numbers/{id}/webhooks` | **`400 Secret key can't be blank`** — por número, hay que aportar el secreto |
| `POST /platform/v1/whatsapp/webhooks` con `phone_number_id` en el cuerpo | **`201`**, y devuelve el `secret_key` |

El cuerpo lleva todo bajo `whatsapp_webhook`. El `secret_key` **viene en la respuesta de creación y
no se puede volver a leer**: si se pierde o se filtra, hay que borrar el webhook y crear otro, que es
justo lo que se hizo la primera vez.

## Lo que falta confirmar, declarado

1. **La entrega de punta a punta**, que depende de que exista una sesión de sandbox activa. Lo demás
   ya está medido contra el servicio real: la firma pasa, el veredicto se compone, y el envío llega
   hasta Kapso —que contesta `403 Active sandbox session required to send messages` cuando el
   destinatario no está registrado—.
2. **La tarifa exacta de Meta para Chile.** El rango de $15 a $22 es de prensa, no de la rate card.
