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
# gthread: AI readings stream for 30–90 s. With sync workers each open stream
# pins a whole worker process, i.e. only 2 readings at a time site-wide.
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 --worker-class gthread --threads 4 \
    --timeout 180 \
    --access-logfile - --error-logfile -
