# Claude Code Directives for WavDash Monorepo

This document provides essential context for working on the **WavDash Monorepo**, which contains three integrated applications:

1. **Laravel App** (`app/`) - Main web application
2. **Audio Service** (`audio-service/`) - FastAPI microservice for audio processing
3. **Marketing Site** (`marketing/`) - Astro-based public marketing website

---

## 🏗️ Monorepo Structure

```
wavdash/
├── app/                    # Laravel 12 application (main app)
│   ├── app/                # Laravel application code
│   ├── resources/          # Frontend React + Inertia.js
│   ├── CLAUDE.md           # Laravel-specific guidance
│   ├── Dockerfile          # Multi-stage Dockerfile
│   └── ...
├── audio-service/          # FastAPI audio processing microservice
│   ├── services/           # Core business logic
│   ├── tasks/              # Celery tasks
│   ├── routes/             # API endpoints
│   ├── CLAUDE.md           # Audio service guidance
│   ├── Dockerfile          # Python/FastAPI Dockerfile
│   └── ...
├── marketing/              # Astro marketing site
│   ├── src/                # Astro pages and components
│   ├── CLAUDE.md           # Marketing site guidance
│   ├── Dockerfile          # Node.js/Astro Dockerfile
│   └── ...
├── docker-compose.yml      # Production orchestration
├── docker-compose.dev.yml  # Development with hot-reload
├── Makefile                # Convenience commands
├── CLAUDE.md               # This file (monorepo guidance)
├── README.md               # Monorepo documentation
└── MIGRATION.md            # Migration guide from separate repos
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended for Full Stack)

```bash
# Start all services in development mode
make dev

# Or detached mode
make dev-detached

# Stop services
make stop
```

**Services available after `make dev-detached`:**
- Laravel App: http://localhost:8000
- Audio Service API: http://localhost:8001
- Marketing Site: http://localhost:4321
- Celery Flower (monitoring): http://localhost:5555
- phpMyAdmin: http://localhost:8080
- Redis Commander: http://localhost:8081
- MailHog (email): http://localhost:8025

### Option 2: Local Development (No Docker)

For faster iteration, you can run services locally:

```bash
# Terminal 1: Laravel App
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

---

## 📋 Common Commands

All commands are available via the root `Makefile`. Run `make help` to see all available commands.

### Development
- `make dev` - Start all services (Docker)
- `make dev-detached` - Start all services in background
- `make dev-local` - Print instructions for local development
- `make stop` - Stop all Docker services
- `make build` - Build all Docker images
- `make clean` - Remove all Docker resources

### Testing
- `make test` - Run all test suites
- `make test-app` - Run Laravel tests only
- `make test-audio` - Run audio service tests only
- `make test-marketing` - Build marketing site (test)

### Code Quality
- `make lint` - Run linters for all services
- `make format` - Format code for all services
- `make analyse` - Run static analysis (Laravel)

### Utilities
- `make app-shell` - Open shell in Laravel container
- `make audio-shell` - Open shell in audio service container
- `make marketing-shell` - Open shell in marketing container
- `make logs` - View logs for all services
- `make install` - Install dependencies for all services

---

## 🔄 Inter-Service Communication

### Service URLs (Docker)

When running via Docker, services communicate using service names:

- **Laravel → Audio Service**: `http://audio-api:8000`
- **Marketing → Laravel**: `http://app:8000`
- **All → Redis**: `redis://redis:6379`
- **Laravel → MySQL**: `mysql://mysql:3306`

### Service URLs (Local)

When running locally:

- **Laravel → Audio Service**: `http://localhost:8001`
- **Marketing → Laravel**: `http://localhost:8000`
- **All → Redis**: `redis://localhost:6379`
- **Laravel → MySQL**: `mysql://localhost:3306`

### Configuration

Each service has environment variables that need to be configured:

**app/.env:**
```bash
AUDIO_SERVICE_URL=http://audio-api:8000  # Docker
# AUDIO_SERVICE_URL=http://localhost:8001  # Local
MARKETING_URL=http://marketing:4321
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

---

## 🎯 Service-Specific Guidance

Each service has its own detailed `CLAUDE.md`:

- **[app/CLAUDE.md](app/CLAUDE.md)** - Laravel application specifics, commands, patterns
- **[audio-service/CLAUDE.md](audio-service/CLAUDE.md)** - Audio processing service details
- **[marketing/CLAUDE.md](marketing/CLAUDE.md)** - Marketing site architecture

**Important:** Always read the service-specific CLAUDE.md when working within that service directory.

---

## 🧪 Testing Strategy

### Individual Service Testing

```bash
# Laravel
cd app && composer run test

# Audio Service
cd audio-service && ./scripts/run_tests.sh

# Marketing
cd marketing && npm run build
```

### Integration Testing

Test cross-service functionality:

1. **Upload Flow**: Marketing → Laravel → Audio Service
2. **Authentication**: Marketing ↔ Laravel
3. **Analysis Pipeline**: Laravel → Audio Service → Callback

---

## 📦 Deployment

### Production Build

```bash
# Build all images
make build

# Start in production mode
make prod

# Stop production
make prod-stop
```

### Environment Variables

Create `.env` files in each service directory based on `.env.example` files.

**Shared Storage:**
All services share a common storage volume for audio files. Ensure `LOCAL_STORAGE_PATH` points to the same location.

---

## 🔀 Git Workflow

### Conventional Commits

Use conventional commit format:

```
<type>(<scope>): <subject>

Types: feat, fix, refactor, perf, style, test, docs, chore, ci
Scopes: app, audio, marketing, docker, ci, docs
```

Examples:
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
- ✅ Reference issues in commit messages

**DO NOT:**
- ❌ Commit directly to `main` without PR
- ❌ Add co-author tags or AI attribution
- ❌ Commit without running tests
- ❌ Mix changes across services in one commit

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `chore/*` - Maintenance tasks

---

## 🛠️ Troubleshooting

### Docker Issues

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

# Kill processes or change ports in docker-compose files
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

---

## 📚 Additional Resources

- [Monorepo README](README.md) - Complete documentation
- [Migration Guide](MIGRATION.md) - How we migrated from separate repos
- [Laravel Docs](app/CLAUDE.md) - Laravel-specific guidance
- [Audio Service Docs](audio-service/CLAUDE.md) - Audio processing details
- [Marketing Docs](marketing/CLAUDE.md) - Marketing site architecture

---

## 🔧 MCP Tools & Integrations

This monorepo uses Claude Code with the following MCP integrations:

- **Laravel Boost** - Laravel-specific tooling and helpers
- **Serena** - Semantic code navigation and editing
- **Context7** - Up-to-date third-party documentation
- **Sequential Thinking** - Decision-making support
- **GitHub** - Repository operations
- **Chrome DevTools** - Browser testing

When working in a specific service, the relevant MCP tools will be available based on that service's `.mcp.json` configuration.

---

## ⚠️ Important Notes

1. **Storage Paths**: All services must use the same storage path structure for audio files
2. **Redis**: Shared between Laravel queues and Celery workers
3. **MySQL**: Used only by Laravel application
4. **Network**: All services communicate via the `wavdash` Docker network
5. **Logs**: Service logs are available in `<service>/storage/logs` or via `make logs`

---

## 🎓 Learning Resources

New to the monorepo? Start here:

1. Read this file completely
2. Explore the `Makefile` with `make help`
3. Read service-specific CLAUDE.md files
4. Run `make dev-detached` to see all services
5. Experiment with `make test` to understand testing

---

This monorepo structure provides:
- ✅ Unified development environment
- ✅ Shared infrastructure (DB, Redis, Storage)
- ✅ Simplified deployment
- ✅ Complete git history preservation
- ✅ Docker-based consistency
- ✅ Flexible local development options
