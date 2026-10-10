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

## Enganchar Kapso

1. **Conectar el número.** `kapso setup`, o «Bring your own SIM» con un chip chileno nuevo, nunca
   registrado antes en WhatsApp. El número tiene que ser **+56**: una herramienta chilena antiestafa
   con número de Estados Unidos es ella misma sospechosa.
2. **Exponer el servidor.** Para probar desde tu casa alcanza un túnel (`cloudflared`, `ngrok`) que
   apunte al puerto 8000.
3. **Crear el webhook**, contra el número:
   ```bash
   node scripts/create.js \
     --phone-number-id <PHONE_NUMBER_ID> \
     --url https://<tu-host>/webhook \
     --events whatsapp.message.received \
     --payload-version v2
   ```
4. **Guardar el `secret_key`.** Kapso lo muestra **una sola vez**, y es `VIGIA_WEBHOOK_SECRET`.
5. **Escribirle al número** y ver la respuesta.

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

## Lo que falta confirmar, declarado

1. **Un envío real.** La ruta de envío
   (`/meta/whatsapp/v24.0/{phone_number_id}/messages`) sale de la referencia oficial de Kapso y hay
   un test que la fija, pero **no se ha mandado nada todavía**. Se confirma con el primer mensaje.
2. **El `secret_key`.** Es una gestión: lo da Kapso al crear el webhook y se muestra una sola vez.
3. **La tarifa exacta de Meta para Chile.** El rango de $15 a $22 es de prensa, no de la rate card.
