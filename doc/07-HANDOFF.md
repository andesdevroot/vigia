# 07 — Handoff

## Estado actual

**T0 — validación de la hipótesis.** Nada construido salvo el esqueleto, y es a propósito: `[T0.2]`
decide si el proyecto existe.

| | |
|---|---|
| Tarea en curso | ninguna. Siguiente: **T0.2** (spike de volumen de CT) |
| Código | `src/vigia/__init__.py` vacío + `tests/test_arquitectura.py` |
| Tests | **2 verdes** |
| Gate | **`./gate.sh`** en verde |
| Árbol git | limpio |

## Último commit

`[T0.1]` Esqueleto, gate y guardián de arquitectura.

## Blockers

Ninguno técnico. **El blocker real es una medición que no se hizo:** cuántos dominios de
suplantación existen. Todo el diseño posterior depende de ese número.

## Decisiones recientes

| Fecha | Decisión |
|---|---|
| 2026-10-04 | **El proyecto arranca con un spike, no con arquitectura.** El proyecto anterior murió por no validar el insumo antes de construir; acá la primera tarea es un número |
| 2026-10-04 | **Cero dependencias en T0.1**, y hay un test que lo fija: agregar una es una decisión, no un accidente |
| 2026-10-04 | **`import vigia` no arrastra red.** Descubrimiento y consulta son cosas distintas, y mezclarlas obliga a tener internet para correr un test unitario |
