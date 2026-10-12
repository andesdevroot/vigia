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

## Lo que sigue faltando

**`T5.5`: saber si está vivo de verdad.** El chequeo de salud dice que el proceso responde, no que los
mensajes estén llegando. Un contador de veredictos en el tiempo es lo que cierra eso.

**Y el número tiene que ser +56.** El sandbox da uno de EE.UU. «Bring your own SIM» permite conectar
un chip chileno. Una herramienta chilena antiestafa con número gringo es ella misma sospechosa.
