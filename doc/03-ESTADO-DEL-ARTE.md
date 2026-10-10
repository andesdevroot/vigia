# 03 — T0.3: estado del arte

**2026-10-04.** Qué está ocupado, qué queda libre, y qué cambia eso en el plan.

## La tesis chilena, leída

**Trincado Muñoz, Gerardo Matías.** *Diseño e implementación de sistema automatizado de recolección
y análisis de mensajes de texto fraudulentos.* Memoria de Ingeniería Civil en Computación,
Universidad de Chile, DCC, **2024**. Guía: Eduardo Riveros Roca.
`sha256:f773f636` · 61 páginas. *(El PDF no se versiona: se guarda la cita y el hash, como el corpus.)*

**Qué hace.** Un **electrodoméstico de captura**: Raspberry Pi 5 con módems USB que recogen SMS del
aire, un clasificador **Random Forest**, base local, backend, frontend y reportes automáticos a las
autoridades.

**Qué NO hace, y es lo que importa:**

| | |
|---|---|
| Corpus público | **No.** Los datos los consiguió del **CSIRT** (con aplazamiento) y por recolección **manual**; los conteos que aparecen son de decenas de mensajes (79, 29, 108, 170…) |
| Identidad estatal | **No menciona la ClaveÚnica ni la suplantación de marca.** Cero apariciones |
| Lista blanca | **No.** Cero apariciones |
| Calibración, abstención, umbral | **No.** La palabra "precisión" no aparece |
| Modelos de lenguaje | **No.** Ni LLM, ni BERT, ni nada por el estilo |
| Sus limitaciones | **Son de hardware.** El capítulo se llama *Limitaciones de Equipamiento*: la Raspberry Pi Zero 2W no daba el procesamiento |

**Y se posiciona sola:** *"da el primer paso para futuros estudios sobre el comportamiento de las
estafas"*. Es un **precursor**, no un competidor.

## Conclusión de la lectura

**El espacio está abierto.** La tesis ocupa un lugar **adyacente** —captura física de SMS con ML
clásico— y deja intacto lo demás: el corpus público, la suplantación de identidad estatal, la
lista blanca y la calibración.

Y es **la cita que más ayuda**: un trabajo chileno que reconoce haber dado el primer paso es el mejor
marco posible para el segundo. El paper se escribe *encima* de ella, no contra ella.

**La alarma anterior era mía, y la causa fue haber leído solo el título.** T0.4 existía exactamente
para esto.

## Lo que queda libre

1. **Español de Chile, con etiqueta que no puso un anotador pagado.** Los corpus existentes son en
   inglés; la tesis chilena es un sistema, no un corpus público con medición.
2. **La calibración de la negativa medida por segmento.** No apareció en ninguno: todos miden
   precisión. **Nadie mide si el umbral deja pasar más estafas contra un segmento.**
3. **La medición negativa del canal de dominio.** Que buscar la marca en el nombre del dominio no
   tenga volumen **no está publicado**, y es un resultado con consecuencia de método.

## Lo que esto cambia

- **La idea 1 (corpus) pierde fuerza como contribución aislada.** Hay prior art chileno y hay corpus
  en inglés. El aporte tiene que ser **la calibración y la equidad del umbral**, no "un corpus más".
- **La idea 2 (lista blanca) tiene prior art** (APWG). El aporte no es el método, es **la medición
  que lo justifica** — y esa medición la tenemos hecha.
- **La idea 4 (adultos mayores) es la que queda más limpia.** Nadie de los revisados mide el efecto
  por segmento.

## Blocker

**Ninguno.** El único que había —no poder leer la tesis 202581— quedó cerrado en T0.4.
