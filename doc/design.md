# design.md — el diseño, vivo

**Última actualización: 2026-10-10.** Este documento se actualiza en **cada iteración**: es la vista
de una sola página de qué estamos construyendo y por qué. El detalle vive en los otros documentos de
`doc/`, y acá se enlazan.

> Los otros documentos están numerados por orden de escritura. Este no, porque es el que se relee.

---

## 1. Qué es

**Un verificador ciudadano de mensajes, por WhatsApp.** La persona reenvía el mensaje sospechoso a un
número y recibe, en un segundo, un veredicto sobre su **enlace**: si es el sitio de la institución
que el mensaje dice ser, o no lo es.

No es un antivirus, no es un navegador y no hay nada que instalar.

## 2. La pregunta que contesta el motor

> **«¿Este enlace es el sitio de la institución que el mensaje dice ser?»**

No es la pregunta con la que empezamos. Empezamos con «¿el enlace es del Estado?», y **la cambió el
corpus** (ver §6): en 45 estafas reales del CSIRT, **el 47 % suplanta a Banco Ripley**, un banco
privado. A esa persona, «el enlace NO es del Estado» le dice algo cierto y **le deja la duda
intacta**.

### Los cinco veredictos

| Veredicto | Qué afirma |
|---|---|
| `COINCIDE` | el mensaje dice ser de X y el enlace es de X |
| `NO_COINCIDE` | el mensaje dice ser de X y el enlace **no** es de X |
| `OFICIAL` | el enlace es del Estado y no se reconoce a nadie en el texto |
| `AJENO` | el enlace no es de nadie conocido |
| `SIN_ENLACES` | no hay enlace que revisar |

## 3. Arquitectura

```
  WhatsApp  ──reenvío──▶  Kapso  ──webhook firmado──▶  servidor
                                                          │
                              ┌───────────────────────────┘
                              ▼
                        firma.py        ¿lo mandó Kapso? HMAC sobre los bytes crudos
                              ▼
                        entrante.py     el sobre → {texto, destinatario, ¿adjunto?}
                              ▼
                        motor.py        ┌ extraer enlaces
                                        ├ comparar con el catálogo (marcas.py)
                                        └ de quién DICE ser  ×  de quién ES el enlace
                              ▼
                        conversacion.py la respuesta en castellano
                              ▼
                        servidor.py     ──▶ Kapso ──▶ WhatsApp
```

| Pieza | Rol | ¿Red? |
|---|---|---|
| `firma.py` | verifica el HMAC del webhook | no |
| `entrante.py` | lee el sobre de Kapso | no |
| `motor.py` | **el veredicto** | no |
| `marcas.py` | el catálogo de instituciones y sus dominios | no |
| `suplantacion.py` | detector de marcas parecidas | no |
| `conversacion.py` | lo que se contesta | no |
| `servidor.py` | HTTP y envío | **sí, y es el único** |

**Todo menos el servidor se prueba sin red**, en menos de un segundo. No es una casualidad: es lo
que permite medir el motor contra un corpus sin levantar nada.

## 4. Los invariantes

Lo que **no** se puede romper, cada uno con su test:

1. **Un enlace malo no se lava con uno bueno.** Basta un enlace que no corresponda para romper la
   coincidencia. Si bastara uno legítimo, el motor premiaría el ataque mejor construido.
2. **Nunca se dice «seguro».** Hay un test que lo prohíbe sobre **todos** los veredictos. Un enlace
   legítimo dentro de un mensaje falso existe.
3. **Enlazar a alguien no es decir ser él.** El reclamo se busca en el texto **con los enlaces
   borrados**, o la URL infla la lista y esconde la incoherencia.
4. **El webhook nunca contesta 500 y nunca procesa un mensaje saliente.** Lo primero evita
   reintentos inútiles; lo segundo evita un bucle que se paga solo.
5. **El mensaje no se guarda.** Ni a disco ni en el registro.
6. **La firma se verifica sobre los bytes crudos**, con comparación de tiempo constante.
7. **El catálogo se verifica abriendo el sitio.** Es el único dato que amplía el camino permisivo, y
   el único que empeora solo con el tiempo.

## 5. Dónde vive la inteligencia, y dónde no

**El veredicto no usa ningún modelo.** Es determinista, y ahí está su valor: se puede auditar, se
puede reproducir y no alucina.

Eso **no** significa renunciar a la IA. Significa ponerla donde no pueda romper la auditabilidad:

| Dónde | ¿IA? | Por qué |
|---|---|---|
| Decidir si un enlace es oficial | **No** | Es una comparación contra un catálogo verificado |
| Extraer **de quién dice ser** el mensaje | **Sí, es el lugar natural** | El corpus escribe «Banco Ripley», «bancoripley» y «banco de estado» para lo mismo |
| Leer una **captura de pantalla** | **Sí** | Hoy el motor no lee imágenes, y la gente manda capturas |
| Mensajes **sin enlace** | **Sí, con cuidado** | Es donde el veredicto hoy se queda mudo |
| El veredicto | **Nunca** | Un modelo en el veredicto destruye lo único que hace confiable a esto |

La regla: **la IA propone, el determinismo decide.** Es la misma tesis de la capa calibrada del
proyecto anterior, aplicada a otro dominio.

## 6. Estado del arte: qué existe y qué no

Verificado a fondo en `doc/03-ESTADO-DEL-ARTE.md`, `doc/12-MEDICION.md` y esta iteración.

**Existe, y conviene decirlo antes de reclamar novedad:**

| Qué | Dónde |
|---|---|
| Chatbot con IA que detecta phishing en WhatsApp | [WhatsPhish (ASEE)](https://peer.asee.org/whatsphish-whatsapp-ai-phishing-detector-chatbot.pdf) |
| Chatbot que identifica estafas y malware en WhatsApp | [Rev. Ingeniería e Innovación, Colombia](https://revistas.unicordoba.edu.co/index.php/rii/article/view/4356) |
| Detección de fraude por IA para WhatsApp y SMS en LatAm | [ScanMessage](https://www.indiehackers.com/post/scanmessage-ai-fraud-detection-for-whatsapp-sms-in-latin-america-f9e1f1adb3) |
| Recolector y clasificador de SMS fraudulentos chilenos | Tesis U. de Chile, 2024 (`doc/03`) |
| Verificación de filtraciones para usuarios chilenos | CiberLupa, ANCI (`doc/04`) |
| Extensiones genéricas anti-phishing | Sentinel, WatchPost |

> **«Una IA que detecta estafas por WhatsApp» NO es novedoso.** Hay al menos dos papers y una
> startup. Cualquier paper que reclame eso, se cae en la revisión.

**Lo que sí queda limpio, y es defendible:**

1. **El ancla es nacional y estructural, no estadística.** `gob.cl` es un segundo nivel de registro
   **exclusivo del Estado**: para certificar que un sitio es estatal no hace falta modelo ni lista,
   basta preguntar si termina en `.gob.cl`. Es una propiedad de la política de registro de Chile, y
   ningún detector probabilístico puede igualarla en ese caso.
2. **La abstención es explícita y está medida.** Todos los sistemas revisados devuelven un puntaje;
   ninguno tiene un veredicto que diga **«no puedo verificar esto»**. Nosotros sí, y medimos cuántas
   estafas reales caen ahí: **44 de 45** si solo se reenvía lo que el Estado publicó.
3. **La coherencia reclamo ↔ enlace.** No «¿es malicioso?» sino «¿es de quien dice ser?». Nadie
   revisado compara las dos cosas.
4. **Mediciones negativas publicadas**, que es lo que casi nadie publica: el canal de Certificate
   Transparency **no tiene volumen** (2–3 de 1.521 dominios), la barra azul del Estado **no verifica
   nada** (`access-control-allow-origin: *` y cero ataduras al dominio), y el propio CSIRT **cita un
   fragmento** sin el enlace en 44 de 45 alertas.

**La frase para el paper:** la contribución no es un detector, es **una capa de verificación
determinista y auditable, anclada en una política de registro nacional, que se abstiene en vez de
adivinar — y la medición de cuánto se abstiene.**

## 7. Lo que está construido

| | Estado |
|---|---|
| El motor y sus cinco veredictos | ✅ 95 tests |
| El webhook y la respuesta por WhatsApp | ✅ **probado con un teléfono real, 1 segundo** |
| El catálogo | ✅ **25 instituciones**: 14 estatales y 11 suplantadas, verificadas por certificado |
| El corpus y la medición | ✅ **45 estafas reales del CSIRT**, y **`nombra` en 39 (87 %)** |
| Costo | ✅ **≈$19 por verificación; las primeras 1.000 del mes, gratis** |

## 8. Lo que falta

| # | Qué | Por qué importa |
|---|---|---|
| `T1.8` | **Extender el catálogo a lo suplantado** | Sin esto el motor no sabe quién es Banco Ripley, y `NO_COINCIDE` es inalcanzable: la medición lo dice con un **0 de 45** |
| `T1.5` | Guardián de privacidad | La regla se cumple; nada impide que se rompa mañana |
| `T0.7` | Medir el mal uso de la barra azul | Falta una clave de urlscan.io |
| `T0.8` | Qué expone la API pública de la ANCI | Si da alertas, nos apoyamos en el Estado en vez de reconstruirlo |
| `T2.1` | El paper | Ver §9 |

## 9. Riesgos abiertos, sin adornos

1. **El insumo se cae si el ciudadano no reenvía el enlace.** En 44 de 45 alertas del CSIRT el
   enlace no está en el texto publicado. Si en la vida real pasa lo mismo, el motor se queda mudo.
   **Es el riesgo número uno y no está medido todavía.**
2. **No hay corpus de mensajes legítimos.** El `0` de falsas acusaciones no está medido: no hay
   denominador. Sin eso, la precisión no se puede afirmar.
3. **`bancoestado.cl`, `santander.cl` y `scotiabank.cl` no se pudieron verificar** desde esta red:
   son el 36 % del corpus y la mitad más valiosa. No se adivinan.
4. **La adopción.** Que el bot funcione no es que alguien lo use. El número +56 es condición para
   salir a la calle, y un chip prepago es el camino.
5. **El sandbox no es producción.** Lo probado es el camino, no la escala.

## 10. Bitácora de iteraciones

| Fecha | Qué cambió en el diseño |
|---|---|
| 2026-10-10 | **`T3.1` armado: tres mensajes de prueba con tres formas de enlace distintas** (acortador, dominio con ruta, empresa del Estado), y **el armado encontró un bug en la frase que más importa**: decía «dice ser de Banco Ripley, Ripley», porque «Ripley» es nombre propio y además alias de «Banco Ripley». Ahora se nombra una sola vez |
| 2026-10-10 | **`T3.1`: el experimento que decide el paper, y un contador que no puede filtrar.** El «98 % mudo» de `T1.7` **es del formato del CSIRT y no de la gente**, así que hay que medirlo con personas: 20 × 3 mensajes reales con el host saneado a `.example`, sin decir la palabra enlace. Y el instrumento (`medicion.py`) escribe **agregados de tres etiquetas**: no tiene dónde guardar el contenido |
| 2026-10-10 | **`T1.8b`: entran BancoEstado, Santander y Scotiabank, y `nombra` llega a 39 de 45 (87 %)**. Estaban declarados imposibles de verificar por DNS; **el blocker no era el sitio sino la sonda**: la raíz de los tres no tiene registro A, solo `www.`, y el DNS local se rodea con `dns.google` y con los certificados emitidos de `crt.sh` |
| 2026-10-10 | **`T1.8`: el catálogo creció a 22 instituciones**, y `nombra` pasó de **0 a 24 de 45 (53 %)**. La medición destapó además un bug: `.../SantaIsabelws/tb.php` contaba `tb.php` como dominio propio — una acusación sobre un dato inventado. **Lo encontró el corpus, no un test unitario** |
| 2026-10-10 | **Nace este documento.** Se fija la arquitectura de siete piezas, los siete invariantes, y la regla «la IA propone, el determinismo decide» |
| 2026-10-10 | **La pregunta cambió** de «¿es del Estado?» a «¿es el sitio de quien dice ser?» (`T1.9`), y la medición mostró que **sin catálogo no cambia nada** |
| 2026-10-10 | **Se midió contra 45 estafas reales del CSIRT**: 0 graves, 0 reconocimientos, 47 % Banco Ripley |
| 2026-10-10 | **Probado de punta a punta con un teléfono real**, en 1 segundo |
