# Deploy Guide

## Local development

```bash
cp .env.example .env       # then fill in ANTHROPIC_API_KEY
docker compose up --build
```

- App (via nginx): http://localhost
- Frontend dev: http://localhost:3000 · Backend API: http://localhost:8000/api/

---

## Production — VPS (Docker + Cloudflare)

The whole stack runs in Docker on one Linux VPS, with **Cloudflare in front**
(orange-cloud proxy) for free TLS + L3/L4 DDoS absorption + WAF. Origin nginx
listens on plain :80 and trusts Cloudflare's `X-Forwarded-Proto`.

### 1. Provision the server
- Ubuntu 22.04+/Debian 12+, 2 vCPU / 2–4 GB RAM minimum.
- Create a non-root sudo user; SSH in as that user.

### 2. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # re-login after this
```

### 3. Firewall (ufw) — expose only what's needed
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH        # 22
sudo ufw allow 80/tcp         # nginx (Cloudflare → origin)
sudo ufw enable
```
> Postgres (5432) and Redis (6379) are **never published** in prod
> (`docker-compose.prod.yml` gives them no host ports). Only nginx is reachable.
> For extra safety, restrict :80 to Cloudflare IP ranges
> (https://www.cloudflare.com/ips/) instead of `allow 80/tcp`.

### 4. fail2ban — block SSH brute force
```bash
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local >/dev/null <<'EOF'
[sshd]
enabled  = true
maxretry = 4
bantime  = 1h
findtime = 10m
EOF
sudo systemctl enable --now fail2ban
```
App-level abuse (login/API floods) is handled by nginx rate-limit zones
(`api_limit` 20 r/s, `auth_limit` 12 r/min, `limit_conn` 50/IP) → HTTP 429.

### 5. Get the code + secrets
```bash
git clone https://github.com/n-sokirko/tarot-online.git
cd tarot-online
cp .env.prod.example .env.prod        # then fill EVERY value
python3 -c "import secrets; print(secrets.token_urlsafe(64))"  # DJANGO_SECRET_KEY
```
`.env.prod` is git-ignored — never commit it. Required keys: `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SETTINGS_MODULE=config.settings.prod`,
`POSTGRES_PASSWORD` (strong), `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_PAYMENT_SECRET`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`,
`NEXT_PUBLIC_API_URL=https://<your-domain>`.

### 6. Cloudflare
- DNS: A record `@` → VPS IP, **proxied** (orange cloud). Same for `www`.
- SSL/TLS mode: **Full**. Enable "Always Use HTTPS" + HSTS.
- WAF: turn on "Bot Fight Mode" and a rate-limiting rule on `/api/v1/auth/*`.
- Tunnel alternative: if you keep `cloudflared`, no inbound port is needed at all —
  drop `ufw allow 80` and mount `cloudflared/` creds (see the `tunnel` service).

### 7. Launch
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```
Backend auto-runs migrate + seed + collectstatic before gunicorn. Create an admin:
```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py createsuperuser
```

### 8. Verify
```bash
curl -I https://<your-domain>/            # 200, security headers present
curl -I https://<your-domain>/api/v1/cards/daily/
```
Confirm the Telegram bot is polling and that `/admin/` + DRF static render
(collectstatic → shared `static_files` volume → nginx `/static/`).

---

## Updates / rollback
- **Update:** `git pull && docker compose -f docker-compose.prod.yml up -d --build`
- **Rollback:** `git checkout <previous-tag>` then re-run the up command.
- **Migrations** are reversible: `... exec backend python manage.py migrate <app> <prev_number>`.
- **Backups:** `... exec db pg_dump -U tarot tarot > backup_$(date +%F).sql` (cron daily).
