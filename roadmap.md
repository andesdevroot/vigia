# roadmap.md — hacia dónde crece vigia

**2026-10-12.** Vista de alto nivel. `task.md` tiene la cola; acá está **el porqué y el orden**.

---

## El invariante que no cambia nunca

> **La IA propone. El determinismo decide.**

Todo lo de abajo crece **alrededor** de eso, nunca a través. Un veredicto que un ciudadano puede
accionar —«este enlace no es de tu banco»— tiene que ser **reproducible, citable y auditable**. Si
una mejora rompe eso, no es una mejora: es otro producto.

**Corolario que hay que decir en voz alta:** el motor **no se entrena**. No es un pendiente, es el
diseño. El modelo de lenguaje llena un formulario de vocabulario cerrado; la regla decide.

---

## Dónde estamos

| | |
|---|---|
| **Funciona** | Probado por WhatsApp: 4 mensajes reales, los 4 entregados, **1–3 segundos** |
| **Medido** | **99,7 %** de cobertura sobre 342 estafas reales · **0 falsas acusaciones de 211** |
| **Verificado** | **220 tests**, sin red, en ~3 s. El núcleo de decisión es stdlib y un test lo impone |
| **Empaquetado** | Imagen, chequeo de salud, puerto por entorno. **Listo para desplegar** |
| **Publicado** | Repositorio público, Apache-2.0, corpus CC BY 4.0 |

**Lo que falta no es motor. Es que lo use gente que no seas tú.**

---

## La pregunta del entrenamiento, y por qué la respuesta es incómoda

Las dos rutas que planteaste tienen respuesta medida. Conviene verla antes de invertir semanas.

### Ruta A — «buscar más phishing en la web»

**Ya se hizo, y dio cero.**

```
350 intentos de cosecha más allá de las 342  ->  0 mensajes nuevos
rendimiento de los prefijos de alerta que quedan  ->  ~1 %
techo realista  ->  ~400
```

El CSIRT publica **5.179 alertas** y de ahí salieron 342 mensajes usables. **El techo es una
propiedad de la fuente, no del esfuerzo.** Y hay fuentes que sí faltan por probar (URLhaus, PhishTank,
prensa, redes), pero **el retorno es marginal**: el motor ya cubre el 99,7 % de lo que hay.

**Más estafas no arreglan nada. El motor ya las detecta.**

### Ruta B — «un algoritmo profundo propio»

**Rompería lo que sostiene el paper, y no ataca el hueco.**

| Si el modelo decide | Si el modelo extrae |
|---|---|
| No se puede auditar | Se audita campo por campo |
| No se puede reproducir | La regla es la misma siempre |
| «Una IA que detecta estafas»: **ya existe** | **Extracción estructurada + decisión determinista: no** |
| No puede decir «no sé» | La abstención es un veredicto |

Y hay un problema más grande: **no hay con qué entrenarlo.** El corpus es de **una sola clase**: 342
estafas y **cero mensajes legítimos**. Una sola clase no entrena un clasificador.

### El hueco real, y es el mismo para todo

> **No existe un corpus público de mensajes legítimos chilenos.**
> Eso bloquea **dos** mediciones, y bloquea también cualquier entrenamiento serio.

**Ese es el trabajo que falta, y no se consigue raspando la web.** Se consigue con **personas** que
compartan los mensajes que **sí** son de su banco.

### Dónde un modelo SÍ ayudaría

| | Qué necesita | Estado |
|---|---|---|
| **El extractor** (entender negación y modismos chilenos) | El conjunto de conformidad, más grande | Se puede crecer hoy |
| **Reemplazar la API por un modelo local** | Datos etiquetados | **Bloqueado por el corpus legítimo** |
| **Imágenes** | Nada: el enlace está escrito en la imagen | Se resuelve con **OCR local**, sin modelo |

**El modelo local es la dirección correcta y la más ambiciosa**: elimina el costo por mensaje y
**elimina el problema de privacidad del §4.7** — nada sale del servidor. Pero está bloqueado por lo
mismo que todo lo demás.

---

## Las fases

### Fase 1 — Que otros puedan usarlo

**Meta: que alguien que no seas tú lo use, y que tú te enteres si se rompe.**

| | |
|---|---|
| **T5.1** Desplegar | ✅ código listo; **falta subirlo** |
| **T5.2** Imágenes por OCR local | ✅ **hecho.** Y los audios ya venían transcritos por Kapso |
| **T5.4** CI en GitHub Actions | ✅ **hecho.** Corre el gate, y construye y levanta la imagen |
| **T5.5** Saber si está vivo | Un servicio caído se ve igual que nadie usándolo |
| **T5.3** Refresco del índice | El 70 % de los `CONFIRMADO` sale de una foto que se genera a mano |

**Sin esta fase, publicar el post manda gente a un número muerto o a un callejón sin salida.**

### Fase 2 — Que sea confiable de verdad

**Meta: cerrar los dos huecos que el paper declara como fallo.**

| | |
|---|---|
| **Corpus de mensajes legítimos** | **El bloqueo raíz.** Sin él, «0 falsas acusaciones» no tiene denominador real |
| **Sensibilidad rediseñada** | ~40 mensajes etiquetados a mano. Hoy la métrica mide otra cosa, y está declarado |
| **Conjunto de conformidad más grande** | 6 sondas es una vara, no un benchmark |
| **T5.6** El hueco de privacidad del transporte | Meta y Kapso ven el mensaje crudo antes de la redacción |

**Sin esta fase, el paper tiene un punto débil que un revisor va a encontrar.**

### Fase 3 — Que viva

**Meta: que funcione sin ti, y que alguien lo pague.**

| | |
|---|---|
| **El número +56** | Hoy es un sandbox de EE.UU. Una herramienta chilena antiestafa con número gringo es ella misma sospechosa |
| **El experimento de `T3.1`** | 20 personas × 3 mensajes. Diseñado, sin correr. **Mide qué fracción de los reenvíos trae el enlace**, y ese número decide la tesis |
| **El CSIRT** | Publican 5.179 alertas que no usa nadie. Una herramienta ciudadana sobre sus datos **es su caso de éxito** |
| **Quién paga los 19 CLP** | ≈ 19 CLP por respuesta, 0 de ingreso. **Es un bien público sin financista, y es el problema abierto** |

### Fase 4 — Investigación

**Meta: el segundo paper, y lo que las mediciones abran.**

| | |
|---|---|
| **La vida media del índice** | **¿Cuánto dura un dominio de fraude publicado por el Estado?** Nadie lo ha medido. Barato, nuevo, y no depende de conseguir más corpus |
| **Modelo local destilado** | Elimina costo y problema de privacidad. **Bloqueado por la Fase 2** |
| **Segundo paper** | «Qué se puede medir con lo que el Estado publica, y qué no» |

---

## El orden, y por qué

```
Fase 1  ->  Fase 3  ->  Fase 2  ->  Fase 4
usarlo      que viva     medirlo     investigarlo
```

**La Fase 1 va primero** porque sin ella no hay usuarios, y sin usuarios la Fase 2 no tiene de dónde
sacar mensajes legítimos.

**La Fase 3 va antes que la 2**, y es contraintuitivo: **el corpus legítimo sale de tener usuarios**,
no de medir mejor. Las 20 personas del experimento son el insumo, no el resultado.

**La Fase 2 cierra el paper.** Cuando exista el corpus legítimo, la sensibilidad se rediseña y la
sección de validez deja de tener huecos.

**La Fase 4 es lo que se abre después**, y el modelo local es la pieza más ambiciosa: haría el
sistema privado de verdad y gratis de operar.

---

## Lo que NO vamos a hacer, y por qué

| | |
|---|---|
| **Entrenar un clasificador de estafas** | El corpus es de una sola clase, y el veredicto dejaría de ser auditable |
| **Cambiar el motor por uno más «profundo»** | El motor no es el punto débil: cubre el 99,7 % con 0 falsas acusaciones |
| **Perseguir las 1.500 muestras** | Ya se midió: el techo es ~400, y es de la fuente |
| **Modelos de visión para las imágenes** | El enlace **está escrito** en la captura. **OCR local es más barato y no filtra** datos personales |
| **Prometer privacidad total** | Meta ve el mensaje, como cualquier WhatsApp. **Se dice, no se esconde** |
| **Reintentos al enviar** | Decisión tomada: reintentar lo que no supimos leer no lo vuelve legible |

---

## La prueba de que una fase terminó

| Fase | Termina cuando |
|---|---|
| **1** | Un desconocido lo usa, y tú te enteras si se cae |
| **2** | El paper puede decir la exactitud contra mensajes legítimos, con denominador |
| **3** | Funciona una semana sin que nadie lo toque, y hay quien pague los mensajes |
| **4** | Hay un segundo resultado medido que nadie tenía |

**Y la meta de todo esto, en una frase:**

> **Que un chileno cualquiera le reenvíe el mensaje raro a un número, y reciba una respuesta en la que
> puede confiar.**
