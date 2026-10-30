# VPS deployment guide

This deploys the demo to a Linux VPS with Docker Compose, Gunicorn, PostgreSQL, and Caddy. It is intentionally small and suitable for a demo—not a production compliance or high-availability runbook.

## What is already prepared

- `compose.yaml` is for local development on port `8010`.
- `compose.vps.yaml` is for the VPS: Gunicorn replaces Django's development server, static files are collected, the database stays private, and the app listens only on `127.0.0.1:8010`.
- `.env.vps.example` lists every required server-side setting.
- `deploy/Caddyfile` is a reverse-proxy template that provides HTTPS.

## 1. Prerequisites

Before deploying:

1. Point an A record such as `demo.example.com` to the VPS public IPv4 address. Add an AAAA record too only if the VPS has working IPv6.
2. Allow inbound TCP ports `80` and `443` in the VPS firewall/security group. Do not expose port `8010` publicly.
3. Install Docker Engine plus the Docker Compose plugin and install Caddy on the VPS.
4. Choose a new, test-mode-only Stripe key pair for this demo. Never use a live Stripe key.

Caddy can automatically obtain and renew HTTPS certificates when the domain resolves to the VPS and ports 80/443 are reachable. It also forwards `X-Forwarded-Proto`, which the application is configured to trust only when `BEHIND_HTTPS_PROXY=true`. [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https), [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

## 2. Copy the project

From your local computer, copy the source without secrets, Docker volumes, or Git metadata:

```bash
rsync -av --delete \
  --include '.env.example' --include '.env.vps.example' \
  --filter=':- .gitignore' --exclude '.git' \
  --exclude '__pycache__' --exclude 'staticfiles' \
  /path/to/zain-store/ \
  your-user@your-vps:/opt/zain-store/
```

On the VPS:

```bash
cd /opt/zain-store
cp .env.vps.example .env
chmod 600 .env
```

Edit `.env` using a terminal editor. Set your actual domain in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`; replace all placeholder secrets. Generate a Django secret value without displaying it in shell history:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
```

## 3. Start the application

From `/opt/zain-store`:

```bash
docker compose -f compose.vps.yaml up --build -d
docker compose -f compose.vps.yaml ps
docker compose -f compose.vps.yaml logs -f zain-store-web
```

Seed data and create the two accounts:

```bash
docker compose -f compose.vps.yaml exec zain-store-web python manage.py seed_catalog
docker compose -f compose.vps.yaml exec zain-store-web python manage.py create_demo_customer --password 'choose-a-temporary-demo-password'
docker compose -f compose.vps.yaml exec zain-store-web python manage.py createsuperuser
```

Confirm the application itself is reachable only from the VPS:

```bash
curl http://127.0.0.1:8010/health/
```

It should return `{"status": "ok"}`.

## 4. Configure HTTPS with Caddy

Copy the template into Caddy's configuration location, replacing `demo.example.com` first:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudoedit /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Then verify in a browser:

```text
https://demo.example.com/health/
```

## 5. Configure the Stripe webhook

In the Stripe Dashboard **test mode**, create a webhook endpoint:

```text
https://demo.example.com/payments/stripe/webhook/
```

Subscribe to:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `checkout.session.expired`

Copy Stripe's endpoint signing secret into `STRIPE_WEBHOOK_SECRET` in `/opt/zain-store/.env`, then restart the web service:

```bash
docker compose -f compose.vps.yaml up -d --force-recreate zain-store-web
```

## 6. Update later

Copy changed source files again, then run:

```bash
cd /opt/zain-store
docker compose -f compose.vps.yaml up --build -d
docker compose -f compose.vps.yaml exec zain-store-web python manage.py migrate
```

Do not run `docker compose down -v` unless you deliberately want to erase the PostgreSQL demo data.
