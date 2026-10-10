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

## El número chileno: sí se puede

«Bring your own SIM»: se conecta un número propio, verificado por SMS o llamada.

- Tiene que ser un número **dedicado**: no puede seguir activo en la app de WhatsApp.
- Chip nuevo, **nunca registrado en WhatsApp**. «El número ya está vinculado» es el fallo típico.
- El plan gratis trae un número de **EE.UU.** pre-verificado, pero permite **1 número conectado**, y
  con eso alcanza para conectar un +56 propio.

**Y esto no es un detalle:** una herramienta chilena contra la estafa, con número de Estados Unidos,
es ella misma sospechosa. El número tiene que ser **+56**.

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
