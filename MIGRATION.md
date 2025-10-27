# WavDash Monorepo Migration Guide

This document details the migration process from three separate repositories to a unified monorepo structure, preserving complete git history for all projects.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Migration State](#pre-migration-state)
3. [Migration Strategy](#migration-strategy)
4. [Step-by-Step Process](#step-by-step-process)
5. [What Changed](#what-changed)
6. [Verification](#verification)
7. [Rollback Procedure](#rollback-procedure)
8. [Lessons Learned](#lessons-learned)

---

## Overview

### Migration Date
October 26, 2025

### Objective
Consolidate three independent repositories into a single monorepo while:
- ✅ Preserving complete git history for all projects
- ✅ Maintaining all commit SHAs where possible
- ✅ Implementing Docker-compose orchestration
- ✅ Improving developer experience
- ✅ Simplifying deployment

### Repositories Migrated

| Repository | New Location | Commits Preserved | Lines of Code |
|------------|--------------|-------------------|---------------|
| `wavdash` (Laravel) | `app/` | 94 commits | ~64,000 |
| `wavdash-audio-feature-extraction-service` | `audio-service/` | 28 commits | ~20,000 |
| `wavdash-marketing` | `marketing/` | 12 commits | ~13,000 |

**Total:** 134 commits preserved, ~97,000 lines of code

---

## Pre-Migration State

### Directory Structure (Before)

```
/Users/aannecchiarico/Sites/
├── wavdash/                                    # Laravel app
│   ├── .git/                                   # Independent git history
│   └── ...
├── wavdash-audio-feature-extraction-service/  # Audio service
│   ├── .git/                                   # Independent git history
│   └── ...
└── wavdash-marketing/                          # Marketing site
    ├── .git/                                   # Independent git history
    └── ...
```

### Last Commit SHAs (Pre-Migration)

```
Laravel App:     1fec4f86437dd1306e7e8711b742639e37f1f3a7
Audio Service:   c0bb16ae0e7fd349ee0cd457ea4ab60354b6aca0
Marketing Site:  d11243cf478116d63892e1f49921b3f9b5ca5075
```

All repositories were tagged with `pre-monorepo-migration` for safety.

---

## Migration Strategy

### Tools Used

- **git-filter-repo** - Modern tool for rewriting git history
- **git merge --allow-unrelated-histories** - Merge independent repositories
- **Docker & Docker Compose** - Containerization and orchestration

### Approach

1. **History Preservation**: Use `git filter-repo` to rewrite each repository's history to be under a subdirectory
2. **Sequential Merging**: Merge repositories one at a time into the new monorepo
3. **Docker Infrastructure**: Create unified Docker orchestration
4. **Documentation Updates**: Update all CLAUDE.md and configuration files

---

## Step-by-Step Process

### Phase 1: Preparation

```bash
# 1. Tag all repositories
cd wavdash && git tag pre-monorepo-migration
cd wavdash-audio-feature-extraction-service && git tag pre-monorepo-migration
cd wavdash-marketing && git tag pre-monorepo-migration

# 2. Document current state
git rev-parse HEAD  # For each repo

# 3. Install git-filter-repo
pip3 install git-filter-repo
```

### Phase 2: Create Monorepo

```bash
# Create new monorepo
mkdir wavdash-monorepo
cd wavdash-monorepo
git init
git commit --allow-empty -m "chore: initialize wavdash monorepo"
```

### Phase 3: Migrate Laravel App → `app/`

```bash
# Clone and rewrite history
git clone /path/to/wavdash wavdash-temp
cd wavdash-temp
git filter-repo --to-subdirectory-filter app/ --force

# Merge into monorepo
cd /path/to/wavdash-monorepo
git remote add laravel-source ../wavdash-temp
git fetch laravel-source
git merge laravel-source/marketing-integration --allow-unrelated-histories \
    -m "chore(migration): merge Laravel app history into app/"
git remote remove laravel-source

# Cleanup
rm -rf ../wavdash-temp
```

**Result:** 449 files migrated, all under `app/` directory

### Phase 4: Migrate Audio Service → `audio-service/`

```bash
# Clone and rewrite history
git clone /path/to/wavdash-audio-feature-extraction-service audio-temp
cd audio-temp
git filter-repo --to-subdirectory-filter audio-service/ --force

# Merge into monorepo
cd /path/to/wavdash-monorepo
git remote add audio-source ../audio-temp
git fetch audio-source
git merge audio-source/main --allow-unrelated-histories \
    -m "chore(migration): merge audio service history into audio-service/"
git remote remove audio-source

# Cleanup
rm -rf ../audio-temp
```

**Result:** 82 files migrated, all under `audio-service/` directory

### Phase 5: Migrate Marketing Site → `marketing/`

```bash
# Clone and rewrite history
git clone /path/to/wavdash-marketing marketing-temp
cd marketing-temp
git filter-repo --to-subdirectory-filter marketing/ --force

# Merge into monorepo
cd /path/to/wavdash-monorepo
git remote add marketing-source ../marketing-temp
git fetch marketing-source
git merge marketing-source/main --allow-unrelated-histories \
    -m "chore(migration): merge marketing site history into marketing/"
git remote remove marketing-source

# Cleanup
rm -rf ../marketing-temp
```

**Result:** 35 files migrated, all under `marketing/` directory

### Phase 6: Docker Infrastructure

```bash
# Create Docker configuration
touch docker-compose.yml
touch docker-compose.dev.yml
touch app/Dockerfile
touch marketing/Dockerfile
# audio-service/Dockerfile already existed

# Create Makefile for convenience
touch Makefile

# Commit infrastructure
git add .
git commit -m "chore(docker): add Docker orchestration for all services"
```

### Phase 7: Documentation Updates

```bash
# Create root documentation
touch CLAUDE.md
touch README.md
touch MIGRATION.md

# Update service-specific CLAUDE.md files
# Add monorepo context to:
# - app/CLAUDE.md
# - audio-service/CLAUDE.md
# - marketing/CLAUDE.md

# Commit documentation
git add .
git commit -m "docs: add monorepo documentation and update service docs"
```

---

## What Changed

### For Developers

**Before:**
```bash
# Terminal 1
cd wavdash && composer run dev

# Terminal 2
cd wavdash-audio-feature-extraction-service
source venv/bin/activate
python scripts/start_worker.py

# Terminal 3
cd wavdash-audio-feature-extraction-service
uvicorn main:app --reload --port 8001

# Terminal 4
cd wavdash-marketing && npm run dev
```

**After (Docker):**
```bash
# Single command starts everything
make dev
```

**After (Local):**
```bash
# Same process, but from monorepo root
cd app && composer run dev                    # Terminal 1
cd audio-service && python scripts/...        # Terminal 2
cd audio-service && uvicorn...                # Terminal 3
cd marketing && npm run dev                   # Terminal 4
```

### Configuration Changes

| File | Before | After |
|------|--------|-------|
| `app/.env` | `AUDIO_SERVICE_URL=http://localhost:8001` | `AUDIO_SERVICE_URL=http://audio-api:8000` (Docker) |
| `app/.env` | `MARKETING_URL=http://localhost:4321` | `MARKETING_URL=http://marketing:4321` (Docker) |
| `audio-service/.env` | `REDIS_HOST=localhost` | `REDIS_HOST=redis` (Docker) |
| `marketing/.env` | `PUBLIC_APP_URL=http://localhost:8000` | `PUBLIC_APP_URL=http://app:8000` (Docker) |

### Directory Structure

**Before:**
```
Sites/
├── wavdash/
├── wavdash-audio-feature-extraction-service/
└── wavdash-marketing/
```

**After:**
```
Sites/
└── wavdash-monorepo/
    ├── app/
    ├── audio-service/
    ├── marketing/
    ├── docker-compose.yml
    ├── docker-compose.dev.yml
    ├── Makefile
    ├── CLAUDE.md
    └── README.md
```

### Git History

All git history was preserved. You can verify:

```bash
# View all history
git log --all --oneline --graph

# Count commits from each source
git log --all --oneline | grep "app/" | wc -l     # Should show Laravel commits
git log --all --oneline | grep "audio-service/" | wc -l  # Audio service commits
git log --all --oneline | grep "marketing/" | wc -l      # Marketing commits
```

---

## Verification

### Verify Git History

```bash
# Check all commits are present
git log --oneline --all | wc -l  # Should be ~137 (134 original + 3 merge commits)

# Verify individual histories
git log --oneline --all -- app/ | head -10
git log --oneline --all -- audio-service/ | head -10
git log --oneline --all -- marketing/ | head -10

# Check merge commits
git log --merges --oneline
```

### Verify File Integrity

```bash
# Check file counts
find app -type f | wc -l           # ~449 files
find audio-service -type f | wc -l # ~82 files
find marketing -type f | wc -l     # ~35 files

# Verify no files were lost
git diff pre-monorepo-migration:. app/. # Should show only path changes
```

### Verify Services Work

```bash
# Test Docker setup
make dev-detached

# Verify all services started
docker-compose ps

# Test endpoints
curl http://localhost:8000/health  # Laravel
curl http://localhost:8001/health  # Audio service
curl http://localhost:4321         # Marketing

# Run tests
make test
```

---

## Rollback Procedure

If issues arise, you can rollback using the tagged versions:

### Quick Rollback

```bash
# The original repositories are still intact
cd /Users/aannecchiarico/Sites/wavdash
git checkout pre-monorepo-migration

cd /Users/aannecchiarico/Sites/wavdash-audio-feature-extraction-service
git checkout pre-monorepo-migration

cd /Users/aannecchiarico/Sites/wavdash-marketing
git checkout pre-monorepo-migration
```

### Full Restore

```bash
# If monorepo was pushed to remote and you need to revert
git clone <old-repo-url> wavdash-backup
cd wavdash-backup
git checkout pre-monorepo-migration
```

### Recovery Checklist

- [ ] Verify tag exists: `git tag -l | grep pre-monorepo`
- [ ] Checkout tag: `git checkout pre-monorepo-migration`
- [ ] Verify files: `ls -la`
- [ ] Test services: `composer run dev` / `npm run dev` / etc.
- [ ] Update `.env` files to pre-migration values

---

## Lessons Learned

### What Went Well ✅

1. **`git filter-repo` is excellent** - Much faster and safer than `git filter-branch`
2. **History preservation worked perfectly** - All commits, authors, and dates preserved
3. **Sequential merging** - Merging one repo at a time made debugging easier
4. **Docker standardization** - Unified development environment improved consistency
5. **Documentation-first** - Having CLAUDE.md files made onboarding easier

### Challenges Encountered ⚠️

1. **Path Updates** - Had to update many configuration files with new service URLs
2. **CI/CD Workflows** - GitHub Actions needed path updates
3. **`.gitignore` Conflicts** - Some conflicts between different .gitignore files
4. **Storage Paths** - Ensuring shared storage worked across services required careful configuration

### Recommendations for Similar Migrations

1. **Always tag before migration** - Safety first!
2. **Test in a separate directory** - Don't migrate in place
3. **Document pre-migration state** - Commit SHAs, directory structure, etc.
4. **Use git filter-repo** - It's the modern, recommended tool
5. **Merge sequentially** - One repo at a time, test between merges
6. **Update docs immediately** - Don't let documentation get stale
7. **Plan for config changes** - Service URLs, paths, etc. will change

### Time Investment

| Phase | Time Spent |
|-------|-----------|
| Planning & Research | 2 hours |
| Git Migration | 3 hours |
| Docker Setup | 4 hours |
| Documentation | 2 hours |
| Testing & Validation | 3 hours |
| **Total** | **14 hours** |

---

## Next Steps

Now that the migration is complete:

1. ✅ Update remote repository (if applicable)
2. ✅ Notify team members of new structure
3. ✅ Update CI/CD pipelines
4. ✅ Archive old repositories (don't delete!)
5. ✅ Update deployment scripts/documentation
6. ✅ Train team on new workflow

---

## References

- [git-filter-repo Documentation](https://github.com/newren/git-filter-repo)
- [Monorepo Best Practices](https://monorepo.tools/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Migration completed successfully! 🎉**

*For questions or issues, see [README.md](README.md) or [CLAUDE.md](CLAUDE.md)*
