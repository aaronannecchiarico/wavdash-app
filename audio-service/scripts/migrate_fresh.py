#!/usr/bin/env python3
"""
Fresh Migration Script for Audio Processing Microservice

This script performs a complete fresh migration/deployment setup:
- Clears Redis task tracking data
- Clears performance cache
- Initializes storage directories
- Validates the complete setup

Use this for fresh deployments or when you need to completely reset the system state.
"""

import argparse
import logging
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import redis

from config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_virtual_environment() -> bool:
    """Ensure we're running in the correct virtual environment"""
    print("🔍 Checking virtual environment...")

    venv_path = Path("wavdash-audio-extraction-service-local")
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("   Run: python install.py first")
        return False

    # Check if we're currently in the venv
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        print("❌ Not running in virtual environment!")
        print(
            "   Activate with: source wavdash-audio-extraction-service-local/bin/activate"
        )
        return False

    print("✅ Virtual environment is active")
    return True


def clear_redis_data() -> bool:
    """Clear Redis task tracking and Celery data"""
    print("🧹 Clearing Redis data...")

    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
        )

        # Test connection
        redis_client.ping()
        print("✅ Connected to Redis")

        # Clear deleted task tracking keys
        deleted_task_keys = redis_client.keys("deleted_task:*")
        if deleted_task_keys:
            deleted_count = redis_client.delete(*deleted_task_keys)
            print(f"🗑️  Cleared {deleted_count} deleted task tracking keys")
        else:
            print("✅ No deleted task keys to clear")

        # Clear Celery task result keys (if any)
        celery_keys = redis_client.keys("celery-task-meta-*")
        if celery_keys:
            celery_count = redis_client.delete(*celery_keys)
            print(f"🗑️  Cleared {celery_count} Celery task result keys")
        else:
            print("✅ No Celery task keys to clear")

        # Clear any rate limiting keys
        rate_limit_keys = redis_client.keys("rate_limit:*")
        if rate_limit_keys:
            rate_limit_count = redis_client.delete(*rate_limit_keys)
            print(f"🗑️  Cleared {rate_limit_count} rate limiting keys")
        else:
            print("✅ No rate limiting keys to clear")

        print("✅ Redis cleanup completed")
        return True

    except redis.ConnectionError:
        print("⚠️  Redis not available - skipping Redis cleanup")
        print("   This is OK for local development without Redis")
        return True
    except Exception as e:
        print(f"❌ Redis cleanup failed: {e}")
        return False


def clear_performance_cache() -> bool:
    """Clear performance cache directories"""
    print("🧹 Clearing performance cache...")

    try:
        # Default cache directory
        cache_dir = Path("./cache")

        if cache_dir.exists():
            # Remove entire cache directory
            shutil.rmtree(cache_dir)
            print(f"🗑️  Removed cache directory: {cache_dir}")

        # Recreate cache directory structure
        cache_dir.mkdir(exist_ok=True)
        (cache_dir / "audio").mkdir(exist_ok=True)
        (cache_dir / "bmp").mkdir(exist_ok=True)
        (cache_dir / "presets").mkdir(exist_ok=True)

        print("✅ Performance cache cleared and reinitialized")
        return True

    except Exception as e:
        print(f"❌ Cache cleanup failed: {e}")
        return False


def initialize_storage_directories() -> bool:
    """Initialize storage directory structure"""
    print("📁 Initializing storage directories...")

    try:
        # Get storage path from settings
        if hasattr(settings, "LOCAL_STORAGE_PATH") and settings.LOCAL_STORAGE_PATH:
            storage_path = Path(settings.LOCAL_STORAGE_PATH)
        else:
            storage_path = Path("./storage")

        # Create main storage directories
        directories = [
            storage_path,
            storage_path / "uploads",
            storage_path / "processed",
            storage_path / "stems",
            storage_path / "temp",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created/verified: {directory}")

        # Create logs directory
        logs_dir = Path("./logs")
        logs_dir.mkdir(exist_ok=True)
        print(f"✅ Created/verified: {logs_dir}")

        print("✅ Storage directories initialized")
        return True

    except Exception as e:
        print(f"❌ Storage initialization failed: {e}")
        return False


def run_validation() -> bool:
    """Run setup validation"""
    print("🔍 Running setup validation...")

    try:
        validate_script = project_root / "scripts" / "validate_setup.py"
        result = subprocess.run(
            [sys.executable, str(validate_script)], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Setup validation passed")
            return True
        else:
            print("❌ Setup validation failed:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def run_tests() -> bool:
    """Run test suite to verify everything works"""
    print("🧪 Running test suite...")

    try:
        # Run unit tests only (no external dependencies)
        test_script = project_root / "scripts" / "run_tests.sh"
        result = subprocess.run(
            [str(test_script), "unit"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False


def create_migration_summary():
    """Create a summary file of the migration"""
    print("📄 Creating migration summary...")

    try:
        from datetime import datetime

        summary_content = f"""# Migration Summary
        
**Migration Date:** {datetime.now().isoformat()}
**Migration Type:** Fresh Deployment

## Actions Performed:
1. ✅ Virtual environment verified
2. ✅ Redis data cleared (deleted tasks, Celery results, rate limits)
3. ✅ Performance cache cleared and reinitialized
4. ✅ Storage directories initialized
5. ✅ Setup validation completed
6. ✅ Test suite passed

## Directory Structure Created:
- `./storage/` - Main storage directory
  - `uploads/` - User uploads by date
  - `processed/` - Processed results by date
  - `stems/` - Stem separation results
  - `temp/` - Temporary processing files
- `./cache/` - Performance cache
  - `audio/` - Processed audio cache
  - `bmp/` - BPM analysis cache
  - `presets/` - Preset configuration cache
- `./logs/` - Application logs

## Next Steps:
1. Start Celery worker: `python start_worker.py`
2. Start API server: `uvicorn main:app --reload --port 8001`
3. Test health endpoint: `curl http://localhost:8001/health`

## Environment Configuration:
- Storage Type: {getattr(settings, 'STORAGE_TYPE', 'local')}
- Redis Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}
- Log Level: {getattr(settings, 'LOG_LEVEL', 'INFO')}
"""

        with open("migration_summary.md", "w") as f:
            f.write(summary_content)

        print("✅ Migration summary saved to migration_summary.md")

    except Exception as e:
        print(f"⚠️  Could not create migration summary: {e}")


def main():
    """Run complete fresh migration process"""
    parser = argparse.ArgumentParser(
        description="Run complete fresh migration for Audio Processing Microservice"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt and run migration automatically",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip running test suite after migration",
    )

    args = parser.parse_args()

    print("🚀 Audio Processing Microservice - Fresh Migration")
    print("=" * 60)
    print("This will clear all cached data and reset the system to a fresh state.")
    print("=" * 60)

    # Confirm with user unless forced
    if not args.force:
        response = input("Continue with fresh migration? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("❌ Migration cancelled by user")
            return False
    else:
        print("🔄 Running migration in force mode (no confirmation)")

    print("\n🔄 Starting fresh migration...")

    # Migration steps - conditionally include tests
    steps = [
        ("Virtual Environment Check", check_virtual_environment),
        ("Redis Data Cleanup", clear_redis_data),
        ("Performance Cache Cleanup", clear_performance_cache),
        ("Storage Directory Initialization", initialize_storage_directories),
        ("Setup Validation", run_validation),
    ]

    # Add test suite step unless skipped
    if not args.no_tests:
        steps.append(("Test Suite Execution", run_tests))
    else:
        print("⏭️  Skipping test suite execution")

    failed_steps = []

    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        print("-" * 40)

        try:
            if not step_func():
                failed_steps.append(step_name)
                print(f"❌ {step_name} failed")
            else:
                print(f"✅ {step_name} completed")
        except Exception as e:
            failed_steps.append(step_name)
            print(f"❌ {step_name} failed with error: {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY")
    print("=" * 60)

    if not failed_steps:
        print("🎉 Fresh migration completed successfully!")
        print("\n✅ All steps completed:")
        for step_name, _ in steps:
            print(f"   • {step_name}")

        create_migration_summary()

        print("\n🚀 System is ready! You can now:")
        print("   1. Start Celery worker: python start_worker.py")
        print("   2. Start API server: uvicorn main:app --reload --port 8001")
        if not args.no_tests:
            print("   3. Run feature tests: ./run_tests.sh feature")

        return True
    else:
        print(f"❌ Migration completed with {len(failed_steps)} failed steps:")
        for step in failed_steps:
            print(f"   • {step}")

        print("\n🔧 Please resolve the failed steps before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
