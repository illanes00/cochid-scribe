# Scribe Deployment Guide

## Infrastructure Registration

Add to `/etc/infra/sites.yaml`:

```yaml
- slug: illanes00-scribe-api
  host: scribe.illanes00.cl
  port: 8132
  health: /health
  path: /api

- slug: illanes00-scribe
  host: scribe.illanes00.cl
  port: 8133
  health: /
  path: /
```

## Systemd Services

### Backend Service

Create `~/.config/systemd/user/scribe-backend.service` (user-level systemd):

```ini
[Unit]
Description=illanes00-scribe-backend (FastAPI)
After=network.target

[Service]
WorkingDirectory=/srv/projects/illanes00-scribe/backend
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/srv/projects/illanes00-scribe/.env
ExecStart=/srv/projects/illanes00-scribe/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8132
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Frontend Service

Create `~/.config/systemd/user/scribe-frontend.service` (user-level systemd):

```ini
[Unit]
Description=illanes00-scribe-frontend (Next.js)
After=network.target

[Service]
WorkingDirectory=/srv/projects/illanes00-scribe/frontend
Environment=NODE_ENV=production
Environment=PORT=8133
ExecStart=npm start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Note:** The frontend uses relative API paths (`/api/v1/*`) which Caddy proxies to the backend.
Do NOT set `NEXT_PUBLIC_API_URL` to a localhost address - it must be empty for production.

## Caddy Configuration

Add to `/etc/caddy/sites.d/apps.caddy`:

```caddy
scribe.illanes00.cl {
    encode zstd gzip

    # API routes go to backend
    handle /api/* {
        reverse_proxy localhost:8132
    }

    # Health check
    @scribe_health path /health /health/
    handle @scribe_health {
        reverse_proxy localhost:8132
    }

    # Everything else goes to frontend
    handle {
        reverse_proxy localhost:8133
    }
}
```

**Important:** Do NOT use `uri strip_prefix /api` - the FastAPI backend expects
the full path including `/api/v1/...`. Client-side fetch requests go directly
to Caddy, not through Next.js rewrites.

## Environment Variables

Create `/etc/infra/env.d/scribe.env`:

```bash
ANTHROPIC_API_KEY=your_key_here
DATABASE_URL=postgresql://scribe:password@localhost:5432/scribe
SECRET_KEY=generate_a_secure_key
```

## Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createuser scribe
sudo -u postgres createdb -O scribe scribe

# Set password
sudo -u postgres psql -c "ALTER USER scribe WITH PASSWORD 'secure_password';"

# Initialize schema
cd /srv/projects/scribe/backend
source venv/bin/activate
python -c "from app.db.session import init_db; init_db()"
```

## Deployment Steps

1. **Clone/Update repository**:
   ```bash
   cd /srv/projects/scribe
   git pull origin main
   ```

2. **Backend setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend setup**:
   ```bash
   cd frontend
   npm ci
   npm run build
   ```

4. **Start services**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable illanes00-scribe-api illanes00-scribe
   sudo systemctl start illanes00-scribe-api illanes00-scribe
   ```

5. **Reload Caddy**:
   ```bash
   sudo systemctl reload caddy
   ```

6. **Verify health**:
   ```bash
   curl http://localhost:8132/health
   curl http://localhost:8133/
   curl https://scribe.illanes00.cl/health
   ```

## CI/CD

CI runs on GitHub Actions (`.github/workflows/ci.yml`).

CD is handled by vps-deploy. The repository should be registered in the deploy system to trigger automatic deployments on push to main.
