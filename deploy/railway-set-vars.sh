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
# Both files are read, in this order, and a later one wins: the Telegram token
# and WEBAPP_URL live in .env, the Paddle and Anthropic model settings only in
# .env.prod. Both are gitignored.
ENV_FILES="$ROOT/.env $ROOT/.env.prod"
found=0
for f in $ENV_FILES; do [ -f "$f" ] && found=1; done
[ "$found" = 1 ] || { echo "no .env or .env.prod in $ROOT" >&2; exit 1; }

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
PADDLE_PRODUCT_CREDITS_LARGE PADDLE_PRICE_CREDITS_LARGE
WEBAPP_URL"

set -- --service "$SERVICE"
applied=""
skipped=""

for key in $KEYS; do
    # Last assignment wins, matching python-decouple reading the same file.
    line=""
    for f in $ENV_FILES; do
        [ -f "$f" ] || continue
        hit="$(grep "^${key}=" "$f" | tail -n 1 || true)"
        [ -n "$hit" ] && line="$hit"
    done
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

[ -n "$applied" ] || { echo "nothing to set from $ENV_FILES" >&2; exit 1; }

echo "service:  $SERVICE"
echo "source:   $ENV_FILES"
echo "setting: $applied"
[ -n "$skipped" ] && echo "missing/empty (set by hand if needed):$skipped"

# --skip-deploys: apply everything first, redeploy once at the end by hand,
# instead of triggering a rebuild per variable.
railway variables "$@" --skip-deploys
echo "done. Redeploy the service for the new values to take effect."
