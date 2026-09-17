# Деплой на Railway (бэкенд + бот) и Vercel (фронт)

Схема вместо домашнего docker-compose + Cloudflare Tunnel:

| Было (docker-compose на ПК) | Стало |
|---|---|
| `db` (postgres:16) | Railway → **Postgres** |
| `redis` | **не нужен** — использовался только как брокер Celery |
| `backend` (gunicorn за nginx) | Railway → сервис **web** (`backend/railway.web.json`) |
| `telegram_bot` (polling) | **внутри web** — webhook, отдельного процесса нет |
| `worker` (celery + beat: пуши 8:00 и 9:00 UTC) | Railway → два **cron-сервиса** (`railway.cron-daily-push.json`, `railway.cron-daily-horoscope.json`) |
| `frontend` + `nginx` + `tunnel` | **Vercel** (root `frontend/`), домен `sokirdon.com` |
| `tts` (Piper) | не переносится: `/api/v1/tts/` отдаёт 503, фронт падает на фоллбэк |

Итого на Railway: **Postgres + web + два крона**. Постоянно работающих процессов
ровно два (Postgres и web) — это и есть причина, по которой всё влезает в
разумные деньги на Hobby (см. раздел 7).

Все сервисы собираются одним образом `backend/Dockerfile.railway` (контекст —
корень репо, чтобы `data/deck` попал в `/data/deck` для `seed_deck`/`seed_runes`),
отличаются только командой запуска.

---

## 1. Что изменилось в коде по сравнению с polling

- `apps/telegram_bot/bot_runtime.py` — мост «синхронный gunicorn → асинхронный
  PTB Application»: один долгоживущий event loop в фоновом потоке на процесс
  воркера. Application инициализируется в нём один раз, `post_init` (меню команд
  и кнопка WebApp) вызывается вручную — `Application.initialize()` сам его не
  зовёт, это делают только `run_polling()`/`run_webhook()`.
- `apps/telegram_bot/views.py` → `POST /api/v1/telegram/webhook/`. Проверяет
  заголовок `X-Telegram-Bot-Api-Secret-Token`; если `TELEGRAM_WEBHOOK_SECRET`
  не задан — отвечает 403 на всё (fail closed). На любую ошибку внутри отвечает
  200, иначе Telegram начнёт откладывать доставку.
- `manage.py set_telegram_webhook` — регистрирует URL у Telegram, идемпотентно,
  вызывается на каждом деплое из `start-railway-web.sh`. Передаёт
  `BOT_ALLOWED_UPDATES` (в нём `chat_member` — без него не считаются приглашения
  в конкурсе) и проверяет результат через `getWebhookInfo`.
- **Грабли, за которые уже платили в Лиане (24.08.2026):** фоновый поток, на
  котором asgiref выполняет `sync_to_async`, никогда не получает сигналы
  `request_started`/`request_finished`, поэтому Django не освежает на нём
  соединение с Postgres. Первое же соединение, которое Postgres закроет по
  простою, убивает все последующие апдейты с `the connection is closed` — молча,
  потому что view всё равно отвечает 200. Лечится вызовом
  `close_old_connections()` в начале `_process_update`. Регрессия закрыта тестом
  `apps/telegram_bot/tests/test_webhook.py`.

> ⚠️ Пока webhook зарегистрирован, локальный `manage.py run_bot` (polling) будет
> падать с `409 Conflict` — Telegram не отдаёт `getUpdates` при живом webhook.
> Вернуться к polling локально: вызвать `deleteWebhook` в Bot API. После
> локальных экспериментов не забудь сделать Redeploy сервиса `web` — он
> перерегистрирует webhook обратно.

## 2. Проект и база

1. Railway → **New Project** → **Empty project** (отдельный проект, не тот, где Liana).
2. **+ Create** → **Database** → **PostgreSQL**. Имя сервиса оставить `Postgres` —
   на него ссылаются переменные ниже. Redis создавать **не нужно**.
3. Перенести данные **до** первого деплоя web (см. раздел 5).

## 3. Переменные

Project Settings → **Shared Variables** (подключаются ко всем сервисам проекта):

| Переменная | Значение |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | новый: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_DEBUG` | `False` |
| `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
| `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
| `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
| `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
| `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |
| `TELEGRAM_BOT_TOKEN` | из `.env` |
| `TELEGRAM_BOT_USERNAME` | `tarott_online_bot` |
| `TELEGRAM_PAYMENT_SECRET` | из `.env` |
| `TELEGRAM_WEBHOOK_SECRET` | новый случайный: `openssl rand -hex 32` |
| `WEBAPP_URL` | `https://sokirdon.com` (до переключения DNS — адрес `*.vercel.app`) |
| `ANTHROPIC_API_KEY` | из `.env.prod` |
| `ANTHROPIC_MODEL_FREE` / `_PREMIUM` / `_DEEP` | из `.env.prod` (можно не задавать — есть дефолты) |
| `GOOGLE_CLIENT_ID` | из `.env.prod` |
| `PADDLE_*` | из `.env.prod` |
| `CORS_ALLOWED_ORIGINS` | `https://sokirdon.com` (+ `https://<проект>.vercel.app` на время проверки) |

`REDIS_URL` больше не нужен. `ANTHROPIC_BASE_URL` / `ANTHROPIC_GATEWAY_AUTH` тоже:
из Railway (US/EU) api.anthropic.com доступен напрямую.

Залить всё это из локального `.env.prod` одной командой — см.
`deploy/railway-set-vars.sh` (инструкция в шапке скрипта).

## 4. Сервисы из GitHub

Для каждого: **+ Create** → **GitHub Repo** → `n-sokirko/tarot-online`, затем в **Settings**:

| Сервис | Settings → Config-as-code → Railway Config File | Root Directory |
|---|---|---|
| `web` | `/backend/railway.web.json` | пусто (корень репо) |
| `cron-daily-push` | `/backend/railway.cron-daily-push.json` | пусто |
| `cron-daily-horoscope` | `/backend/railway.cron-daily-horoscope.json` | пусто |

- **Variables** → *Shared Variable* → подключить переменные из раздела 3 к
  каждому сервису.
- Только `web`: **Settings → Networking → Generate Domain**, затем добавить ему
  свои (не shared) переменные:
  - `DJANGO_ALLOWED_HOSTS` = `${{RAILWAY_PUBLIC_DOMAIN}},healthcheck.railway.app`
  - `CSRF_TRUSTED_ORIGINS` = `https://${{RAILWAY_PUBLIC_DOMAIN}}`
  - `TELEGRAM_WEBHOOK_BASE_URL` = `https://${{RAILWAY_PUBLIC_DOMAIN}}`

  (`healthcheck.railway.app` обязателен — с этим Host Railway дёргает `/api/healthz/`,
  без него Django отвечает 400 и деплой не проходит healthcheck.)
- Ветка деплоя — `master`. `watchPatterns` в конфигах: изменения только во `frontend/`
  бэкенд не передеплоят.
- Кроны Railway считает по **UTC** и поднимает контейнер только на время задачи;
  `restartPolicyType: NEVER` — отработал и погас.

Проверка после деплоя `web`:

```bash
curl https://<web-domain>/api/healthz/
```

Должно вернуться `{"status": "ok"}`. В логах деплоя должна быть строка
`Confirmed via getWebhookInfo`, а `getWebhookInfo` в Bot API — показывать
`<web-domain>/api/v1/telegram/webhook/`. Дальше — написать боту `/start`.

Кроны руками: Railway → сервис → **Deploy** (одноразовый запуск), или локально
`python manage.py send_daily_push --tg-id <свой id>`.

Админка: `https://<web-domain>/admin/` (статика отдаётся WhiteNoise).

## 5. Перенос базы с ПК

Живые данные — в docker-томе `taro_cards_pgdata` (не в локальном PostgreSQL 17 —
там dev-копия). Запустить только контейнер БД (без бота!) и снять дамп:

```bash
docker compose -f docker-compose.prod.yml up -d db
```

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U tarot -d tarot --no-owner --no-privileges --clean --if-exists > tarot.sql
```

```bash
docker compose -f docker-compose.prod.yml stop db
```

Залить в Railway (Postgres → Variables → `DATABASE_PUBLIC_URL`):

```bash
psql "<DATABASE_PUBLIC_URL>" -v ON_ERROR_STOP=1 -f tarot.sql
```

`tarot.sql` содержит персональные данные — не коммить, удалить после переноса.

Если web уже успел задеплоиться на пустую базу — не страшно: `--clean --if-exists`
перезапишет таблицы. После заливки сделай **Redeploy** сервиса `web`, чтобы
`migrate` докатил миграции, которых не было в старой базе.

## 6. Фронт на Vercel

1. Vercel → **Add New Project** → `n-sokirko/tarot-online` → **Root Directory: `frontend`**.
2. Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `https://<web-domain>` (без `/` на конце)
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = из `.env.prod`
3. Deploy → проверь на `https://<проект>.vercel.app`.
4. Settings → Domains → `sokirdon.com` (+ `www`). В Cloudflare DNS удалить запись
   туннеля для `sokirdon.com` и создать те записи, что покажет Vercel,
   **Proxy status: DNS only** (серое облако).
5. После переключения: `WEBAPP_URL=https://sokirdon.com` в Railway и убрать
   `*.vercel.app` из `CORS_ALLOWED_ORIGINS`.

Paddle: webhook-URL в кабинете Paddle поменять с `https://sokirdon.com/api/v1/billing/webhooks/paddle/`
на `https://<web-domain>/api/v1/billing/webhooks/paddle/`.

## 7. Стоимость

Railway считает по факту: ~$10 за ГБ RAM в месяц и ~$20 за vCPU в месяц.
Постоянно работают только два контейнера:

| Сервис | ~RAM | ~$/мес |
|---|---|---|
| web (gunicorn, 1 воркер × 8 потоков) | ~150–200 МБ | ~2 |
| Postgres | ~130 МБ | ~1.3 |
| два крона (2 запуска в сутки по ~30 с) | — | центы |

≈ **$3–3.5/мес** за таро. Аккаунт общий с Liana Studio (ещё ~$3.5), включённых
в Hobby $5 на оба проекта **не хватит** — закладывай ~$2–3 сверх подписки.
Если стоит жёсткий лимит расходов, при его достижении Railway останавливает
сервисы всех проектов аккаунта, включая Лиану.

Ручки экономии, если нужно:

- `WEB_CONCURRENCY` в сервисе `web` — по умолчанию 1; больше воркеров = больше RAM.
- Кроны можно удалить совсем (ежедневные пуши перестанут уходить) — экономия центы.
