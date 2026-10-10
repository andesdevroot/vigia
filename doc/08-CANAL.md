# 08 — El canal: por dónde entra la protección

## El error de la idea 1

La extensión de navegador **sirve en escritorio y no en el teléfono**, que es donde ocurre el fraude.

| Plataforma | ¿Acepta extensiones? |
|---|---|
| Chrome, escritorio | Sí |
| **Chrome, Android** | **No** |
| Safari, iOS | Sí, pero hay que activarlas a mano en Ajustes |

El fraude de ClaveÚnica llega por **SMS y WhatsApp al teléfono**. Una protección que solo existe en el
escritorio no cubre a la gente que recibe el ataque.

**El detector estaba bien. El canal estaba mal.**

## La regla

> **El gesto tiene que ser uno solo, y ya conocido.**

El usuario chileno ya sabe **reenviar** un mensaje: lo hace con las cadenas. No sabe instalar
extensiones, y nadie se lo va a explicar.

**Corolario:** la interfaz es el reenvío, no la instalación.

## Las tres formas, ordenadas por fricción

| | Forma | Instalaciones | Gestos | Funciona en |
|---|---|---|---|---|
| 1 | Reenviar a un número (WhatsApp) | **0** | 1 | cualquier teléfono |
| 2 | App «Trámites» con links oficiales | 1 | 2 | Android / iOS |
| 3 | Extensión de navegador | 1 | 3 | **solo escritorio** |

### Forma 1 — Reenviar a un número

> «¿Te llegó un mensaje raro? Reenvíalo al 9-XXXX-XXXX y en 5 segundos te dice si es real.»

- Un gesto: mantener apretado → **Reenviar**. El mismo que ya usa con las cadenas.
- Funciona en cualquier teléfono. No hay nada que instalar ni que actualizar.
- **Privacidad vendible:** el robot **no lee los chats**. WhatsApp no se lo permite: solo ve lo que el
  usuario le manda. Eso es un hecho técnico, no una promesa.
- Usa el mismo motor ya diseñado (lista `.gob.cl`, homoglifos, clasificación).

### Forma 2 — App «Trámites»

No es un navegador. Es una lista de ~20 trámites con el link oficial **escrito adentro**.

> El eslogan es la función: **«no abras el link del SMS, entra por acá».**

En Android, si se comparte un link a la app, la app dice si es oficial — **compartir** también es un
gesto que ya existe. Es el mismo trato de la app del banco: se instala porque el beneficio es obvio,
no porque haya que cambiar de costumbre.

### Forma 3 — La extensión

Solo escritorio. **No es el producto: es un accesorio.** Se hace al final, o no se hace.

## Lo que NO se hace

| Idea | Por qué no |
|---|---|
| Navegador propio | Nadie cambia de navegador |
| Teclado o servicio de accesibilidad | Google Play restringe ese permiso, y asusta |
| App que lea las notificaciones | Nadie acepta ese permiso |

## Lo que el Estado ya tiene, y el hueco

| Canal | Qué responde | Cuándo |
|---|---|---|
| [CiberLupa](https://ciberlupa.anci.gob.cl) | ¿mis datos **ya** se filtraron? | **después** |
| [Reporte Ciudadano](https://csirt.gob.cl/reportar/personas/) | denunciar un sitio | **después** |
| 1510 | teléfono, con humano | a demanda |
| — | **¿aprieto este link?** | **antes** |

**El Estado cubre el después. La pregunta de antes no la contesta nadie.** Es la misma tesis de
siempre: se le pide al ciudadano que mire la URL con el ojo.

## Costo, sin inventar

WhatsApp pasó a **cobrar la conversación de servicio**. Falta medir el precio por verificación. Hasta
no medirlo, la forma 1 es una hipótesis, no un negocio.

## Próximo

`T0.8` — qué expone la API Pública de Ciberseguridad de ANCI (`anci.gob.cl/api/v1/docs`). La página
no carga sin JavaScript, así que **no se sabe todavía**. Si entrega alertas o indicadores, la
herramienta se construye **encima del Estado en vez de competir con él**.
