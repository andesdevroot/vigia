# task.md — cola de trabajo

`doc/` es la fuente de verdad. Acá va **qué falta y en qué estado**.

| # | Tarea | Estado |
|---|---|---|
| T0.1 | Esqueleto, gate y guardián de arquitectura | ✅ |
| T0.2 | Spike: medir el volumen real de CT | ✅ **el canal no tiene volumen** |
| T0.3 | Estado del arte | ✅ |
| T0.4 | Leer la tesis chilena 202581 | ✅ **el espacio está abierto** |
| T0.5 | ¿Es obtenible la lista de dominios del Estado? | ✅ **es completa por política** |
| T0.6 | ¿La barra azul verifica algo? | ✅ **no verifica nada** |
| T0.7 | Medir cuánto se usa mal la barra | 🚧 **diseño listo, bloqueada por acceso** |
| T0.8 | ¿Qué expone la API pública de ANCI? | ⬜ |
| T1.1 | El motor de respuesta: texto → veredicto | ✅ **44 tests verdes** |
| T1.2 | Costo real por verificación | ✅ **≈$19, y las primeras 1.000 gratis** |
| T1.3 | Catálogo de instituciones chilenas | ✅ **14 verificadas abriendo el sitio** |
| T1.4 | Endpoint que une el motor con Kapso | ✅ **74 tests verdes** |
| T1.5 | Regla de privacidad del mensaje reenviado | ⬜ **escrita y cumplida; falta el test** |
| T1.6 | Prueba de punta a punta por WhatsApp | ✅ **funcionó, y encontró un bug** |
| T1.7 | Medir si acierta contra estafas reales | ✅ **45 del CSIRT; 0 graves** |
| T1.8 | Extender el catálogo a lo suplantado | ⬜ **el corpus dice: 47 % Banco Ripley** |
| T1.9 | Reformular la pregunta del producto | ⬜ **«¿es el sitio de la institución que dice ser?»** |
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
