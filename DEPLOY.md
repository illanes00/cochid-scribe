# Scribe Deployment Guide

## Infrastructure Registration

Add to `/etc/infra/sites.yaml`:

```yaml
- slug: illanes00-scribe-api
  host: scribe.illanes00.cl
  port: 8121
  health: /health
  path: /api

- slug: illanes00-scribe
  host: scribe.illanes00.cl
  port: 8122
  health: /
  path: /
```

## Systemd Services

### Backend Service

Create `/etc/systemd/system/illanes00-scribe-api.service`:

```ini
[Unit]
Description=Scribe API (FastAPI)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/projects/scribe/backend
Environment=PORT=8121
Environment=DATABASE_URL=postgresql://scribe:PASSWORD@localhost:5432/scribe
EnvironmentFile=/etc/infra/env.d/scribe.env
ExecStart=/srv/projects/scribe/backend/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Frontend Service

Create `/etc/systemd/system/illanes00-scribe.service`:

```ini
[Unit]
Description=Scribe Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/projects/scribe/frontend
Environment=PORT=8122
Environment=NEXT_PUBLIC_API_URL=https://scribe.illanes00.cl/api
ExecStart=/usr/bin/node /srv/projects/scribe/frontend/.next/standalone/server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Caddy Configuration

Create `/etc/caddy/sites.d/illanes00-scribe.caddy`:

```caddy
scribe.illanes00.cl {
    import tls_cf

    # API backend - DO NOT use uri strip_prefix, backend expects /api/v1/* paths
    handle /api/* {
        reverse_proxy localhost:8121
    }

    # Health check for backend
    handle /health {
        reverse_proxy localhost:8121
    }

    # Frontend
    handle {
        reverse_proxy localhost:8122
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
   curl http://localhost:8121/health
   curl http://localhost:8122/
   curl https://scribe.illanes00.cl/health
   ```

## CI/CD

CI runs on GitHub Actions (`.github/workflows/ci.yml`).

CD is handled by vps-deploy. The repository should be registered in the deploy system to trigger automatic deployments on push to main.
