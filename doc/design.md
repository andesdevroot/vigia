# design.md — el diseño, vivo

**Última actualización: 2026-10-10.** Este documento se actualiza en **cada iteración**: es la vista
de una sola página de qué estamos construyendo y por qué. El detalle vive en los otros documentos de
`doc/`, y acá se enlazan.

> Los otros documentos están numerados por orden de escritura. Este no, porque es el que se relee.
>
> **Los cuatro documentos del método**, y para qué sirve cada uno:
>
> | | |
> |---|---|
> | **`spec.md`** | **El contrato**: qué tiene que hacer el sistema, requisito por requisito, cada uno con su test. `tests/test_spec.py` lo hace cumplir |
> | **`doc/design.md`** | Este archivo: **cómo** está construido, por qué, y la bitácora |
> | **`task.md`** | La cola: qué falta y en qué estado |
> | `doc/00-METODOLOGIA.md` | El método: SDD, TDD, y qué se actualiza en cada iteración |

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
| `indicadores.py` | **el índice del Estado**: dominios ya publicados como fraudulentos | no |
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
| Buscar el enlace en los indicadores del Estado | **No** | Es una búsqueda en 738 dominios ya publicados |
| Extraer **de quién dice ser** el mensaje | **Sí, es el lugar natural** | El corpus escribe «Banco Ripley», «bancoripley» y «banco de estado» |
| Extraer **qué pide** el mensaje | **Sí, y es el núcleo nuevo** | Medido: el extractor sin modelo **marca 3 de 6 frases legítimas**, y las tres son consejos contra el phishing. Entender la **negación** es lo que se le exige |
| Elegir **qué modelo** | **Sí, y se decide midiendo** | Una sola implementación compatible con OpenAI sirve para DeepSeek y para JEV: enfrentarlos es cambiar dos valores. **Gana el que supere las sondas** |
| Leer una **captura de pantalla** | **Sí, con un límite duro** | De la imagen sale **texto**, y el texto pasa por el motor. Nunca el veredicto |
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
|---|---|---|
| 2026-10-12 | **El estado se expone cerrado por defecto, y la razón es asimétrica.** Sin token configurado la ruta **no existe**: no hay superficie que atacar, en vez de una que hay que recordar proteger. Y con un token equivocado contesta **404 y no 401** — un 401 diría «acá hay algo». La comparación es de tiempo constante, porque comparar con `==` filtra por el tiempo en qué prefijo se equivocó el que prueba |---|
| 2026-10-12 | **La CI corre el gate, no sus pasos.** La distinción parece menor y no lo es: una CI con su propia lista de comprobaciones puede quedar en verde mientras `./gate.sh` está en rojo, y entonces la insignia miente. Y el segundo trabajo **levanta la imagen de verdad**, porque construir no basta: una imagen que compila y no arranca pasa todos los tests y no sirve para nada |---|
| 2026-10-12 | **El OCR es local, y eso es una decisión de privacidad, no de precio.** Una captura de banco trae el nombre, el saldo y el teléfono de la persona: mandarla a un proveedor de visión sería cambiar el único activo que tenemos por comodidad de implementación. Y no hace falta: **en una captura el enlace está escrito**, así que hay que leerla, no entenderla. El invariante queda fijado **sobre el código fuente**: `imagen.py` no puede importar nada de red, y un test lo revisa. El lector recibe **bytes, no una URL** — si alguien quiere mandar la imagen afuera, tiene que cambiar la firma y romper un test que dice que no |---|
| 2026-10-12 | **Aparece `roadmap.md`, y con él una decisión que había que escribir: el motor no se entrena.** No como pendiente, sino como invariante: un clasificador entrenado no se puede auditar, y la auditabilidad es lo que sostiene el paper. Las dos rutas que se propusieron tienen respuesta medida —buscar más phishing ya se hizo (350 intentos, **0 nuevos**), y un algoritmo profundo rompería lo que hace citable el veredicto **sin atacar el hueco real**. Y el hueco es el mismo para todo: **no existe un corpus público de mensajes legítimos chilenos**, y eso bloquea dos mediciones y cualquier entrenamiento serio. El orden queda: **usarlo, que viva, medirlo, investigarlo** — la Fase 3 va antes que la 2 porque **el corpus legítimo sale de tener usuarios**, no de medir mejor |---|
| 2026-10-12 | **El despliegue entra al diseño, y con dos invariantes nuevos.** El **chequeo de salud va sin firma** —la plataforma no puede firmar— y **no revela nada de adentro**: que el servicio esté vivo es público, qué versión corre no. Y **la imagen no instala nada**: un `pip install` metería dependencias por la puerta de atrás y la reproducibilidad del veredicto se perdería sin que ningún test se entere. Los dos quedan fijados por tests, no por disciplina |---|
| 2026-10-11 | **El repositorio es público, y la reproducibilidad se verificó donde importa.** `git clone` a un directorio vacío y `./gate.sh` da **211 tests verdes**: es la diferencia entre prometer reproducibilidad y reproducirlo. Antes de publicar se auditó **toda la historia de git** buscando los cinco secretos: **ninguno aparece en ningún blob**, y `.env` nunca estuvo versionado. Lo único que quedó es el UUID del webhook, que no es una credencial. Y el corpus se revisó: **cero RUT, cero teléfonos** |---|
| 2026-10-11 | **Tres invariantes nuevos, y los tres protegen algo.** El **límite** protege el dinero (≈ 19 CLP por respuesta) y es **por persona**, no global, para que un spammer no deje sin servicio al resto; y **no calla de golpe**, avisa una vez. El **aviso de privacidad** deja de ser una promesa escrita y viaja en la primera respuesta. Y el **registro** dice por qué no se respondió, porque un envío que falla se veía igual que un mensaje sin nada que responder — la cuarta vez que ese modo de fallo aparece |---|
| 2026-10-11 | **Probado por WhatsApp: el robot ya contesta lo que el enlace no puede.** Cuatro mensajes reales, los cuatro `delivered`, **1–3 s** con el modelo en el camino. El caso nuevo es el **mensaje sin enlace que pide la clave**: antes salía `SIN_ENLACES` —mudo— y ahora dice de quién dice ser y qué pide. Y el caso mixto —enlace malo *y* petición— dice **las dos cosas**, que es el arreglo de la cascada funcionando en producción |---|
| 2026-10-11 | **La petición se suma al veredicto del enlace, no lo reemplaza.** Al cablear el extractor, **74 de las 342** estafas cambiaron `no_coincide` por `pide_lo_indebido` y el ciudadano dejaba de enterarse de que el enlace era falso. La cascada ponía la petición antes que los enlaces; ahora `PIDE_LO_INDEBIDO` queda **solo para el mensaje sin enlace**, que es lo único que el enlace no puede cubrir. Regla escrita: *un enlace malo no se lava porque el mensaje además pida algo, y una petición indebida no se lava porque el enlace sea oficial*. **Los 196 tests estaban verdes con la regresión dentro**: la encontró la medición |---|
| 2026-10-11 | **`T4.8b`: el extractor queda cableado al robot, y con él se cierra la brecha 2.** `main()` arma la caché con el modelo **solo si hay clave**: sin ella el robot no se rompe, se degrada. Y `componer` **evalúa dos veces** —una para saber de quién dice ser el mensaje, otra con la petición puesta— porque el extractor necesita el reclamo antes de poder extraer. Las dos veces decide el motor; el modelo solo llena el formulario en el medio. Los **28 mensajes del corpus sin enlace** dejan de salir mudos. Fijado con un `ExtractorFalso` y dos tests, sin red |---|
| 2026-10-11 | **`T4.5`: el extractor con modelo, y la privacidad resuelta a medias.** El modelo llena el formulario y **no decide**; el vocabulario es cerrado, así que **no puede inventar una categoría**. Y la respuesta a «¿caché y se borra?» es que **no alcanza**: el problema no es nuestra copia sino la transmisión. Se resuelve **redactando antes de mandar** —el modelo necesita la petición, no el mensaje— y cacheando el **resultado** (`hash → extracción`), no el texto. El test de privacidad encontró **3 fugas** en las 342 |---|
| 2026-10-11 | **`T4.4`: la regla de la petición, y el baseline que no sirve.** Esquema cerrado + regla citable («ninguna institución pide su clave ni sus datos por mensaje»), y el veredicto `PIDE_LO_INDEBIDO` para el mensaje sin enlace. **Y el extractor de referencia marca 3 de 6 frases que una institución sí escribiría** — las tres con negación, y las tres son **consejos contra el phishing**. Eso convierte «¿hace falta un modelo?» en una **vara medible**: tiene que entender la negación, o no se justifica |---|
| 2026-10-11 | **`T4.3`: aparece la precisión, y con ella el conjunto queda cerrado.** El control invertido —mismo texto, enlace real— da **0 falsas acusaciones de 211**. Y encontró el bug que ninguna otra medición vio: el motor inventaba dominios **en minúscula** (`paquete.por`), porque la regla era una heurística. **Ahora es la lista de 1.437 TLD de la IANA**, que es la autoridad. Tercera vez la misma lección: *la heurística falla y la fuente no* |
| 2026-10-11 | **El corpus no puede crecer: el techo es lo que el Estado publica.** 350 intentos, **0 mensajes nuevos**; el rendimiento del prefijo `acf` es **~1 %**. Queda en 342 con techo ~400, y **no existe un corpus chileno público más grande** — el paper tiene que decirlo. En el camino se cerró `T0.8`: la **API Pública de Ciberseguridad** (`/api/v1/openapi.json`) da **1.052 alertas con IoC estructurados**, mejor ingeniería y **el mismo alcance**: los mismos 738 dominios. Y se corrigió un bug real (`traer` sin reintentos descartaba códigos en silencio) y **una sospecha mía que la medición refutó**: creí que se habían perdido ~378 alertas `acf`, y no |
| 2026-10-11 | **El corpus pasa de medición a guardián.** `tests/test_corpus.py`: 342 estafas reales, **cero indulgencias** sobre el mensaje completo, y los fallos conocidos **declarados uno por uno** para que un fallo nuevo haga ruido. Con un trinquete: la cobertura de hoy es el piso de mañana. Y la conclusión sobre «entrenar», escrita: **una sola clase no se entrena, y el 99,7 % ya está cubierto por reglas** |
| 2026-10-11 | **`T4.2`: el motor gana un sexto veredicto, y es el más fuerte.** `CONFIRMADO` no juzga el enlace por su forma sino por su **historia**: 738 dominios que el Estado ya publicó como fraudulentos, con la alerta citada. **70 % del corpus queda confirmado, y el 97 % recibe respuesta útil.** Y los tests rompieron cuatro veces al construirlo, con razón: el índice traía **`bit.ly`** —70 alertas— y **`com.br`** (un sufijo público, no un dominio). Confirmarlos habría condenado a medio internet y a todo Brasil. **El filtro vive en la consulta, no solo en el archivo** |
| 2026-10-10 | **Aparece `spec.md`, y con él el SDD de verdad.** 78 requisitos numerados, cada uno con el test que lo verifica, y **`tests/test_spec.py` falla si un requisito no tiene test o apunta a uno que no existe** — verificado rompiéndolo a propósito. Escribirlo encontró un requisito sin cobertura (**`REQ-12`**, el envío no sigue redirecciones), que es exactamente para lo que sirve. Y queda como regla que **todos los `.md` se actualizan en el mismo commit que cierra la tarea** |
| 2026-10-10 | **La brecha son tres, y la grande es que la mayoría del fraude no trae enlace.** Medido: **1 de cada 4 chilenos cayó** en smishing y **+30 % en un año**. Se abre `doc/14-GAP.md` con las cinco opciones y la decisión: **el LLM extrae la petición en campos cerrados y una regla escrita decide** — «ninguna institución pide su clave ni sus datos por mensaje». El LLM **propone**, la regla **decide**, y la abstención sigue siendo un veredicto |
| 2026-10-10 | **`T3.1` armado: tres mensajes de prueba con tres formas de enlace distintas** (acortador, dominio con ruta, empresa del Estado), y **el armado encontró un bug en la frase que más importa**: decía «dice ser de Banco Ripley, Ripley», porque «Ripley» es nombre propio y además alias de «Banco Ripley». Ahora se nombra una sola vez |
| 2026-10-10 | **`T3.1`: el experimento que decide el paper, y un contador que no puede filtrar.** El «98 % mudo» de `T1.7` **es del formato del CSIRT y no de la gente**, así que hay que medirlo con personas: 20 × 3 mensajes reales con el host saneado a `.example`, sin decir la palabra enlace. Y el instrumento (`medicion.py`) escribe **agregados de tres etiquetas**: no tiene dónde guardar el contenido |
| 2026-10-10 | **`T1.8b`: entran BancoEstado, Santander y Scotiabank, y `nombra` llega a 39 de 45 (87 %)**. Estaban declarados imposibles de verificar por DNS; **el blocker no era el sitio sino la sonda**: la raíz de los tres no tiene registro A, solo `www.`, y el DNS local se rodea con `dns.google` y con los certificados emitidos de `crt.sh` |
| 2026-10-10 | **`T1.8`: el catálogo creció a 22 instituciones**, y `nombra` pasó de **0 a 24 de 45 (53 %)**. La medición destapó además un bug: `.../SantaIsabelws/tb.php` contaba `tb.php` como dominio propio — una acusación sobre un dato inventado. **Lo encontró el corpus, no un test unitario** |
| 2026-10-10 | **Nace este documento.** Se fija la arquitectura de siete piezas, los siete invariantes, y la regla «la IA propone, el determinismo decide» |
| 2026-10-10 | **La pregunta cambió** de «¿es del Estado?» a «¿es el sitio de quien dice ser?» (`T1.9`), y la medición mostró que **sin catálogo no cambia nada** |
| 2026-10-10 | **Se midió contra 45 estafas reales del CSIRT**: 0 graves, 0 reconocimientos, 47 % Banco Ripley |
| 2026-10-10 | **Probado de punta a punta con un teléfono real**, en 1 segundo |
