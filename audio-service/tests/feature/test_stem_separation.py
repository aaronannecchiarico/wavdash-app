#!/usr/bin/env python3
"""
Test stem separation functionality with MPS compatibility fixes
"""

import sys
import time
import logging
from pathlib import Path

def test_stem_separation():
    """Test the stem separation task"""
    print("🎵 Testing Stem Separation with MPS Compatibility")
    print("=" * 60)
    
    try:
        # Import Celery app and task
        from celery_app import celery_app
        from tasks.audio_processing import separate_audio_stems
        print("✅ Celery app and stem separation task imported successfully")
        
        # Test with existing test audio file
        test_file = Path("tests/fixtures/test_audio.wav")
        if not test_file.exists():
            print("❌ Test audio file not found. Please run test_setup.py first.")
            assert False, "Test failed"
        
        # Read the audio file
        with open(test_file, 'rb') as f:
            audio_data = f.read()
        
        print(f"🎼 Testing with: {test_file.name} ({len(audio_data)} bytes)")
        
        # Submit task to Celery with htdemucs model
        print("📤 Submitting stem separation task to Celery...")
        print("⚠️  Note: Using CPU for Celery worker (MPS causes crashes)")
        
        task = separate_audio_stems.delay(audio_data, test_file.name, "htdemucs")
        
        print(f"✅ Task submitted with ID: {task.id}")
        print("⏳ Waiting for task completion (this may take a while)...")
        
        # Wait for completion with extended timeout for stem separation
        max_wait = 300  # 5 minutes timeout
        start_time = time.time()
        
        while not task.ready():
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                print(f"❌ Task timeout after {max_wait} seconds")
                assert False, "Test failed"
            
            # Check task state
            state = task.state
            if state == 'PROGRESS':
                try:
                    info = task.info
                    progress = info.get('progress', 0)
                    status = info.get('status', 'Processing...')
                    print(f"⏳ Progress: {progress}% - {status}")
                except:
                    print(f"⏳ State: {state}")
            
            time.sleep(5)  # Check every 5 seconds for stem separation
        
        # Get result
        if task.successful():
            result = task.result
            print("🎉 Stem separation completed successfully!")
            
            # Display result summary
            if isinstance(result, dict):
                print(f"\\n📊 Stem Separation Results:")
                print(f"   File: {result.get('filename', 'unknown')}")
                print(f"   Model: {result.get('model_used', 'unknown')}")
                print(f"   Sample Rate: {result.get('sample_rate', 0)} Hz")
                print(f"   Stem Count: {result.get('stem_count', 0)}")
                
                if 'stems' in result:
                    stems = result['stems']
                    print(f"\\n🎯 Available Stems:")
                    for stem_name, file_path in stems.items():
                        print(f"   • {stem_name}: {file_path}")
                        
                        # Check if file exists
                        if Path(file_path).exists():
                            file_size = Path(file_path).stat().st_size
                            print(f"     Size: {file_size / 1024:.1f} KB")
                        else:
                            print(f"     ⚠️ File not found!")
                
                print(f"\\n✅ Stem separation service working! 🎵")
                print("\\n💡 Tips:")
                print("• Stem files are saved as temporary files")
                print("• Copy them to permanent location if needed")
                print("• Larger files will take longer to process")
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
        print("Make sure all dependencies are installed")
        assert False, "Test failed"
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        assert False, "Test failed"

def main():
    """Run the test"""
    print("🧪 Setting up test environment...")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    success = test_stem_separation()
    
    if success:
        print(f"\\n🎉 Stem separation test passed!")
        print("\\n📋 Ready for production:")
        print("✅ Demucs model loading working")
        print("✅ CPU processing for Celery workers")  
        print("✅ MPS compatibility issues resolved")
        print("\\n🔗 Use this endpoint in your Laravel app:")
        print("• POST /separate-stems - Async stem separation")
    else:
        print(f"\\n❌ Stem separation test failed!")
        print("Troubleshooting:")
        print("• Make sure Redis is running")
        print("• Start Celery worker: python start_worker.py") 
        print("• Check that test_audio.wav exists")
        print("• Monitor Celery logs for errors")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)