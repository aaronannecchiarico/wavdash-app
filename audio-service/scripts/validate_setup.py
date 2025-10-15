#!/usr/bin/env python3
"""
Validate the application setup and test structure
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_directory_structure():
    """Check that all required directories exist"""
    print("🔍 Checking directory structure...")

    required_dirs = [
        "tests",
        "tests/unit",
        "tests/feature",
        "tests/fixtures",
        "utils",
        "models",
        "services",
        "tasks",
        "logs",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"  ✅ {dir_path}")

    if missing_dirs:
        print("❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
        return False

    return True


def check_required_files():
    """Check that all required files exist"""
    print("\\n🔍 Checking required files...")

    required_files = [
        "main.py",
        "celery_app.py",
        "config.py",
        "requirements.txt",
        "pytest.ini",
        "scripts/run_tests.sh",
        "tests/fixtures/test_audio.wav",
        "tests/fixtures/audio_fixtures.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")

    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False

    return True


def check_test_files():
    """Check test files exist"""
    print("\\n🔍 Checking test files...")

    test_files = [
        "tests/unit/test_audio_utils.py",
        "tests/unit/test_device_utils.py",
        "tests/unit/test_audio_models.py",
        "tests/unit/test_config.py",
        "tests/feature/test_setup.py",
        "tests/feature/test_feature_service.py",
        "tests/feature/test_celery_integration.py",
        "tests/feature/test_stem_separation.py",
    ]

    missing_tests = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_tests.append(test_file)
        else:
            print(f"  ✅ {test_file}")

    if missing_tests:
        print("❌ Missing test files:")
        for test_file in missing_tests:
            print(f"  - {test_file}")
        return False

    return True


def check_imports():
    """Check that key imports work"""
    print("\\n🔍 Checking imports...")

    try:
        import config

        print("  ✅ config")
    except ImportError as e:
        print(f"  ❌ config: {e}")
        return False

    try:
        from models.audio_models import AudioProcessingRequest

        print("  ✅ models.audio_models")
    except ImportError as e:
        print(f"  ❌ models.audio_models: {e}")
        return False

    try:
        from utils.audio_utils import load_audio_from_bytes

        print("  ✅ utils.audio_utils")
    except ImportError as e:
        print(f"  ❌ utils.audio_utils: {e}")
        return False

    try:
        from tests.fixtures.audio_fixtures import AudioFixtures

        print("  ✅ tests.fixtures.audio_fixtures")
    except ImportError as e:
        print(f"  ❌ tests.fixtures.audio_fixtures: {e}")
        return False

    return True


def check_virtual_environment():
    """Check virtual environment"""
    print("\\n🔍 Checking virtual environment...")

    venv_path = Path("beatforge-audio-extraction-service-local")
    if not venv_path.exists():
        print("  ❌ Virtual environment not found")
        print("     Run: python install.py")
        return False

    print("  ✅ Virtual environment exists")

    # Check if we're currently in the venv
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("  ✅ Currently in virtual environment")
    else:
        print("  ⚠️  Not currently in virtual environment")
        print(
            "     Activate with: source beatforge-audio-extraction-service-local/bin/activate"
        )

    return True


def main():
    """Run all validation checks"""
    print("🧪 Application Setup Validation")
    print("=" * 40)

    checks = [
        ("Directory Structure", check_directory_structure),
        ("Required Files", check_required_files),
        ("Test Files", check_test_files),
        ("Python Imports", check_imports),
        ("Virtual Environment", check_virtual_environment),
    ]

    all_passed = True
    results = []

    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results.append((check_name, False))
            all_passed = False

    # Summary
    print("\\n" + "=" * 40)
    print("📊 Validation Summary")
    print("=" * 40)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<20} {status}")

    print()
    if all_passed:
        print("🎉 All validation checks passed!")
        print("\\n🚀 Ready to run tests:")
        print("   ./scripts/run_tests.sh")
        return 0
    else:
        print("💥 Some validation checks failed")
        print("\\n🔧 Fix the issues above before running tests")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
