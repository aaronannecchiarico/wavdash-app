# R2 Storage Strategy for Docker Orchestration

## Overview

WavDash uses **Cloudflare R2** for cloud storage with a two-bucket strategy:
- **Private Bucket (`audio-private`)**: Original uploads, processed files, stems (access-controlled)
- **Public Bucket (`audio-public`)**: Streaming files, publicly accessible

Both Laravel and the audio service share the same R2 credentials and endpoint.

---

## Storage Modes

The monorepo supports **two storage modes** for flexibility:

### 1. R2 Mode (Recommended for Docker/Production)
- All files stored in Cloudflare R2
- No local storage needed
- Services communicate via R2 API
- Production-like environment

### 2. Local Mode (Development Only)
- Files stored in shared Docker volume
- Faster iteration (no network calls)
- Requires volume mounting between containers
- SQLite database in local mode

---

## Environment Configuration Strategy

### Root `.env` (Docker Compose - Gitignored)

Store **shared R2 credentials** in the root `.env` file:

```bash
# Storage Mode (r2 or local)
STORAGE_MODE=r2

# Cloudflare R2 Credentials (shared by all services)
R2_ACCESS_KEY_ID=11760940e627fef435050e9985bea9ae
R2_SECRET_ACCESS_KEY=076d469498642649b5459f4a8cb6850f7e551f66931253ec6a1bfadfdab6397a
R2_ENDPOINT=https://269eb01228379eea0a8b591aee2544f5.r2.cloudflarestorage.com

# R2 Buckets
R2_PRIVATE_BUCKET=audio-private
R2_PUBLIC_BUCKET=audio-public
R2_PUBLIC_URL=https://pub-8a24a10ad9344723ab338aea65b02338.r2.dev

# Shared Storage Path (for local mode)
SHARED_STORAGE_PATH=/app/shared-storage
```

**Security Note:** This file is gitignored and contains sensitive credentials.

### Service `.env` Files

**app/.env** (Laravel):
```bash
# Storage Configuration
FILESYSTEM_DISK=${STORAGE_MODE:-r2}

# R2 Private Bucket (uploads, processed, stems)
R2_PRIVATE_BUCKET=${R2_PRIVATE_BUCKET}
R2_PRIVATE_ENDPOINT=${R2_ENDPOINT}

# R2 Public Bucket (streaming)
R2_PUBLIC_BUCKET=${R2_PUBLIC_BUCKET}
R2_PUBLIC_ENDPOINT=${R2_ENDPOINT}
R2_PUBLIC_URL=${R2_PUBLIC_URL}

# R2 Credentials
R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
```

**audio-service/.env** (FastAPI):
```bash
# Storage Configuration
STORAGE_TYPE=${STORAGE_MODE:-r2}

# R2 Configuration (for R2 mode)
R2_BUCKET=${R2_PRIVATE_BUCKET}
R2_ENDPOINT=${R2_ENDPOINT}
R2_PUBLIC_URL=${R2_PUBLIC_URL}
R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}

# Local Storage Configuration (for local mode)
LOCAL_STORAGE_PATH=${SHARED_STORAGE_PATH}
```

---

## Docker Compose Integration

### Updated `docker-compose.dev.yml`

The development compose file should inject R2 credentials and support both storage modes:

```yaml
services:
  app:
    environment:
      # Storage mode
      - FILESYSTEM_DISK=${STORAGE_MODE:-r2}

      # R2 credentials (from root .env)
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_PRIVATE_BUCKET=${R2_PRIVATE_BUCKET}
      - R2_PRIVATE_ENDPOINT=${R2_ENDPOINT}
      - R2_PUBLIC_BUCKET=${R2_PUBLIC_BUCKET}
      - R2_PUBLIC_ENDPOINT=${R2_ENDPOINT}
      - R2_PUBLIC_URL=${R2_PUBLIC_URL}

    volumes:
      # Shared storage (for local mode)
      - shared-storage:${SHARED_STORAGE_PATH:-/app/shared-storage}

  audio-api:
    environment:
      # Storage mode
      - STORAGE_TYPE=${STORAGE_MODE:-r2}

      # R2 credentials
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_BUCKET=${R2_PRIVATE_BUCKET}
      - R2_ENDPOINT=${R2_ENDPOINT}
      - R2_PUBLIC_URL=${R2_PUBLIC_URL}

      # Local storage (for local mode)
      - LOCAL_STORAGE_PATH=${SHARED_STORAGE_PATH}

    volumes:
      # Shared storage (for local mode)
      - shared-storage:${SHARED_STORAGE_PATH:-/app/shared-storage}

  audio-worker:
    environment:
      # Same as audio-api
      - STORAGE_TYPE=${STORAGE_MODE:-r2}
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_BUCKET=${R2_PRIVATE_BUCKET}
      - R2_ENDPOINT=${R2_ENDPOINT}
      - R2_PUBLIC_URL=${R2_PUBLIC_URL}
      - LOCAL_STORAGE_PATH=${SHARED_STORAGE_PATH}

    volumes:
      - shared-storage:${SHARED_STORAGE_PATH:-/app/shared-storage}

volumes:
  shared-storage:
    driver: local
```

---

## Usage Scenarios

### Scenario 1: Docker Development with R2 (Production-like)

**Root `.env`:**
```bash
STORAGE_MODE=r2
R2_ACCESS_KEY_ID=11760940e627fef435050e9985bea9ae
R2_SECRET_ACCESS_KEY=076d469498642649b5459f4a8cb6850f7e551f66931253ec6a1bfadfdab6397a
# ... other R2 vars
```

**Start services:**
```bash
make dev-detached
```

**Benefits:**
- Production-like environment
- No local storage needed
- Tests R2 integration

### Scenario 2: Docker Development with Local Storage (Faster iteration)

**Root `.env`:**
```bash
STORAGE_MODE=local
SHARED_STORAGE_PATH=/app/shared-storage
# R2 credentials can be omitted or left blank
```

**Start services:**
```bash
make dev-detached
```

**Benefits:**
- Faster processing (no network calls)
- No R2 costs during development
- Shared volume between containers

### Scenario 3: Local Development (No Docker) with R2

**app/.env:**
```bash
FILESYSTEM_DISK=r2
R2_ACCESS_KEY_ID=11760940e627fef435050e9985bea9ae
# ... your actual R2 credentials
```

**audio-service/.env:**
```bash
STORAGE_TYPE=r2
R2_ACCESS_KEY_ID=11760940e627fef435050e9985bea9ae
# ... your actual R2 credentials
```

**Start services:**
```bash
# Use your current local setup
cd app && composer run dev
# etc.
```

---

## Security Best Practices

### 1. Credential Management

**Root `.env` (NEVER commit):**
- Contains actual R2 credentials
- Gitignored via `.gitignore`
- Injected into containers via Docker Compose

**Root `.env.example` (Safe to commit):**
```bash
# Storage Mode (r2 or local)
STORAGE_MODE=r2

# Cloudflare R2 Credentials
R2_ACCESS_KEY_ID=your_r2_access_key_here
R2_SECRET_ACCESS_KEY=your_r2_secret_key_here
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com

# R2 Buckets
R2_PRIVATE_BUCKET=audio-private
R2_PUBLIC_BUCKET=audio-public
R2_PUBLIC_URL=https://your-public-bucket.r2.dev

# Shared Storage Path (for local mode)
SHARED_STORAGE_PATH=/app/shared-storage
```

### 2. Service `.env.example` Files

Update to reference root environment variables:

**app/.env.example:**
```bash
# Reference: Copy R2 values from root .env for local development
# For Docker, these are injected automatically

# Storage Configuration
FILESYSTEM_DISK=r2  # or 'local' for local mode

# R2 Configuration (copy from root .env)
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_PRIVATE_BUCKET=audio-private
R2_PRIVATE_ENDPOINT=
R2_PUBLIC_BUCKET=audio-public
R2_PUBLIC_ENDPOINT=
R2_PUBLIC_URL=
```

### 3. Production Deployment

For production:
1. Use **GitHub Secrets** or environment variable injection
2. Never commit actual R2 credentials to git
3. Use R2 mode exclusively (no local storage)
4. Rotate credentials regularly

---

## Migration Checklist

- [ ] Update root `.env` with R2 credentials
- [ ] Update `docker-compose.dev.yml` with environment injection
- [ ] Update service `.env.example` files with documentation
- [ ] Test R2 mode: `STORAGE_MODE=r2 make dev-detached`
- [ ] Test local mode: `STORAGE_MODE=local make dev-detached`
- [ ] Verify file uploads work in both modes
- [ ] Verify audio processing works in both modes
- [ ] Update documentation with storage mode instructions

---

## Troubleshooting

### R2 Connection Issues

```bash
# Check R2 credentials are injected
docker-compose exec app env | grep R2

# Test R2 connectivity from Laravel
docker-compose exec app php artisan tinker
>>> Storage::disk('r2')->exists('test.txt')

# Test R2 from audio service
docker-compose exec audio-api python -c "from config import settings; print(settings.R2_ENDPOINT)"
```

### Local Storage Issues

```bash
# Check shared volume exists
docker volume ls | grep shared-storage

# Check volume is mounted
docker-compose exec app ls -la /app/shared-storage
docker-compose exec audio-api ls -la /app/shared-storage

# Verify permissions
docker-compose exec app touch /app/shared-storage/test.txt
docker-compose exec audio-api ls /app/shared-storage/
```

---

## Recommendation

**For your setup, I recommend:**

1. **Docker Development**: Use **R2 mode** (production-like)
   - Simpler setup (no volume mounting complexity)
   - Tests actual production flow
   - Your R2 credentials are already configured

2. **Local Development** (No Docker): Use **R2 mode**
   - Matches your current setup
   - Both services already configured for R2
   - Consistent with Docker environment

3. **Keep local storage mode** as an option for:
   - Offline development
   - Rapid iteration without network calls
   - Testing storage abstraction

This strategy gives you flexibility while defaulting to the production-like R2 setup.
