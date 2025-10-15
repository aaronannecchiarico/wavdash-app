#!/usr/bin/env python3
"""
Installation script for audio processing microservice
Installs all required packages with proper error handling and platform detection
"""

import platform
import subprocess
import sys


def run_pip_install(packages, description):
    """Install packages with pip"""
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    print(f"\n{description}...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Complete installation for audio processing microservice"""
    print("Audio Processing Microservice Installation")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")

    # Check virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        print("❌ Please activate your virtual environment first!")
        print("Create and activate a virtual environment:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        return False

    print(f"✓ Using virtual environment: {sys.prefix}")

    # Detect Apple Silicon for MPS support
    is_apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    if is_apple_silicon:
        print("✓ Detected Apple Silicon - MPS acceleration will be available")

    # All required packages
    packages = [
        # Web framework
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "python-multipart",
        # Task queue
        "celery",
        "redis",
        # Configuration
        "python-decouple",
        # Machine Learning & Audio Processing
        "numpy",
        "torch",
        "torchaudio",
        "soundfile",
        "librosa",
        "demucs",
        # Optional utilities
        "httpx",
        "structlog",
        "tqdm",
        "psutil",
        "python-json-logger",
    ]

    print(f"\nInstalling {len(packages)} core packages...")

    # Install one by one to see which ones work
    successful = []
    failed = []

    for package in packages:
        if run_pip_install([package], f"Installing {package}"):
            successful.append(package)
        else:
            failed.append(package)

    print(f"\n{'='*60}")
    print("INSTALLATION SUMMARY")
    print("=" * 60)
    print(f"✓ Successful ({len(successful)}): {', '.join(successful)}")
    if failed:
        print(f"✗ Failed ({len(failed)}): {', '.join(failed)}")

    # Test all critical imports
    print(f"\nTesting imports...")

    test_packages = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("celery", "Task queue"),
        ("redis", "Message broker"),
        ("torch", "PyTorch machine learning"),
        ("numpy", "Numerical computing"),
        ("pydantic", "Data validation"),
        ("soundfile", "Audio I/O"),
        ("librosa", "Audio analysis"),
        ("demucs", "AI stem separation"),
    ]
    working_imports = []

    for pkg, desc in test_packages:
        try:
            __import__(pkg)
            working_imports.append(pkg)
            print(f"✓ {pkg} - {desc}")
        except ImportError:
            print(f"✗ {pkg} - {desc}")

    # Check PyTorch device support
    try:
        import torch

        print(f"\nPyTorch Device Support:")
        print(f"  Version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if hasattr(torch.backends, "mps"):
            print(f"  MPS available: {torch.backends.mps.is_available()}")
    except ImportError:
        pass

    critical_packages = ["fastapi", "celery", "torch", "librosa", "demucs"]
    critical_working = [pkg for pkg in critical_packages if pkg in working_imports]

    if len(critical_working) == len(critical_packages):
        print(f"\n🎉 Complete installation successful!")
        print(f"✓ All {len(critical_packages)} critical packages working")
        print(f"✓ {len(working_imports)}/{len(test_packages)} total packages working")

        # Create/update .env file
        env_content = f"""# Audio Processing Microservice Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Device Configuration (auto detects best available: mps, cuda, cpu)
DEMUCS_DEVICE=auto

# Logging
LOG_LEVEL=INFO

# Audio Processing
SAMPLE_RATE=22050
MAX_FILE_SIZE=104857600

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
"""

        try:
            with open(".env", "w") as f:
                f.write(env_content)
            print("✓ Created configuration file (.env)")
        except Exception as e:
            print(f"⚠️  Could not create .env file: {e}")

        print("\n🚀 Setup Complete! Next steps:")
        print("1. Test setup: python test_setup.py")
        print("2. Start Celery worker: python start_worker.py")
        print("3. Start API server: uvicorn main:app --reload")
        print("4. View API docs: http://localhost:8000/docs")
        print("5. Health check: http://localhost:8000/health")

        device_info = ""
        if is_apple_silicon:
            device_info = " (with Apple MPS acceleration)"

        print(f"\n✅ Audio processing microservice ready{device_info}!")
        print("Features available:")
        print("  • Audio feature extraction (MFCC, chroma, spectral features)")
        print("  • AI-powered stem separation (vocals, drums, bass, other)")
        print("  • Asynchronous processing with Celery + Redis")
        print("  • RESTful API with automatic documentation")

        return True
    else:
        missing = [pkg for pkg in critical_packages if pkg not in working_imports]
        print(f"\n❌ Installation incomplete!")
        print(f"Critical packages missing: {', '.join(missing)}")
        print(
            f"Working: {len(critical_working)}/{len(critical_packages)} critical packages"
        )
        print("\nTry installing missing packages manually:")
        for pkg in missing:
            print(f"  pip install {pkg}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
