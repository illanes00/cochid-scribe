# Scribe Deployment Guide

This guide covers deploying and maintaining Scribe in production.

## Architecture Overview

```
                    ┌─────────────┐
                    │   Caddy     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │  Frontend   │ │  Backend    │ │   Static    │
    │  (Next.js)  │ │  (FastAPI)  │ │   Files     │
    │  :3000      │ │  :8000      │ │  /uploads   │
    └─────────────┘ └──────┬──────┘ └─────────────┘
                           │
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    │   Database  │
                    └─────────────┘
```

## Production Environment

- **URL**: https://scribe.illanes00.cl
- **Server**: VPS with self-hosted GitHub Actions runner
- **Services**: Managed via systemd user services

### Service Ports

| Service  | Internal Port | External URL |
|----------|---------------|--------------|
| Backend  | 8132          | /api/v1/*    |
| Frontend | 8133          | /*           |

## Deployment Process

### Automatic Deployment (CD)

Merges to `main` trigger automatic deployment via GitHub Actions:

1. Saves current commit SHA for rollback
2. Pulls latest code
3. Installs dependencies
4. Runs database migrations
5. Builds frontend
6. Restarts services
7. Health checks with automatic rollback on failure

### Manual Deployment

```bash
# SSH to server
ssh user@vps-deploy

# Navigate to project
cd /srv/projects/illanes00-scribe

# Pull latest changes
git fetch origin && git reset --hard origin/main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd ../frontend
npm install
npm run build

# Restart services
systemctl --user restart scribe-backend scribe-frontend

# Verify
curl http://localhost:8132/health
curl http://localhost:8133/
```

## Database Management

### Migrations

```bash
cd backend
source venv/bin/activate

# Check current revision
alembic current

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"
```

### Backup

```bash
# PostgreSQL backup
pg_dump scribe > backup_$(date +%Y%m%d).sql

# SQLite backup (development)
cp scribe.db scribe_backup_$(date +%Y%m%d).db
```

## Monitoring

### Health Checks

```bash
# Simple health check
curl https://scribe.illanes00.cl/health

# Detailed health check
curl https://scribe.illanes00.cl/api/v1/health/detailed
```

### Logs

```bash
# Backend logs
journalctl --user -u scribe-backend -f

# Frontend logs
journalctl --user -u scribe-frontend -f

# Combined
journalctl --user -u scribe-backend -u scribe-frontend -f
```

### Log Format (Production)

Backend uses structured JSON logging in production:

```json
{
  "event": "http.request",
  "method": "GET",
  "path": "/api/v1/documents",
  "status_code": 200,
  "duration_ms": 45.2,
  "timestamp": "2024-01-20T12:00:00Z"
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
systemctl --user status scribe-backend

# Check for port conflicts
sudo lsof -i :8132

# Check Python dependencies
cd backend && source venv/bin/activate
pip check
```

### Database Connection Issues

```bash
# Test connection
PGPASSWORD=xxx psql -h localhost -U scribe -d scribe -c "SELECT 1"

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Frontend Build Fails

```bash
cd frontend

# Clear cache
rm -rf .next node_modules
npm install
npm run build

# Check for TypeScript errors
npx tsc --noEmit
```

### Rollback Procedure

```bash
# Find previous working commit
git log --oneline -10

# Rollback to specific commit
git reset --hard <commit-sha>

# Rebuild and restart
cd backend && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
systemctl --user restart scribe-backend scribe-frontend
```

## Configuration

### Environment Variables

Backend (`.env`):
```
DATABASE_URL=postgresql://user:pass@localhost/scribe
ANTHROPIC_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=...
ENVIRONMENT=production
```

Frontend:
```
BACKEND_URL=http://127.0.0.1:8132
```

### Systemd Services

Backend service (`~/.config/systemd/user/scribe-backend.service`):
```ini
[Unit]
Description=Scribe Backend API
After=network.target

[Service]
Type=simple
WorkingDirectory=/srv/projects/illanes00-scribe/backend
Environment=PATH=/srv/projects/illanes00-scribe/backend/venv/bin
ExecStart=/srv/projects/illanes00-scribe/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8132
Restart=always

[Install]
WantedBy=default.target
```

Frontend service (`~/.config/systemd/user/scribe-frontend.service`):
```ini
[Unit]
Description=Scribe Frontend
After=network.target

[Service]
Type=simple
WorkingDirectory=/srv/projects/illanes00-scribe/frontend
ExecStart=/usr/bin/npm start -- -p 8133
Restart=always

[Install]
WantedBy=default.target
```

## Security Checklist

- [ ] Database credentials not in code
- [ ] API keys in environment variables
- [ ] HTTPS enabled via Caddy
- [ ] CORS configured for production domain
- [ ] Health endpoints don't expose sensitive info
- [ ] Uploads directory permissions set correctly

## Performance Tips

1. **Database**: Add indexes for frequently queried columns
2. **Frontend**: Enable Next.js standalone mode for smaller Docker images
3. **Caching**: Consider adding Redis for session/cache storage
4. **CDN**: Use Cloudflare for static asset caching
