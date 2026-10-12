# 09 — La interfaz: Kapso

## El veredicto

**Sirve, y es la pieza que faltaba.** Convierte «reenviar a un número» en algo que se arma en días y
no en meses.

## Qué es

La puerta oficial a WhatsApp para desarrolladores: **Meta Business Partner**, 30.000+ desarrolladores.
Sin esto habría que montar a mano el onboarding de Meta, que es la parte aburrida y la que más se
demora.

## El número que decidía el proyecto

Desde el **1 de octubre de 2026**, Meta cobra los mensajes de servicio de WhatsApp Business Platform:

- **1.000 mensajes de servicio gratis al mes, por número.**
- Después, **entre $15 y $22 por mensaje** ([T13, 02-10-2026](https://www.t13.cl/noticia/tendencias/whatsapp-cobrara-entre-15-22-por-mensaje-quienes-se-les-aplicara-medida-2-10-2026)).
- **Solo aplica a la API.** Responder a mano desde el celular sigue siendo gratis.

Lo que se cobra es **nuestra respuesta**, no el reenvío del ciudadano.

## Cuánto cuesta proteger a N personas

| Verificaciones al mes | Meta | Kapso | Total |
|---|---|---|---|
| 1.000 | $0 — dentro de la franja gratis | Free $0 | **$0** |
| 2.000 | ~$18.500 | Free $0 | ~$18.500 |
| 10.000 | ~$166.500 | Pro USD 25 ≈ $24.000 | **~$190.000** |

**Alrededor de $19 por verificación, y las primeras mil del mes salen gratis.** Diez mil consultas
ciudadanas al mes por menos de doscientas lucas.

Kapso pasa las tarifas de Meta **a costo, sin margen**, y su plan gratis incluye 2.000 mensajes al
mes. Con eso el arranque es de costo cero de verdad.

## Qué pone Kapso, y qué no

| Pone | No pone |
|---|---|
| El número y su verificación | **El veredicto** |
| Webhooks de mensajes entrantes | La lista `.gob.cl` |
| Envío de respuestas y plantillas | El motor |
| Inbox, workflows, funciones serverless, MCP y CLI | |

**El motor es nuestro y es Python. Kapso es la boca.** La división es limpia: a Kapso le llega un
mensaje y le devolvemos un texto.

## El número: tres caminos, y el más caro no es el mejor

**Para probar no hace falta nada.** «Instant setup» da un número **gratis, ya verificado, de Estados
Unidos**, sin SIM y sin cuenta de Twilio. Y —esto es lo que hay que decir claro— **el teléfono
personal de quien prueba no se toca**: se le escribe al robot desde el WhatsApp propio, y el número
dedicado es el del robot. Que sea +56 importa para producción, no para probar.

| Camino | País | Costo | Plan |
|---|---|---|---|
| «Instant setup» | **EE.UU.**, por defecto | **$0** | Gratis, ya disponible |
| «Bring your own SIM» | el que sea, **+56 incluido** | un chip prepago | Gratis en adelante |
| «Provide local numbers» | el que sea | **USD 400/mes** de add-on, más Twilio y Telnyx propios | Pro o superior; **no existe en el plan gratis** |

**Requisitos de «Bring your own SIM»**, que es el camino bueno para Chile:

- El número es **dedicado al robot**: no puede seguir activo en la app de WhatsApp.
- Chip **nuevo, nunca registrado en WhatsApp**. «El número ya está vinculado» es el fallo típico.
- El plan gratis permite **1 número conectado**, y con eso alcanza.

**Y esto no es un detalle de prolijidad:** una herramienta chilena contra la estafa, con número de
Estados Unidos, es ella misma sospechosa. Para salir a la calle el número tiene que ser **+56**. Para
probar hoy, no.

## Lo que falta verificar, declarado

1. **La tarifa exacta de Meta para Chile.** El rango de $15 a $22 es de prensa, no de la rate card.
   Se confirma con la primera factura.
2. **El runtime de las «Functions» de Kapso** — la página da 404. Si no corren Python, el motor va a
   un host propio. **Da lo mismo:** el motor es stdlib pura y cero dependencias, así que se muda a
   cualquier parte sin tocar una línea.

## La regla de privacidad, que hay que escribir antes de la primera línea

Al reenviar, el ciudadano nos entrega **su número de teléfono**, y el mensaje reenviado puede traer
datos personales suyos o de terceros.

> **El mensaje no se guarda.** Se procesa, se responde y se olvida.

Si se guarda algo, que sea el veredicto y el dominio — para medir — nunca el texto ni el número. La
promesa «el robot no lee tus chats» se sostiene sola; la de «no guardamos lo que nos mandas» hay que
cumplirla.


## Las capturas y los audios (`T5.2`)

**El caso que iba a pasar el primer día:** la gente manda capturas, no texto. Hasta `T5.2` el robot
contestaba «cópialo a mano», y eso casi nadie lo hace.

### Dos campos del sobre que no estaban usados

| | |
|---|---|
| **`transcript`** | **Kapso ya transcribe los audios.** Viene en el sobre, listo. Los audios funcionan **sin escribir una línea** y sin bajar nada |
| **La URL de la imagen** | Documenta tres ayudas: `media_data`, `media_url`, `message_type_data` |

**Sobre la URL, y es una advertencia:** la documentación pública de Kapso **no fija la forma exacta**,
y sus páginas se renderizan con JavaScript, así que no se puede leer la estructura desde fuera.

Por eso `entrante.py` **busca en siete caminos** (`CLAVES_MEDIA`) y toma el primero que sea `http`.
Es más robusto que apostar a uno solo y descubrirlo en producción.

> **Lo que falta confirmar: un mensaje real con imagen**, para ver el sobre de verdad y dejar el
> camino verdadero primero. Hasta entonces, el parseo defensivo cubre la duda.

### El invariante de privacidad

```
imagen  ->  descarga (tope 8 MB)  ->  OCR LOCAL  ->  texto  ->  motor determinista
```

**La imagen nunca sale del servidor**, nunca toca el disco, y `imagen.py` **no puede importar red** —
hay un test que lo revisa sobre el código fuente.
