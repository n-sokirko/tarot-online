# Tarot Online — Project Manifest

> Этот файл — главная инструкция для Claude Code и всех субагентов.
> **Прочитай его целиком, прежде чем делать что-либо.**

---

## 1. Что мы строим

**Tarot Online** — веб-приложение для онлайн-расклада карт Таро.

Идея коротко: пользователь заходит, формулирует свой вопрос, тасует виртуальную колоду, вытаскивает карты, и AI-агент пишет ему персональную интерпретацию.

Это **НЕ** «гадание на будущее». Это:

- сторителлинг
- интроспекция
- эмоциональный UX
- мистическая атмосфера, но без эзотерического шарлатанства

Все агенты должны держать этот тон в голове при работе.

---

## 2. Стек

### Frontend
- **Next.js 14+** (App Router)
- **TypeScript** strict
- **Tailwind CSS**
- **Framer Motion** — анимации тасования, переворот карт
- **shadcn/ui** — UI компоненты
- **next-intl** — i18n (RU / EN)

### Backend
- **Django 5** + **Django REST Framework**
- **PostgreSQL 16**
- **Celery + Redis** — фоновые задачи (генерация интерпретаций)
- **DRF Spectacular** — OpenAPI

### AI
- **Claude API** (Anthropic) — narrative-генерация раскладов
- Системные промпты лежат в `backend/apps/tarot/prompts/`

### Infra
- **Docker Compose** — локально
- **Vercel** — frontend
- **Railway** или **Render** — backend + Postgres
- **GitHub Actions** — CI

---

## 3. Структура репозитория

```
taro_cards/
├── CLAUDE.md                  ← этот файл
├── README.md
├── docker-compose.yml
├── .gitignore
├── .env.example
│
├── .claude/
│   └── agents/                ← определения субагентов
│       ├── frontend.md
│       ├── backend.md
│       ├── tarot-ai.md
│       ├── qa.md
│       ├── deploy.md
│       ├── database.md
│       └── content.md
│
├── frontend/                  ← Next.js
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── messages/              ← переводы RU/EN
│   ├── public/
│   │   └── cards/             ← изображения карт
│   ├── package.json
│   └── next.config.mjs
│
├── backend/                   ← Django
│   ├── manage.py
│   ├── config/
│   │   ├── settings/
│   │   └── urls.py
│   ├── apps/
│   │   ├── tarot/             ← карты, расклады, интерпретации
│   │   ├── users/             ← аккаунты, история
│   │   └── readings/          ← сессии раскладов
│   ├── requirements.txt
│   └── Dockerfile
│
├── data/
│   └── deck/
│       └── rider-waite.json   ← seed: 78 карт RU+EN
│
└── docs/
    ├── architecture.md
    ├── deploy.md
    └── prompts.md
```

---

## 4. Правила игры (НЕ нарушать)

1. **Никогда не ломать существующие API.** Меняешь схему ответа — добавь новую версию endpoint'а.
2. **Mobile-first.** UI верстается сначала под телефон, потом под десктоп.
3. **Always type-safe.** TypeScript strict, Pydantic/serializers на бэке.
4. **Все тексты — через i18n.** Никаких хардкод-строк на русском или английском в JSX/HTML.
5. **AI-вызовы — только через сервисный слой.** Никаких прямых fetch'ей к Anthropic из компонентов.
6. **Секреты — только через ENV.** Никаких ключей в коде, никогда.
7. **Тесты обязательны** для AI-логики, парсера колоды, аутентификации.
8. **Эстетика важна.** Это продукт про атмосферу. Серый bootstrap-UI — нет.

---

## 5. Команда субагентов

Когда задача комплексная — главная сессия Claude Code делегирует её подходящему субагенту.

| Агент | Зона ответственности |
|---|---|
| `frontend-agent` | Next.js UI, анимации, i18n, доступность |
| `backend-agent` | Django API, бизнес-логика, auth |
| `tarot-ai-agent` | Промпты, narrative, интерпретации раскладов |
| `qa-agent` | Тесты, регрессии, проверка UI/API |
| `deploy-agent` | Docker, CI/CD, Vercel/Railway, env |
| `database-agent` | Миграции, схема, индексы, бэкапы |
| `content-agent` | Описания карт, SEO-тексты, onboarding |

Определения и system prompts лежат в `.claude/agents/`.

### Когда какого агента звать

- «Сделай красивую анимацию тасования» → `frontend-agent`
- «Добавь endpoint /api/spreads/» → `backend-agent`
- «Сгенерируй интерпретацию Кельтского креста» → `tarot-ai-agent`
- «Прогон тестов перед мерджем» → `qa-agent`
- «Задеплой stage» → `deploy-agent`
- «Добавь поле user.timezone» → `database-agent` (миграция) + `backend-agent` (логика)
- «Напиши описания 22 Старших Арканов» → `content-agent`

### Правило границ

Каждый агент **никогда не лезет в чужую зону**. Frontend-agent не правит Django models. Backend-agent не правит CSS. Если задача затрагивает несколько зон — главная сессия разбивает её и делегирует частями.

---

## 6. Roadmap (MVP-first)

**Этап 1 — Колода и shuffle (текущий)**
- 78 карт с изображениями и описаниями (RU+EN)
- Анимация тасования
- Расклад из 3 карт
- Базовые описания карт (без AI)

**Этап 2 — AI-интерпретация**
- Форма вопроса пользователя
- Вызов Claude API с системным промптом
- Streaming ответа
- Сохранение расклада в БД

**Этап 3 — Аккаунты и история**
- Регистрация / вход (email + magic link)
- История раскладов пользователя
- Возможность вернуться к прошлому раскладу

**Этап 4 — Premium**
- Stripe / ЮKassa подписка
- Премиум-расклады (Кельтский крест, Древо жизни)
- Расширенные интерпретации

---

## 7. Тон AI-интерпретаций (важно)

Все тексты от tarot-ai-agent должны быть:

- **мистическими**, но не пугающими
- **тёплыми** и поддерживающими
- **эмоционально умными** — обращаться к чувствам пользователя
- **сюжетными** — это история, а не справка
- **этически нейтральными** — никаких категорических предсказаний болезней, смертей, разводов
- **разнообразными** — никаких шаблонных «вас ждут перемены»

Подробные правила и примеры — в `.claude/agents/tarot-ai.md`.

---

## 8. Полезные команды

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Всё сразу через Docker
docker compose up --build
```

---

## 9. Когда сомневаешься

1. Перечитай этот файл.
2. Прочти определение нужного субагента в `.claude/agents/`.
3. Если задача неочевидна — задай уточняющий вопрос пользователю **до** того, как писать код.

Никогда не угадывай требования. Лучше переспросить, чем переделывать.
