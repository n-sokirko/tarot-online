# Деплой на Railway (бэкенд + бот) и Vercel (фронт)

Схема вместо домашнего docker-compose + Cloudflare Tunnel:

| Было (docker-compose на ПК) | Стало |
|---|---|
| `db` (postgres:16) | Railway → **Postgres** |
| `redis` | Railway → **Redis** |
| `backend` (gunicorn за nginx) | Railway → сервис **web** (`backend/railway.web.json`) |
| `telegram_bot` (polling) | Railway → сервис **bot** (`backend/railway.bot.json`) |
| `worker` (celery + beat: пуши 8:00 и 9:00 UTC) | Railway → сервис **worker** (`backend/railway.worker.json`) |
| `frontend` + `nginx` + `tunnel` | **Vercel** (root `frontend/`), домен `sokirdon.com` |
| `tts` (Piper) | не переносится: `/api/v1/tts/` отдаёт 503, фронт падает на фоллбэк |

Все три сервиса собираются одним образом `backend/Dockerfile.railway` (контекст —
корень репо, чтобы `data/deck` попал в `/data/deck` для `seed_deck`/`seed_runes`),
отличаются только командой запуска.

> ⚠️ **Бот должен работать ровно в одном экземпляре.** Два процесса с polling на
> один токен → `409 Conflict`, бот «молчит» через раз. Не запускай локальный
> `docker compose ... telegram_bot`, пока бот живёт на Railway, и не ставь сервису
> bot больше одной реплики.

---

## 1. Проект и база

1. Railway → **New Project** → **Empty project** (отдельный проект, не тот, где Liana).
2. **+ Create** → **Database** → **PostgreSQL**. Затем так же **Redis**.
   Оставь имена сервисов `Postgres` и `Redis` — на них ссылаются переменные ниже.
3. Перенеси данные **до** создания web/bot/worker (см. раздел 5).

## 2. Общие переменные

Project Settings → **Shared Variables** (их потом подключаем ко всем трём сервисам):

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
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `TELEGRAM_BOT_TOKEN` | из `.env` |
| `TELEGRAM_BOT_USERNAME` | `tarott_online_bot` |
| `TELEGRAM_PAYMENT_SECRET` | из `.env` |
| `WEBAPP_URL` | `https://sokirdon.com` (до переключения DNS — адрес `*.vercel.app`) |
| `ANTHROPIC_API_KEY` | из `.env.prod` |
| `ANTHROPIC_MODEL_FREE` / `_PREMIUM` / `_DEEP` | из `.env.prod` (можно не задавать — есть дефолты) |
| `GOOGLE_CLIENT_ID` | из `.env.prod` |
| `PADDLE_*` | из `.env.prod` |
| `CORS_ALLOWED_ORIGINS` | `https://sokirdon.com` (+ `https://<проект>.vercel.app` на время проверки) |

`ANTHROPIC_BASE_URL` / `ANTHROPIC_GATEWAY_AUTH` не нужны: из Railway (US/EU) api.anthropic.com доступен напрямую.

## 3. Три сервиса из GitHub

Для каждого: **+ Create** → **GitHub Repo** → `n-sokirko/tarot-online`, затем в **Settings**:

| Сервис | Settings → Config-as-code → Railway Config File | Root Directory |
|---|---|---|
| `web` | `/backend/railway.web.json` | пусто (корень репо) |
| `bot` | `/backend/railway.bot.json` | пусто |
| `worker` | `/backend/railway.worker.json` | пусто |

- **Variables** → *Shared Variable* → подключить все переменные из раздела 2.
- Только `web`: **Settings → Networking → Generate Domain**, затем добавить ему переменные:
  - `DJANGO_ALLOWED_HOSTS` = `${{RAILWAY_PUBLIC_DOMAIN}},healthcheck.railway.app`
  - `CSRF_TRUSTED_ORIGINS` = `https://${{RAILWAY_PUBLIC_DOMAIN}}`
  (`healthcheck.railway.app` обязателен — с этим Host Railway дёргает `/api/healthz/`,
  без него Django отвечает 400 и деплой не проходит healthcheck.)
- Ветка деплоя — `master`. `watchPatterns` в конфигах: изменения только во `frontend/`
  бэкенд не передеплоят.

Проверка после деплоя `web`:
```bash
curl https://<web-domain>/api/healthz/          # {"status": "ok"}
```
Логи `bot` должны содержать `Bot polling started`, `worker` — `beat: Starting...`.

Админка: `https://<web-domain>/admin/` (статика отдаётся WhiteNoise).

## 4. Фронт на Vercel

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

## 5. Перенос базы с ПК

Живые данные — в docker-томе `taro_cards_pgdata` (не в локальном PostgreSQL 17 —
там dev-копия). Запустить только контейнер БД (без бота!) и снять дамп:

```bash
docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U tarot -d tarot --no-owner --no-privileges --clean --if-exists > tarot.sql
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

## 6. Стоимость

Hobby включает ~$5 потребления в месяц на **весь аккаунт** — он общий с другими
проектами. Postgres + Redis + три постоянно работающих процесса почти наверняка
выйдут за эти $5; следи за Usage в Railway. Если стоит жёсткий лимит расходов,
при его достижении Railway останавливает сервисы всех проектов аккаунта.
