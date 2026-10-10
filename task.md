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

## ⬜ T0.5 — ¿Es obtenible la lista de dominios del Estado?

Para la vía de certificación por lista blanca hace falta la lista **completa** de dominios oficiales.
Si no es obtenible ni completa, esa vía muere como las demás — y conviene saberlo antes de construir.

- **Entregable:** la lista, su origen, y si es completa o parcial. Más una decisión escrita.
- **Criterio de aceptación:** cuántos dominios `.gob.cl` hay, de dónde salen, y si un dominio oficial
  podría faltar (lo que produciría un falso negativo en la certificación).
- **Riesgo:** que la lista no exista publicada y haya que construirla por rastreo, con lo que la
  completitud pasa a ser indemostrable.

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

## ⬜ T0.6 — El paper de medición

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
