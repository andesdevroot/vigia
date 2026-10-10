# 07 — Handoff

## Estado actual

**T0 — validación de la hipótesis.** Nada construido salvo el esqueleto, y es a propósito: `[T0.2]`
decide si el proyecto existe.

| | |
|---|---|
| Tarea en curso | ninguna. Siguiente: **T0.5** (¿es obtenible la lista de dominios del Estado?) |
| Código | `suplantacion.py` (detector, 30 tests) · `scripts/medir_ct.py` (spike) |
| Tests | **30 verdes** |
| Gate | **`./gate.sh`** en verde |
| Árbol git | limpio |

## Último commit

`[T0.4]` Leída la tesis chilena: el espacio está abierto.

## Blockers

**La hipótesis original está refutada por medición.** El canal de Certificate Transparency no
sostiene el proyecto: 2–3 dominios de 1.521. La vía muerta es **buscar la marca en el nombre del
dominio**; el phishing pone la marca en el **contenido**.

**Ninguno.** La tesis chilena se leyó (T0.4) y **deja el espacio abierto**: es un sistema de captura
física con Random Forest, sin corpus público, sin ClaveÚnica, sin lista blanca y sin calibración. Se
posiciona como precursora. Ver `doc/03-ESTADO-DEL-ARTE.md`.

## Decisiones recientes

| Fecha | Decisión |
|---|---|
| 2026-10-04 | **La tesis chilena deja el espacio abierto.** Es captura física + Random Forest; sus limitaciones son de hardware. Se cita como precursora, no como competidora |
| 2026-10-04 | **El espacio no está vacío, y en Chile tampoco.** Hay una tesis de la U. de Chile sobre mensajes fraudulentos, y la lista blanca ya está publicada (APWG). Lo que queda limpio es la **calibración por segmento** |
| 2026-10-04 | **El canal CT queda cerrado.** No por un defecto del detector —hay dos, y son corregibles— sino porque la suplantación no vive en el nombre del dominio. Ver `doc/02-MEDICION-CT.md` |
| 2026-10-04 | **El detector no se borra, se deja de usar.** La taxonomía es correcta y los dos defectos quedan documentados |
| 2026-10-04 | **El proyecto arranca con un spike, no con arquitectura.** El proyecto anterior murió por no validar el insumo antes de construir; acá la primera tarea es un número |
| 2026-10-04 | **Cero dependencias en T0.1**, y hay un test que lo fija: agregar una es una decisión, no un accidente |
| 2026-10-04 | **`import vigia` no arrastra red.** Descubrimiento y consulta son cosas distintas, y mezclarlas obliga a tener internet para correr un test unitario |
