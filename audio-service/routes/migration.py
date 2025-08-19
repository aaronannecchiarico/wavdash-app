"""
Migration and Maintenance Routes
Handles fresh migrations and system maintenance operations
Only available in development/local environments (DEBUG=true)
"""

import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/migration",
    tags=["Migration & Maintenance"]
)


class MigrationResponse(BaseModel):
    """Response model for migration operations"""
    success: bool
    message: str
    details: dict = {}


def _check_development_environment():
    """Check if we're in a development environment"""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Migration endpoints are only available in development environments (DEBUG=true)"
        )


def _run_migration_script(script_name: str, force: bool = True, no_tests: bool = True) -> tuple[bool, str, str]:
    """Run a migration script and return success status, stdout, stderr"""
    script_path = Path(script_name)
    if not script_path.exists():
        return False, "", f"Script {script_name} not found"
    
    # Build command with appropriate flags
    cmd = [sys.executable, script_name]
    if force:
        cmd.append("--force")
    if no_tests and script_name == "migrate_fresh.py":
        cmd.append("--no-tests")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        success = result.returncode == 0
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "", f"Script {script_name} timed out after 5 minutes"
    except Exception as e:
        return False, "", f"Error running {script_name}: {str(e)}"


@router.post("/fresh", response_model=MigrationResponse)
async def run_fresh_migration():
    """
    Run complete fresh migration process
    
    This endpoint performs a complete system reset:
    - Clears Redis task tracking data
    - Clears performance cache
    - Initializes storage directories
    - Seeds system with default data
    - Validates setup
    
    ⚠️ WARNING: This will clear all cached data and task history!
    
    Only available when DEBUG=true (development/local environments)
    """
    _check_development_environment()
    
    logger.info("Starting fresh migration via API endpoint")
    
    migration_details = {
        "steps_completed": [],
        "steps_failed": [],
        "warnings": []
    }
    
    try:
        # Step 1: Run fresh migration
        logger.info("Running migrate_fresh.py")
        success, stdout, stderr = _run_migration_script("migrate_fresh.py")
        
        if not success:
            migration_details["steps_failed"].append("migrate_fresh.py")
            migration_details["migrate_fresh_error"] = stderr or "Unknown error"
            return MigrationResponse(
                success=False,
                message="Fresh migration failed",
                details=migration_details
            )
        
        migration_details["steps_completed"].append("migrate_fresh.py")
        migration_details["migrate_fresh_output"] = stdout
        
        # Step 2: Run data seeding
        logger.info("Running seed_data.py")
        success, stdout, stderr = _run_migration_script("seed_data.py")
        
        if not success:
            migration_details["steps_failed"].append("seed_data.py")
            migration_details["seed_data_error"] = stderr or "Unknown error"
            migration_details["warnings"].append("Migration completed but seeding failed")
        else:
            migration_details["steps_completed"].append("seed_data.py")
            migration_details["seed_data_output"] = stdout
        
        # Determine overall success
        overall_success = len(migration_details["steps_failed"]) == 0
        
        if overall_success:
            logger.info("Fresh migration completed successfully via API")
            return MigrationResponse(
                success=True,
                message="Fresh migration and seeding completed successfully",
                details=migration_details
            )
        else:
            logger.warning("Fresh migration completed with some failures")
            return MigrationResponse(
                success=False,
                message="Migration completed with errors - check details",
                details=migration_details
            )
            
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        migration_details["steps_failed"].append("unexpected_error")
        migration_details["unexpected_error"] = str(e)
        
        return MigrationResponse(
            success=False,
            message=f"Migration failed with unexpected error: {str(e)}",
            details=migration_details
        )


@router.post("/migrate-only", response_model=MigrationResponse)
async def run_migration_only():
    """
    Run only the migration step (without seeding)
    
    This clears Redis data, cache, and initializes storage directories
    but does not seed default data.
    
    Only available when DEBUG=true (development/local environments)
    """
    _check_development_environment()
    
    logger.info("Starting migration-only via API endpoint")
    
    try:
        success, stdout, stderr = _run_migration_script("migrate_fresh.py")
        
        if success:
            logger.info("Migration-only completed successfully via API")
            return MigrationResponse(
                success=True,
                message="Migration completed successfully",
                details={"migrate_fresh_output": stdout}
            )
        else:
            logger.error(f"Migration-only failed: {stderr}")
            return MigrationResponse(
                success=False,
                message="Migration failed",
                details={"migrate_fresh_error": stderr or "Unknown error"}
            )
            
    except Exception as e:
        logger.error(f"Unexpected error during migration-only: {e}")
        return MigrationResponse(
            success=False,
            message=f"Migration failed with unexpected error: {str(e)}",
            details={"unexpected_error": str(e)}
        )


@router.post("/seed-only", response_model=MigrationResponse)
async def run_seeding_only():
    """
    Run only the seeding step (without migration)
    
    This seeds the system with default data, tempo presets,
    and test fixtures without clearing existing data.
    
    Only available when DEBUG=true (development/local environments)
    """
    _check_development_environment()
    
    logger.info("Starting seeding-only via API endpoint")
    
    try:
        success, stdout, stderr = _run_migration_script("seed_data.py")
        
        if success:
            logger.info("Seeding-only completed successfully via API")
            return MigrationResponse(
                success=True,
                message="Seeding completed successfully",
                details={"seed_data_output": stdout}
            )
        else:
            logger.error(f"Seeding-only failed: {stderr}")
            return MigrationResponse(
                success=False,
                message="Seeding failed",
                details={"seed_data_error": stderr or "Unknown error"}
            )
            
    except Exception as e:
        logger.error(f"Unexpected error during seeding-only: {e}")
        return MigrationResponse(
            success=False,
            message=f"Seeding failed with unexpected error: {str(e)}",
            details={"unexpected_error": str(e)}
        )


@router.get("/status")
async def migration_status():
    """
    Get migration system status and available operations
    
    Only available when DEBUG=true (development/local environments)
    """
    _check_development_environment()
    
    # Check if migration scripts exist
    migrate_script_exists = Path("migrate_fresh.py").exists()
    seed_script_exists = Path("seed_data.py").exists()
    
    return {
        "debug_mode": settings.DEBUG,
        "migration_available": migrate_script_exists,
        "seeding_available": seed_script_exists,
        "available_endpoints": [
            "/migration/fresh - Complete fresh migration with seeding",
            "/migration/migrate-only - Migration without seeding", 
            "/migration/seed-only - Seeding without migration",
            "/migration/status - This status endpoint"
        ],
        "environment": {
            "storage_type": settings.STORAGE_TYPE,
            "redis_host": settings.REDIS_HOST,
            "redis_port": settings.REDIS_PORT
        }
    }