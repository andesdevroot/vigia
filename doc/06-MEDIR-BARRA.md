# 06 — T0.7: medir el mal uso de la barra

**2026-10-04.** Diseño listo. **El número no se pudo obtener: blocker de acceso, declarado.**

## El diseño, que es lo que queda hecho

**La pregunta:** ¿cuántos sitios que **no** son del Estado muestran la barra?

**Por qué es la pregunta correcta.** T0.6 demostró **por inspección de cabeceras** que la barra es una
imagen pública sin atadura al dominio: cualquiera la copia. Eso ya es un hecho, no hace falta medirlo.
Lo que falta es la **magnitud**: *"es falsificable en teoría"* es un argumento; *"N sitios la usan sin
ser del Estado"* es un resultado.

**El método, en tres pasos:**

1. **Buscar páginas que carguen el recurso de la barra** (`media.anci.gob.cl/.../ANCI_*.svg`).
2. **Restar** los dominios que terminan en `.gob.cl` — esos son legítimos por definición (T0.5).
3. **Contar lo que queda**, y listar los dominios.

Ni un paso más. No hay crawling masivo, no hay usuarios, no hay datos personales.

## El blocker

**Hace falta un índice de subrecursos —qué página cargó qué archivo— y no hay uno abierto.**

| vía | estado |
|---|---|
| **urlscan.io** (indexa los recursos que carga cada página) | La búsqueda por `filename:` devolvió **0**, y las consultas por comodín **`403 Forbidden`**: la API de búsqueda que sirve **necesita clave** |
| **Common Crawl** | No sirve: sus registros traen enlaces de la página, **no los subrecursos** que carga. La barra es una imagen, así que es invisible ahí |
| **Rastrear `.cl`** | Necesita una lista semilla y tiempo de crawleo. Posible, pero es infraestructura, no un spike |
| **Buscadores** | Indexan texto, no el código fuente de las páginas. No responden "quién carga este archivo" |

**No inventé el número.** Un método malo que devuelve un número es peor que un blocker declarado:
daría una cifra que parece un resultado y no lo es. Es la misma regla de T0.3.

## Las dos salidas, y las dos son gestiones

1. **Clave de urlscan.io** — gratis, con registro. Cinco minutos. **Es la vía recomendada:** su API
   está hecha exactamente para esta pregunta, y ya indexa recursos cargados.
2. **Rastrear una muestra de `.cl`.** Más control y ningún tercero, pero hay que construir el rastreo
   y elegir la muestra — y entonces la completitud pasa a ser discutible.

## Lo que no cambia

**El hallazgo de T0.6 se sostiene sin este número**: `access-control-allow-origin: *`, cero ataduras
al dominio, verificado en las cabeceras. El paper puede escribirse con eso. **El número agrega
magnitud, no existencia.**
