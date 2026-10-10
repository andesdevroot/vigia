#!/usr/bin/env bash
# Prueba de punta a punta: el motor, el webhook y WhatsApp, en un solo comando.
#
# Abre el túnel, registra o actualiza el webhook en Kapso, levanta el servidor, y al salir apaga el
# webhook para no dejarlo apuntando a un túnel muerto. No imprime ni copia secretos: los escribe en
# `.env`.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Falta .env. Copia el ejemplo y pega la API key:"
  echo
  echo "    cp .env.example .env"
  exit 1
fi

set -a
# shellcheck disable=SC1091
. ./.env
set +a

: "${KAPSO_API_KEY:?falta KAPSO_API_KEY en .env}"

PUERTO="${VIGIA_PUERTO:-8000}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"
export VIGIA_PUERTO="$PUERTO"

YA_LIMPIE=0
limpiar() {
  [ "$YA_LIMPIE" = 0 ] || return 0
  YA_LIMPIE=1
  kill "$SERVIDOR" 2>/dev/null || true
  if [ -n "${TUNEL:-}" ]; then
    kill "$TUNEL" 2>/dev/null || true
  fi
  python3 scripts/registrar_webhook.py --apagar 2>/dev/null || true
  return 0
}
trap limpiar EXIT INT TERM

echo "Abriendo el túnel..."
ngrok http "$PUERTO" --log stdout >/dev/null 2>&1 &
TUNEL=$!

URL=""
for _ in $(seq 1 20); do
  sleep 1
  URL=$(curl -sS --max-time 2 http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
tuneles = json.load(sys.stdin).get('tunnels', [])
print(next((t['public_url'] for t in tuneles if t['public_url'].startswith('https')), ''))
" 2>/dev/null || true)
  [ -n "$URL" ] && break
done

if [ -z "$URL" ]; then
  echo "No se pudo abrir el túnel. Comprueba ngrok con: ngrok config check"
  exit 1
fi

echo "Registrando el webhook en Kapso..."
python3 scripts/registrar_webhook.py "$URL"

# El servidor arranca DESPUÉS, a propósito: necesita el secreto que acaba de quedar en `.env`.
set -a
. ./.env
set +a
: "${VIGIA_WEBHOOK_SECRET:?no quedó VIGIA_WEBHOOK_SECRET en .env}"

echo "Levantando el servidor en el puerto $PUERTO..."
uv run python -m vigia.servidor &
SERVIDOR=$!

cat <<FIN

  Listo.

    1. Si es la primera vez: en Kapso, WhatsApp -> Sandbox -> Add Test Number,
       registra tu número y manda el código de 6 caracteres (vence en 15 min).
    2. Escríbele al sandbox desde tu WhatsApp y mira la respuesta.

  Ctrl-C corta el servidor, el túnel y apaga el webhook.

FIN

wait "$SERVIDOR"
