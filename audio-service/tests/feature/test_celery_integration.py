#!/usr/bin/env python3
"""
Test Celery integration with the new audio feature extraction service
"""

from pathlib import Path
import sys
import time


def test_celery_task():
    """Test the Celery audio processing task"""
    print("🧪 Testing Celery Integration with New Feature Extraction")
    print("=" * 60)

    try:
        # Import Celery app
        from celery_app import celery_app
        from tasks.audio_processing import process_audio_features

        print("✅ Celery app and tasks imported successfully")

        # Test with the existing test audio file
        test_file = Path("tests/fixtures/test_audio.wav")
        if not test_file.exists():
            print("❌ Test audio file not found. Please run test_setup.py first.")
            assert False, "Test failed"

        # Read the audio file
        with open(test_file, "rb") as f:
            audio_data = f.read()

        print(f"🎼 Testing with: {test_file.name} ({len(audio_data)} bytes)")

        # Submit task to Celery
        print("📤 Submitting task to Celery...")
        task = process_audio_features.delay(audio_data, test_file.name)

        print(f"✅ Task submitted with ID: {task.id}")
        print("⏳ Waiting for task completion...")

        # Wait for completion with timeout
        max_wait = 60  # 60 seconds timeout
        start_time = time.time()

        while not task.ready():
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                print(f"❌ Task timeout after {max_wait} seconds")
                assert False, "Test failed"

            # Check task state
            state = task.state
            if state == "PROGRESS":
                try:
                    info = task.info
                    progress = info.get("progress", 0)
                    status = info.get("status", "Processing...")
                    print(f"⏳ Progress: {progress}% - {status}")
                except:
                    print(f"⏳ State: {state}")

            time.sleep(2)

        # Get result
        if task.successful():
            result = task.result
            print("🎉 Task completed successfully!")

            # Display result summary
            if isinstance(result, dict):
                print(f"\n📊 Results Summary:")

                # Metadata
                if "metadata" in result:
                    metadata = result["metadata"]
                    print(f"   File: {metadata.get('filename', 'unknown')}")
                    print(f"   Duration: {metadata.get('duration', 0):.2f}s")
                    print(
                        f"   Processing Time: {metadata.get('processing_time', 0):.2f}s"
                    )

                # Musical analysis
                if "features" in result:
                    features = result["features"]
                    print(f"\n🎯 Musical Analysis:")

                    if "key" in features:
                        key_info = features["key"]
                        print(f"   Key: {key_info.get('key', 'unknown')}")
                        print(f"   Key Confidence: {key_info.get('confidence', 0):.2f}")

                    if "tempo" in features:
                        tempo_info = features["tempo"]
                        print(f"   BPM: {tempo_info.get('bpm', 0):.1f}")
                        print(
                            f"   Beat Regularity: {tempo_info.get('beat_regularity', 0):.2f}"
                        )

                    if "energy" in features:
                        energy_info = features["energy"]
                        print(
                            f"   Loudness: {energy_info.get('overall_loudness_db', 0):.1f} dB"
                        )
                        print(
                            f"   Dynamic Range: {energy_info.get('dynamic_range_db', 0):.1f} dB"
                        )

                    print(f"\n🔍 Feature Categories Available: {list(features.keys())}")

                print(f"\n✅ New feature extraction service working in Celery! 🎵")
                assert True  # Test passed
            else:
                print(f"❌ Unexpected result format: {type(result)}")
                assert False, "Test failed"

        else:
            print(f"❌ Task failed!")
            if task.failed():
                print(f"Error: {task.traceback}")
            assert False, "Test failed"

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the Celery worker can find the services module")
        assert False, "Test failed"
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        assert False, "Test failed"


def main():
    """Run the test"""
    success = test_celery_task()

    if success:
        print(f"\n🎉 Celery integration test passed!")
        print("\n📋 Ready for production:")
        print("✅ New feature extraction service working")
        print("✅ Celery task processing working")
        print("✅ Lightweight results for Laravel integration")
        print("\n🔗 Use these endpoints in your Laravel app:")
        print("• POST /extract-features - Async processing")
        print("• GET /task-summary/{task_id} - Lightweight results")
        print("• POST /extract-features-sync - Immediate results")
    else:
        print(f"\n❌ Celery integration test failed!")
        print("Make sure:")
        print("• Celery worker is running")
        print("• Redis is available")
        print("• All dependencies are installed")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
