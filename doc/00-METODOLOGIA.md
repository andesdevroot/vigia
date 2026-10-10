# 00 — Metodología de trabajo

**v1.0 · 2026-10-04**

## Spec-Driven Development

- **`doc/` es la fuente de verdad**: qué se construye, por qué, y con qué criterios.
- **`task.md` es la cola de trabajo**: pendientes y estado.
- El código se escribe para cumplir la especificación. Si la spec cambia, se actualiza `doc/` en el
  mismo commit o en uno previo.

## TDD estricto: RED → GREEN → REFACTOR

**RED** un test que falle y demuestre la carencia · **GREEN** el código mínimo que lo pasa ·
**REFACTOR** limpiar con la suite en verde.

```
leer doc/ → escribir test → uv run pytest (RED) → implementar
          → uv run pytest (GREEN) → refactor → commit
```

## Commits atómicos

Uno por tarea completada. Si no cabe en un commit, **se divide la tarea** — no se parte el commit.

## Verificación

**El gate es un solo comando: `./gate.sh`** (pytest + ruff + mypy, con `set -euo pipefail`). **No se
commitea si el gate no pasa.**

**Antes de un cambio transversal, se leen los puntos de uso.** Renombrar, cambiar la forma de un
modelo o tocar números que otros tests fijan exige buscar los llamadores *antes* de editar. Suponer
la forma del código existente es la causa más frecuente de reintentos, y es el error que más se
repitió en el proyecto anterior: **tres veces un reemplazo masivo rompió algo que el test encontró
después.** El test es la red, no el método.

**Los invariantes transversales viven en `tests/test_consistencia.py`**, no dispersos por tarea.

## Regla de oro

> **Nunca hacer commit con tests rojos.**

## Handoff entre sesiones

**Al iniciar:** leer `task.md` y `doc/07-HANDOFF.md` **antes** de escribir código.
**Al cerrar:** actualizar los dos, **en el mismo commit que cierra la tarea**.

**No citar el hash del propio commit.** Un commit no puede contener su propio hash: escribirlo lo
cambia, y corregirlo lo cambia otra vez. La tarea en curso se referencia por su **tag** (`[T0.1]`);
los hashes se listan solo para commits **anteriores**, que ya son inmutables.

## Definición de terminado

1. El test se escribió antes y se verificó en **rojo**.
2. `uv run pytest` en verde, sin tests saltados.
3. `./gate.sh` en verde.
4. REFACTOR hecho; la suite sigue verde.
5. `task.md` y `doc/07-HANDOFF.md` actualizados **en el mismo commit**.
