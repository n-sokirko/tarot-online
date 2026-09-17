#!/bin/sh
# Railway "web" service entrypoint. Same steps as the backend command in
# docker-compose.prod.yml, minus nginx: gunicorn binds Railway's $PORT directly
# and WhiteNoise (config/settings/prod.py) serves /static/ for the admin.
set -e
python manage.py migrate --noinput
python manage.py seed_deck
python manage.py seed_runes
python manage.py seed_plans
python manage.py collectstatic --noinput
# The bot runs inside this process via webhook (apps/telegram_bot/bot_runtime.py),
# not as a separate always-on polling service. Re-registering on every deploy is
# idempotent; `|| true` so a Telegram API blip never blocks the release.
python manage.py set_telegram_webhook || true
# gthread: AI readings stream for 30-90 s. With sync workers each open stream
# pins a whole worker process, i.e. only WEB_CONCURRENCY readings at a time
# site-wide. One worker by default keeps the Railway Hobby bill down (~150 MB
# instead of ~300 MB); raise WEB_CONCURRENCY in the service variables if the
# site starts queueing.
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}" --worker-class gthread --threads 8 \
    --timeout 180 \
    --access-logfile - --error-logfile -
