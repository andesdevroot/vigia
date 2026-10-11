# 07 — Handoff

## Estado actual

**Construido y funcionando.** Un ciudadano reenvía un mensaje por WhatsApp y recibe, en un segundo,
un veredicto sobre su enlace. Probado con un teléfono real y medido contra 45 estafas del CSIRT.

| | |
|---|---|
| Tarea en curso | **`T4.1` — cosechar 300+ alertas del CSIRT**, y después la opción A (índice de IoC). El análisis de la brecha está en `doc/14-GAP.md` |
| Después | `T4.2` índice de IoC · `T4.3` control invertido · `T4.4` extractor de la petición + regla |
| Medido | **45 estafas reales del CSIRT**: `nombra` **39 (87 %)**, `GRAVE` **0**, y el insumo se cae en el 98 % si solo se reenvía la cita. Ver `doc/12-MEDICION.md` |
| Pregunta del motor | **«¿este enlace es el sitio de la institución que el mensaje dice ser?»** (`COINCIDE` / `NO_COINCIDE`), con `OFICIAL` / `AJENO` de respaldo |
| Catálogo | **25 instituciones**: 14 estatales y 11 suplantadas, todas verificadas por certificado |
| Funcionando | **Probado de punta a punta el 2026-10-10 17:17**: un teléfono real mandó el phishing y recibió el veredicto en **1 segundo** |
| Código | `marcas` · `firma` · `entrante` · `motor` · `conversacion` · `servidor` (+ `suplantacion`) |
| Datos | `corpus/alertas_csirt.json` (45) · `corpus/prueba_t31.json` (3 mensajes de prueba) · `scripts/` |
| Tests | **109 verdes, 1 de integración**, sin red, en menos de un segundo |
| Gate | **`./gate.sh`** en verde |
| Árbol git | limpio, y `.env` fuera del control de versiones |

## Último commit

`[T3.1]` El protocolo del experimento y un contador que no puede filtrar.

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
| 2026-10-10 | **La brecha son tres y la grande no es la que parecía** (`doc/14-GAP.md`). Medido: **1 de cada 4 chilenos cayó** en smishing, **+30 % en un año**. La brecha 1 —el enlace está y no sabemos de quién dice ser— es 6 de 45 y se cierra con catálogo. **La brecha 2 es que buena parte del fraude no trae enlace, y ahí el motor no dice nada.** Y la brecha 3: hay **785 informes de IoC del Estado** sin usar |
| 2026-10-10 | **El LLM extrae; la regla decide.** La opción descartada es la que ya existe —un LLM que dictamina si es fraude, como WhatsPhish, el chatbot colombiano y ScanMessage—: no es auditable, no puede decir «no sé», y **es peor que lo que ya tenemos**. La que se adopta: el modelo llena un formulario de campos cerrados —`dice_ser`, `pide`, `urgencia`— y decide **una regla escrita y citable**: **«ninguna institución pide su clave ni sus datos por mensaje»** |
| 2026-10-10 | **La privacidad se rompe si el texto va a un LLM externo, y hay que declararlo.** La promesa es «el mensaje no se guarda»; transmitirlo a un tercero no es lo mismo. Hay que elegir antes de construir: decirlo en la bienvenida, correr un modelo local, o exigir no-retención al proveedor |
| 2026-10-10 | **La medición del modelo no se hace por gusto, se hace midiendo.** JEV no tiene **ni una** medición en este proyecto. Elegir un modelo por preferencia sería el error que este proyecto evita en todo lo demás: se mide DeepSeek y JEV contra el corpus y gana el que acierte |
| 2026-10-10 | **`T3.1` se pausa: no hay 20 personas.** El protocolo y el contador quedan escritos y probados. Se reemplaza por el **control invertido** (`T4.3`): cada mensaje del corpus con el enlace de la institución **real**, que aísla la variable y da el denominador que faltaba |
| 2026-10-10 | **La pregunta del producto está mal planteada, y lo dijo el corpus.** El motor contesta «¿el enlace es del Estado?», pero **el 47 % de lo suplantado en 45 alertas reales es Banco Ripley**, un banco privado. A esa persona «NO es del Estado» le dice algo cierto y le deja la duda intacta. La pregunta que el corpus pide es **«¿este enlace es el sitio de la institución que el mensaje dice ser?»** |
| 2026-10-10 | **La pregunta del motor pasó a «¿este enlace es el sitio de la institución que el mensaje dice ser?»** (`T1.9`). Dos veredictos nuevos —`COINCIDE` y `NO_COINCIDE`— y los dos viejos como respaldo. **Y la medición no cambió ni un número: `nombra` sigue en 0**, porque el catálogo no tiene a los suplantados. **Cambiar la pregunta era necesario y no es suficiente**: sin `T1.8`, el motor no puede decir «el mensaje dice ser de Banco Ripley» porque no sabe quién es |
| 2026-10-10 | **Enlazar a alguien no es decir ser él.** La URL contaba como reclamo: `Banco Ripley le informa: ingrese a claveunica.gob.cl` reclamaba ClaveÚnica por enlazarla, y el veredicto daba `COINCIDE` — escondiendo la incoherencia que el motor existe para encontrar. **El reclamo se busca en el texto con los enlaces borrados** |
| 2026-10-10 | **El motor nombra la marca imitada en 0 de 45 casos.** No es un fallo del detector: es que el catálogo solo tiene instituciones estatales bajo `.gob.cl`, y lo que se suplanta son bancos. Medido: Banco Ripley 21 veces, BancoEstado 16, Copec, Santander y Soprole una cada uno |
| 2026-10-10 | **La medición no puede ser tautológica, y hay que decirlo.** Agregarle al mensaje la URL que el informe declara maliciosa garantiza que el veredicto sea `AJENO`: eso confirma la regla y **no mide ningún acierto**. El único número que vale de esa columna es **`GRAVE = 0`**: en 45 estafas reales el motor nunca dio por bueno el enlace malo |
| 2026-10-10 | **El insumo del CSIRT es un fragmento, no el mensaje.** En **44 de 45** citas el enlace no está dentro del texto citado. Si alguien reenviara exactamente lo publicado por el Estado, no le serviríamos en el 98 % de los casos. La medición dice más sobre el insumo que sobre el motor |
| 2026-10-10 | **Leer la composición de un corpus antes de recorrerlo.** De los 785 informes del repositorio del CSIRT, **499 no citan ningún mensaje**. Recorrerlos primero costó **cuarenta consultas para cero ejemplos**. Los 259 de phishing son los que sirven |
| 2026-10-10 | **El servidor corría el motor SIN catálogo, y ningún test lo veía.** `atender` y `construir_servidor` traían la lista vacía por defecto y `main` no pasaba ninguna, así que en producción un mensaje legítimo del SERNAC se leía como ajeno. Los 90 tests estaban verdes porque **todos pasaban el catálogo a mano**: un test unitario no dice nada sobre con qué argumentos se llama a la función en producción. Se descubrió **comparando la respuesta que llegó a un teléfono real con la que daba el mismo texto en local** |
| 2026-10-10 | **Probado de punta a punta, con un teléfono real.** 2026-10-10 17:17: un mensaje de phishing entrante y el veredicto saliente **un segundo después**, ambos `delivered`. Cierra la pregunta de `doc/08-CANAL.md`: el canal funciona sin instalar nada. **No dice nada sobre si el veredicto es correcto en general** — eso es calibración, y sigue pendiente |
| 2026-10-10 | **Para comparar hay que tener las dos salidas.** El bug del catálogo no salió de leer el código ni de correr los tests: salió de **poner la respuesta que llegó al teléfono al lado de la que daba el mismo texto en local** y ver que no coincidían |
| 2026-10-10 | **El webhook se crea por proyecto, no por número.** `POST /platform/v1/whatsapp/phone_numbers/{id}/webhooks` devuelve `400 Secret key can't be blank` —por número hay que aportar el secreto—, mientras que `POST /platform/v1/whatsapp/webhooks` con `phone_number_id` en el cuerpo devuelve `201` y **el `secret_key` en la respuesta, una sola vez**. Se midió, no se dedujo |
| 2026-10-10 | **El número que hay conectado es el Sandbox**, que Kapso crea solo y admite **un único destinatario**: el número que se registre como sesión de prueba. Sirve para probar sin comprar nada y **sin ceder el teléfono personal** —registrarlo ahí es ser remitente autorizado, no dueño del número— |
| 2026-10-10 | **Un fallo al responder dejaba menos rastro que un mensaje sin nada que responder.** El manejador se tragaba la excepción y contestaba 200 igual, así que el `403` del sandbox no dejó rastro en el primer intento. Ahora **se registra el motivo** —el código HTTP o el tipo de excepción, nunca el contenido ni el destinatario— y la respuesta pública sigue siendo mínima |
| 2026-10-10 | **El `secret_key` que se imprime, se rota.** El primer webhook se creó con un comando que mostró el secreto en la salida; se borró el webhook y se creó otro, de modo que el expuesto quedara inservible. **Un secreto que se ve una vez y se filtra no se protege: se reemplaza** |
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
