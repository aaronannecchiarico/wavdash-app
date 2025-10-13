#!/usr/bin/env python3
"""
Data Seeder for Audio Processing Microservice

This script seeds the system with necessary data and configurations:
- Validates tempo presets are available
- Creates test fixtures if needed
- Initializes performance monitoring
- Sets up any default configurations

This is run as part of fresh migrations or can be run standalone.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import soundfile as sf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_tempo_presets() -> bool:
    """Verify all tempo presets are properly configured"""
    print("🎵 Verifying tempo presets...")
    
    try:
        from services.tempo_presets import get_tempo_presets_service
        from models.tempo_models import TempoPresetEnum
        
        service = get_tempo_presets_service()
        all_presets = service.get_all_presets()
        
        expected_presets = [
            TempoPresetEnum.SPED_UP,
            TempoPresetEnum.SLOWED_REVERB,
            TempoPresetEnum.NIGHTCORE,
            TempoPresetEnum.CHOPPED_SCREWED,
            TempoPresetEnum.TIME_STRETCHED
        ]
        
        missing_presets = []
        for preset in expected_presets:
            if preset not in all_presets:
                missing_presets.append(preset.value)
            else:
                preset_config = service.get_preset(preset)
                print(f"✅ {preset.value}: {preset_config.name}")
        
        if missing_presets:
            print(f"❌ Missing presets: {missing_presets}")
            return False
        
        print(f"✅ All {len(expected_presets)} tempo presets verified")
        return True
        
    except Exception as e:
        print(f"❌ Tempo preset verification failed: {e}")
        return False


def create_test_audio_fixtures() -> bool:
    """Create test audio fixtures if they don't exist"""
    print("🎼 Creating test audio fixtures...")
    
    try:
        fixtures_dir = Path("tests/fixtures")
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test audio file if it doesn't exist
        test_audio_path = fixtures_dir / "test_audio.wav"
        
        if not test_audio_path.exists():
            # Generate a simple test tone
            sample_rate = 22050
            duration = 3.0  # 3 seconds
            frequency = 440.0  # A4 note
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Create a simple sine wave with some harmonics
            audio_data = (
                np.sin(2 * np.pi * frequency * t) * 0.3 +
                np.sin(2 * np.pi * frequency * 2 * t) * 0.1 +
                np.sin(2 * np.pi * frequency * 3 * t) * 0.05
            )
            
            # Add some envelope to make it more realistic
            fade_samples = int(0.1 * sample_rate)  # 0.1 second fade
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            audio_data[:fade_samples] *= fade_in
            audio_data[-fade_samples:] *= fade_out
            
            # Save as WAV file
            sf.write(test_audio_path, audio_data, sample_rate)
            print(f"✅ Created test audio: {test_audio_path}")
        else:
            print(f"✅ Test audio exists: {test_audio_path}")
        
        # Verify the file is readable
        try:
            data, sr = sf.read(test_audio_path)
            print(f"✅ Test audio verified: {len(data)} samples at {sr}Hz")
        except Exception as e:
            print(f"❌ Test audio verification failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test fixture creation failed: {e}")
        return False


def initialize_performance_monitoring() -> bool:
    """Initialize performance monitoring with default settings"""
    print("📊 Initializing performance monitoring...")
    
    try:
        from services.performance_cache import get_performance_cache, get_performance_monitor
        
        # Initialize cache
        cache = get_performance_cache()
        cache_stats = cache.get_cache_stats()
        print(f"✅ Performance cache initialized: {cache_stats['total_files']} files")
        
        # Initialize monitor
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics()
        print(f"✅ Performance monitor initialized: {metrics['total_requests']} requests tracked")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring initialization failed: {e}")
        return False


def validate_environment_config() -> bool:
    """Validate environment configuration is complete"""
    print("⚙️  Validating environment configuration...")
    
    try:
        from config import settings
        
        # Check critical settings
        required_settings = [
            'REDIS_HOST',
            'REDIS_PORT', 
            'SAMPLE_RATE',
            'MAX_FILE_SIZE'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)
            else:
                value = getattr(settings, setting)
                print(f"✅ {setting}: {value}")
        
        if missing_settings:
            print(f"❌ Missing required settings: {missing_settings}")
            return False
        
        # Validate storage configuration
        storage_type = getattr(settings, 'STORAGE_TYPE', 'local')
        print(f"✅ Storage type: {storage_type}")
        
        if storage_type == 'local':
            storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
            print(f"✅ Local storage path: {storage_path}")
        elif storage_type == 'r2':
            r2_bucket = getattr(settings, 'R2_BUCKET', None)
            if not r2_bucket:
                print("❌ R2 storage configured but R2_BUCKET not set")
                return False
            print(f"✅ R2 bucket: {r2_bucket}")
        
        print("✅ Environment configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False


def create_default_configurations() -> bool:
    """Create default configuration files if needed"""
    print("📄 Creating default configurations...")
    
    try:
        # Create default logging configuration if it doesn't exist
        logging_config_path = Path("logging_config.json")
        
        if not logging_config_path.exists():
            default_logging_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                        "level": "INFO"
                    },
                    "file": {
                        "class": "logging.FileHandler",
                        "filename": "logs/microservice.log",
                        "formatter": "default",
                        "level": "DEBUG"
                    }
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                }
            }
            
            with open(logging_config_path, 'w') as f:
                json.dump(default_logging_config, f, indent=2)
            print(f"✅ Created logging config: {logging_config_path}")
        else:
            print(f"✅ Logging config exists: {logging_config_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration creation failed: {e}")
        return False


def run_seeding_tests() -> bool:
    """Run basic tests to verify seeded data works"""
    print("🧪 Running seeding verification tests...")
    
    try:
        # Test tempo presets
        from services.tempo_presets import get_tempo_presets_service
        from models.tempo_models import TempoPresetEnum
        
        service = get_tempo_presets_service()
        
        # Test preset retrieval
        nightcore = service.get_preset(TempoPresetEnum.NIGHTCORE)
        if not nightcore or nightcore.tempo_factor != 1.4:
            print("❌ Nightcore preset validation failed")
            return False
        
        # Test preset info API format
        info = service.get_all_presets_info()
        if len(info) < 5:
            print("❌ Preset info API validation failed")
            return False
        
        print("✅ Tempo preset tests passed")
        
        # Test audio fixtures
        fixtures_path = Path("tests/fixtures/test_audio.wav")
        if not fixtures_path.exists():
            print("❌ Test audio fixture missing")
            return False
        
        # Try to load the test audio
        import soundfile as sf
        data, sr = sf.read(fixtures_path)
        if len(data) == 0 or sr != 22050:
            print("❌ Test audio fixture validation failed")
            return False
        
        print("✅ Audio fixture tests passed")
        
        print("✅ All seeding verification tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Seeding verification failed: {e}")
        return False


def main():
    """Run complete data seeding process"""
    print("🌱 Audio Processing Microservice - Data Seeding")
    print("=" * 50)
    
    # Seeding steps
    steps = [
        ("Environment Configuration Validation", validate_environment_config),
        ("Tempo Presets Verification", verify_tempo_presets),
        ("Test Audio Fixtures Creation", create_test_audio_fixtures),
        ("Performance Monitoring Initialization", initialize_performance_monitoring),
        ("Default Configurations Creation", create_default_configurations),
        ("Seeding Verification Tests", run_seeding_tests)
    ]
    
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
    print("\n" + "=" * 50)
    print("📊 SEEDING SUMMARY")
    print("=" * 50)
    
    if not failed_steps:
        print("🎉 Data seeding completed successfully!")
        print("\n✅ All seeding steps completed:")
        for step_name, _ in steps:
            print(f"   • {step_name}")
        
        print("\n🌱 System is now seeded with:")
        print("   • 5 tempo processing presets")
        print("   • Test audio fixtures")
        print("   • Performance monitoring baseline")
        print("   • Default configurations")
        
        return True
    else:
        print(f"❌ Seeding completed with {len(failed_steps)} failed steps:")
        for step in failed_steps:
            print(f"   • {step}")
        
        print("\n🔧 Please resolve the failed steps.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)