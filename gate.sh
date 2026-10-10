#!/usr/bin/env bash
# El gate único. O sale en verde, o no sale.
#
# `pipefail` no es decorativo: sin él, `ruff | tail` devuelve el código de salida de `tail` y un gate
# en rojo pasa desapercibido. Ya ocurrió dos veces en el proyecto anterior.
set -euo pipefail
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"

echo "--- pytest ---"
uv run pytest "$@"
echo "--- ruff ---"
uv run ruff check .
echo "--- mypy (src y tests) ---"
uv run mypy
echo
echo "GATE EN VERDE"
