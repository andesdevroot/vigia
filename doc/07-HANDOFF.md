# 07 — Handoff

## Estado actual

**T0 — validación de la hipótesis.** Nada construido salvo el esqueleto, y es a propósito: `[T0.2]`
decide si el proyecto existe.

| | |
|---|---|
| Tarea en curso | **Prueba real por WhatsApp.** Todo el código está; falta conectar el número y las credenciales |
| Bloqueada aparte | **T0.7**: falta una clave de urlscan.io (gratis) · **T0.8**: qué expone la API de ANCI |
| Falta confirmar | Un envío real por la API de Kapso, y el `secret_key` del webhook (lo da Kapso una sola vez) |
| Código | `marcas` · `firma` · `entrante` · `motor` · `conversacion` · `servidor` (+ `suplantacion`) |
| Tests | **90 verdes, 1 de integración**, sin red, en menos de un segundo |
| Gate | **`./gate.sh`** en verde |
| Árbol git | limpio |

## Último commit

`[T1.4b]` El webhook que contesta por WhatsApp.

## Blockers

**La hipótesis original está refutada por medición.** El canal de Certificate Transparency no
sostiene el proyecto: 2–3 dominios de 1.521. La vía muerta es **buscar la marca en el nombre del
dominio**; el phishing pone la marca en el **contenido**.

**De acceso, no técnico.** La lista de inscripciones de ANCI no se publica; se pide por Ley de
Transparencia. Y el resto quedó cerrado: la tesis chilena se leyó (T0.4) y **deja el espacio abierto**: es un sistema de captura
física con Random Forest, sin corpus público, sin ClaveÚnica, sin lista blanca y sin calibración. Se
posiciona como precursora. Ver `doc/03-ESTADO-DEL-ARTE.md`.

## Decisiones recientes

| Fecha | Decisión |
|---|---|
| 2026-10-10 | **Un número local por Kapso cuesta USD 400 al mes, así que no es el camino.** «Provide local numbers» es un add-on de Pro o superior y **no existe en el plan gratis**; «Instant setup» da un número de EE.UU. gratis y ya verificado, y «Bring your own SIM» conecta un +56 propio con un chip prepago. **La consecuencia práctica: probar no requiere comprar nada, ni tocar el teléfono personal de nadie** —se le escribe al robot desde el WhatsApp propio—. El +56 es una condición para salir a la calle, no para probar |
| 2026-10-10 | **El catálogo es el único dato que amplía el camino permisivo, así que se verifica abriendo el sitio.** 14 instituciones, cada una con su certificado leído y su evidencia fechada en `doc/11-MARCAS.md`. **Cuatro de catorce entradas de un borrador escrito de memoria estaban mal** — `servel.gob.cl` no existe, `fonasa.cl` es un redirector, `sii.gob.cl` manda a `homer.sii.cl`, `codelco.cl` a `codelco.com`. Un test marcado `integracion` vuelve a medir la lista entera: es el único dato del proyecto que empeora solo con el tiempo |
| 2026-10-10 | **Un dominio que no se pudo verificar no se adivina.** BancoEstado, Banco de Chile, Registro Civil, MINSAL y JUNAEB quedaron fuera porque su DNS no resuelve desde esta máquina. **Consecuencia declarada:** hoy un mensaje legítimo de BancoEstado se leería como ajeno, que es el error que el catálogo existe para evitar |
| 2026-10-10 | **El umbral de edición escala con el largo de la marca.** Era el defecto que midió `T0.2` y volvió a aparecer al enchufar el catálogo: **`bit.ly` entraba como suplantación del SII**. Tres letras toleran una errata; seis, dos |
| 2026-10-10 | **Un enlace conocido no se acusa, ni siquiera en un mensaje que sí es falso.** En un mensaje mezclado —uno real de adorno, uno falso para apretar— la respuesta dice «`sernac.cl` es de SERNAC» y «`bit.ly` NO es del Estado». Acusar al real sería falso y confuso a la vez |
| 2026-10-10 | **El webhook nunca contesta 500 y nunca procesa un mensaje saliente.** Lo primero porque un 500 hace que Kapso reintente lo que no supimos leer; lo segundo porque contestarle a nuestra propia respuesta generaría respuestas infinitas, pagando cada una. Los dos tienen test |
| 2026-10-10 | **La firma se verifica sobre los bytes crudos.** Parsear y re-serializar cambia el espaciado y rompe el HMAC; el arreglo natural —aflojar la comparación— es el que abre la puerta. La comparación es de tiempo constante, y el largo se comprueba antes |
| 2026-10-10 | **El servidor no guarda ni registra el mensaje, y no sigue redirecciones.** `urlopen` sigue las redirecciones por defecto y **reenvía las cabeceras**, incluida la clave de API, al host de destino: bastaría un 302 para llevársela |
| 2026-10-10 | **El canal sobrevive al costo: unas $19 por verificación.** Desde el 1 de octubre de 2026 Meta cobra los mensajes de servicio de WhatsApp Business Platform —**1.000 gratis por número al mes** y después $15 a $22 ([T13](https://www.t13.cl/noticia/tendencias/whatsapp-cobrara-entre-15-22-por-mensaje-quienes-se-les-aplicara-medida-2-10-2026))—. Se cobra **nuestra respuesta**, no el reenvío. 1.000 verificaciones al mes: **$0**. 10.000: ~$190.000. **T1.2 cerrada sin blocker** |
| 2026-10-10 | **La interfaz es Kapso** ([kapso.com](https://kapso.com/)), Meta Business Partner: número, webhooks entrantes y respuestas, con las tarifas de Meta a costo y sin margen. Plan gratis de 2.000 mensajes/mes. **Kapso pone la boca; el veredicto sigue siendo nuestro** — y como el motor es stdlib pura y cero dependencias, se muda a cualquier host sin tocar una línea |
| 2026-10-10 | **El número tiene que ser +56.** El plan gratis de Kapso trae un número de EE.UU., pero «Bring your own SIM» permite conectar un chileno propio: chip nuevo, verificado por SMS, nunca registrado antes en WhatsApp. **Una herramienta chilena antiestafa con número gringo es ella misma sospechosa** |
| 2026-10-10 | **El mensaje reenviado no se guarda.** Al reenviar, el ciudadano entrega su número y a veces datos de terceros. Se procesa, se responde y se olvida; si se guarda algo para medir, es el veredicto y el dominio, nunca el texto ni el número. La promesa «el robot no lee tus chats» se sostiene sola; la de «no guardamos lo que nos mandas» hay que cumplirla |
| 2026-10-10 | **El motor contesta sobre el enlace, nunca sobre el mensaje.** Tres veredictos: `OFICIAL` (todos los enlaces son `.gob.cl`), `AJENO` (alguno no lo es) y `SIN_ENLACES` (no hay qué revisar). **Un enlace bueno no lava a uno malo**, y hay un test que lo fija con varios textos: si bastara uno del Estado, el motor premiaría el ataque mejor construido. **No existe la palabra «seguro» en la respuesta, y hay un test que la prohíbe.** Ver `task.md` `[T1.1]` |
| 2026-10-10 | **La primera versión no depende de un corpus.** La regla «¿termina en `.gob.cl`?» es completa por política de registro (`T0.5`), así que el motor arranca sin el insumo que mató al proyecto anterior. El catálogo de marcas chilenas queda como tarea aparte: sin él se sabe igual si el enlace es del Estado, solo se pierde el nombre de la marca imitada |
| 2026-10-10 | **El canal es el mensaje, no el navegador.** Chrome de Android no acepta extensiones y el fraude de ClaveÚnica llega por SMS y WhatsApp al teléfono: la extensión solo cubriría escritorio, donde el ataque no ocurre. **La forma principal es reenviar el mensaje a un número** (0 instalaciones, 1 gesto); la app de trámites queda como alternativa y la extensión como accesorio. **El detector no cambia: cambia la boca.** Ver `doc/08-CANAL.md` |
| 2026-10-10 | **El Estado cubre el después, no el antes.** CiberLupa dice si tus datos **ya** se filtraron; Reporte Ciudadano sirve para denunciar **después**; el 1510 tiene humano. **Nadie contesta «¿aprieto este link?».** Queda como tarea `T0.8` averiguar qué expone la API pública de ANCI: si da alertas, el proyecto se construye **encima del Estado** |
| 2026-10-04 | **T0.7 bloqueada, y se declara en vez de rodearse.** Medir el mal uso de la barra necesita un índice de subrecursos; urlscan lo tiene pero su API pide clave, y Common Crawl no registra subrecursos. **No se inventó un número** |
| 2026-10-04 | **La barra azul no verifica nada.** `access-control-allow-origin: *` y cero ataduras al dominio: es una imagen que cualquiera copia. El dominio `.gob.cl` sí es sólido. **El ancla está bien puesta y el letrero está suelto** |
| 2026-10-04 | **Un título no es una fuente.** Cuatro veces se concluyó desde el título o la memoria y las cuatro la conclusión cambió al abrir la fuente. La regla quedó en `00-METODOLOGIA.md`, con la tabla de los cuatro casos |
| 2026-10-04 | **`.gob.cl` es un ancla de confianza completa por política de registro.** No hace falta una lista: solo el Estado puede inscribir bajo `gob.cl`. Y la **ANCI ya declaró la teoría** de la identificabilidad — lo que falta es **medir si funciona** |
| 2026-10-04 | **La tesis chilena deja el espacio abierto.** Es captura física + Random Forest; sus limitaciones son de hardware. Se cita como precursora, no como competidora |
| 2026-10-04 | **El espacio no está vacío, y en Chile tampoco.** Hay una tesis de la U. de Chile sobre mensajes fraudulentos, y la lista blanca ya está publicada (APWG). Lo que queda limpio es la **calibración por segmento** |
| 2026-10-04 | **El canal CT queda cerrado.** No por un defecto del detector —hay dos, y son corregibles— sino porque la suplantación no vive en el nombre del dominio. Ver `doc/02-MEDICION-CT.md` |
| 2026-10-04 | **El detector no se borra, se deja de usar.** La taxonomía es correcta y los dos defectos quedan documentados |
| 2026-10-04 | **El proyecto arranca con un spike, no con arquitectura.** El proyecto anterior murió por no validar el insumo antes de construir; acá la primera tarea es un número |
| 2026-10-04 | **Cero dependencias en T0.1**, y hay un test que lo fija: agregar una es una decisión, no un accidente |
| 2026-10-04 | **`import vigia` no arrastra red.** Descubrimiento y consulta son cosas distintas, y mezclarlas obliga a tener internet para correr un test unitario |
