# 17 — Desplegar: sacar el robot del notebook

**2026-10-12.** El bloqueo que impedía que alguien más lo usara.

## El problema que resuelve

Hasta ahora el servidor corría así:

```bash
bash scripts/probar_local.sh     # levanta ngrok, registra el webhook, arranca el servidor
```

**Y eso tiene tres fallas que ninguna prueba local muestra:**

| | |
|---|---|
| **Si se cierra el notebook, el servicio muere** | No hay nadie que lo reinicie |
| **La URL del webhook cambia en cada arranque** | Hay que volver a registrarlo, y si se olvida, los mensajes se pierden **sin ningún error visible** |
| **No hay forma de saber si está vivo** | Un servicio caído se ve igual que nadie usándolo |

> **Un número que no contesta destruye más confianza que no tener número.**

## Qué se agregó

| | |
|---|---|
| **`Dockerfile`** | La imagen. **No instala nada**, y hay un test que lo impone |
| **`GET /`** | Chequeo de salud. Sin firma —la plataforma no puede firmar— y sin revelar nada de adentro |
| **`src/vigia/salud.py`** | El chequeo desde adentro del contenedor, en stdlib para no meter `curl` |
| **`tesseract-ocr`** | El OCR de las capturas, **adentro del contenedor** |
| **`puerto_del_entorno()`** | `PORT` primero, que es la convención de las plataformas |

**Lo que NO cambió:** el motor, los tests, ni una línea del núcleo de decisión.

## Las tres variables de entorno

| Variable | Para qué |
|---|---|
| `KAPSO_API_KEY` | Mandar las respuestas |
| `VIGIA_WEBHOOK_SECRET` | Verificar la firma de los mensajes entrantes |
| `DEEPSEEK_API_KEY` | El extractor. **Sin ella el robot igual funciona**: se degrada al comportamiento anterior |

Opcionales: `VIGIA_MAXIMO` y `VIGIA_VENTANA_S` (el límite por persona), `DEEPSEEK_BASE_URL`,
`DEEPSEEK_MODELO`, `KAPSO_API_BASE_URL`.

**Los secretos van por variables de entorno, nunca por `COPY`.** Un `.env` copiado a una imagen queda
en sus capas para siempre, y las capas se publican.

## Dónde desplegarlo

El servidor es **Python puro sin dependencias**, así que cabe en el plan más chico de cualquier
plataforma. Los tres candidatos, con lo que importa de cada uno:

| | Costo | Por qué |
|---|---|---|
| **[Fly.io](https://fly.io)** | ~2–5 USD/mes | La imagen corre tal cual. Máquina chica siempre encendida, dominio `*.fly.dev` con TLS |
| **[Render](https://render.com)** | Gratis con suspensión | El plan gratis **duerme** el servicio: el primer mensaje tras dormir tarda ~30 s. Sirve para probar, **no para un número público** |
| **[Railway](https://railway.app)** | ~5 USD/mes | El más simple de los tres. Buen panel y registros |

**Para un número que la gente va a usar de verdad, hace falta una máquina que no duerma.** El plan
gratis de Render no sirve para eso, y conviene saberlo antes y no después.

### Fly.io, paso a paso

```bash
fly launch --no-deploy          # detecta el Dockerfile solo
fly secrets set KAPSO_API_KEY=... VIGIA_WEBHOOK_SECRET=... DEEPSEEK_API_KEY=...
fly deploy
fly open                        # abre la URL: tiene que decir {"ok": true}
```

**Lo que hay que revisar después del primer deploy:**

```bash
curl https://<tu-app>.fly.dev/          # {"ok": true}
fly logs                                 # sin errores al arrancar
```

Y el `fly.toml` necesita una cosa **explícita**, porque el valor por defecto apaga la máquina cuando
nadie la usa:

```toml
[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false      # <- un número público no puede dormirse
  min_machines_running = 1

[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/"
```

## Y después: apuntar el webhook a la URL fija

**Esta es la parte que cambia respecto de `ngrok`.** Antes había que reescribir la URL en cada
arranque; ahora no:

```bash
python3 scripts/registrar_webhook.py https://<tu-app>.fly.dev
```

**Se corre una vez.** La URL ya no cambia.

Y si algún día hay que apagarlo:

```bash
python3 scripts/registrar_webhook.py --apagar
```

**Conviene recrear el webhook en vez de reusar el que existe.** Su UUID quedó en la historia pública
del repositorio, y aunque no es una credencial, recrearlo es más limpio.

## La única cosa que la imagen instala, y por qué no rompe nada

`Dockerfile` instala **`tesseract-ocr` y `tesseract-ocr-spa`**. Es lo único que se instala, y conviene
entender la distinción:

> **El núcleo de decisión sigue siendo stdlib.** Tesseract es una herramienta de **entrada**, como el
> propio servidor HTTP. Sin él, el robot pide el texto a mano y **todo lo demás funciona igual**.

El test que prohíbe `pip install` sigue pasando, y hay uno nuevo que exige el OCR **con el idioma**:
sin el paquete `-spa`, el OCR de un mensaje chileno inventa palabras.

**Y la captura no sale del contenedor.** Corre local, por la entrada estándar, y nunca toca el disco.

## La CI construye la imagen antes de que la subas

`.github/workflows/gate.yml` tiene un trabajo que hace `docker build`, **levanta el contenedor** y le pide el chequeo de salud. Es el único lugar donde eso se puede probar: no hay docker en la máquina de desarrollo.

**Y comprueba el OCR**, que es lo único que la imagen instala:

```bash
docker run --rm --entrypoint tesseract vigia --version
docker run --rm --entrypoint sh vigia -c 'tesseract --list-langs | grep -q spa'
```

Si algo de eso falla, **te enteras antes de desplegar**, no en el primer `fly deploy`.

## Saber si está vivo, y si contesta

Dos cosas distintas, y la segunda es la que importa.

| | |
|---|---|
| **¿El proceso vive?** | El chequeo de salud (`GET /`). Se le pone un monitor externo gratis —UptimeRobot, BetterStack— que lo llame cada cinco minutos y te avise si deja de contestar |
| **¿Está contestando mensajes?** | `GET /estado` con token. **Esto no lo cubre ningún monitor externo**, porque un servicio caído y uno que nadie usa se ven igual desde afuera |

### El token, y por qué está cerrado por defecto

```bash
fly secrets set VIGIA_ESTADO_TOKEN=$(openssl rand -hex 32)
```

> **Sin `VIGIA_ESTADO_TOKEN` la ruta no existe.** Contesta 404, igual que cualquier otra que no esté. No hay una superficie que uno tenga que acordarse de proteger.

Y con un token equivocado contesta **404, no 401**: un 401 diría «acá hay algo».

### Consultarlo

```bash
curl -H "Authorization: Bearer $VIGIA_ESTADO_TOKEN" https://<tu-app>.fly.dev/estado
```

```json
{
  "llegaron": 47,
  "contestados": 47,
  "sin_contestar": 0,
  "silencio": {"firma_invalida": 0, "limite": 2, "sin_destinatario": 0},
  "veredicto": {"confirmado": 12, "no_coincide": 30, "ajeno": 5},
  "ultimo_mensaje": "2026-10-12T19:40:11",
  "segundos_desde_el_ultimo": 128
}
```

### Los tres números que hay que mirar

| | |
|---|---|
| **`sin_contestar`** | **Si sube, algo se rompió.** Debería ser 0 salvo por el límite |
| **`segundos_desde_el_ultimo`** | Distingue «nadie lo usa» de «el webhook murió». Si es grande y alguien debería estar usándolo, el problema es el webhook |
| **`silencio.firma_invalida`** | **Si sube de golpe, es una alarma**: o cambió el secreto, o alguien está probando. No es un mensaje: es un ataque o una mala configuración |

**Y `veredicto` dice si el motor sigue funcionando.** Si todo sale `sin_enlaces`, el extractor se rompió, y el total no lo mostraría.

## Lo que sigue faltando

**`T5.5`: saber si está vivo de verdad.** El chequeo de salud dice que el proceso responde, no que los
mensajes estén llegando. Un contador de veredictos en el tiempo es lo que cierra eso.

**Y el número tiene que ser +56.** El sandbox da uno de EE.UU. «Bring your own SIM» permite conectar
un chip chileno. Una herramienta chilena antiestafa con número gringo es ella misma sospechosa.
