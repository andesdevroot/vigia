# 07 — Handoff

## Estado actual

**T0 — validación de la hipótesis.** Nada construido salvo el esqueleto, y es a propósito: `[T0.2]`
decide si el proyecto existe.

| | |
|---|---|
| Tarea en curso | ninguna. Siguiente: **T0.3** (estado del arte) antes de pivotar |
| Código | `suplantacion.py` (detector, 30 tests) · `scripts/medir_ct.py` (spike) |
| Tests | **30 verdes** |
| Gate | **`./gate.sh`** en verde |
| Árbol git | limpio |

## Último commit

`[T0.2]` Spike de CT: el canal no tiene volumen.

## Blockers

**La hipótesis original está refutada por medición.** El canal de Certificate Transparency no
sostiene el proyecto: 2–3 dominios de 1.521. La vía muerta es **buscar la marca en el nombre del
dominio**; el phishing pone la marca en el **contenido**.

**Lo que sigue no es código: es decidir si el pivote tiene espacio.** De ahí T0.3.

## Decisiones recientes

| Fecha | Decisión |
|---|---|
| 2026-10-04 | **El canal CT queda cerrado.** No por un defecto del detector —hay dos, y son corregibles— sino porque la suplantación no vive en el nombre del dominio. Ver `doc/02-MEDICION-CT.md` |
| 2026-10-04 | **El detector no se borra, se deja de usar.** La taxonomía es correcta y los dos defectos quedan documentados |
| 2026-10-04 | **El proyecto arranca con un spike, no con arquitectura.** El proyecto anterior murió por no validar el insumo antes de construir; acá la primera tarea es un número |
| 2026-10-04 | **Cero dependencias en T0.1**, y hay un test que lo fija: agregar una es una decisión, no un accidente |
| 2026-10-04 | **`import vigia` no arrastra red.** Descubrimiento y consulta son cosas distintas, y mezclarlas obliga a tener internet para correr un test unitario |
