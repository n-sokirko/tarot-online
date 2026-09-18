# Деплой на Railway (бэкенд + бот) и Vercel (фронт)

Схема вместо домашнего docker-compose + Cloudflare Tunnel:

| Было (docker-compose на ПК) | Стало |
|---|---|
| `db` (postgres:16) | Railway → **Postgres** |
| `redis` | **не нужен** — использовался только как брокер Celery |
| `backend` (gunicorn за nginx) | Railway → сервис **web** |
| `telegram_bot` (polling) | **внутри web** — webhook, отдельного процесса нет |
| `worker` (celery + beat: пуши 8:00 и 9:00 UTC) | Railway → два **cron-сервиса** |
| `frontend` + `nginx` + `tunnel` | **Vercel** (root `frontend/`), домен `sokirdon.com` |
| `tts` (Piper) | не переносится: `/api/v1/tts/` отдаёт 503, фронт падает на фоллбэк |

Итого на Railway: **Postgres + web + два крона**. Постоянно работающих процессов
ровно два (Postgres и web) — отсюда и цена (раздел 7).

Проект: `tarot-online`, окружение `production`, домен сервиса web —
`https://web-production-af39f.up.railway.app`.

Вся конфигурация инфраструктуры описана кодом в **`.railway/railway.ts`**
(Infrastructure as Code). Старый `railway.json` / config-as-code **задеприкейчен**:
Railway API на попытку задать «Railway Config File» отвечает ошибкой и отправляет
на IaC. Поэтому `backend/railway.*.json` из репо удалены.

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

## 2. Инструменты

```bash
npm install -g @railway/cli
```

```bash
railway login
```

SDK для IaC ставится в корень репо (`package.json` в корне существует только
ради него):

```bash
npm install
```

> ⚠️ **Гит-баш на Windows:** команды `railway config plan/apply` запускают
> `node`, который проверяет версию CLI через `process.env._`. Под Git Bash туда
> попадает `.../npm/railway` (shell-обёртка без расширения), `execFileSync` её не
> запускает, и вылезает ложное «requires Railway CLI 5.42.1 or newer».
> Лечится вызовом бинарника напрямую:
> `"$APPDATA/npm/node_modules/@railway/cli/bin/railway.exe" config plan`.
> Остальные команды (`railway variables`, `railway logs`, ...) работают как есть.

## 3. Проект и база

```bash
railway init --name tarot-online
```

```bash
railway add --database postgres
```

Имя сервиса БД должно остаться `Postgres` — на него ссылается `.railway/railway.ts`.
Redis создавать **не нужно**.

## 4. Переменные

Делятся на две части — так, чтобы в git не попало ни одного секрета.

**Несекретные и ссылки на БД** описаны прямо в `.railway/railway.ts`:
`DJANGO_SETTINGS_MODULE`, `DJANGO_DEBUG`, `TELEGRAM_BOT_USERNAME`,
`POSTGRES_*` (через `Postgres.env.PG*`), а для `web` ещё
`DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` и `TELEGRAM_WEBHOOK_BASE_URL`
(все три через `${{RAILWAY_PUBLIC_DOMAIN}}`).

`healthcheck.railway.app` в `DJANGO_ALLOWED_HOSTS` обязателен — с этим Host
Railway дёргает `/api/healthz/`, без него Django отвечает 400 и деплой не
проходит healthcheck.

**Секреты** помечены в том же файле как `preserve()` (IaC их не трогает) и
заливаются отдельно, из локальных `.env` и `.env.prod` — оба gitignored, читаются
именно в таком порядке, `.env.prod` перекрывает:

```bash
sh deploy/railway-set-vars.sh web
```

```bash
sh deploy/railway-set-vars.sh cron-daily-push
```

```bash
sh deploy/railway-set-vars.sh cron-daily-horoscope
```

Скрипт печатает только имена переменных, не значения. Отдельно, руками, задаются
два секрета, которых нет ни в одном `.env` (генерируются заново для Railway):

- `DJANGO_SECRET_KEY` — `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `TELEGRAM_WEBHOOK_SECRET` — `python -c "import secrets; print(secrets.token_hex(32))"`

`REDIS_URL` больше не нужен. `ANTHROPIC_BASE_URL` / `ANTHROPIC_GATEWAY_AUTH` тоже:
из Railway (US/EU) api.anthropic.com доступен напрямую.
`CORS_ALLOWED_ORIGINS` пока не задан — фронта на Vercel ещё нет, а `sokirdon.com`
и так разрешён регуляркой в `config/settings/prod.py`.

## 5. Сервисы и деплой

Сервисы создаются пустыми, конфигурацию им раздаёт IaC:

```bash
railway add --service web --repo n-sokirko/tarot-online --branch master
```

Так же `cron-daily-push` и `cron-daily-horoscope`. Затем — секреты (раздел 4),
и только потом:

```bash
railway config plan
```

```bash
railway config apply
```

`plan` ничего не меняет и показывает полный дифф; `apply` применяет и запускает
деплой. Публичный домен для `web` (нужен для `${{RAILWAY_PUBLIC_DOMAIN}}`):

```bash
railway domain --service web
```

Кроны Railway считает по **UTC** и поднимает контейнер только на время задачи;
`restartPolicyType: NEVER` — отработал и погас. Расписания (8:00 и 9:00 UTC)
повторяют `CELERY_BEAT_SCHEDULE` из `config/settings/base.py`.

Проверка после деплоя:

```bash
curl https://web-production-af39f.up.railway.app/api/healthz/
```

Должно вернуться `{"status": "ok"}`. В логах деплоя (`railway logs --deployment
--service web`) должны быть строки `Confirmed via getWebhookInfo` и
`Booting worker`. Прогнать крон руками, не дожидаясь расписания: Railway →
сервис → **Deploy**, либо локально
`python manage.py send_daily_push --tg-id <свой id>`.

Админка: `https://web-production-af39f.up.railway.app/admin/` (статика — WhiteNoise).

## 6. Перенос базы с ПК

> ⚠️ Деплой поднимается на **пустой** базе: миграции применяются, `seed_deck` /
> `seed_runes` / `seed_plans` наполняют справочники, но пользователей, подписок,
> платежей и конкурса в ней нет. И как только webhook зарегистрирован, бот уже
> отвечает живым людям из этой пустой базы: постоянные подписчики увидят себя
> новичками без Premium, а всё, что они успеют нажать, сотрёт восстановление
> дампа (`--clean`). Либо переноси дамп сразу, либо сними webhook
> (`deleteWebhook`) до момента переноса — Telegram придержит апдейты и доставит
> их, когда вебхук вернётся.
>
> **Снятый вручную webhook живёт только до следующего деплоя** `web`:
> `start-railway-web.sh` на каждом старте зовёт `set_telegram_webhook` и
> регистрирует его заново. Так что пуш в `backend/**` между `deleteWebhook` и
> восстановлением базы молча вернёт бота в эфир.

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

У Railway-Postgres **нет публичного адреса** — ни `DATABASE_PUBLIC_URL`, ни
TCP-прокси по умолчанию. Дотянуться можно двумя способами; предпочтительнее
первый, он вообще ничего не выставляет наружу:

```bash
railway ssh keys add
```

Без аргументов — сам подхватит `~/.ssh/*.pub`. С `--key <путь>` под Git Bash
падает с «Key not found». Затем, в отдельном окне (держит туннель, пока не
Ctrl+C):

```bash
railway connect Postgres --tunnel-only --port 55432
```

Второй способ — `railway tcp-proxy create --service Postgres --port 5432`, но
тогда база на время заливки видна из интернета; после переноса прокси надо
удалить.

Дамп из postgres:16-alpine начинается и заканчивается директивами
`\restrict` / `\unrestrict` — их понимает только psql 17.6+/16.10+. Если
локальный клиент старее (здесь psql 17.0), эти две строки надо выкинуть, иначе
`invalid command \restrict`:

```bash
grep -v -e '^.restrict ' -e '^.unrestrict ' tarot.sql > tarot.clean.sql
```

Заливка (пароль — `railway variables --service Postgres --kv`, но выводить его
в терминал не стоит, читай сразу в переменную):

```bash
PGPASSWORD="$PW" psql -h 127.0.0.1 -p 55432 -U postgres -d railway -v ON_ERROR_STOP=1 -f tarot.clean.sql
```

`tarot.sql` содержит персональные данные — не коммить, удалить после переноса
вместе с `tarot.clean.sql`.

`--clean --if-exists` перезапишет уже созданные таблицы, так что порядок
«сначала деплой, потом дамп» допустим. Но учти: дамп несёт с собой и таблицу
`django_migrations`. Если он снят со старой базы, а в коде с тех пор появились
новые миграции, Django после заливки будет считать их неприменёнными, хотя
таблицы от первого деплоя уже существуют. Проверить перед редеплоем:

```bash
python manage.py showmigrations --plan
```

(с `POSTGRES_*`, указывающими на туннель) — ни одной строки `[ ]` быть не
должно. После заливки — **Redeploy** сервиса `web`: он докатит миграции и
заново зарегистрирует webhook.

## 7. Фронт на Vercel

Развёрнут 17.09.2026: проект `tarot-online`, прод на
`https://tarot-online-fawn.vercel.app`, GitHub-интеграция подключена —
пуш в `master` деплоит сам.

```bash
vercel login
```

```bash
cd frontend && vercel link --yes --project tarot-online
```

Переменные (обе с `NEXT_PUBLIC_`, то есть попадают в клиентский бандл —
секретов туда класть нельзя):

```bash
printf '%s' "https://web-production-af39f.up.railway.app" | vercel env add NEXT_PUBLIC_API_URL production
```

`NEXT_PUBLIC_GOOGLE_CLIENT_ID` — так же, значение из `.env.prod`.
В коде используется именно `NEXT_PUBLIC_API_URL` (`lib/api.ts`), без `/api/v1` на
конце; `NEXT_PUBLIC_API_BASE_URL` из `.env.example` — устаревшее имя, нигде не
читается.

```bash
vercel deploy --prod --yes
```

```bash
vercel git connect "https://github.com/n-sokirko/tarot-online.git"
```

> ⚠️ `vercel git connect` без URL падает с «No local Git repository found»: он
> ищет `.git` в текущей папке (`frontend/`) и не поднимается к корню репо.
>
> ⚠️ После `vercel link` из `frontend/` **Root Directory проекта остаётся `.`**.
> CLI-деплою это не мешает (он грузит текущую папку), а вот сборка по
> пушу полезет в корень репо и наткнётся на тамошний `package.json`
> (там только SDK Railway). Починить через API проекта:
> `PATCH /v9/projects/<id>?teamId=<team>` с `{"rootDirectory":"frontend"}`
> (токен — в `%APPDATA%/xdg.data/com.vercel.cli/auth.json`).

Бэкенду нужно разрешить этот origin, иначе все запросы упрутся в CORS
(в `prod.py` регуляркой разрешён только `sokirdon.com`):

```bash
railway variables --service web --skip-deploys --set "CORS_ALLOWED_ORIGINS=https://tarot-online-fawn.vercel.app" --set "WEBAPP_URL=https://tarot-online-fawn.vercel.app"
```

`WEBAPP_URL` так же надо поставить обоим кронам — на него смотрят кнопка
WebApp в меню бота и ссылки в ежедневных пушах. После — Redeploy `web`.

### Перевод домена (сделано 18.09.2026)

`sokirdon.com` и `www.sokirdon.com` привязаны к проекту Vercel
(`verified: true`), DNS переставлен с туннеля на Vercel.

Правку зоны делает `deploy/cf-dns-vercel.py`: он берёт зонный API-токен из
`~/.cloudflared/cert.pem` (тот же, которым работает `cloudflared tunnel route
dns`), так что отдельный секрет хранить не надо. По умолчанию сухой прогон:

```bash
python deploy/cf-dns-vercel.py
```

```bash
python deploy/cf-dns-vercel.py --apply
```

Скрипт трогает только апекс и `www`; `api.sokirdon.com` оставляет как есть.
Если делать руками — до переезда апекс смотрел на прокси Cloudflare
(`104.21.48.6`, `172.67.175.40`) перед мёртвым туннелем; надо удалить записи
туннеля и создать:

| Имя | Тип | Значение | Proxy |
|---|---|---|---|
| `sokirdon.com` | A | `216.198.79.1` | DNS only |
| `sokirdon.com` | A | `64.29.17.1` | DNS only |
| `www` | CNAME | `5d8c0496c7026cc1.vercel-dns-017.com` | DNS only |

Запасной вариант, если эти не зайдут: A → `76.76.21.21`,
CNAME → `cname.vercel-dns.com`.

> ⚠️ **Серое облако обязательно.** При включённом прокси Vercel видит
> адреса Cloudflare вместо своих и не выпускает сертификат.

Проверить, что Vercel увидел переезд (должно стать `misconfigured: false`):

```bash
curl -s "https://api.vercel.com/v6/domains/sokirdon.com/config?teamId=<team>" -H "Authorization: Bearer <token>"
```

Сертификат Vercel после переезда DNS может не выпуститься сам — апекс отдаёт
`SSL_ERROR_SYSCALL`, хотя по HTTP уже 200, а `vercel certs ls` пуст. Тогда
запросить явно:

```bash
vercel certs issue sokirdon.com www.sokirdon.com
```

После переключения на Railway возвращены `WEBAPP_URL=https://sokirdon.com`
(`web` и оба крона) и `CORS_ALLOWED_ORIGINS` с обоими хостами плюс адрес
Vercel для проверок, затем сделан Redeploy `web`.

> ⚠️ **Paddle остался на старом адресе.** Раньше `sokirdon.com` вёл на бэкенд,
> теперь — на фронт во Vercel, поэтому webhook
> `https://sokirdon.com/api/v1/billing/webhooks/paddle/` упирается в 404.
> В кабинете Paddle его надо сменить на
> `https://web-production-af39f.up.railway.app/api/v1/billing/webhooks/paddle/`,
> иначе платежи через Paddle не долетают до бэкенда.

## 8. Стоимость

Railway считает по факту: ~$10 за ГБ RAM в месяц и ~$20 за vCPU в месяц.
Факт на 17.09.2026, когда на аккаунте была только Liana Studio (`railway usage`):
расчётный счёт **$1.37/мес** на весь аккаунт. Таро по той же топологии должно
дать сопоставимую цифру, то есть суммарно ориентировочно **$3/мес** — внутри
включённых в Hobby $5, но без большого запаса.

Постоянно работают только два контейнера:

| Сервис | ~RAM | ~$/мес |
|---|---|---|
| web (gunicorn, 1 воркер × 8 потоков) | ~150–200 МБ | ~1–2 |
| Postgres | ~130 МБ | ~1 |
| два крона (2 запуска в сутки по ~30 с) | — | центы |

Следи за `railway usage`. Если поставить жёсткий лимит расходов, при его
достижении Railway останавливает сервисы **всех** проектов аккаунта, включая
Лиану.

Ручки экономии, если нужно:

- `WEB_CONCURRENCY` в сервисе `web` — по умолчанию 1; больше воркеров = больше RAM.
- Кроны можно удалить совсем (ежедневные пуши перестанут уходить) — экономия центы.
