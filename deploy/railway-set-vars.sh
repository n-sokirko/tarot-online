#!/bin/sh
# Push the backend's production environment into a Railway service.
#
# Reads values from the local .env.prod / .env (gitignored, never leaves this
# machine except to Railway) and sets them on ONE service. Secrets are never
# echoed — only variable names are printed.
#
# Usage:
#   railway login                       # once, opens a browser
#   railway link                        # pick the tarot project + environment
#   sh deploy/railway-set-vars.sh web
#   sh deploy/railway-set-vars.sh cron-daily-push
#   sh deploy/railway-set-vars.sh cron-daily-horoscope
#
# Service-specific variables (public domain, webhook base URL) are NOT set here
# — see docs/deploy-railway.md section 4.
set -eu

SERVICE="${1:-}"
if [ -z "$SERVICE" ]; then
    echo "usage: sh deploy/railway-set-vars.sh <service-name>" >&2
    exit 2
fi

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env.prod"
[ -f "$ENV_FILE" ] || ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || { echo "no .env.prod or .env in $ROOT" >&2; exit 1; }

# Copied verbatim from $ENV_FILE when present. Everything else in that file
# (REDIS_URL, POSTGRES_*, TTS_*, nginx/tunnel settings) is deliberately left
# out: Railway supplies the database values through ${{Postgres.*}} references
# and the rest belongs to the retired docker-compose stack.
KEYS="TELEGRAM_BOT_TOKEN TELEGRAM_BOT_USERNAME TELEGRAM_PAYMENT_SECRET
TELEGRAM_REQUIRED_CHANNEL TELEGRAM_REQUIRED_CHANNEL_URL
ANTHROPIC_API_KEY ANTHROPIC_MODEL_FREE ANTHROPIC_MODEL_PREMIUM ANTHROPIC_MODEL_DEEP
GOOGLE_CLIENT_ID
PADDLE_ENV PADDLE_API_KEY PADDLE_WEBHOOK_SECRET PADDLE_CLIENT_TOKEN
PADDLE_PRODUCT_PREMIUM_MONTHLY PADDLE_PRICE_PREMIUM_MONTHLY
PADDLE_PRODUCT_CREDITS_SMALL PADDLE_PRICE_CREDITS_SMALL
PADDLE_PRODUCT_CREDITS_LARGE PADDLE_PRICE_CREDITS_LARGE"

set -- --service "$SERVICE"
applied=""
skipped=""

for key in $KEYS; do
    # Last assignment wins, matching python-decouple reading the same file.
    line="$(grep "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
    if [ -z "$line" ]; then
        skipped="$skipped $key"
        continue
    fi
    value="${line#*=}"
    # Strip one layer of surrounding quotes, as decouple does.
    case "$value" in
        \"*\") value="${value#\"}"; value="${value%\"}" ;;
        \'*\') value="${value#\'}"; value="${value%\'}" ;;
    esac
    [ -n "$value" ] || { skipped="$skipped $key"; continue; }
    set -- "$@" --set "${key}=${value}"
    applied="$applied $key"
done

[ -n "$applied" ] || { echo "nothing to set from $ENV_FILE" >&2; exit 1; }

echo "service:  $SERVICE"
echo "source:   $ENV_FILE"
echo "setting: $applied"
[ -n "$skipped" ] && echo "missing/empty (set by hand if needed):$skipped"

# --skip-deploys: apply everything first, redeploy once at the end by hand,
# instead of triggering a rebuild per variable.
railway variables "$@" --skip-deploys
echo "done. Redeploy the service for the new values to take effect."
