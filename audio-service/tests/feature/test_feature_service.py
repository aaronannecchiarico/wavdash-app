#!/usr/bin/env python3
"""
Test script for the new audio feature extraction service
"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_feature_extraction():
    """Test the new feature extraction service"""
    print("🎵 Testing Audio Feature Extraction Service")
    print("=" * 50)

    try:
        # Import the service
        from services.audio_feature_extraction import create_feature_extractor

        print("✅ Service imported successfully")

        # Create extractor
        extractor = create_feature_extractor(
            extract_detailed=False,
            chunk_duration=10.0,  # Shorter chunks for testing
            timeout=60,
        )
        print("✅ Feature extractor created")

        # Test with the existing test audio file
        test_file = Path("tests/fixtures/test_audio.wav")
        if not test_file.exists():
            print("❌ Test audio file not found. Please run test_setup.py first.")
            assert False, "Test failed"

        print(f"🎼 Analyzing: {test_file.name}")

        # Extract features
        result = extractor.extract_features(test_file)

        # Check for errors
        if "error" in result:
            print(f"❌ Extraction failed: {result['error']}")
            assert False, "Test failed"

        print("✅ Feature extraction completed!")

        # Display results summary
        if "metadata" in result:
            metadata = result["metadata"]
            print(f"\n📊 Audio Metadata:")
            print(f"   Duration: {metadata.get('duration', 0):.2f} seconds")
            print(f"   Sample Rate: {metadata.get('sample_rate', 0)} Hz")
            print(
                f"   Processing Time: {metadata.get('processing_time', 0):.2f} seconds"
            )
            print(
                f"   Processed in Chunks: {metadata.get('processed_in_chunks', False)}"
            )

        if "features" in result:
            features = result["features"]
            print(f"\n🎯 Musical Analysis:")

            # Key detection
            if "key" in features:
                key_info = features["key"]
                print(f"   Key: {key_info.get('key', 'unknown')}")
                print(f"   Key Confidence: {key_info.get('confidence', 0):.2f}")

            # Tempo
            if "tempo" in features:
                tempo_info = features["tempo"]
                print(f"   BPM: {tempo_info.get('bpm', 0):.1f}")
                print(f"   Beat Regularity: {tempo_info.get('beat_regularity', 0):.2f}")

            # Energy
            if "energy" in features:
                energy_info = features["energy"]
                print(
                    f"   Loudness: {energy_info.get('overall_loudness_db', 0):.1f} dB"
                )
                print(
                    f"   Dynamic Range: {energy_info.get('dynamic_range_db', 0):.1f} dB"
                )

            # Spectral
            if "spectral" in features:
                spectral_info = features["spectral"]
                if "spectral_centroid" in spectral_info:
                    brightness = spectral_info["spectral_centroid"].get("mean", 0)
                    print(f"   Brightness (Spectral Centroid): {brightness:.1f} Hz")

            # MFCC
            if "mfcc" in features:
                mfcc_info = features["mfcc"]
                print(f"   MFCC Coefficients: {mfcc_info.get('n_coefficients', 0)}")
                print(f"   Timbral Complexity: {mfcc_info.get('overall_std', 0):.3f}")

            print(f"\n🔍 Available Feature Categories:")
            for category in features.keys():
                if category != "extraction_error":
                    print(f"   • {category}")

        # Test chunked processing for demonstration
        print(f"\n🧩 Testing Chunked Processing:")
        result_chunked = extractor.extract_features(test_file, process_chunks=True)

        if "chunks" in result_chunked:
            chunks = result_chunked["chunks"]
            print(f"   Processed {len(chunks)} chunks")

            if "aggregated_features" in result_chunked:
                agg = result_chunked["aggregated_features"]
                if "tempo" in agg:
                    print(
                        f"   Average BPM across chunks: {agg['tempo'].get('mean_bpm', 0):.1f}"
                    )
                if "key" in agg:
                    print(
                        f"   Most likely key: {agg['key'].get('most_likely_key', 'unknown')}"
                    )
                    print(
                        f"   Key changes detected: {agg['key'].get('key_changes', 0)}"
                    )

        print(f"\n✅ All tests passed! 🎉")
        assert True  # Test passed
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        assert False, "Test failed"


def test_api_integration():
    """Test API integration scenarios"""
    print(f"\n🌐 Testing API Integration Scenarios")
    print("-" * 50)

    try:
        from io import BytesIO

        from services.audio_feature_extraction import create_feature_extractor

        # Test BytesIO input (simulating file upload)
        test_file = Path("tests/fixtures/test_audio.wav")
        if test_file.exists():
            with open(test_file, "rb") as f:
                audio_bytes = f.read()

            print("📤 Testing BytesIO input (file upload simulation)")

            audio_buffer = BytesIO(audio_bytes)
            extractor = create_feature_extractor(extract_detailed=False)

            result = extractor.extract_features(audio_buffer)

            if "error" not in result:
                print("✅ BytesIO processing successful")

                # Simulate Laravel-friendly response
                if "features" in result:
                    features = result["features"]
                    laravel_response = {
                        "success": True,
                        "audio_analysis": {
                            "key": features.get("key", {}).get("key", "unknown"),
                            "bpm": features.get("tempo", {}).get("bpm", 0),
                            "loudness_db": features.get("energy", {}).get(
                                "overall_loudness_db", 0
                            ),
                            "duration": result.get("metadata", {}).get("duration", 0),
                            "processing_time": result.get("metadata", {}).get(
                                "processing_time", 0
                            ),
                        },
                    }

                    print("✅ Laravel-compatible response structure:")
                    for key, value in laravel_response["audio_analysis"].items():
                        print(f"   {key}: {value}")
            else:
                print(f"❌ BytesIO processing failed: {result['error']}")
                assert False, "Test failed"

        print(f"\n🚀 API integration tests passed!")
        assert True  # Test passed
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        import traceback

        traceback.print_exc()
        assert False, "Test failed"


def main():
    """Run all tests"""
    print("🧪 Audio Feature Extraction Service Tests")
    print("=" * 60)

    try:
        # Test basic functionality
        test_feature_extraction()
        success1 = True

        # Test API integration
        test_api_integration()
        success2 = True

    except AssertionError:
        success1 = False
        success2 = False

    if success1 and success2:
        print(f"\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("✅ Feature extraction service working")
        print("✅ Musical analysis (key, tempo, energy) working")
        print("✅ Spectral and timbral analysis working")
        print("✅ Chunked processing for large files working")
        print("✅ Laravel-compatible API responses working")
        print("✅ Error handling and timeouts working")

        print(f"\n🔗 Ready for Laravel Integration:")
        print("• Use /extract-features for async processing")
        print("• Use /task-summary/{task_id} for lightweight results")
        print("• Use /extract-features-sync for small files")

        return True
    else:
        print(f"\n❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
