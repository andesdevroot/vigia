# task.md — cola de trabajo

`doc/` es la fuente de verdad. Acá va **qué falta y en qué estado**.

| # | Tarea | Estado |
|---|---|---|
| T0.1 | Esqueleto, gate y guardián de arquitectura | ✅ |
| T0.2 | Spike: medir el volumen real de CT | ✅ **cerrada: el canal no tiene volumen** |
| T0.3 | Doc: taxonomía de la suplantación de marcas chilenas | ⬜ |

## T0.1 — Esqueleto, gate y guardián de arquitectura ✅

`pyproject.toml` (uv, Python 3.13, cero dependencias), `gate.sh` (pytest + ruff + mypy con
`set -euo pipefail`), y `tests/test_arquitectura.py` con dos invariantes reales: **importar `vigia`
no arrastra la librería de red** (comprobado en un proceso limpio, porque en el de pytest ya podría
estar importada), y **T0.1 no agrega dependencias** — si aparece una, que sea una decisión.

## ⬜ T0.2 — Spike: medir el volumen real de CT

**Es la tarea que decide si el proyecto existe.** Sin ella no se diseña nada más.

- **Entregable:** un script que consume los logs de Certificate Transparency, filtra `.cl`, y calcula
  similitud contra la lista de dominios del Estado y de la banca chilena. Más el número.
- **Criterio de aceptación:** el conteo de dominios de suplantación, la tasa de falsos positivos
  sobre dominios legítimos, y una decisión escrita: **sigue o no sigue**.
- **Por qué no es una tarea de aplicación:** no hay interfaz ni CLI. Es un número y un documento.
- **Riesgo:** el stream de CT es grande. Si el costo de filtrarlo supera el valor del resultado, eso
  también es una respuesta.


## ✅ T0.2 — Spike: el volumen real de CT

**Cerrada con una decisión negativa, que es un resultado.** 28 consultas, 1.521 dominios, **76
coincidencias de las cuales 74 son basura** (`sii` con 3 letras y umbral 2 matchea medio internet, y
`.si` es Eslovenia). La señal real son **2–3 dominios**.

**La conclusión no es "el detector está mal": es que la suplantación no vive en el nombre del
dominio.** El phishing usa dominios desechables y pone la marca en el **contenido**. Detalle en
[`doc/02-MEDICION-CT.md`](doc/02-MEDICION-CT.md).

**El spike funcionó**: una hora de medición mató la hipótesis antes de tres semanas de construcción.

## ✅ T0.3 — Estado del arte

**Cerrada con un resultado incómodo: el espacio NO está vacío, y en Chile tampoco.**
[`doc/03-ESTADO-DEL-ARTE.md`](doc/03-ESTADO-DEL-ARTE.md).

- **Existe una tesis de la U. de Chile** sobre recolección y análisis de mensajes fraudulentos
  (202581). Es el prior art nacional más cercano y **no se pudo leer**: el repositorio está detrás
  de un muro anti-scraping.
- **La lista blanca ya está publicada** como técnica (APWG eCrime 2023), y el triaje por checklist
  también (TraceScope, arXiv 2604.21840).
- **Lo que queda limpio:** español de Chile con etiqueta no paga, **calibración medida por
  segmento** (nadie mide si el umbral deja pasar más estafas contra un grupo), y **la medición
  negativa del canal de dominio**.

**Primera acción de la tarea siguiente: conseguir la tesis 202581.** Sin leerla no se puede afirmar
novedad frente a Chile.

## ⬜ T0.4 — Conseguir y leer la tesis 202581

**Bloquea cualquier afirmación de novedad.** Vías: el repositorio con un navegador real, el autor, o
la escuela de ingeniería. Su autor probable es Javier Bustos, que habla públicamente de IA y análisis
de Internet.

## ⬜ T0.5 — ¿Es obtenible la lista de dominios del Estado?

Para la vía de certificación por lista blanca hace falta la lista completa de dominios oficiales.
Si no es obtenible ni completa, esa vía muere como las demás — y conviene saberlo antes de construir.
