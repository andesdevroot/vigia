# 12 — La medición: 45 estafas reales

## De dónde salieron, y por qué de ahí

Del **CSIRT**, que es el Estado etiquetando la estafa. Dos fuentes que se complementan:

| Fuente | Qué aporta |
|---|---|
| [`github.com/csirtcl/Fraude`](https://github.com/csirtcl/Fraude) | 785 informes con la URL maliciosa y el dominio, en texto limpio |
| `csirt.gob.cl/alertas/{codigo}/` | el texto del mensaje, **citado literalmente** entre comillas tipográficas |

De los 785 informes, **499 son de «Falsificación de Registros o Identidad» y no citan ningún
mensaje**. Ir por ellos primero devolvió **cero ejemplos después de cuarenta consultas** — el primer
intento, y el que enseñó a leer la composición del repositorio antes de recorrerlo.

Los que sirven son los **259 de phishing y smishing**. De ahí salieron **45**, con su código, su URL
maliciosa y su fuente citable. Están en `corpus/alertas_csirt.json`.

## El resultado

```
                        la cita del CSIRT   la cita + el enlace del informe
  avisa                        1  (2%)             45  (100%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
  nombran la marca imitada     0                   0
```

## Lo que estos números NO dicen

**La columna de la derecha es tautológica y no es un resultado.** Ahí se le agregó al mensaje la URL
que el propio informe declara maliciosa, así que el motor dice «no es del Estado» porque se le dio
un enlace que no lo es. Confirma que la regla funciona; **no mide ningún acierto.**

**No hay falsas acusaciones medidas.** Para eso haría falta un corpus de mensajes legítimos, y no
existe. El `0` de la columna `GRAVE` es real y es lo único tranquilizador: **el motor nunca dio por
bueno el enlace de una estafa**, en 45 casos.

Lo que sí dice la columna de la izquierda es sobre el **insumo**, no sobre el motor:

> **El CSIRT cita un fragmento, no el mensaje completo.** En 44 de 45 casos el enlace no está dentro
> de la cita.

O sea: si un ciudadano reenviara exactamente lo que el Estado publicó, **no le serviríamos en el 98 %
de los casos.** En el SMS real el enlace estaba; el informe lo reporta aparte.

## Hallazgo 1 — A quién suplantan de verdad

Contadas sobre las 45 citas:

| Veces | Institución |
|---|---|
| **21** | **Banco Ripley** |
| **16** | **BancoEstado** (escrito «banco de estado») |
| 1 | Copec |
| 1 | Santander |
| 1 | Soprole |

**Casi la mitad son un banco privado.** Y el motor **nombra la marca imitada en 0 de 45 casos**,
porque el catálogo de `T1.3` solo tiene instituciones del Estado que usan `.gob.cl`.

## Hallazgo 2 — La pregunta del producto está mal planteada

El motor contesta **«¿el enlace es del Estado?»**. Pero el 47 % de lo que se suplanta es **Banco
Ripley**, que no es del Estado. A esa persona la respuesta «el enlace NO es del Estado» no le sirve:
le dice algo cierto y le deja la duda intacta.

La pregunta que el corpus pide es otra:

> **«¿Este enlace es el sitio de la institución que el mensaje dice ser?»**

Es un cambio de fondo, no de redacción: obliga a tener catálogo de **lo suplantado**, no solo de lo
estatal, y a que el veredicto hable de la institución nombrada.

## Lo que se puede verificar del hallazgo 1

Los dominios de los suplantados, leídos de su certificado:

| Dominio | Certificado |
|---|---|
| `bancoripley.cl` | `O=BANCO RIPLEY` |
| `bci.cl` | `O=Banco de Credito e Inversiones` |
| `itau.cl` | `O=BANCO ITAU CHILE` |
| `bancochile.cl` | `businessCategory=Private Organization` |
| `bancofalabella.cl`, `ripley.cl`, `soprole.cl`, `copec.cl` | `CN` del dominio |
| **`bancoestado.cl`, `santander.cl`, `scotiabank.cl`** | **sin certificado desde esta máquina** |

Los tres últimos quedan **fuera** por el mismo blocker de DNS que ya declaró `T1.3`. No se adivinan.

## T1.9 — Cambiar la pregunta, y lo que costó

La pregunta pasó de «¿el enlace es del Estado?» a **«¿este enlace es el sitio de la institución que el
mensaje dice ser?»**. Veredictos nuevos: `COINCIDE` y `NO_COINCIDE`.

**Una trampa que apareció al implementarlo:** la URL contaba como «dice ser». Un mensaje
`Banco Ripley le informa: ingrese a claveunica.gob.cl` reclamaba ClaveÚnica por el solo hecho de
enlazarla, así que la lista de reclamadas incluía a las dos y el veredicto daba `COINCIDE` —
escondiendo justo la incoherencia que el motor existe para encontrar. **Enlazar a alguien no es decir
ser él.** Ahora el reclamo se busca en el texto **con los enlaces borrados**.

### La medición con la pregunta nueva no cambió ni un número

```
                         la cita del CSIRT   cita + enlace del informe
  nombra                       0   (0%)             0    (0%)
  avisa                        1   (2%)            45  (100%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
  reconoció de quién dice ser  0                   0
```

**Cero reconocimientos.** No es un fallo de `T1.9`: es que **el catálogo no tiene a los
suplantados**. `nombra` solo se alcanza reconociendo la institución, y el catálogo de `T1.3` son
instituciones estatales bajo `.gob.cl` — mientras que el corpus suplanta bancos.

> **Cambiar la pregunta era necesario, y no es suficiente.** Sin `T1.8` el motor no puede decir «el
> mensaje dice ser de Banco Ripley», porque no sabe quién es Banco Ripley.

Es el orden correcto igual: si el catálogo hubiera crecido primero, el motor habría dicho «el enlace
es de una institución oficial: bancoripley.cl (Banco Ripley)», que no es lo que hay que leer.

## T4.4 — La regla de la petición, y la vara para el modelo

**El modelo extrae; la regla decide.** Esquema cerrado y una regla citable: *ninguna institución pide
su clave, sus datos personales ni una transferencia por mensaje*.

### El extractor de referencia no sirve, y ahora se sabe cuánto

```
sondas (frases que una institución SÍ escribiría): 3 de 6 marcadas como fraude
  MARCA  «Recuerde: nunca le pediremos su clave por mensaje ni por teléfono.»
  MARCA  «Su clave es personal. No la comparta con nadie.»
  MARCA  «Para su seguridad, no entregue sus datos personales por mensaje.»
  ok     «Su trámite fue recibido. Revise el estado en nuestro sitio oficial.»
  ok     «Le informamos que su solicitud fue aprobada. No es necesario hacer nada más.»
  ok     «Este es un aviso informativo. No responda a este mensaje.»
```

**Las tres que falla son las tres con negación, y son consejos contra el phishing.** Marca
precisamente los mensajes que enseñan a la gente a cuidarse.

> Eso convierte «¿hace falta un modelo?» en una **vara medible**: tiene que entender la negación y
> ganarle a 3 de 6, o no justifica su costo, su latencia, ni mandar el mensaje de un ciudadano a un
> tercero.

### Y dos cosas que este corpus no permite medir

| | |
|---|---|
| **Cobertura de la regla** | **0.** Las 342 estafas ya traen enlace: solo una queda muda |
| **Precisión de la regla** | **No medible.** Necesita mensajes legítimos, y no existen |

**El mismo hueco, por segunda vez.** El corpus de mensajes legítimos dejó de ser una tarea de
calibración y pasó a ser **el insumo que falta** para dos mediciones distintas.

## T4.8b — DeepSeek contra la vara, y el cableado

### El modelo pasa la vara, sonda por sonda

```
extractor                          falsas alarmas  aciertos   veredicto
------------------------------------------------------------------------------
referencia (sin modelo)            3 de 6            2/40       no sirve
DeepSeek deepseek-chat             0 de 6            1/40       PASA
JEV typesafe/jev-router            0 de 6            0/40       NO VERIFICABLE (31 fallidas)
```

**La vara eran las 6 sondas**, porque **3 de 6 son consejos contra el phishing** y el extractor de
referencia los marca. DeepSeek devuelve `pide=[]` en las seis, **con 0 llamadas fallidas**. La vara se
cumple.

**La columna de aciertos no dice nada, y hay que declararlo:** sobre 40 mensajes del corpus, el
extractor encuentra 1 «acierto» contra 2 del baseline. Ese número mide el **veredicto final**, que
exige reconocer además el reclamo —y el corpus del CSIRT es casi todo «pinche un enlace», que **no es
una petición indebida**—. **La sensibilidad sigue sin medirse bien**; ver arriba.

### JEV se descarta por costo, no por saldo

`typesafe/jev-router` **enruta a modelos pagados sin decir cuál ni a qué precio** (en la prueba derivó
a `deepseek/deepseek-v4.1-flash`). En un servicio público el costo por verificación tiene que ser **un
número**. Y su precio reportado era **`-1`**, que no es un precio.

Coste de la alternativa, medido: `deepseek-chat` a **USD 0,32 / millón de tokens de entrada** →
**≈ 0,13 CLP por mensaje**, contra **≈ 19 CLP de la respuesta de WhatsApp**: **0,7 %**. El costo no es
el argumento en contra; la opacidad sí.

### Y los **28 mensajes sin enlace** dejan de quedar mudos

El extractor ya estaba medido pero **no estaba conectado**. Cableado: `main()` arma
`CacheDeExtraccion(ExtractorLLM(...))` **solo si existe la clave**, y `conversacion.componer` lo usa
evaluando **dos veces** —la primera para saber de quién dice ser el mensaje, la segunda con la
petición puesta—.

**Lo que cambia, en números:** de las 342 estafas, **28 no traen enlace** y hasta hoy respondían
`SIN_ENLACES`. Con el extractor pasan a tener veredicto **si piden algo indebido**. Es la brecha 2 del
`doc/14-GAP.md`, y es la única forma de cubrirla: el enlace no está, así que el motor no tiene nada que
juzgar.

**Sin la clave el robot no se rompe: se degrada** al comportamiento anterior.


### Y el cableado destapó una regresión que ningún test veía

Conectar el extractor **cambió el veredicto de 74 de las 342 estafas**: las que **nombran** a la
institución (`no_coincide`) pasaban a `pide_lo_indebido`, y la respuesta **dejaba de decir que el
enlace era falso**. Peor: la medición se hizo con un extractor que **siempre** dice que pide datos,
o sea el peor caso — y el peor caso es alcanzable, porque el nivel de falsa alarma del modelo es bajo
pero no cero.

```
veredicto        antes  despues   despues del arreglo
no_coincide         74        0                    74
pide_lo_indebido     0       74                     0
tapados              0       74                     0
```

**Los 196 tests estaban verdes con la regresión dentro.** Lo encontró la medición, no un test: es la
cuarta vez en el proyecto que un número rompe algo que los tests no veían.

**Y el vocabulario se filtraba a la respuesta:** decía `pide datos_personales`. El vocabulario cerrado
es para el modelo; el ciudadano lee castellano.


### Probado por WhatsApp: las dos respuestas correctas, y la latencia

Cuatro mensajes reales, medidos contra la API de Kapso (no contra la consola), los cuatro
`outbound delivered`:

| Mensaje | Respuesta | Latencia |
|---|---|---|
| Enlace malo de BancoEstado **+** pide los datos | Nombra el enlace **y** la petición | **2 s** |
| Sin enlace, pide la clave y el RUT | `PIDE_LO_INDEBIDO`: dice de quién dice ser y qué pide | **1 s** |
| Enlace `claveunica-gob-cl.xyz` | «NO es del Estado», con la suplantación nombrada | **1 s** |
| El mismo, repetido | Idéntico | **3 s** |

**1–3 segundos con el modelo en el camino.** El costo del modelo sigue siendo **≈ 0,13 CLP**, o sea
**0,7 % de los ≈ 19 CLP** que cuesta la respuesta de WhatsApp: la latencia y el costo del extractor no
son el problema; la privacidad y la trazabilidad sí, y están tratadas.

## T4.3 — El control invertido, y la precisión

**El mismo texto de la estafa, con el enlace de la institución real.** Eso aísla una sola variable:
si el motor acusa, la causa no puede ser el texto.

```
CONTROL INVERTIDO: 211 mensajes de 342
  coincide  190  (90%)
  oficial    21  (10%)
  mudo        0   (0%)
  acusa       0   (0%)
```

**0 falsas acusaciones de 211.** Y con eso el paper tiene los dos números que necesita:

| | |
|---|---|
| **Cobertura** | **99,7 %** de las estafas recibe respuesta útil sobre el mensaje completo |
| **Precisión** | **0 falsas acusaciones de 211** sobre mensajes con enlace correcto |

**Es un control construido, no un corpus recogido.** El texto es idéntico al de una estafa real y solo
cambia el enlace, así que mide la acusación que induce **el texto** — no la que induciría un mensaje
legítimo de verdad, cuya redacción y petición son distintas. La limitación se declara.

### Y encontró un bug que ninguna otra medición vio

La única falsa acusación decía `paquete.por`. El SMS real: «falta un número de calle en el
**paquete.por** favor actualice» — **sin espacio y en minúscula**, así que la regla de «punto seguido
de mayúscula» no lo cortaba.

**La regla correcta no es una heurística: es la lista de la IANA.** Se incorporaron sus **1.437 TLD**
al paquete; ahora un host cuenta solo si su última etiqueta es un TLD de verdad. `por` y `sin` no lo
son. `cl`, `xyz`, `sbs` y `live` sí — **el phishing usa TLD reales**, así que el filtro no deja pasar
nada.

> **Tercera vez la misma lección:** la heurística falla y la fuente no. `operativos.Sin`, `paquete.por`
> y `tb.php` son el mismo error con tres caras.

## T4.2 — El índice del Estado, y el número que faltaba

**738 dominios** que el CSIRT ya publicó como fraudulentos, consultados como historia y no como
forma. Detalle en `doc/15-INDICE.md`.

```
                         la cita del CSIRT   cita + enlace del informe
  confirmado                   0   (0%)           239  (70%)
  nombra                       0   (0%)            74  (22%)
  avisa                        9   (3%)            28   (8%)
  mudo                       330  (96%)             1   (0%)
  GRAVE                        3   (1%)             0   (0%)
```

**El 97 % de las estafas recibe una respuesta útil** sobre el mensaje completo, y **el 70 % con la
alerta del Estado citada**. Una queda muda. Ninguna grave.

Y `nombra` bajó de 210 a 74 porque `CONFIRMADO` **manda**: cuando el Estado ya determinó que un
dominio es fraude, decir además de quién decía ser el mensaje es secundario.

### Lo que los tests encontraron al romperse

El índice traía **`bit.ly`** —reportado por **70 alertas**— y **`com.br`, `com.au` y `com.np`**.

Lo primero porque un acortador aloja los enlaces de todo el mundo. Lo segundo porque **`com.br` no
es un dominio: es un sufijo de registro**, y `etiqueta_registrable` reduce por etiquetas contadas sin
conocer la lista de sufijos públicos, así que `algo.com.br` se volvía `com.br`.

Confirmar cualquiera de los dos habría condenado a medio internet y a todo Brasil. **Los dos filtros
viven en la consulta, no solo en el archivo.**

> Es la misma lección de `T0.2` y de `T4.1`, por tercera vez: **el fraude vive en el contenido, no en
> el contenedor.** El dominio del acortador no es el ataque; la ruta que aloja sí.

## T4.1 — El corpus crece a 342, y aparecen dos cosas

Con el sitemap del CSIRT (**5.179 alertas**) en vez del repositorio de indicadores —que solo cubre
los códigos viejos— el corpus pasó de 45 a **342 estafas**.

```
                         la cita del CSIRT   cita + enlace del informe
  nombra                       0   (0%)           210  (61%)
  avisa                        9   (3%)           131  (38%)
  mudo                       330  (96%)             1   (0%)
  GRAVE                        3   (1%)             0   (0%)
  reconoció de quién dice ser  189                 210
```

### Hallazgo 1 — El motor inventaba dominios, y se los decía al ciudadano

El texto real de un SMS dice, sin espacio después del punto:

> «...nuestros servidores ya estan operativos**.**Sin embargo...»

**El motor leyó `operativos.Sin` como un dominio.** Igual con `seguridad.Le`, `cuenta.Esto` e
`identidad.Paraverifica`. Y como no son de la institución reclamada, la respuesta al ciudadano decía:

> «El mensaje dice ser de BancoEstado y el enlace **operativos.sin** no es de BancoEstado.»

**Un dominio que no existe, nombrado como si fuera el sitio del atacante.** Es la peor clase de error
que tiene este proyecto: una acusación sobre un dato inventado.

Se arregla cortando el host donde empieza una oración (`.Mayúscula`), respetando los dominios
escritos **todo en mayúsculas**, que sí son dominios. Y se nota en el número: **`nombra` pasó de 5 a
0 y `avisa` de 19 a 9** en la columna del fragmento — esos veredictos los estaba produciendo el ruido.

> **Lo encontró el corpus de 342, no un test unitario.** Es la cuarta vez en este proyecto.

### Hallazgo 2 — Los 3 `GRAVE`, y son la carnada

Los tres tienen la misma forma: **el mensaje nombra un dominio legítimo y el enlace malo está en otra
parte.**

| Caso | Dominio que nombra | Enlace malicioso real |
|---|---|---|
| `fph24-00951` | `interior.gob.cl` | `cloudflare-ipfs.com/ipfs/...` |
| `8fph23-00745` | `www.bancoestado.cl` | `ucmstudio.info/...` |
| `8fph23-00755` | `www.bancoestado.cl` | `ucmstudio.info/...` |

**En el mensaje completo no hay ninguno: `GRAVE = 0`.** Los tres aparecen **solo en la cita
recortada**, donde el enlace malo no está y lo único que queda es el señuelo.

Dos conclusiones, y la segunda es la importante:

1. El motor es seguro con mensajes completos, que es lo que un ciudadano reenviaría.
2. **Un mensaje incompleto puede recibir una respuesta demasiado confiada.** Si alguien manda solo la
   mitad, el motor puede decir «el enlace es del Estado» porque el único que quedó es el señuelo.

**Y eso no se arregla con una regla más.** `operativos.Sin` y `claveunica.gob.cl.xyz` son
lexicalmente idénticos: los dos son un punto y letras. Lo que los distingue es **qué pide el
mensaje** — y por eso el camino es la extracción de la petición de `T4.4`, no otra expresión regular.

> Es la justificación medida de la opción C: **la ambigüedad del dominio suelto no se resuelve
> mirando el dominio.**

## T1.8 / T1.8b — El catálogo crece, y el número se mueve

Las instituciones entraron **porque el corpus las midió**, y solo las que se pudieron **verificar por
certificado**. La progresión, sobre los mismos 45 casos:

| Catálogo | `nombra` | `GRAVE` |
|---|---|---|
| 14 instituciones, todas estatales | **0 (0 %)** | 0 |
| +8 suplantadas (Banco Ripley, BCI, Itaú, Copec, Soprole…) | **24 (53 %)** | 0 |
| +3 bancos (BancoEstado, Santander, Scotiabank) | **39 (87 %)** | 0 |

```
                         la cita del CSIRT   cita + enlace del informe
  nombra                       1   (2%)            39  (87%)
  avisa                        0   (0%)             6  (13%)
  mudo                        44  (98%)             0    (0%)
  GRAVE                        0   (0%)             0    (0%)
  reconoció de quién dice ser  38                   39
```

**De 0 a 87 % cambiando datos, no código.** El motor es el mismo: lo que cambió fue que ahora sabe
quiénes son Banco Ripley y BancoEstado.

Lo que **no** se movió, y es lo tranquilizador: **`GRAVE` sigue en 0.** En 45 estafas reales, y con
un catálogo once veces más grande que al principio, el motor nunca dio por bueno el enlace malo.

## Cómo se reproduce, y con qué se mide

```bash
python3 scripts/cosechar_alertas.py 45   # cosecha; ~2 minutos, con pausa entre consultas
python3 scripts/medir_motor.py           # mide e imprime el cuadro y los fallos
```

Solo se **lee** lo publicado con TLP:CLEAR. No se visita ningún sitio malicioso: la URL se guarda
como texto.
