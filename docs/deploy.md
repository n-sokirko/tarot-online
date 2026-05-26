# Deploy Guide

Owned by `deploy-agent`.

## Local development

```bash
cp .env.example .env       # then fill in ANTHROPIC_API_KEY
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- API docs: http://localhost:8000/api/docs/
- Postgres: localhost:5432 (user/pass: tarot/tarot)

## Staging

- Push to branch `staging` → Vercel preview + Railway staging deploy auto-triggered

## Production

- Tag `vX.Y.Z` on `main` → release pipeline runs
- Pre-deploy: QA agent runs full checklist (see `agents/qa.md`)
- Post-deploy: monitor Sentry + Anthropic dashboard for 15 minutes

## Rollback

- Vercel: redeploy previous deployment from dashboard
- Railway: rollback button on the service
- Migrations: every migration must be reversible; run `python manage.py migrate <app> <previous_number>`
