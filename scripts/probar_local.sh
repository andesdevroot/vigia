#!/usr/bin/env bash
# Prueba de punta a punta: el motor, el webhook y WhatsApp, en un solo comando.
#
# Levanta el servidor, le abre un túnel con ngrok y dice exactamente qué URL pegar en Kapso.
# No imprime ni copia ningún secreto.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Falta .env. Copia el ejemplo y pega ahí los valores:"
  echo
  echo "    cp .env.example .env"
  exit 1
fi

set -a
# shellcheck disable=SC1091
. ./.env
set +a

: "${KAPSO_API_KEY:?falta KAPSO_API_KEY en .env}"
: "${VIGIA_WEBHOOK_SECRET:?falta VIGIA_WEBHOOK_SECRET en .env}"

PUERTO="${VIGIA_PUERTO:-8000}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"
export VIGIA_PUERTO="$PUERTO"

echo "Levantando el webhook en el puerto $PUERTO..."
uv run python -m vigia.servidor &
SERVIDOR=$!

YA_LIMPIE=0
limpiar() {
  [ "$YA_LIMPIE" = 0 ] || return 0
  YA_LIMPIE=1
  kill "$SERVIDOR" 2>/dev/null || true
  if [ -n "${TUNEL:-}" ]; then
    kill "$TUNEL" 2>/dev/null || true
  fi
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

cat <<FIN

  Webhook listo.

    1. En Kapso, crea el webhook contra esta URL, con el evento
       whatsapp.message.received y payload_version v2:

         $URL/webhook

    2. Copia el secret_key que Kapso muestra UNA SOLA VEZ y pégalo en .env
       como VIGIA_WEBHOOK_SECRET. Si ya lo tenías, no hay nada que hacer.

    3. Escríbele desde tu WhatsApp al número del robot y mira la respuesta.

  Ctrl-C corta el servidor y el túnel.

FIN

wait "$SERVIDOR"
