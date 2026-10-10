# task.md — cola de trabajo

`doc/` es la fuente de verdad. Acá va **qué falta y en qué estado**.

| # | Tarea | Estado |
|---|---|---|
| T0.1 | Esqueleto, gate y guardián de arquitectura | ✅ |
| T0.2 | **Spike: medir el volumen real de CT** (decide si el proyecto sigue) | ⬜ |
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
