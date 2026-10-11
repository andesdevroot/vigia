# 14 — La brecha, medida, y las opciones para cerrarla

## 1. Qué está pasando en Chile, con números

| Dato | Fuente |
|---|---|
| **1 de cada 4 chilenos cayó** en una estafa por SMS | ESET Latam, vía [Diario El Día, 21-08-2026](https://www.diarioeldia.cl/noticias/2026/08/21/148405-una-de-cada-4-personas-en-chile-cayo-en-estafa-sms-por-cobros) |
| **La estafa por SMS subió 30 %** en un año | [Diario El Día, 06-08-2026](https://www.diarioeldia.cl/noticias/2026/08/06/146974-aumenta-30por_ciento-la-estafa-por-sms-en-chile-y-expertos-alertan-no-atacan-tu-inteligencia) |
| **89,7 % de los usuarios de internet usa WhatsApp** | FNE, vía [T13](https://www.t13.cl/noticia/tendencias/whatsapp-cobrara-entre-15-22-por-mensaje-quienes-se-les-aplicara-medida-2-10-2026) |
| Hay una **«Ley Neme»** en trámite contra el smishing | [BioBioChile, 19-08-2026](https://www.biobiochile.cl/noticias/sociedad/curiosidades/2026/08/19/buscan-crear-ley-neme-para-combatir-el-smishing-4-faciles-consejos-para-no-ser-una-victima.shtml) |

**Cita para el paper:** *«No atacan tu inteligencia»* — es lo que dicen los expertos sobre por qué cae
la gente. No es un problema de personas descuidadas; es un problema de **falta de verificación
disponible en el momento**.

### Las campañas más masivas, por suplantación

| Campaña | Cómo se ve | Fuente |
|---|---|---|
| **Cobros y servicios básicos** | «tiene un pago pendiente» | la que más cae: 25 % |
| **Paquete retenido (Correos de Chile)** | «No podemos entregar su paquete» | [T13](https://www.t13.cl/noticia/nacional/no-podemos-entregar-su-paquete-alerta-por-falso-mensaje-texto-se-hace-pasar-por-04-07-2023), [CSIRT 8FPH23-00847](https://csirt.gob.cl/alertas/8fph23-00847-01/) |
| **Premios y sorteos (Copec, aniversarios)** | «canjea tu regalo» | CSIRT FPH25-01054 |
| **Beneficios estatales falsos** | bonos, IFE, **bono del sistema frontal** | [TVN](https://www.tvn.cl/actualidad-y-tendencias/datos-y-servicios/alerta-por-estafas-con-falsos-bonos-del-sistema-frontal-asi-roban-datos) |
| **Bancos: bloqueo o actividad inusual** | «su tarjeta fue bloqueada» | corpus `T1.7`: **21 de 45** |
| **TAG y multas de tránsito** | «problema con su TAG» | MOP / prensa |
| **SIM swapping / portabilidad** | el teléfono se queda sin señal | [SERNAC](https://www.sernac.cl/portal/604/w3-article-86565.html) |
| **Falsos ejecutivos** | llamada, sin enlace | caso Amparo Noguera: **$900 millones** |

**Y el 100 % de las 45 alertas del CSIRT que cosechamos suplanta a un banco o a una empresa.
Ninguna suplanta a un organismo del Estado.** Es un dato incómodo y hay que decirlo.

## 2. La brecha son **tres**, no una

### Brecha 1 — El enlace está, pero no sabemos de quién dice ser

Medido: **6 de 45 (13 %)** de las estafas del CSIRT caen en `AJENO` —«el enlace no es del Estado»—
porque el motor **no reconoce ninguna institución reclamada** en el texto. Dice algo cierto y débil.

Se cierra con **catálogo y mejores alias**: es el trabajo de `T1.8`, y es mecánico.

### Brecha 2 — **No hay enlace.** Y acá el motor se queda mudo

Es lo que el usuario del proyecto vio antes que yo. Casos reales:

```
«Su cuenta será bloqueada. Llame al 22 555 1234»          → SIN_ENLACES, el motor no dice nada
«Deposite en la cuenta corriente 12345678»                 → SIN_ENLACES
«Su paquete no pudo entregarse, responda este mensaje»     → SIN_ENLACES
SIM swapping: una solicitud de portabilidad, sin mensaje    → el motor ni se entera
```

**Este es el hueco de verdad.** El motor solo sabe de enlaces, y buena parte del fraude chileno no
usa enlace: usa **una petición**. Pedir la clave, pedir datos, pedir una transferencia, pedir una
llamada.

### Brecha 3 — Tenemos 785 indicadores del Estado y no los usamos

El CSIRT publica `github.com/csirtcl/Fraude` con **785 informes de IoC**, y cada uno trae las URLs y
los dominios que **el Estado ya determinó maliciosos**. Hoy el motor no los mira: juzga el enlace por
su forma, no por su historia.

Eso es gratis, determinista, y **cita al Estado como evidencia** en vez de predecir nada.

## 3. Las opciones

### Opción A — Buscar el enlace en los indicadores del Estado

**Qué es:** si el enlace del mensaje está en los 785 informes del CSIRT, es fraude, y se responde con
la cita de la alerta.

| | |
|---|---|
| **Costo** | bajo: es un índice y una búsqueda por dominio |
| **Determinista** | sí, entero |
| **Auditable** | sí, y la evidencia la puso el Estado |
| **Novedad** | media: las listas de bloqueo existen; **citar la alerta al ciudadano, no** |
| **Cubre** | solo mensajes con enlace, y solo campañas ya reportadas |

### Opción B — Un LLM que extrae **de quién dice ser** el mensaje

**Qué es:** el LLM lee el texto y responde una sola cosa: *«¿de qué institución dice ser? Devuelve el
nombre o NADA»*. Después decide el catálogo de siempre.

| | |
|---|---|
| **Costo** | bajo |
| **Auditable** | **sí, y se puede medir**: la extracción se evalúa contra el corpus etiquetado |
| **Novedad** | baja por sí sola |
| **Cubre** | la brecha 1, y mejora los alias («banco de estado», «BCI», «Scotiabank») |

### Opción C — Un LLM que extrae **qué pide** el mensaje, y una regla que decide

**Es la que creo que es el núcleo.** El LLM llena un formulario de campos cerrados, y **ninguna
decisión la toma él**:

```json
{
  "dice_ser": "BancoEstado",
  "pide": ["clave", "datos_personales", "llamar_telefono"],
  "urgencia": "bloqueo",
  "tiene_enlace": false
}
```

Y la regla que decide es **una frase escrita, citable y verificable**:

> **Ninguna institución pide su clave, sus datos personales ni una transferencia por mensaje.** Lo
> dicen ellas mismas: el SII, el Servel, el BancoEstado y la ANCI publican exactamente eso.

| | |
|---|---|
| **Costo** | bajo (una llamada por mensaje, centavos) |
| **Determinista** | **la decisión sí**; el LLM solo rellena campos |
| **Auditable** | sí: se audita el formulario y se audita la regla |
| **Novedad** | **alta, si se plantea así**: no es «una IA que detecta estafas» |
| **Cubre** | **la brecha 2**, que es la grande |

**La clave del diseño:** el LLM **propone**, la regla **decide**. Y la precisión del extractor se
mide contra un corpus etiquetado, que ya existe y es público.

### Opción D — Leer capturas de pantalla

| | |
|---|---|
| **Cubre** | la gente manda fotos, no texto |
| **Costo** | medio (visión, más caro que texto) |
| **Riesgo** | leer una imagen y **alucinar** el dominio que «ve» |

**Con un límite duro:** de una imagen se puede extraer **el texto**, y el texto pasa por el mismo
motor determinista. **Nunca el veredicto de la imagen.** Así una alucinación de visión no puede
inventar un dominio y declararlo oficial.

### Opción E — Un LLM que decide si es fraude

**Es la que ya existe y por eso la descarto.** [WhatsPhish](https://peer.asee.org/whatsphish-whatsapp-ai-phishing-detector-chatbot.pdf),
[el chatbot colombiano](https://revistas.unicordoba.edu.co/index.php/rii/article/view/4356) y
[ScanMessage](https://www.indiehackers.com/post/scanmessage-ai-fraud-detection-for-whatsapp-sms-in-latin-america-f9e1f1adb3)
hacen eso. No es novedoso, no es auditable, y **es peor que lo que ya tenemos**: un clasificador
probabilístico no puede decir «no sé», y este proyecto entero se sostiene sobre poder decirlo.

## 4. Qué opino

**Que tu instinto es correcto en el diagnóstico y hay que corregirlo en la solución.**

Correcto: **la brecha está donde el motor no llega, y es la mayoría del fraude.** El motor actual
cubre mensajes con enlace; el fraude chileno que más cae usa **una petición**.

Corrección: **no con un LLM que juzgue, sino con un LLM que rellene un formulario.** La diferencia no
es de estilo, es la diferencia entre un paper que se sostiene y uno que se cae:

| Si el LLM decide | Si el LLM extrae |
|---|---|
| no se puede auditar | se audita campo por campo |
| no se puede reproducir | la regla es la misma siempre |
| «una IA que detecta estafas»: **ya existe** | **extracción estructurada + decisión determinista: no** |
| no puede decir «no sé» | la abstención sigue siendo un veredicto |

**Mi recomendación: A + C, en ese orden.** A es media tarde de trabajo y ya tiene los datos. C es el
núcleo nuevo, y **la regla que lo hace funcionar es una frase que las instituciones publican**.

D después, con el límite de que de la imagen solo sale texto.

**Y la tesis del paper quedaría así:**

> El cuello de botella del fraude ciudadano **no es clasificar**: es que la mayoría de los mensajes
> fraudulentos **no traen nada que clasificar**. Un motor que solo juzga enlaces acierta en el 87 %
> de las estafas publicadas y **no dice nada** en las que no traen enlace. La contribución es un
> motor que **extrae la petición** con un modelo y la juzga con una **regla escrita**, manteniendo la
> abstención como veredicto de primera clase — y la medición de cuánto cubre cada capa.

## 5. Tres problemas honestos, antes de escribir una línea

### 1. La privacidad se rompe, y hay que decirlo

Hoy el proyecto promete: **«el mensaje no se guarda»**. Si el texto se le manda a un LLM externo,
**el contenido sale de nuestro servidor**. Puede que no se guarde, pero se transmite a un tercero, y
eso **no es lo que prometimos**.

Tres salidas, y hay que elegir una **antes** de construir:

1. **Decirlo** en el mensaje de bienvenida: «para analizarlo se lo pasamos a un modelo; no lo
   guardamos». Honesto, y probablemente suficiente.
2. **Modelo local.** Nada sale del servidor, y el costo por mensaje sube.
3. **Solo extraer y descartar en el mismo proceso**, sin retención, con un proveedor que no entrene
   con los datos. Es lo que hacen los que se lo toman en serio.

### 2. «IA que detecta estafas» ya existe, y hay que citarlo

Dos papers y una startup. La novedad **no puede** ser el detector. Tiene que ser la arquitectura:
extracción estructurada, decisión determinista, abstención medida, y la cita del Estado como
evidencia.

### 3. La calibración sigue bloqueada, pero menos

Decir «0 falsas acusaciones» sin un corpus de mensajes **legítimos** no tiene denominador. Sin las 20
personas, hay un camino:

- **El control invertido.** Cada mensaje del corpus, con su enlace reemplazado por **el de la
  institución real que suplanta**. Mismo texto, enlace correcto. No es un corpus de mensajes
  legítimos —es construido y hay que declararlo—, pero **aísla la variable**: cualquier falsa
  acusación que aparezca viene del extractor, no del texto.
- **Y crecer el corpus fraudulento**: el CSIRT tiene **5.179 alertas** y 785 informes de IoC. Hoy
  cosechamos 45. Se pueden cosechar **300 o 400**, y eso sí es un conjunto de evaluación en serio.

## 6. Lo que yo haría ahora, en orden

| # | Qué | Por qué primero |
|---|---|---|
| 1 | **Cosechar 300+ alertas** en vez de 45 | da un conjunto de evaluación de verdad, y ya está la maquinaria |
| 2 | **Opción A**: el índice de IoC del Estado | media tarde, determinista, y cita al Estado |
| 3 | **El control invertido** | da el denominador que falta para hablar de falsas acusaciones |
| 4 | **Opción C**: el extractor de la petición + la regla | el núcleo nuevo |
| 5 | Decidir **qué modelo** midiendo, no por gusto | DeepSeek y JEV, contra el corpus, y gana el que acierte |

**El paso 5 es importante y no lo salto:** no tenemos ni una medición de JEV en este proyecto. Elegir
el modelo por preferencia sería exactamente el error que este proyecto evita en todo lo demás.
