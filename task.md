# task.md — cola de trabajo

**`spec.md` es el contrato** (qué tiene que hacer el sistema, requisito por requisito, y cada uno
nombra el test que lo verifica). **`doc/` es la fuente de verdad** (qué se construye, por qué, y con
qué criterios). **`doc/design.md` es el diseño vivo.** Acá va **qué falta y en qué estado**.

**Al cerrar una tarea se actualizan todos los `.md` que toca, en el mismo commit** — la tabla está en
[`doc/00-METODOLOGIA.md`](doc/00-METODOLOGIA.md). La razón: este proyecto **mide, y vuelve a medir**,
así que un documento que no se actualiza pasa de fuente de verdad a archivo viejo que contradice al
código.

| | |
|---|---|
| Requisitos en `spec.md` | **129** |
| Tests | **188 casos** (179 funciones; dos están parametrizadas) |
| Guardián de la especificación | `tests/test_spec.py` falla si un requisito queda sin test |

| # | Tarea | Estado |
|---|---|---|
| T0.1 | Esqueleto, gate y guardián de arquitectura | ✅ |
| T0.2 | Spike: medir el volumen real de CT | ✅ **el canal no tiene volumen** |
| T0.3 | Estado del arte | ✅ |
| T0.4 | Leer la tesis chilena 202581 | ✅ **el espacio está abierto** |
| T0.5 | ¿Es obtenible la lista de dominios del Estado? | ✅ **es completa por política** |
| T0.6 | ¿La barra azul verifica algo? | ✅ **no verifica nada** |
| T0.7 | Medir cuánto se usa mal la barra | 🚧 **diseño listo, bloqueada por acceso** |
| T0.8 | ¿Qué expone la API pública de ANCI? | ✅ **1.052 alertas con IoC estructurados** |
| T1.1 | El motor de respuesta: texto → veredicto | ✅ **44 tests verdes** |
| T1.2 | Costo real por verificación | ✅ **≈$19, y las primeras 1.000 gratis** |
| T1.3 | Catálogo de instituciones chilenas | ✅ **14 verificadas abriendo el sitio** |
| T1.4 | Endpoint que une el motor con Kapso | ✅ **74 tests verdes** |
| T1.5 | Regla de privacidad del mensaje reenviado | ⬜ **escrita y cumplida; falta el test** |
| T1.6 | Prueba de punta a punta por WhatsApp | ✅ **funcionó, y encontró un bug** |
| T1.7 | Medir si acierta contra estafas reales | ✅ **45 del CSIRT; 0 graves** |
| T1.8 | Extender el catálogo a lo suplantado | ✅ **25 instituciones; `nombra` 0 → 39 de 45 (87 %)** |
| T3.1 | Medir si la gente reenvía el enlace | ⏸️ **sin las 20 personas; se reemplaza por T4.1** |
| T4.1 | Cosechar 300+ alertas del CSIRT | ✅ **342, y encontró dos cosas** |
| T4.2 | Índice de IoC del Estado (opción A) | ✅ **738 dominios; `confirmado` en 239 de 342** |
| T4.3 | Control invertido (enlace real, mismo texto) | ✅ **0 falsas acusaciones de 211** |
| T4.7 | Cosechar hasta 1.500 | ✅ **no se puede: el techo es ~400, y está medido** |
| T4.4 | Extractor de la petición + regla (opción C) | ✅ **regla lista; el baseline no sirve, y está medido** |
| T4.5 | Extractor con modelo, redacción y caché | ✅ **sin red en los tests; la privacidad, resuelta a medias** |
| T4.8 | Enfrentar DeepSeek y JEV contra la vara | ✅ **DeepSeek PASA; JEV descartado por costo opaco** |
| T4.6 | Invariantes sobre el corpus real | ✅ **342 estafas, cero indulgencias** |
| T1.9 | Reformular la pregunta del producto | ✅ **y la medición no cambió: falta T1.8** |
| T2.1 | El paper de medición | ⬜ |

**T0 es una fase de validación, no de construcción.** Tres de las cinco tareas cerraron con una
decisión, y dos de esas decisiones fueron negativas. Es a propósito: el proyecto anterior murió por
construir sin validar el insumo.

---

## ✅ T0.1 — Esqueleto, gate y guardián de arquitectura

`pyproject.toml` (uv, Python 3.13, **cero dependencias**), `gate.sh` (pytest + ruff + mypy con
`set -euo pipefail`) y `tests/test_arquitectura.py` con dos invariantes reales:

- **Importar `vigia` no arrastra la librería de red**, comprobado en un proceso limpio — en el de
  pytest ya podría estar importada y la comprobación no probaría nada.
- **T0.1 no agrega dependencias.** Si aparece una, que sea una decisión y no un accidente.

## ✅ T0.2 — Spike: el volumen real de Certificate Transparency

**Cerrada con una decisión negativa, que es un resultado.** 28 consultas, 1.521 dominios vistos,
**76 coincidencias de las cuales 74 son basura**.

El ruido tiene causa identificable, y son **dos defectos del detector**, los dos corregibles y
ninguno decisivo:

1. **El umbral de edición no escala con el largo de la marca.** `sii` tiene tres letras y con umbral 2
   se parece al 66 % de la palabra: `kis.si`, `cci.fr`, `asi.is`, `hki.si`.
2. **No hay filtro de TLD relevante.** `.si` es el ccTLD de **Eslovenia**: entra el mundo entero.

**La señal real: 2–3 dominios** (`bancoestado--cl.xyz`, `derivacionbancoestado.cl`, un homoglifo).
`bancochile`: 0. `claveunica`: 0.

**La conclusión no es "el detector está mal": es que la suplantación no vive en el nombre del
dominio.** El phishing usa dominios desechables con nombre neutro y pone la marca en el **contenido**;
además usa hosting gratuito, donde el certificado lo emite el host.

Detalle en [`doc/02-MEDICION-CT.md`](doc/02-MEDICION-CT.md). **Un spike de una hora mató la hipótesis
antes de tres semanas de construcción.**

## ✅ T0.3 — Estado del arte

Primera pasada, con un resultado incómodo: **el espacio no está vacío, y en Chile tampoco.** Existe
una tesis de la U. de Chile sobre mensajes fraudulentos; la lista blanca ya está publicada como
técnica ([APWG eCrime 2023](https://docs.apwg.org/ecrimeresearch/2023/20240080211286378.pdf)) y el
triaje por checklist también ([TraceScope](https://arxiv-org.ezproxy.obspm.fr/html/2604.21840v1)).

**Lo que queda limpio, y sigue en pie después de T0.4:**

1. Español de Chile con etiqueta que **no** puso un anotador pagado.
2. **Calibración medida por segmento.** Ninguno de los revisados lo hace: todos miden precisión,
   nadie mide si el umbral deja pasar más estafas contra un grupo.
3. **La medición negativa del canal de dominio**, que no está publicada.

Detalle en [`doc/03-ESTADO-DEL-ARTE.md`](doc/03-ESTADO-DEL-ARTE.md).

## ✅ T0.4 — Leer la tesis chilena 202581

**Leída, y cambia la conclusión: el espacio está abierto.**

Trincado Muñoz, *Diseño e implementación de sistema automatizado de recolección y análisis de mensajes
de texto fraudulentos*, Ingeniería Civil en Computación, **U. de Chile, 2024**, 61 páginas,
`sha256:f773f636`.

**Qué es:** un **electrodoméstico de captura**. Raspberry Pi 5 con módems USB que recogen SMS del
aire, clasificador **Random Forest**, base local, backend, frontend y reportes automáticos.

**Qué deja intacto:**

| | |
|---|---|
| Corpus público | **No.** Datos del **CSIRT** (con aplazamiento) y recolección **manual**: decenas de mensajes (79, 29, 108, 170) |
| ClaveÚnica y suplantación de marca | **Cero menciones** |
| Lista blanca | **Cero menciones** |
| Calibración | La palabra *"precisión"* **no aparece** |
| Modelos de lenguaje | Ninguno |
| Sus limitaciones | **De hardware.** El capítulo se llama *Limitaciones de Equipamiento* |

**Se posiciona sola:** *"da el primer paso para futuros estudios"*. Es un **precursor**, no un
competidor — la cita que más ayuda, porque el paper se escribe **encima** de ella.

**La alarma de T0.3 fue mía, por haber leído solo el título.** T0.4 existía para eso.

## ✅ T0.5 — La lista de dominios del Estado

**Respuesta: es obtenible, y mejor que obtenible — es completa por POLÍTICA, no por enumeración.**

`gob.cl` **no es un TLD: es un segundo nivel administrado por el Estado** (ANCI / CSIRT Nacional, con
registro en `nic.gob.cl`). Solo pueden inscribir órganos de la Administración del Estado. **Para
certificar que un sitio es del Estado no hace falta una lista: basta preguntar si termina en
`.gob.cl`.** La completitud depende de una restricción de registro, no de tener el listado entero.

Medido por CT: **221 dominios** `.gob.cl` registrables.

**Y el hallazgo que cambia el proyecto: la ANCI ya escribió la tesis.** Declara la
*identificabilidad* como objetivo, dice que *"todos los engaños de ingeniería social dependen de la
falta de identificabilidad"*, bloquea la jerarquía `gov.cl`, obliga a registrar el `.cl` solo para
redirigir, y creó una **barra azul** de sitio oficial.

**Lo malo:** la idea de la lista blanca no es nuestra. El Estado la implementó.
**Lo bueno, y es mejor:** **nadie publicó una medición de si funciona.**

Detalle en [`doc/04-LISTA-GOB-CL.md`](doc/04-LISTA-GOB-CL.md).

## ⬜ T0.8 — ¿Qué expone la API pública de ANCI?

La ANCI publica una **API Pública de Ciberseguridad** (`https://anci.gob.cl/api/v1/docs`, espejo en
`csirt.gob.cl/api/v1/docs`). La documentación **no carga sin JavaScript**, así que hoy no se sabe qué
entrega.

- **Entregable:** qué endpoints hay, qué datos dan, si necesitan clave, y qué licencia tienen.
- **Por qué importa:** si entrega alertas o indicadores, la herramienta se apoya en la ANCI en vez de
  reconstruir lo que la ANCI ya tiene. Cambia el costo de todo el proyecto.
- **Criterio de aceptación:** la lista de endpoints, o la constancia escrita de que no hay acceso
  abierto.
- **Riesgo:** que exista pero sea solo para organismos del Estado. **Eso también es un resultado.**

## ⬜ T2.1 — El paper de medición

> *Measuring a national trust anchor: does `.gob.cl` give the Chilean State identifiability online?*

Tres preguntas medibles, en orden de costo:

1. **¿La barra azul es falsificable?** Es un control **visual**: el PNG y el CSS se copian. Es la
   hipótesis más atacable y la más barata de medir.
2. **¿El ancla se sostiene?** Censo de `.gob.cl` contra las reglas de ANCI (nombres de empresa,
   genéricos reservados, un subdominio por institución).
3. **¿Dónde queda el ataque?** Homoglifo **en el propio TLD** (`gob.cl` con cirílica), `.cl` que
   parece oficial, y la barra copiada sobre un dominio ajeno.

**Bloqueo de acceso, no de datos:** la lista de inscripciones de ANCI no se publica. Se puede pedir
por Ley de Transparencia, y eso es una gestión.

## ✅ T0.6 — La barra azul no verifica nada

**El hallazgo, en una línea: la barra es una imagen pública, sin control de acceso y sin nada que la
ate al dominio.**

```
$ curl -I https://media.anci.gob.cl/images/ANCI_Icono_Blanco.original.svg
HTTP/2 200
content-type: image/svg+xml
access-control-allow-origin: *
```

`access-control-allow-origin: *` significa que cualquier sitio del mundo puede cargar el recurso. Y
en la página de la barra **no hay ninguna verificación de dominio, ni DNSSEC, ni token firmado, ni
script que compruebe que el sitio termina en `.gob.cl`**.

**La barra es una imagen que cualquiera copia.** Un sitio falso la pega y queda idéntico. Pero el
dominio **sí** es sólido (T0.5): depende de una restricción de registro que el Estado controla.

> **El ancla está bien puesta y el letrero está suelto.**

Detalle en [`doc/05-BARRA-AZUL.md`](doc/05-BARRA-AZUL.md).

## ⬜ T0.7 — Medir cuánto se usa mal la barra

**Convierte "es falsificable en teoría" en "N sitios la usan sin ser del Estado".** Un número, no un
argumento.

- **Método:** rastrear la web chilena buscando el recurso de la barra incrustado, y contar por dominio.
- **Criterio de aceptación:** el número, y la lista de dominios no oficiales que la muestran.
- **Ética:** no se construye ningún sitio de phishing. Solo se observan sitios existentes, sin
  interactuar con usuarios ni recoger datos personales. Lo que se encuentre va primero a la ANCI.
- **Riesgo:** que casi nadie la use mal, en cuyo caso la barra es inofensiva y el hallazgo pierde
  fuerza — pero **eso también es un resultado**.

## 📌 Decisión de canal — el mensaje, no el navegador

La forma del producto cambió: **la extensión de navegador queda como accesorio y el canal principal
es el reenvío de un mensaje.** Chrome de Android no acepta extensiones, y el fraude de ClaveÚnica
llega por SMS y WhatsApp al teléfono. Detalle en [`doc/08-CANAL.md`](doc/08-CANAL.md).

## ✅ T1.1 — El motor de respuesta

`src/vigia/motor.py`, stdlib pura, 14 tests nuevos (**44 verdes**).

**Contesta una sola pregunta: ¿el enlace del mensaje es del Estado?** No contesta si el mensaje
convence, y esa abstención **es** el producto.

| Veredicto | Cuándo |
|---|---|
| `OFICIAL` | **todos** los enlaces son de `.gob.cl`, y hay al menos uno |
| `AJENO` | hay al menos un enlace que no lo es |
| `SIN_ENLACES` | no hay enlaces que revisar |

**El invariante, y el test que lo fija: un enlace bueno no lava a uno malo.** Si bastara uno del
Estado, el motor daría su visto bueno justo al mensaje mejor construido — el que pone
`claveunica.gob.cl` de adorno al lado de `bit.ly/x`.

**Se ve así:**

```
AJENO        El enlace claveunica-gob-cl.xyz NO es del Estado. El enlace se parece a claveunica.
             El mensaje dice ser del Estado y el enlace no lo es.
OFICIAL      El enlace es del Estado: claveunica.gob.cl. Eso dice del enlace, no del mensaje: si
             le piden su ClaveUnica, su clave o sus datos personales, no los entregue.
SIN_ENLACES  El mensaje no trae ningún enlace, así que no se puede verificar. Dice ser del Estado,
             y decirlo no lo hace cierto.
```

**No dice «es seguro», y hay un test que lo prohíbe.** Es la línea roja: un enlace del Estado dentro
de un mensaje falso existe, y una herramienta que lo declare seguro es peor que no tener
herramienta.

**Lo que no necesita: ni corpus ni modelo.** La regla «¿termina en `.gob.cl`?» es completa por
política de registro (`T0.5`), así que la primera versión no depende de un insumo que podría no
existir — que es exactamente lo que mató al proyecto anterior.

**Y sí cubre el ataque que el ojo pierde:** `claveunica.gоb.cl` con la `o` cirílica da `AJENO`, con
el aviso de que usa letras que no son latinas.

## ✅ T1.2 — Cuánto cuesta cada verificación

**Unas $19, y las primeras 1.000 del mes son gratis.** El canal sobrevive: no hay blocker de costo.

Desde el **1 de octubre de 2026** Meta cobra los mensajes de servicio de WhatsApp Business Platform:
**1.000 gratis por número al mes**, y después **entre $15 y $22 cada uno**
([T13](https://www.t13.cl/noticia/tendencias/whatsapp-cobrara-entre-15-22-por-mensaje-quienes-se-les-aplicara-medida-2-10-2026)).
Lo que se cobra es **nuestra respuesta**, no el reenvío del ciudadano.

| Verificaciones al mes | Total |
|---|---|
| 1.000 | **$0** |
| 2.000 | ~$18.500 |
| 10.000 | ~$190.000 |

**La interfaz es [Kapso](https://kapso.com/)**, Meta Business Partner: número, webhooks de entrada y
envío de respuestas, con las tarifas de Meta a costo. Plan gratis con 2.000 mensajes al mes.

**El número tiene que ser +56.** El plan gratis trae un número de EE.UU., pero «Bring your own SIM»
permite conectar un chileno propio —chip nuevo, verificado por SMS, nunca registrado en WhatsApp—.
Una herramienta chilena antiestafa con número gringo es ella misma sospechosa.

Detalle, y lo que falta verificar, en [`doc/09-INTERFAZ.md`](doc/09-INTERFAZ.md).

## ✅ T1.4 — El endpoint que une el motor con Kapso

Cinco piezas, y **solo la última toca la red**: `firma.py` (verifica el HMAC), `entrante.py` (lee el
sobre), `motor.py` (el veredicto), `conversacion.py` (lo que se contesta) y `servidor.py` (HTTP y
envío). 74 tests verdes, sin red, en menos de un segundo.

**Lo que recibe la persona:**

```
ENTRA: Estimado usuario: su ClaveUnica sera BLOQUEADA. Regularice en
       http://claveunica-gob-cl.xyz/renovar
SALE:  El enlace claveunica-gob-cl.xyz NO es del Estado. El mensaje dice ser del
       Estado y el enlace no lo es.

ENTRA: BANCOESTADO: detectamos un cargo. Valide en bit.ly/3xR9k
SALE:  El enlace bit.ly NO es del Estado.

ENTRA: (una captura de pantalla)
SALE:  No puedo leer imágenes. Mándame el mensaje como texto: mantén apretado el
       mensaje, elige Copiar y pégalo acá.
```

**Tres invariantes, cada uno con su test:**

1. **Un mensaje saliente no se procesa.** Si el motor contestara a sus propios mensajes, cada
   respuesta generaría otra, para siempre y pagando cada una. Es el único error que no se nota en un
   test unitario y sí en la factura.
2. **La firma se verifica sobre los bytes crudos, no sobre el JSON.** Parsear y re-serializar cambia
   el espaciado y rompe el HMAC; el arreglo natural —aflojar la comparación— es el que abre la
   puerta.
3. **El servidor siempre contesta 200.** Un 500 hace que Kapso reintente, y reintentar lo que no
   supimos leer no lo vuelve legible.

**Y lo que no hace:** no escribe en disco, no registra el cuerpo del mensaje, y no sigue
redirecciones —`urlopen` las sigue por defecto y **reenvía la clave de API** al host de destino—.

**Cómo se corre, y lo que falta confirmar, en [`doc/10-CORRER.md`](doc/10-CORRER.md).**

**El hueco que queda a la vista:** `BANCOESTADO` en el texto no se reconoce como «dice ser del
Estado», porque el catálogo de marcas es `T1.3`. El enlace igual se marca; lo que falta es el
nombre.

## ✅ T1.3 — El catálogo de instituciones

`src/vigia/marcas.py`: 14 instituciones, **cada una verificada abriendo el sitio y leyendo su
certificado**. 90 tests verdes.

**Este es el único dato del proyecto que amplía el camino permisivo.** Todo lo demás es conservador:
ante la duda, no concluye. Un dominio de más acá no produce una falsa alarma — produce un **falso
negativo**: el motor daría por bueno el enlace del atacante. Por eso nada se escribió de memoria.

**Por qué hacía falta, y es un caso medido:** `gob.cl` es exclusivo del Estado (`T0.5`), pero no
todas sus instituciones lo usan. **`servel.gob.cl` no existe y `servel.cl` sí.** Sin catálogo, un
mensaje legítimo del Servel se leía como falso — el peor error posible, porque enseña a desconfiar de
lo verdadero.

| | |
|---|---|
| Verificadas | ClaveÚnica, SII, ChileAtiende, SUBTEL, FONASA, Servel, SERNAC, Carabineros, PDI, Correos, Metro, TVN, Codelco, TGR |
| Fuera, declarado | BancoEstado, Banco de Chile, Registro Civil, MINSAL, JUNAEB: **su DNS no resuelve desde esta máquina**. No se adivinó el dominio |

**Cuatro de catorce entradas del borrador escrito de memoria estaban mal.** Ninguna se habría notado
sin abrir el sitio. Detalle y evidencia en [`doc/11-MARCAS.md`](doc/11-MARCAS.md).

**Y el mecanismo contra la pudrición:** `test_los_dominios_del_catalogo_siguen_vivos`, marcado
`integracion`, vuelve a medir la lista entera. Una lista de confianza es el único dato de este
proyecto que empeora solo con el tiempo.

**Defecto de `T0.2` que se arregló de paso:** al enchufar el catálogo, **`bit.ly` entraba como
suplantación del SII**. Era el umbral de edición que no escalaba con el largo de la marca — `sii`
tiene tres letras y con umbral 2 se parece al 66 % de la palabra. Ahora una marca de tres letras
tolera una errata y una de seis, dos.

## ✅ T1.6 — La primera prueba de punta a punta, y el bug que encontró

**Un teléfono real, un mensaje real, una respuesta real.** 2026-10-10, 17:17. Registrado por Kapso:

| Cuándo | Dirección | Estado | Contenido |
|---|---|---|---|
| 17:17:18 | entrante | entregado | «Estimado usuario: su ClaveUnica sera BLOQUEADA. Regularice en http://claveunica-gob-cl.xyz/renovar» |
| 17:17:19 | saliente | entregado | «El enlace claveunica-gob-cl.xyz NO es del Estado. El mensaje dice ser del Estado y el enlace no lo es.» |

**Un segundo** entre el mensaje y la respuesta. La entrega del webhook: `delivered`, `HTTP 200`, un
solo intento.

**El montaje:** número **Sandbox** de Kapso (`597907523413541`) · webhook `4ace2423-…` contra el túnel
de ngrok · `whatsapp.message.received`, `payload_version v2`.

**Lo que cierra:** el canal elegido en `doc/08-CANAL.md` funciona de verdad, con un teléfono común,
**sin instalar nada**. Era la pregunta que quedaba abierta.

### Y comparar la respuesta real con la local encontró un bug grave

En local, el mismo texto agregaba **«El enlace se parece a ClaveÚnica.»** Por el teléfono, no. La
causa: **`atender` y `construir_servidor` traían el catálogo vacío por defecto, y `main` no pasaba
ninguno.**

O sea: **el servidor corría el motor sin catálogo.** Un mensaje legítimo del SERNAC se habría leído
como ajeno — el error exacto que `T1.3` existía para evitar. En local no aparecía porque **todos los
tests pasaban el catálogo a mano**.

Medido, con el mismo mensaje:

```
sin catálogo        El enlace sernac.cl NO es del Estado.
con catálogo        El enlace es de una institución oficial: sernac.cl (SERNAC).
```

Ahora el default es `MARCAS` en los tres puntos y hay un test que lo fija **donde se rompió**.

**Lo que esto enseña:** un test unitario en verde no dice nada sobre *con qué argumentos* se llama a
la función en producción. Se descubrió **comparando la salida real con la local**, no leyendo el
código.

### Confirmado en producción a las 17:38

El mismo mensaje, después del arreglo:

```
17:17:19   El enlace claveunica-gob-cl.xyz NO es del Estado. El mensaje dice ser del Estado…
17:38:39   El enlace claveunica-gob-cl.xyz NO es del Estado. El enlace se parece a ClaveÚnica.
           El mensaje dice ser del Estado…
```

**Un segundo** entre la entrada y la salida otra vez, `delivered`, `HTTP 200`. La frase que faltaba
ahora está. **Comparar las dos salidas es lo que cerró el ciclo**; sin la primera, el bug seguía
adentro.

**Lo que la prueba NO dice:** que el veredicto sea correcto en general. Dice que el camino funciona.
La calibración sigue pendiente, y para medirla haría falta un corpus — que este proyecto decidió no
guardar.

## ✅ T1.7 — Medir si acierta, contra estafas reales

**45 estafas cosechadas del CSIRT**, con su URL maliciosa y su fuente citable. `doc/12-MEDICION.md`.

```
                        la cita del CSIRT   la cita + el enlace del informe
  avisa                        1  (2%)             45  (100%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
  nombran la marca imitada     0                   0
```

**La columna derecha es tautológica y no es un resultado**: se le agregó al mensaje la URL que el
informe declara maliciosa, así que «no es del Estado» está garantizado. Confirma la regla, no mide un
acierto. **La única cifra tranquilizadora es el `0` de `GRAVE`**: en 45 estafas reales el motor nunca
dio por bueno el enlace malo.

**La columna izquierda habla del insumo, no del motor:** el CSIRT cita un **fragmento**, y en 44 de
45 el enlace no está dentro de la cita. Si alguien reenviara exactamente lo que el Estado publicó,
**no le serviríamos en el 98 % de los casos.**

### Los dos hallazgos

**1. Lo que se suplanta son bancos, no el Estado.** Contado sobre las 45 citas: **Banco Ripley 21
veces**, BancoEstado 16, y uno cada uno para Copec, Santander y Soprole. El motor **nombra la marca
imitada en 0 de 45**, porque el catálogo de `T1.3` solo tiene instituciones estatales bajo `.gob.cl`.

**2. La pregunta del producto está mal planteada.** El 47 % de lo suplantado es un banco privado. A
esa persona, «el enlace NO es del Estado» le dice algo cierto y **le deja la duda intacta**. El corpus
pide otra pregunta: **«¿este enlace es el sitio de la institución que el mensaje dice ser?»**.

### Se puede verificar, y se verificó

Leyendo el certificado: `bancoripley.cl` → `O=BANCO RIPLEY`, `bci.cl` → `O=Banco de Credito e
Inversiones`, `itau.cl` → `O=BANCO ITAU CHILE`. **`bancoestado.cl`, `santander.cl` y `scotiabank.cl`
no tienen certificado desde esta máquina**: quedan fuera por el mismo blocker de DNS, no se adivinan.

### Y un costo que se pagó

De los 785 informes del repositorio, **499 son de «Falsificación de Registros o Identidad» y no citan
ningún mensaje**. Ir por ellos primero devolvió **cero ejemplos después de cuarenta consultas**. Hay
que leer la composición del repositorio antes de recorrerlo.

## ✅ T1.9 — La pregunta del producto

De **«¿el enlace es del Estado?»** a **«¿este enlace es el sitio de la institución que el mensaje dice
ser?»**. Dos veredictos nuevos —`COINCIDE` y `NO_COINCIDE`— y dos viejos que quedan de respaldo
—`OFICIAL` y `AJENO`— para cuando no se reconoce ninguna institución reclamada.

**Una trampa que apareció al implementarlo:** la URL contaba como «dice ser». El mensaje
`Banco Ripley le informa: ingrese a claveunica.gob.cl` reclamaba ClaveÚnica **por el solo hecho de
enlazarla**, así que la lista de reclamadas incluía a las dos y el veredicto daba `COINCIDE` —
escondiendo justo la incoherencia que el motor existe para encontrar.

> **Enlazar a alguien no es decir ser él.** El reclamo se busca en el texto **con los enlaces
> borrados**.

**Y la medición con la pregunta nueva no cambió ni un número: `nombra` sigue en 0.** No es un fallo
de esta tarea — es que **el catálogo no tiene a los suplantados**. `nombra` solo se alcanza
reconociendo la institución. **Cambiar la pregunta era necesario y no es suficiente:** sin `T1.8`, el
motor no puede decir «el mensaje dice ser de Banco Ripley» porque no sabe quién es Banco Ripley.

## ✅ T1.8 — El catálogo, extendido a lo suplantado

**Ocho instituciones nuevas, y no por gusto: por la medición.** El corpus dice a quién suplantan de
verdad — **Banco Ripley 21 veces**, BancoEstado 16, Copec y Soprole una cada uno. Entraron las que se
pudieron **verificar por certificado**: Banco Ripley, Ripley, BCI, Banco Itaú, Banco de Chile, Banco
Falabella, Copec y Soprole. Catálogo: **22 instituciones**.

```
                         la cita del CSIRT   cita + enlace del informe
  nombra                       0   (0%)            24  (53%)   ← era 0
  avisa                        1   (2%)            21  (47%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
```

**`nombra` pasó de 0 a 24 de 45 (53 %).** Y con `T1.8b` —BancoEstado, Santander y Scotiabank— llegó
a **39 de 45 (87 %)**. **De 0 a 87 % cambiando datos, no código.** `GRAVE` siguió en **0**.

### `T1.8b` — el blocker no era el sitio, era la sonda

BancoEstado es el **36 % del corpus** y estaba declarado imposible de verificar porque su DNS no
resolvía desde esta máquina. **Dos hallazgos lo desarmaron:**

1. **La raíz de los tres no tiene registro A.** Solo `www.` resuelve — el mismo patrón de
   `fonasa.gob.cl`. Preguntar por la raíz y concluir «no existe» era el error.
2. **El DNS local se puede rodear.** `dns.google` resuelve por HTTPS, y `crt.sh` da los certificados
   **emitidos**, que prueban que el dominio existe y quién lo pidió.

Los certificados son concluyentes porque nombran **subsistemas internos de un banco**:
`*.open-banking-mtls-prod.bancoestado.cl`, `*.dev.wp.banco.santander.cl`,
`Portal-ScotiaEmpresas.scotiabank.cl`. Nadie más tendría esos nombres.

> **Un dominio que «no resuelve» no es un dominio que no existe.** Antes de declararlo hueco hay que
> probar `www.`, preguntar por HTTPS y mirar los certificados emitidos.

**Un detalle del mundo real que sale en los datos:** buena parte de esos mensajes enlazan a
**`bit.ly`**. El atajo de URL es la norma, no la excepción.

### Y la medición destapó un bug que ningún test unitario veía

`.../SantaIsabelws/tb.php?ea=1` hacía que **`tb.php` contara como un dominio propio**, y el motor lo
nombraba como si fuera un sitio del atacante: una acusación sobre un dato inventado. La causa era
leer el host sin separar la ruta. Corregido, con dos tests, y el bug valía un caso más (23 → 24).

> **Los alias son parte del dato.** El corpus escribe «Banco Ripley», «bancoripley» y «banco
> ripley» para lo mismo; comparar solo contra el nombre normalizado perdía dos de las tres.

## 🚧 T3.1 — ¿La gente reenvía el enlace?

**Es el único número sin medir, y el que decide el paper.** Si el ciudadano reenvía el texto sin el
enlace, el motor se queda mudo. Protocolo completo en [`doc/13-PROTOCOLO.md`](doc/13-PROTOCOLO.md).

**Una aclaración que cambia el diseño:** el «98 % mudo» de `T1.7` **es del formato del CSIRT, no de
la gente**. La alerta publica el texto por un lado y la URL por otro; en el SMS original el enlace
estaba. Así que no es una predicción: es un artefacto de la fuente. Eso convierte a `T3.1` en el
experimento que decide entre dos lecturas opuestas, y **las dos son publicables**.

**El diseño:** brazo controlado de **20 personas no técnicas × 3 mensajes reales** del corpus, dichos
con una sola frase —*«mándale estos mensajes al robot y mira qué te dice»*— **sin mencionar la
palabra enlace**. Más un brazo observacional de dos semanas con estafas reales.

**Los mensajes son reales en su texto e inofensivos en su enlace:** el host se reemplaza por uno
reservado (`.example`, RFC 2606) que **no existe y no puede existir**. La forma del enlace se
conserva, el veredicto del robot no cambia, y nadie puede pinchar y llegar a algo.

### Y el instrumento no puede filtrar

`src/vigia/medicion.py`: un contador **apagado por defecto** (`VIGIA_CONTAR=1`) que escribe
agregados.

```json
{"2026-10-11": {"con_adjunto": 1, "con_enlace": 1, "texto_sin_enlace": 1}}
```

**No hay ningún camino por el que el contenido llegue a ese archivo.** El contador recibe el mensaje
y devuelve una de tres etiquetas: no tiene dónde poner el texto ni el número. Hay un test que cuenta
un mensaje con una marca secreta y comprueba que la marca **no aparece**.

> Un instrumento de medición **que no puede** guardar lo que mide es más fuerte que una promesa, y
> para el paper es un argumento y no una nota al pie.

Probado por HTTP de verdad: tres mensajes, tres modalidades, un archivo con tres números.

## ✅ T4.1 — El corpus crece a 342, y aparecen dos cosas

Del **sitemap del CSIRT (5.179 alertas)** en vez del repositorio de indicadores, que solo cubre los
códigos viejos. Corpus: **45 → 342 estafas**.

```
                         la cita del CSIRT   cita + enlace del informe
  nombra                       0   (0%)           210  (61%)
  avisa                        9   (3%)           131  (38%)
  mudo                       330  (96%)             1   (0%)
  GRAVE                        3   (1%)             0   (0%)
```

### 1. El motor inventaba dominios, y se los decía al ciudadano

El SMS dice, sin espacio tras el punto: «...ya estan operativos**.**Sin embargo...». **El motor leyó
`operativos.Sin` como un dominio**, y la respuesta decía «el enlace **operativos.sin** no es de
BancoEstado» — **un dominio que no existe**, nombrado como el sitio del atacante.

Arreglado cortando el host donde empieza una oración, respetando los dominios en mayúsculas.
**`nombra` pasó de 5 a 0 y `avisa` de 19 a 9**: esos veredictos los producía el ruido.

> **Lo encontró el corpus de 342, no un test unitario.** Cuarta vez.

### 2. Los 3 `GRAVE` son la carnada

Los tres nombran **un dominio legítimo** (`interior.gob.cl`, `www.bancoestado.cl`) mientras el enlace
malo está en otra parte. **En el mensaje completo no hay ninguno: `GRAVE = 0`.** Solo aparecen en la
cita recortada, donde el enlace malo no está y lo único que queda es el señuelo.

> **Un mensaje incompleto puede recibir una respuesta demasiado confiada.**

**Y no se arregla con una regla más:** `operativos.Sin` y `claveunica.gob.cl.xyz` son lexicalmente
idénticos. Lo que los distingue es **qué pide el mensaje**. Es la justificación medida de la opción C
(`T4.4`): **la ambigüedad del dominio suelto no se resuelve mirando el dominio.**

## ✅ T4.2 — El índice de indicadores del Estado

**738 dominios que el Estado ya publicó como fraudulentos**, con las alertas que lo dicen. Detalle en
[`doc/15-INDICE.md`](doc/15-INDICE.md).

```
                         la cita del CSIRT   cita + enlace del informe
  confirmado                   0   (0%)           239  (70%)   ← nuevo
  nombra                       0   (0%)            74  (22%)
  avisa                        9   (3%)            28   (8%)
  mudo                       330  (96%)             1   (0%)
  GRAVE                        3   (1%)             0   (0%)
```

**El 97 % de las estafas recibe una respuesta útil** sobre el mensaje completo: 239 confirmadas con
la alerta citada, 74 con la institución nombrada, 28 avisadas. Una queda muda. Ninguna grave.

**Y no predice: cita.** `CONFIRMADO` no dice «creo que esto es malo», dice **«el CSIRT publicó que
este dominio es fraudulento, en esta alerta»**, y el ciudadano puede ir a leerla. Por eso manda
sobre todos los demás veredictos.

### Los tests rompieron cuatro veces, y tenían razón

`bit.ly` **está en el índice del Estado** —70 alertas lo reportan—. Confirmarlo habría condenado a
medio internet: una URL maliciosa en un acortador no vuelve fraudulento al acortador.

Buscando por dato y no por memoria apareció algo peor: el índice guardaba **`com.br` (14 alertas),
`com.au` (10) y `com.np` (8)**. Eso no son dominios, son **sufijos de registro**
(`etiqueta_registrable` reduce por etiquetas contadas y no conoce los sufijos públicos), así que
`algo.com.br` se volvía `com.br` y confirmarlo condenaba a **todo Brasil**.

Ambas cosas se filtran **en la consulta, no solo al construir el índice**: aunque el archivo traiga
un `bit.ly`, la respuesta nunca puede confirmarlo. **Un dato que no se puede defender en la consulta
no se defiende en ninguna parte.**

## ✅ T4.6 — El corpus como guardián, no solo como medición

`tests/test_corpus.py`: **342 estafas reales, cero indulgencias**. Recorre el corpus y exige que
ninguna reciba un veredicto favorable sobre el mensaje completo.

**Y los fallos conocidos van declarados uno por uno**, con su razón:

```python
GRAVES_CONOCIDOS = {
    "fph24-00951": "el enlace malo no está en la cita: lo único que queda es el señuelo",
    ...
}
```

> **Un fallo conocido y escrito es un fallo vigilado; uno sin escribir parece nuevo cada vez.** Si
> aparece un cuarto, el test falla.

Hay además un **trinquete**: la cobertura de respuesta útil de hoy (99,7 %) es el piso de mañana. Un
cambio que la baje falla acá y no en la cara de alguien.

**Sobre entrenar:** el corpus tiene **una sola clase** —342 fraudulentos, cero legítimos— así que no
se puede entrenar nada, y hay un test que lo deja escrito para que el día que aparezcan negativos,
alguien se entere de que la limitación cambió. El razonamiento completo, en
[`doc/14-GAP.md`](doc/14-GAP.md).

## ✅ T4.7 — ¿Se puede cosechar hasta 1.500? **No, y está medido**

Se intentó: **350 intentos sobre alertas sin cosechar, 0 mensajes nuevos.** El rendimiento del
prefijo `acf` es de **~1 %** — de diez códigos revisados, **todos tienen URL y ninguno cita un
mensaje**.

**El techo no es el esfuerzo: es lo que el Estado publica.** De las 5.179 alertas del sitemap, la
mayoría son de vulnerabilidades y campañas **sin mensaje citado**. El corpus se queda en **342**, con
techo ~400.

> **No hay un corpus chileno público más grande**, y el paper tiene que decirlo en voz alta en vez de
> disimularlo. Cualquier trabajo que afirme entrenar con fraude chileno está usando esto o algo
> privado.

### Y en el camino: la API (`T0.8`, cerrada)

`csirt.gob.cl/api/v1/openapi.json` responde **200** — la API Pública de Ciberseguridad que la
documentación escondía detrás de JavaScript. `GET /api/v1/alerts/` da **1.052 alertas** con IoC ya
separados: `url`, `dominio`, `sha256`, `ipv4`, `mitre-attck`.

**Mejor ingeniería, mismo alcance:** el índice reconstruido por la API tiene **los mismos 738
dominios**. Ni más datos, ni el mensaje citado (cero de cincuenta).

### Un bug real, y una sospecha mía que el número refutó

`traer` no tenía reintentos: un fallo de red descartaba el código **en silencio**. Se agregaron.

Y al ver 303 `8fph` contra 3 `acf` habiendo 381, **supuse** que se habían perdido ~378 por red. **La
medición dijo que no.** La sospecha era mía; el número la corrigió. **Segunda vez en el día**,
después de los «124 tests».

## ✅ T4.3 — El control invertido, y el denominador que faltaba

**El mismo texto de la estafa, con el enlace de la institución real.** Aísla una sola variable: si el
motor acusa, la causa no puede ser el texto.

```
CONTROL INVERTIDO: 211 mensajes de 342
  coincide  190  (90%)
  oficial    21  (10%)
  mudo        0   (0%)
  acusa       0   (0%)

  FALSAS ACUSACIONES: 0 de 211 = 0.0%
```

**Y con esto el paper ya tiene los dos números:** cobertura **99,7 %** sobre el mensaje completo, y
precisión **0 falsas acusaciones de 211**.

**Es un control construido, no un corpus recogido**, y se declara: mide la acusación que induce el
**texto**. No mide la falsa acusación sobre mensajes legítimos de verdad, cuya redacción y petición
son distintas.

### Y encontró el bug que faltaba: **el motor inventaba dominios en minúscula**

La única falsa acusación decía:

> «El enlace correos.cl es de Correos de Chile. El enlace **paquete.por** NO es del Estado.»

El SMS dice «falta un número de calle en el **paquete.por** favor actualice». Mi regla anterior —«un
punto seguido de mayúscula es una oración»— **atrapaba `operativos.Sin` pero no `paquete.por`**.

**La regla correcta no es una heurística: es preguntarle a la IANA.** Se incorporó su lista de
**1.437 TLD** al paquete, y ahora un host cuenta solo si su última etiqueta es un TLD de verdad.
`por` y `sin` no lo son; `cl`, `xyz`, `sbs` y `live` sí — el phishing usa TLD reales, así que el
filtro no deja pasar nada.

**Los reservados de RFC 2606 se aceptan a propósito** (`.example`, `.test`, `.invalid`): los mensajes
de prueba de `T3.1` los usan **porque no pueden resolver**, y sin eso el motor dejaría de leer sus
propios mensajes de prueba. Un test lo fija.

## ✅ T4.4 — La regla de la petición, y por qué el baseline no sirve

**El modelo extrae; la regla decide.** `src/vigia/peticion.py`: esquema cerrado (`pide`: clave, datos,
transferencia, llamar, pinchar, responder) y una regla citable:

> **Ninguna institución pide su clave, sus datos personales ni una transferencia por mensaje.**
> Hacen falta **las dos** condiciones: el reclamo y la petición indebida.

Nuevo veredicto **`PIDE_LO_INDEBIDO`**, que cubre lo que el enlace no puede: el mensaje sin enlace que
pide la clave.

### Y el extractor de referencia **no sirve**, medido

```
sondas (frases que una institución SÍ escribiría): 3 de 6 marcadas como fraude
  MARCA  «Recuerde: nunca le pediremos su clave por mensaje ni por teléfono.»
  MARCA  «Su clave es personal. No la comparta con nadie.»
  MARCA  «Para su seguridad, no entregue sus datos personales por mensaje.»
  ok     «Su trámite fue recibido. Revise el estado en nuestro sitio oficial.»
  ok     «Le informamos que su solicitud fue aprobada. No es necesario hacer nada más.»
  ok     «Este es un aviso informativo. No responda a este mensaje.»
```

**Las tres que falla son las tres con negación, y son consejos contra el phishing.** El extractor de
referencia marca precisamente los mensajes que enseñan a la gente a cuidarse.

> **Ese es el argumento medido a favor de un extractor con modelo** — y le pone la vara: tiene que
> entender la negación. Un modelo que no le gane a 3 de 6 no justifica su costo, su latencia, ni
> mandar el mensaje de un ciudadano a un tercero.

Las sondas quedan como **conjunto de conformidad** en `peticion.SONDAS`, y las tres falsas alarmas
están **declaradas una por una** en el test: si aparece una cuarta falla, y si alguna se resuelve
también — porque eso significa que llegó un extractor mejor.

### Y lo que **no** se puede medir, otra vez

**La cobertura que gana la regla es 0 sobre este corpus**: las 342 estafas del CSIRT ya traen enlace,
así que solo una queda muda. **La precisión tampoco se puede medir**: hace falta un corpus de mensajes
legítimos, y no existe. **Es el mismo hueco, por segunda vez.**

## ✅ T4.5 — El extractor con modelo, la redacción y la caché

**El modelo llena el formulario; la regla decide.** `src/vigia/extractor.py`: una sola implementación
compatible con la API de OpenAI —**sirve para DeepSeek y para JEV**, y enfrentarlos es cambiar dos
valores— con el `abrir` inyectado, igual que el respondedor de Kapso. **Los 24 tests nuevos corren sin
red.**

### La privacidad: «que quede en caché y se borre» **no alcanza**

**El problema no es nuestra copia.** Cuando el texto sale hacia un proveedor, **la transmisión ya
ocurrió**, y lo que él retenga no lo controlamos. Borrar nuestra caché no borra la suya.

**Lo que sí sirve: no mandar el dato.** Y el modelo **no necesita el mensaje, necesita la petición**:
para saber si un texto pide la clave no hacen falta el RUT, el teléfono ni el enlace.

```
entra:  "Su RUT 12.345.678-9, llame al +56 9 1234 5678 o entre a https://malo.xyz/a"
sale:   "Su [RUT], llame al [TELEFONO] o entre a [ENLACE]"
```

El enlace también se tapa: **el dominio malicioso no sale del servidor.** El motor ya lo juzgó antes.

**Y ahí sí la caché tiene sentido, la del resultado:** `hash(texto redactado) → extracción`. Una
campaña de diez mil mensajes **se transmite una vez**, y lo guardado son hashes y seis etiquetas.
Nunca el texto.

### El test de privacidad encontró 3 fugas en las 342

Recorriendo el corpus entero, tres mensajes salían con códigos dentro de alfanuméricos
(`D541472056CL`, `BCE001547-56`) que `\b` no atrapaba. No son datos personales, pero son
identificables y **no aportan nada a la extracción**. El patrón se arregló y quedó sin fronteras de
palabra, a propósito.

### Y el vocabulario sigue cerrado

El modelo **no puede inventar una categoría**: lo que no esté en la lista se descarta. Es lo que
mantiene auditable un extractor llenado por un modelo.

### Lo que falta para cerrarlo

**Medir si el modelo le gana al baseline.** Tiene que superar las 6 sondas de `peticion.SONDAS`, y hoy
el extractor de referencia marca 3 mal —las tres con negación—. Eso necesita credenciales de DeepSeek
o de JEV, y hay que decidir cuál se usa **midiendo**, no por gusto.

## ✅ T4.8 — Enfrentar DeepSeek y JEV contra la vara

`scripts/comparar_extractores.py`: mide **falsas alarmas sobre las 6 sondas** y **sensibilidad sobre
una muestra del corpus**, y dice cuál gana. **Sin claves corre igual**, y muestra el baseline solo.

```bash
cp .env.example .env      # y pega ahí las claves
python3 -u scripts/comparar_extractores.py
```

Las variables están en `.env.example`: `DEEPSEEK_API_KEY` (API directa) y `OPENROUTER_API_KEY` (JEV se
sirve **por OpenRouter**, y su identificador verificado es **`typesafe/jev-router`**, no `jev-1.13`).

**Regla de aceptación: el modelo tiene que dejar las falsas alarmas en 0 sobre esas 6 frases.** Un
modelo que marque «nunca le pediremos su clave» no se usa: marcaría los mensajes que enseñan a la
gente a cuidarse.

## 🚧 T4.8 — El primer enfrentamiento, y un falso aprobado

```
extractor                          falsas alarmas  aciertos   veredicto
------------------------------------------------------------------------------
referencia (sin modelo)            3 de 6            2/40       no sirve
DeepSeek deepseek-chat             0 de 6            1/40       PASA
JEV typesafe/jev-router            0 de 6            0/40       NO VERIFICABLE (31 fallidas)
```

**DeepSeek entiende la negación, verificado sonda por sonda:** las 6 en `pide=[]`, **0 fallos**. Es el
argumento medido a favor del modelo, cumplido.

**JEV se descarta, y no por el saldo: por el costo opaco.** `typesafe/jev-router` **enruta a modelos
pagados sin decir cuál ni a qué precio** —en la prueba derivó a `deepseek/deepseek-v4.1-flash`— y en un
servicio público el costo por verificación tiene que ser **un número, no una sorpresa**.

Y hay una demostración concreta: en las 6 sondas, **JEV dio 1 fallo `HTTP 402` y aun así imprimió 6
«ok»**. Ese «ok» era una llamada caída, no una respuesta. **La misma trampa, ahora en la vara**: sin el
contador de fallos, JEV habría aprobado.

### Y el instrumento tenía el mismo defecto que medía

Informó **«JEV PASA»** mientras todas sus llamadas fallaban: **una petición vacía se ve igual que un
modelo que no encontró nada.** Un proveedor caído daba cero falsas alarmas y parecía intachable.

Se agregó un **contador de fallos**, y ahora un modelo con llamadas fallidas sale **«NO VERIFICABLE»**
en vez de aprobado. Hay un test que lo fija con el caso exacto que ocurrió.

> **Tercera vez hoy que un fallo se disfraza de éxito.** Las otras dos: los «124 tests» y las «378
> alertas `acf` perdidas».

### Y la sensibilidad está mal medida, declarado

El `aciertos` mide el veredicto final, que exige que **además** se reconozca el reclamo. Y el corpus
del CSIRT es mayormente de **pinchar un enlace** —que no es una petición indebida—, así que mide otra
cosa. **La vara es la métrica válida; la sensibilidad hay que rediseñarla** midiendo la extracción
contra etiquetas hechas a mano.

## ✅ T4.8b — DeepSeek conectado al robot, y el caso que deja de quedar mudo

**Lo que faltaba no era el modelo: era el cable.** El extractor estaba escrito y medido, pero el
servidor no lo llamaba. Ahora `main()` arma `CacheDeExtraccion(ExtractorLLM(...))` **solo si existe
`DEEPSEEK_API_KEY`**, y `conversacion.componer` lo usa.

```
sin la clave   → el robot funciona igual que antes (degradación silenciosa, sin romperse)
con la clave   → el mensaje sin enlace que pide la clave sale PIDE_LO_INDEBIDO
```

### `componer` evalúa dos veces, y tiene que hacerlo

El extractor **necesita saber de quién dice ser el mensaje** para extraer la petición, y eso lo
resuelve el motor. Así que se evalúa una primera vez para obtener `reclamadas` → `dice_ser`, se llama
al extractor, y se evalúa de nuevo con la petición puesta. **El motor decide las dos veces; el modelo
solo llena el formulario en el medio.**

### Y el caso que esto desbloquea es el 8 % del corpus

En las 342 estafas, **28 no traen enlace** (`avisa`) y una más queda muda. Hasta hoy salían con
`SIN_ENLACES`. Con el extractor conectado pasan a tener veredicto —**si piden algo indebido**—, que es
exactamente la brecha que `T4.4` declaró y no podía cerrar sola.

### Verificado sin red

`tests/test_servidor.py` usa un `ExtractorFalso` con la petición inyectada: **un test fija que el
mensaje sin enlace ya no queda mudo**, y **otro fija que sin extractor el robot se comporta como
antes**. La regla de arriba queda clavada en los tests, no en la buena voluntad.

## 🚧 T0.7 — Medir el mal uso de la barra

**El diseño está hecho y el número no se pudo obtener: blocker de acceso, declarado.**

Hace falta un índice de **subrecursos** —qué página cargó qué archivo— y no hay uno abierto.
urlscan.io lo tiene pero **su API de búsqueda necesita clave**; Common Crawl no sirve porque registra
los enlaces de la página y **no los subrecursos**, y la barra es una imagen.

**No se inventó un número.** Un método malo que devuelve una cifra es peor que un blocker declarado:
daría algo que parece un resultado y no lo es.

Detalle y método en [`doc/06-MEDIR-BARRA.md`](doc/06-MEDIR-BARRA.md).

**Salida recomendada: una clave de urlscan.io** (gratis, con registro). Es una gestión, no un problema
técnico.

**Y lo importante:** el hallazgo de T0.6 **se sostiene sin este número**. El número agrega magnitud,
no existencia.
