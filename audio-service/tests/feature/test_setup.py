#!/usr/bin/env python3
"""
Test script to verify the audio processing service setup
"""

from pathlib import Path
import sys
import time

import numpy as np


def test_imports():
    """Test all required imports"""
    print("Testing imports...")

    try:
        from fastapi import FastAPI

        print("✅ FastAPI")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        assert False, "Test failed"

    try:
        from celery_app import celery_app

        print("✅ Celery")
    except ImportError as e:
        print(f"❌ Celery: {e}")
        assert False, "Test failed"

    try:
        import redis

        r = redis.Redis(host="localhost", port=6379)
        r.ping()
        print("✅ Redis connection")
    except Exception as e:
        print(f"❌ Redis: {e}")
        assert False, "Test failed"

    try:
        import torch

        print(f"✅ PyTorch {torch.__version__}")

        if torch.backends.mps.is_available():
            print("✅ MPS (Metal Performance Shaders) available")
        elif torch.cuda.is_available():
            print("✅ CUDA available")
        else:
            print("✅ CPU mode")

    except ImportError as e:
        print(f"❌ PyTorch: {e}")
        assert False, "Test failed"

    try:
        import librosa

        print(f"✅ Librosa {librosa.__version__}")
    except ImportError as e:
        print(f"❌ Librosa: {e}")
        assert False, "Test failed"

    try:
        import soundfile as sf

        print("✅ SoundFile")
    except ImportError as e:
        print(f"❌ SoundFile: {e}")
        assert False, "Test failed"

    try:
        import demucs

        print("✅ Demucs")
    except ImportError as e:
        print(f"❌ Demucs: {e}")
        assert False, "Test failed"

    assert True  # Test passed


def test_device_detection():
    """Test device detection"""
    print("\nTesting device detection...")

    from utils.device_utils import get_device_info, get_optimal_device

    optimal_device = get_optimal_device()
    print(f"✅ Optimal device: {optimal_device}")

    device_info = get_device_info()
    print(f"✅ Platform: {device_info['platform']} {device_info['architecture']}")
    print(f"✅ PyTorch: {device_info['torch_version']}")

    if device_info.get("mps", {}).get("available"):
        print("✅ MPS support detected")

    assert optimal_device is not None
    assert device_info is not None


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")

    from config import settings

    print(f"✅ Config loaded")
    print(f"✅ Host: {settings.HOST}:{settings.PORT}")
    print(f"✅ Redis: {settings.REDIS_URL}")
    print(f"✅ Device: {settings.DEMUCS_DEVICE}")
    print(f"✅ Debug: {settings.DEBUG}")

    assert hasattr(settings, "HOST")
    assert hasattr(settings, "PORT")
    assert hasattr(settings, "REDIS_URL")


def test_celery_tasks():
    """Test Celery task imports"""
    print("\nTesting Celery tasks...")

    from tasks.audio_processing import process_audio_features, separate_audio_stems

    print("✅ Audio processing tasks imported")

    # Test task registration
    from celery_app import celery_app

    registered_tasks = list(celery_app.tasks.keys())
    audio_tasks = [t for t in registered_tasks if "audio_processing" in t]

    print(f"✅ Registered audio tasks: {len(audio_tasks)}")
    for task in audio_tasks:
        print(f"  - {task}")

    assert process_audio_features is not None
    assert separate_audio_stems is not None
    assert len(audio_tasks) >= 0


def test_app_creation():
    """Test FastAPI app creation"""
    print("\nTesting FastAPI app...")

    from main import app

    print("✅ FastAPI app created")

    # Get route information
    routes = [route.path for route in app.routes]
    print(f"✅ Available routes: {len(routes)}")
    for route in routes:
        print(f"  - {route}")

    assert app is not None
    assert len(routes) > 0


def create_test_audio():
    """Create a simple test audio file"""
    print("\nCreating test audio file...")

    try:
        import soundfile as sf

        # Create a simple sine wave (440Hz for 1 second)
        sample_rate = 22050
        duration = 1.0
        frequency = 440.0

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * frequency * t)

        test_file = Path("tests/fixtures/test_audio.wav")
        sf.write(test_file, audio, sample_rate)

        print(f"✅ Test audio created: {test_file}")
        print(f"   Duration: {duration}s, Sample rate: {sample_rate}Hz")

        return test_file

    except Exception as e:
        print(f"❌ Test audio creation failed: {e}")
        return None


def main():
    """Run all tests"""
    print("🎵 Audio Processing Microservice Setup Test")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Device Detection", test_device_detection),
        ("Configuration", test_config),
        ("Celery Tasks", test_celery_tasks),
        ("FastAPI App", test_app_creation),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{test_name.upper()}")
        print("-" * len(test_name))
        results[test_name] = test_func()

    # Create test audio file
    test_audio_file = create_test_audio()

    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start Celery worker: python start_worker.py")
        print("2. Start FastAPI server: uvicorn main:app --reload")
        print("3. Open browser: http://localhost:8000/docs")

        if test_audio_file:
            print(
                f"4. Test with: curl -X POST -F 'audio_file=@{test_audio_file}' http://localhost:8000/extract-features"
            )
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
