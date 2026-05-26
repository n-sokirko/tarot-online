# Tarot Online

Web-приложение для онлайн-раскладов Таро с AI-интерпретацией. Next.js + Django + PostgreSQL, мультиязычное (RU/EN), с системой субагентов Claude Code для разделения труда.

> Подробный манифест проекта и правила — в [`CLAUDE.md`](./CLAUDE.md).

## Что внутри

- `CLAUDE.md` — главный манифест для Claude Code
- `agents/` — определения 7 субагентов (frontend, backend, tarot-ai, qa, deploy, database, content)
- `frontend/` — Next.js 14, TypeScript, Tailwind, Framer Motion, next-intl
- `backend/` — Django 5, DRF, Celery, Postgres, Anthropic SDK
- `data/deck/` — seed-данные колоды Таро (78 карт, RU + EN)
- `docs/` — архитектура, схема БД, deploy guide, changelog промптов

## Первый запуск

### 1. Включить агентов в Claude Code

Папка `agents/` лежит в корне для удобства редактирования. Чтобы Claude Code увидел субагентов, переименуй её в `.claude/agents/`:

**Windows (PowerShell):**
```powershell
Rename-Item -Path .\agents -NewName .claude\agents
```

Или вручную: создай папку `.claude/` и перенеси содержимое `agents/` внутрь.

После этого запусти `claude` в корне проекта — субагенты подхватятся автоматически.

### 2. Локальный стек через Docker

```bash
cp .env.example .env
# Открой .env и впиши ANTHROPIC_API_KEY=sk-ant-...

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- API docs (Swagger): http://localhost:8000/api/docs/

### 3. Без Docker (две вкладки терминала)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

(Тебе понадобится локальный Postgres — поправь переменные в `.env`.)

## Команда субагентов

| Агент | Когда звать |
|---|---|
| `frontend-agent` | UI, анимации, i18n, accessibility |
| `backend-agent` | Django API, бизнес-логика, auth |
| `tarot-ai-agent` | Промпты, narrative-генерация |
| `qa-agent` | Тесты, регрессии, проверка качества |
| `deploy-agent` | Docker, CI/CD, Vercel/Railway |
| `database-agent` | Миграции, схема, индексы |
| `content-agent` | Описания карт, UI-копи |

Полные определения и system prompts — в `agents/`.

## Roadmap

1. **MVP** (текущий) — колода, shuffle, расклад 3 карты, базовые описания
2. **AI-интерпретация** — Claude API, streaming, сохранение в БД
3. **Аккаунты и история** — magic-link auth, история раскладов
4. **Premium** — Stripe, премиум-расклады (Кельтский крест и др.)

## Что делать дальше

Открой проект в Claude Code и попроси главную сессию:

> Прочитай `CLAUDE.md`, потом изучи каждое определение в `agents/`. Затем составь план реализации MVP по этапу 1 и предложи, какому агенту делегировать каждый кусок.

Так агенты познакомятся друг с другом, и можно начинать делегировать.

## Лицензия

TBD.
