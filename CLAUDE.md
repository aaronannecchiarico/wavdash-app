# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# WavDash Monorepo

This monorepo contains three integrated applications for an AI-powered audio processing platform:

1. **Laravel App** (`app/`) - Main web application (Laravel 12 + React + Inertia.js)
2. **Audio Service** (`audio-service/`) - FastAPI microservice for audio processing
3. **Marketing Site** (`marketing/`) - Astro-based public marketing website

## 🚀 Quick Start

### Docker via Colima (Recommended)

**Prerequisites**: Colima installed and running (`brew install colima docker docker-compose`)

```bash
# Start Colima (if not running)
colima start

# Start all services in development mode (detached)
make dev-detached

# Stop all services
make stop
```

**Services after `make dev-detached`:**
- Laravel App: http://localhost:8000
- Audio Service API: http://localhost:8001
- Marketing Site: http://localhost:4321
- Celery Flower (monitoring): http://localhost:5555
- phpMyAdmin: http://localhost:8080
- Redis Commander: http://localhost:8081
- MailHog (email): http://localhost:8025

**Database**: Uses MySQL in Docker containers (production-like environment)

### Local Development (No Docker)

**Database**: Uses SQLite for Laravel (no MySQL required)

```bash
# Terminal 1: Laravel App (SQLite)
cd app && composer run dev

# Terminal 2: Audio Service Worker
cd audio-service
source wavdash-audio-extraction-service-local/bin/activate
python scripts/start_worker.py

# Terminal 3: Audio Service API
cd audio-service
source wavdash-audio-extraction-service-local/bin/activate
uvicorn main:app --reload --port 8001

# Terminal 4: Marketing Site
cd marketing && npm run dev
```

**Note**: Redis is optional for local dev (use `QUEUE_CONNECTION=sync` in Laravel)

## 📋 Essential Commands

All commands via root `Makefile`. Run `make help` to see all options.

### Development
- `make dev` - Start all services (Docker, attached logs)
- `make dev-detached` - Start all services in background
- `make stop` - Stop all Docker services
- `make build` - Build all Docker images
- `make clean` - Remove all Docker resources
- `make install` - Install dependencies for all services

### Testing
- `make test` - Run all test suites
- `make test-app` - Run Laravel tests (PHPUnit)
- `make test-audio` - Run audio service tests (pytest)
- `make test-marketing` - Build marketing site (test)

### Code Quality
- `make lint` - Run linters for all services
- `make format` - Format code for all services
- `make analyse` - Run static analysis (Laravel PHPStan)

### Utilities
- `make app-shell` - Open shell in Laravel container
- `make audio-shell` - Open shell in audio service container
- `make marketing-shell` - Open shell in marketing container
- `make logs` - View logs for all services
- `make logs-app` - View Laravel logs only
- `make logs-audio` - View audio service logs only

### Database
- `make migrate` - Run Laravel migrations
- `make migrate-fresh` - Fresh migration with seeding

### Production
- `make prod` - Start services in production mode
- `make prod-stop` - Stop production services
- `make prod-logs` - View production logs
- `make prod-build` - Build production images
- Production uses `docker-compose.yml` + `docker-compose.prod.yml` overlay
- Nginx configs in `deploy/nginx/` — one per domain (wavdash.com, app.wavdash.com, ws.wavdash.com)
- VPS provisioning guide: `deploy/RUNBOOK.md`
- Production env template: `.env.production.example`

## 🔄 Inter-Service Communication

### Service URLs (Docker)
- **Laravel → Audio Service**: `http://audio-api:8000`
- **Marketing → Laravel**: `http://app:8000`
- **All → Redis**: `redis://redis:6379`
- **Laravel → MySQL**: `mysql://mysql:3306`

### Service URLs (Local)
- **Laravel → Audio Service**: `http://localhost:8001`
- **Marketing → Laravel**: `http://localhost:8000`
- **All → Redis**: `redis://localhost:6379` (optional)
- **Laravel Database**: SQLite file at `app/database/database.sqlite`

### Environment Configuration

Each service has environment variables in `.env` files. Copy from `.env.example` files.

**app/.env:**
```bash
# Database - SQLite for local, MySQL for Docker
DB_CONNECTION=sqlite  # Local development
# DB_CONNECTION=mysql  # Docker/production

# Service URLs
AUDIO_SERVICE_URL=http://audio-api:8000  # Docker
# AUDIO_SERVICE_URL=http://localhost:8001  # Local

# Queue - optional for local dev
QUEUE_CONNECTION=sync  # Local (no Redis needed)
# QUEUE_CONNECTION=redis  # Docker/production
```

**audio-service/.env:**
```bash
REDIS_HOST=redis  # Docker
# REDIS_HOST=localhost  # Local
LOCAL_STORAGE_PATH=./storage  # Shared with Laravel
```

**marketing/.env:**
```bash
PUBLIC_APP_URL=http://app:8000  # Docker
# PUBLIC_APP_URL=http://localhost:8000  # Local
```

## 🏗️ Architecture Overview

### Data Flow
1. **User uploads audio** → Marketing/App → Storage
2. **Processing request** → Laravel → Audio Service (async via Celery)
3. **Analysis complete** → Callback → Laravel → WebSocket event → UI update

### Technology Stack

**Laravel App:**
- Laravel 12, Laravel Octane (FrankenPHP), Laravel Reverb (WebSockets)
- React 19 + Inertia.js v2, TypeScript, Tailwind CSS v4
- Filament v4 (admin panel at `/admin`)
- Database: SQLite (local) / MySQL 8.0 (Docker/production)

**Audio Service:**
- FastAPI, Celery + Redis
- Librosa (audio analysis), Demucs (stem separation)
- Python 3.11+

**Marketing Site:**
- Astro 5, React 19, TypeScript, Tailwind CSS v4

**Shared Infrastructure:**
- Redis 7 (cache/queue), Colima + Docker Compose
- GitHub Actions for CI/CD

### Storage Structure
All services share common storage volume for audio files. User-based organization:
```
uploads/{user_id}/YYYY/MM/DD/filename.mp3
processed/{user_id}/YYYY/MM/DD/filename_features.json
stems/{user_id}/YYYY/MM/DD/filename/vocals.wav
```

## 🎯 Service-Specific Guidance

Each service has detailed `CLAUDE.md` files:

- **[app/CLAUDE.md](app/CLAUDE.md)** - Laravel commands, patterns, architecture
- **[audio-service/CLAUDE.md](audio-service/CLAUDE.md)** - Audio processing details
- **[marketing/CLAUDE.md](marketing/CLAUDE.md)** - Marketing site specifics

**Important:** Read the service-specific CLAUDE.md when working in that service directory.

## 🔀 Git Workflow

### Conventional Commits

**Format:**
```
<type>(<scope>): <subject>

Types: feat, fix, refactor, perf, style, test, docs, chore, ci
Scopes: app, audio, marketing, docker, ci, docs
```

**Examples:**
```bash
feat(app): add user dashboard
fix(audio): resolve BPM detection issue
docs(marketing): update component documentation
chore(docker): optimize build caching
```

### Git Rules

**DO:**
- ✅ Use conventional commit format
- ✅ Run tests before committing (`make test`)
- ✅ Format code before committing (`make format`)
- ✅ Keep commits focused and atomic

**DO NOT:**
- ❌ Commit directly to `main` without PR
- ❌ Add co-author tags or AI attribution (no "Co-Authored-By: Claude" or "Generated with Claude Code")
- ❌ Commit without running tests
- ❌ Mix changes across services in one commit

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `chore/*` - Maintenance tasks

## 🛠️ Troubleshooting

**YAML validation (no pyyaml on macOS):**
- Use `ruby -ryaml -e "YAML.safe_load(File.read('file.yml'))"` instead of Python yaml module

### Docker/Colima Issues

**Colima not running:**
```bash
colima status
colima start
# If issues: colima delete && colima start
```

**Services won't start:**
```bash
make clean  # Remove all Docker resources
make build  # Rebuild images
make dev    # Start fresh
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8001
lsof -i :4321
```

**Colima resource limits:**
```bash
colima status
# Adjust if needed
colima stop
colima start --cpu 4 --memory 8
```

### Local Development Issues

**Laravel:**
```bash
cd app
php artisan config:clear
php artisan cache:clear
php artisan route:clear
composer dump-autoload
```

**Audio Service:**
```bash
cd audio-service
source wavdash-audio-extraction-service-local/bin/activate
python scripts/validate_setup.py
```

**Marketing:**
```bash
cd marketing
rm -rf node_modules package-lock.json
npm install
```

### Inter-Service Communication

**Laravel can't reach audio service:**
- Check `AUDIO_SERVICE_URL` in `app/.env`
- Verify audio service is running: `curl http://localhost:8001/health`
- Check Docker network: `docker network inspect wavdash_wavdash`

**Marketing can't authenticate with Laravel:**
- Check `PUBLIC_APP_URL` in `marketing/.env`
- Verify CORS settings in `app/config/cors.php`
- Check session/cookie domain settings

## 📚 Additional Resources

- [README.md](README.md) - Complete documentation
- [MIGRATION.md](MIGRATION.md) - Migration guide from separate repos
- [.github/workflows/ci.yml](.github/workflows/ci.yml) - CI/CD pipeline

## ⚠️ Important Notes

1. **Storage Paths**: All services must use the same storage path structure for audio files
2. **Redis**: Shared between Laravel queues and Celery workers
3. **MySQL**: Used only by Laravel application (in Docker)
4. **Network**: All services communicate via the `wavdash` Docker network
5. **Logs**: Service logs available in `<service>/storage/logs` or via `make logs`
6. **Commit Messages**: Never include AI attribution or co-author tags

---

This monorepo provides:
- ✅ Unified development environment
- ✅ Shared infrastructure (DB, Redis, Storage)
- ✅ Simplified deployment
- ✅ Complete git history preservation
- ✅ Docker-based consistency
- ✅ Flexible local development options
