# WavDash Monorepo

> AI-powered audio processing platform with Laravel, FastAPI, and Astro

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📦 What is This?

WavDash is an AI-powered audio processing platform built as a monorepo. Users upload songs, and the platform analyzes them, separates stems (vocals, drums, bass, etc.), and provides tools for remixing and playback — including a physical Raspberry Pi stem mixer for live performance.

- **Laravel App** (`app/`) - Full-featured web application with React/Inertia.js frontend, file management, and audio pipeline orchestration
- **Audio Service** (`audio-service/`) - FastAPI microservice for audio analysis (BPM, key, loudness) and AI stem separation via Demucs
- **Marketing Site** (`marketing/`) - Astro-based public marketing website with shared authentication
- **Pi Stem Mixer** (`pi/`) - Raspberry Pi 5 hardware mixer with physical faders, buttons, LEDs, and TFT display for real-time stem control

## 🚀 Quick Start

### Prerequisites

- **Colima & Docker Compose** (recommended for containerized development)
  - Install: `brew install colima docker docker-compose`
  - Start: `colima start`
- **OR** for local development:
  - PHP 8.3+, Composer
  - Node.js 20+
  - Python 3.11+
  - SQLite 3 (included with macOS/PHP)
  - Redis 7+ (optional - for queue testing)

### Start All Services (Docker via Colima)

```bash
# Clone the repository
git clone https://github.com/your-org/wavdash.git
cd wavdash

# Ensure Colima is running
colima status || colima start

# Start all services in development mode
make dev-detached
```

**Access Points:**
- Laravel App: http://localhost:8000
- Audio Service: http://localhost:8001
- Marketing Site: http://localhost:4321
- Celery Monitor (Flower): http://localhost:5555
- Redis Commander: http://localhost:8081
- MailHog: http://localhost:8025

### Local Development (No Docker)

```bash
# Install all dependencies
make install

# Then run in separate terminals:
# Terminal 1: Laravel
cd app && composer run dev

# Terminal 2: Audio Worker
cd audio-service
source wavdash-audio-extraction-service-local/bin/activate
python scripts/start_worker.py

# Terminal 3: Audio API
cd audio-service
source wavdash-audio-extraction-service-local/bin/activate
uvicorn main:app --reload --port 8001

# Terminal 4: Marketing
cd marketing && npm run dev
```

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete development guide for Claude Code
- **[MIGRATION.md](MIGRATION.md)** - Migration guide from separate repos
- **[app/CLAUDE.md](app/CLAUDE.md)** - Laravel app specifics
- **[audio-service/CLAUDE.md](audio-service/CLAUDE.md)** - Audio service details
- **[marketing/CLAUDE.md](marketing/CLAUDE.md)** - Marketing site architecture
- **[pi/README.md](pi/README.md)** - Raspberry Pi stem mixer

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Marketing Site │         │   Laravel App    │         │  Pi Stem Mixer   │
│    (Astro)      │◄───────►│  (Inertia.js)    │────────►│  (Raspberry Pi)  │
└─────────────────┘         └────────┬─────────┘         └──────────────────┘
                                     │                     6 faders, LEDs,
                                     ▼                     TFT display, encoder
                            ┌──────────────────┐
                            │  Audio Service   │
                            │    (FastAPI)     │
                            └────────┬─────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
                ┌─────────┐    ┌─────────┐    ┌──────────┐
                │  MySQL  │    │  Redis  │    │  Storage │
                └─────────┘    └─────────┘    └──────────┘
```

### Data Flow

1. **User uploads audio** → App processes client-side to OGG → Storage
2. **Stem separation** → Laravel → Audio Service (async via Celery) → 6 individual stems
3. **Analysis complete** → Callback → Laravel → WebSocket event → UI update
4. **Hardware playback** → Laravel auto-pushes OGG stems over Tailscale → Pi receiver → real-time mixing with physical faders

## 🛠️ Development Commands

All commands available via `Makefile`. Run `make help` for full list.

### Essential Commands

```bash
make dev              # Start all services (Docker)
make dev-detached     # Start all services in background
make stop             # Stop all services
make test             # Run all tests
make logs             # View all logs
make clean            # Clean Docker resources
```

### Per-Service Commands

```bash
make test-app         # Test Laravel only
make test-audio       # Test audio service only
make app-shell        # Shell into Laravel container
make audio-shell      # Shell into audio container
make logs-app         # Laravel logs only
```

### Raspberry Pi Commands

```bash
make pi-sync          # Rsync pi/ to Raspberry Pi
make pi-test          # Sync + run tests on Pi
make pi-run           # Sync + run player interactively
make pi-receiver      # Sync + start receiver interactively
make pi-ssh           # SSH to Pi
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run individual service tests
make test-app          # Laravel tests (PHPUnit)
make test-audio        # Audio service tests (pytest)
make test-marketing    # Marketing build test
```

## 🎨 Technology Stack

### Laravel App
- Laravel 12
- React 19 + Inertia.js v2
- TypeScript
- Tailwind CSS v4
- Filament v4 (admin panel)
- Laravel Octane (FrankenPHP)
- Laravel Reverb (WebSockets)

### Audio Service
- FastAPI
- Celery + Redis
- Librosa (audio analysis)
- Demucs (stem separation)
- Python 3.11+

### Marketing Site
- Astro 5
- React 19
- Tailwind CSS v4
- TypeScript

### Infrastructure
- **Database**: SQLite (local dev), MySQL 8.0 (Docker/production)
- **Cache/Queue**: Redis 7
- **Containers**: Colima + Docker Compose
- **CI/CD**: GitHub Actions

## 📂 Project Structure

```
wavdash/
├── app/                    # Laravel application
│   ├── app/                # Application code
│   ├── resources/          # Frontend (React/Inertia)
│   ├── tests/              # PHPUnit tests
│   ├── Dockerfile          # Laravel Docker config
│   └── CLAUDE.md           # Laravel docs
├── audio-service/          # FastAPI microservice
│   ├── services/           # Business logic
│   ├── tasks/              # Celery tasks
│   ├── routes/             # API endpoints
│   ├── tests/              # Pytest tests
│   ├── Dockerfile          # Python Docker config
│   └── CLAUDE.md           # Audio service docs
├── marketing/              # Astro marketing site
│   ├── src/                # Pages & components
│   ├── public/             # Static assets
│   ├── Dockerfile          # Node Docker config
│   └── CLAUDE.md           # Marketing docs
├── pi/                     # Raspberry Pi stem mixer
│   ├── receiver/           # FastAPI stem receiver
│   ├── player/             # Audio engine + hardware I/O
│   ├── deploy/             # systemd services + setup
│   └── README.md           # Pi-specific docs
├── docker-compose.yml      # Production orchestration
├── docker-compose.dev.yml  # Development config
├── Makefile                # Dev commands
├── CLAUDE.md               # Main documentation
├── README.md               # This file
└── MIGRATION.md            # Migration guide
```

## 🔧 Configuration

### Environment Variables

Each service requires its own `.env` file. Copy from examples:

```bash
cp app/.env.example app/.env
cp audio-service/.env.example audio-service/.env
cp marketing/.env.example marketing/.env
```

### Key Configuration

**app/.env:**
```env
AUDIO_SERVICE_URL=http://audio-api:8000  # Docker
DB_HOST=mysql
REDIS_HOST=redis
MARKETING_URL=http://marketing:4321
```

**audio-service/.env:**
```env
REDIS_HOST=redis
LOCAL_STORAGE_PATH=./storage
```

**marketing/.env:**
```env
PUBLIC_APP_URL=http://app:8000
```

## 🚢 Deployment

### Production

```bash
# Build all images
make build

# Start in production mode
docker-compose up -d
```

### Environment-Specific

- **Local**: Use `docker-compose.dev.yml` for hot-reload
- **Staging/Production**: Use base `docker-compose.yml`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Format code (`make format`)
6. Commit using conventional commits (`feat(app): add new feature`)
7. Push to your fork
8. Create a Pull Request

### Commit Convention

```
<type>(<scope>): <subject>

Types: feat, fix, refactor, perf, style, test, docs, chore, ci
Scopes: app, audio, marketing, docker, ci, docs
```

## 🙏 Acknowledgments

- Laravel for the amazing framework
- FastAPI for the high-performance API framework
- Astro for the modern static site generator
- Celery for distributed task processing
- Librosa & Demucs for audio processing capabilities

## 📞 Support

- **Documentation**: See [CLAUDE.md](CLAUDE.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/wavdash/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/wavdash/discussions)