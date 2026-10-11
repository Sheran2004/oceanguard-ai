# Production Deployment Guide

This guide walks through deploying OceanGuard AI to a production environment.

## 1. Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Python    | 3.11+   | 3.12 recommended |
| Node.js   | 18+     | only for building the frontend |
| Docker    | 24+     | optional but recommended |
| PostgreSQL| 14+     | optional — SQLite also supported for low traffic |

## 2. Environment Variables

Copy `.env.example` to `.env` and set the production values:

```bash
cp .env.example .env
```

Critical variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_ENV` | Set to `production` for JSON logs | `production` |
| `SECRET_KEY` | JWT signing key — **must be a long random string** | `openssl rand -hex 32` |
| `DATABASE_URL` | Production database URL | `postgresql+psycopg2://user:pass@db:5432/oceaguard` |
| `CORS_ORIGINS` | Comma-separated origins | `https://oceanguard.example.com` |
| `RATE_LIMIT_PER_MINUTE` | Per-IP rate limit | `120` |
| `BACKEND_HOST` / `BACKEND_PORT` | Bind address | `0.0.0.0` / `8000` |
| `UPLOAD_DIR`, `REPORT_DIR` | Persistent storage paths | `/var/lib/oceanguard/uploads` |
| `MAX_UPLOAD_SIZE_MB` | Upload size cap | `25` |

## 3. Backend Deployment (Docker — recommended)

```bash
# 1. Generate a strong secret
export SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -hex 16)

# 2. Build and start all services
docker compose --profile production up -d --build

# 3. Check health
curl -fsS http://localhost/health

# 4. Tail logs
docker compose logs -f backend
```

This brings up:
- `postgres` — PostgreSQL 16
- `backend` — Gunicorn with 4 Uvicorn workers (multi-process)
- `frontend` — nginx serving the built React bundle
- `nginx` — reverse proxy on ports 80/443

## 4. Backend Deployment (bare-metal)

```bash
# System dependencies
sudo apt install -y python3.12 python3.12-venv libgl1 libglib2.0-0 nginx postgresql

# Create user
sudo useradd -r -m -s /bin/bash oceanguard
sudo -u oceanguard mkdir /opt/oceanguard
cd /opt/oceanguard
git clone <your-repo> .

# Python env
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

# Migrate DB
cp .env.example .env  # then edit
.venv/bin/python scripts/generate_demo_data.py --clear --scans 8

# systemd unit at /etc/systemd/system/oceaguard-backend.service:
cat > /tmp/oceaguard-backend.service <<'EOF'
[Unit]
Description=OceanGuard AI Backend
After=network.target

[Service]
Type=simple
User=oceanguard
WorkingDirectory=/opt/oceanguard
EnvironmentFile=/opt/oceanguard/.env
ExecStart=/opt/oceanguard/.venv/bin/gunicorn app.main:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile -
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
sudo mv /tmp/oceanguard-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oceaguard-backend
```

## 5. Frontend Deployment

The frontend is a static SPA. Build once and serve with any HTTP server:

```bash
cd frontend
npm ci
npm run build
# Output is in frontend/dist
```

In production, copy `frontend/dist/` to `/var/www/oceaguard/` and serve via nginx:

```nginx
server {
    listen 80;
    server_name oceanguard.example.com;

    root /var/www/oceaguard;
    index index.html;

    location / {
        try_files $uri /index.html;  # SPA fallback
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 6. TLS / HTTPS

Use **Let's Encrypt** via certbot:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d oceaguard.example.com
```

Certificates auto-renew via a cron timer. Update `infra/nginx/nginx.conf` to listen on 443 if you prefer a hand-rolled config.

## 7. Database Migrations

The current release uses `Base.metadata.create_all()` for convenience. For production schema evolution use Alembic:

```bash
# One-time setup
cd backend
.venv/bin/alembic init alembic
# Configure alembic.ini / env.py to use app.models.database.Base.metadata

# Create + apply
.venv/bin/alembic revision --autogenerate -m "describe change"
.venv/bin/alembic upgrade head
```

## 8. Observability

| Concern | Recommendation |
|---------|----------------|
| Logs | Ship JSON logs from stdout to Loki / CloudWatch / ELK |
| Metrics | Prometheus exporter (`prometheus-fastapi-instrumentator`) |
| Tracing | OpenTelemetry SDK + OTLP exporter |
| Alerts | Health-check probe on `/health` (already configured in Docker) |
| Backups | `pg_dump` cron for PostgreSQL; periodic snapshots of `uploads/` |

## 9. Smoke Test

After deployment:

```bash
# Health
curl https://example.com/health

# Login
curl -X POST https://example.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'

# Browser
open https://example.com
```

## 10. Hardening Checklist

- [ ] Rotate default seeded passwords (`admin`, `demo-operator`)
- [ ] Set a real `SECRET_KEY` (≥32 bytes)
- [ ] Restrict `CORS_ORIGINS` to your domain
- [ ] Disable `ENABLE_DEMO_MODE` when a real model is loaded
- [ ] Enable HTTPS only (set `listen 80` to redirect)
- [ ] Set up backups for PostgreSQL and `uploads/`
- [ ] Configure log shipping to a central store
- [ ] Wire Prometheus + alerting
- [ ] Run `pytest` and lint in CI before deploying
- [ ] Review `infra/nginx/nginx.conf` rate limits

## 11. Updating

```bash
cd /opt/oceanguard
git pull
.venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart oceanguard-backend
cd frontend && npm ci && npm run build
sudo rsync -a dist/ /var/www/oceanguard/
```

---

**Questions?** See `README.md` for project overview or open an issue.