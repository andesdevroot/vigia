# 07 — Handoff

## Estado actual

**T0 — validación de la hipótesis.** Nada construido salvo el esqueleto, y es a propósito: `[T0.2]`
decide si el proyecto existe.

| | |
|---|---|
| Tarea en curso | ninguna. Siguiente: **T0.4** (leer la tesis 202581) |
| Código | `suplantacion.py` (detector, 30 tests) · `scripts/medir_ct.py` (spike) |
| Tests | **30 verdes** |
| Gate | **`./gate.sh`** en verde |
| Árbol git | limpio |

## Último commit

`[T0.3]` Estado del arte: el espacio no está vacío, y en Chile tampoco.

## Blockers

**La hipótesis original está refutada por medición.** El canal de Certificate Transparency no
sostiene el proyecto: 2–3 dominios de 1.521. La vía muerta es **buscar la marca en el nombre del
dominio**; el phishing pone la marca en el **contenido**.

**El espacio no está vacío.** Existe una tesis de la U. de Chile sobre mensajes fraudulentos y **no
se pudo leer** (muro anti-scraping). Sin leerla no se puede afirmar novedad frente a Chile, y eso
bloquea el pivote. Ver `doc/03-ESTADO-DEL-ARTE.md`.

## Decisiones recientes

| Fecha | Decisión |
|---|---|
| 2026-10-04 | **El espacio no está vacío, y en Chile tampoco.** Hay una tesis de la U. de Chile sobre mensajes fraudulentos, y la lista blanca ya está publicada (APWG). Lo que queda limpio es la **calibración por segmento** |
| 2026-10-04 | **El canal CT queda cerrado.** No por un defecto del detector —hay dos, y son corregibles— sino porque la suplantación no vive en el nombre del dominio. Ver `doc/02-MEDICION-CT.md` |
| 2026-10-04 | **El detector no se borra, se deja de usar.** La taxonomía es correcta y los dos defectos quedan documentados |
| 2026-10-04 | **El proyecto arranca con un spike, no con arquitectura.** El proyecto anterior murió por no validar el insumo antes de construir; acá la primera tarea es un número |
| 2026-10-04 | **Cero dependencias en T0.1**, y hay un test que lo fija: agregar una es una decisión, no un accidente |
| 2026-10-04 | **`import vigia` no arrastra red.** Descubrimiento y consulta son cosas distintas, y mezclarlas obliga a tener internet para correr un test unitario |
