// Railway Infrastructure as Code for the tarot backend.
//
// Topology: Postgres + one always-on web service + two cron services. The
// Telegram bot is NOT a service — it runs as a webhook inside the web process
// (apps/telegram_bot/bot_runtime.py), and the two daily pushes are cron runs of
// plain management commands, so neither Celery nor Redis is deployed. See
// docs/deploy-railway.md.
//
// Secrets are deliberately absent from this file: it is committed to git.
// Anything marked preserve() keeps whatever is already set on the service and
// is uploaded out of band by deploy/railway-set-vars.sh, which reads the
// gitignored .env.prod.
//
//   railway config plan     # preview, changes nothing
//   railway config apply    # apply
import { defineRailway, github, postgres, preserve, project, service, volume } from "railway/iac";

export default defineRailway(() => {
  const tarotOnline = github("n-sokirko/tarot-online", { branch: "master", checkSuites: false });

  const Postgres = postgres("Postgres", { region: "sfo" });
  Postgres.networking = { privateNetworkEndpoint: "postgres" };
  const postgresVolume = volume("postgres-volume", {
    alerts: { usage: { "80": {}, "95": {}, "100": {} } },
    allowOnlineResize: true,
    region: "sfo",
    sizeMB: 5000,
  });

  // The image is the same for every service (repo root as build context so
  // data/deck lands at /data/deck for seed_deck / seed_runes) — they differ
  // only in their start command.
  const build = {
    builder: "DOCKERFILE" as const,
    dockerfilePath: "backend/Dockerfile.railway",
    watchPatterns: ["backend/**", "data/**"],
  };

  // Every service talks to the same database and needs the same credentials.
  // Django reads POSTGRES_* (config/settings/base.py), not DATABASE_URL.
  const common = {
    DJANGO_SETTINGS_MODULE: "config.settings.prod",
    DJANGO_DEBUG: "False",
    DJANGO_SECRET_KEY: preserve(),

    POSTGRES_HOST: Postgres.env.PGHOST,
    POSTGRES_PORT: Postgres.env.PGPORT,
    POSTGRES_DB: Postgres.env.PGDATABASE,
    POSTGRES_USER: Postgres.env.PGUSER,
    POSTGRES_PASSWORD: Postgres.env.PGPASSWORD,

    TELEGRAM_BOT_USERNAME: "tarott_online_bot",
    TELEGRAM_BOT_TOKEN: preserve(),
    TELEGRAM_PAYMENT_SECRET: preserve(),
    TELEGRAM_WEBHOOK_SECRET: preserve(),
    TELEGRAM_REQUIRED_CHANNEL: preserve(),
    TELEGRAM_REQUIRED_CHANNEL_URL: preserve(),

    ANTHROPIC_API_KEY: preserve(),
    ANTHROPIC_MODEL_FREE: preserve(),
    ANTHROPIC_MODEL_PREMIUM: preserve(),
    ANTHROPIC_MODEL_DEEP: preserve(),

    GOOGLE_CLIENT_ID: preserve(),
    PADDLE_ENV: preserve(),
    PADDLE_API_KEY: preserve(),
    PADDLE_WEBHOOK_SECRET: preserve(),
    PADDLE_CLIENT_TOKEN: preserve(),
    PADDLE_PRODUCT_PREMIUM_MONTHLY: preserve(),
    PADDLE_PRICE_PREMIUM_MONTHLY: preserve(),
    PADDLE_PRODUCT_CREDITS_SMALL: preserve(),
    PADDLE_PRICE_CREDITS_SMALL: preserve(),
    PADDLE_PRODUCT_CREDITS_LARGE: preserve(),
    PADDLE_PRICE_CREDITS_LARGE: preserve(),

    // Points at Vercel until sokirdon.com is switched over; used for the bot's
    // WebApp menu button and the links inside the daily pushes.
    WEBAPP_URL: preserve(),
  };

  const web = service("web", {
    source: tarotOnline,
    build,
    deploy: {
      startCommand: "sh start-railway-web.sh",
      healthcheckPath: "/api/healthz/",
      healthcheckTimeout: 300,
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 5,
    },
    replicas: { sfo: 1 },
    env: {
      ...common,
      // healthcheck.railway.app is required: Railway probes /api/healthz/ with
      // that Host header, and without it Django answers 400 and the deploy
      // never goes healthy.
      DJANGO_ALLOWED_HOSTS: "${{RAILWAY_PUBLIC_DOMAIN}},healthcheck.railway.app",
      CSRF_TRUSTED_ORIGINS: "https://${{RAILWAY_PUBLIC_DOMAIN}}",
      // manage.py set_telegram_webhook (run from start-railway-web.sh) appends
      // /api/v1/telegram/webhook/ to this and registers it with Telegram.
      TELEGRAM_WEBHOOK_BASE_URL: "https://${{RAILWAY_PUBLIC_DOMAIN}}",
      CORS_ALLOWED_ORIGINS: preserve(),
    },
  });

  // Cron services boot the same image, run one management command and exit —
  // Railway bills only the seconds they are up. Schedules are UTC, matching the
  // CELERY_BEAT_SCHEDULE they replace (config/settings/base.py).
  const cronDailyPush = service("cron-daily-push", {
    source: tarotOnline,
    build,
    deploy: {
      startCommand: "python manage.py send_daily_push",
      cronSchedule: "0 8 * * *",
      restartPolicyType: "NEVER",
    },
    replicas: { sfo: 1 },
    env: { ...common },
  });

  const cronDailyHoroscope = service("cron-daily-horoscope", {
    source: tarotOnline,
    build,
    deploy: {
      startCommand: "python manage.py send_daily_horoscope",
      cronSchedule: "0 9 * * *",
      restartPolicyType: "NEVER",
    },
    replicas: { sfo: 1 },
    env: { ...common },
  });

  return project("tarot-online", {
    resources: [Postgres, postgresVolume, web, cronDailyPush, cronDailyHoroscope],
  });
});
