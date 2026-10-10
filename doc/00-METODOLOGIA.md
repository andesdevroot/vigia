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

## Un título no es una fuente

**La regla:** antes de afirmar algo sobre un documento, un dato o un sistema, **abrirlo y leerlo**.
Un título, un resumen, un fragmento de buscador o el recuerdo de algo leído antes **no alcanzan**.

**Por qué está escrita acá.** En este proyecto pasó cuatro veces, y las cuatro la conclusión cambió
al mirar la fuente:

| se dijo | la fuente decía |
|---|---|
| "el canal de CT tiene volumen" | 2–3 dominios de 1.521 |
| "el espacio está ocupado por una tesis chilena" | la tesis hace captura física con Random Forest; no ocupa nada nuestro |
| "la lista blanca es una idea nuestra" | el Estado chileno la implementó hace años (ANCI controla `.gob.cl`) |
| "la estimación de costo es X" | el costo real era otro, y solo se supo corriendo el código |

**Lo que cuesta:** una tarea entera de más (T0.3 → T0.4) y una alarma que resultó falsa. Lo que
habría costado leer primero: minutos.

**Corolario:** cuando la fuente no se puede leer —un PDF con muro, un dato que no está— eso **se
declara como blocker y se dice por qué**, no se reemplaza por una suposición. En T0.3 se declaró, y
por eso T0.4 existió.

## Cómo se escribe acá

- **Simple y directo.** La respuesta empieza por lo que importa, no por el proceso.
- **Sin jerga propia.** Si un término solo lo entiende quien escribió el código, no sirve.
- **Los números antes que los adjetivos.** "2 de 1.521" y no "el volumen es bajo".
- **Lo que no se sabe, se dice.** Y lo que se supone, se marca como suposición.
- **Sin relleno.** Si la respuesta son tres líneas, son tres líneas.
