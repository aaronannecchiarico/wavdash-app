"""
Unit tests for config module
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestConfig:
    """Test cases for configuration settings"""

    def test_config_import(self):
        """Test that config can be imported"""
        try:
            import config

            assert hasattr(config, "settings")
        except ImportError:
            pytest.fail("Could not import config module")

    def test_settings_attributes(self):
        """Test that settings has expected attributes"""
        from config import settings

        # Basic server settings
        assert hasattr(settings, "HOST")
        assert hasattr(settings, "PORT")
        assert hasattr(settings, "DEBUG")

        # Redis settings
        assert hasattr(settings, "REDIS_HOST")
        assert hasattr(settings, "REDIS_PORT")
        assert hasattr(settings, "REDIS_URL")

        # Audio processing settings
        assert hasattr(settings, "SAMPLE_RATE")
        assert hasattr(settings, "SUPPORTED_FORMATS")
        assert hasattr(settings, "MAX_FILE_SIZE")

        # Device settings
        assert hasattr(settings, "DEMUCS_DEVICE")

    def test_settings_types(self):
        """Test that settings have correct types"""
        from config import settings

        assert isinstance(settings.HOST, str)
        assert isinstance(settings.PORT, int)
        assert isinstance(settings.DEBUG, bool)

        assert isinstance(settings.REDIS_HOST, str)
        assert isinstance(settings.REDIS_PORT, int)
        assert isinstance(settings.REDIS_URL, str)

        assert isinstance(settings.SAMPLE_RATE, int)
        assert isinstance(settings.SUPPORTED_FORMATS, (list, tuple))
        assert isinstance(settings.MAX_FILE_SIZE, int)

    def test_redis_url_format(self):
        """Test Redis URL format"""
        from config import settings

        expected_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
        assert settings.REDIS_URL == expected_url

    def test_supported_formats_content(self):
        """Test supported formats contain expected values"""
        from config import settings

        expected_formats = ["wav", "mp3", "flac", "m4a", "ogg"]

        for fmt in expected_formats:
            assert fmt in settings.SUPPORTED_FORMATS

    def test_sample_rate_reasonable(self):
        """Test sample rate is reasonable"""
        from config import settings

        assert 8000 <= settings.SAMPLE_RATE <= 48000

    def test_max_file_size_reasonable(self):
        """Test max file size is reasonable"""
        from config import settings

        # Should be at least 1MB, at most 1GB
        assert 1024 * 1024 <= settings.MAX_FILE_SIZE <= 1024 * 1024 * 1024

    def test_port_reasonable(self):
        """Test port is in reasonable range"""
        from config import settings

        assert 1024 <= settings.PORT <= 65535

    @patch.dict(os.environ, {"DEBUG": "True"})
    def test_debug_env_var_true(self):
        """Test DEBUG environment variable parsing (True)"""
        # Need to reimport to pick up env change
        import importlib
        import config

        importlib.reload(config)

        assert config.settings.DEBUG == True

    @patch.dict(os.environ, {"DEBUG": "False"})
    def test_debug_env_var_false(self):
        """Test DEBUG environment variable parsing (False)"""
        import importlib
        import config

        importlib.reload(config)

        assert config.settings.DEBUG == False

    @patch.dict(os.environ, {"PORT": "9000"})
    def test_port_env_var(self):
        """Test PORT environment variable parsing"""
        import importlib
        import config

        importlib.reload(config)

        assert config.settings.PORT == 9000

    @patch.dict(os.environ, {"REDIS_HOST": "custom-redis"})
    def test_redis_host_env_var(self):
        """Test REDIS_HOST environment variable"""
        import importlib
        import config

        importlib.reload(config)

        assert config.settings.REDIS_HOST == "custom-redis"
        assert "custom-redis" in config.settings.REDIS_URL

    @patch.dict(os.environ, {"REDIS_PORT": "6380"})
    def test_redis_port_env_var(self):
        """Test REDIS_PORT environment variable"""
        import importlib
        import config

        importlib.reload(config)

        assert config.settings.REDIS_PORT == 6380
        assert ":6380" in config.settings.REDIS_URL

    @patch.dict(os.environ, {"DEMUCS_DEVICE": "cuda"})
    def test_demucs_device_env_var(self):
        """Test DEMUCS_DEVICE environment variable"""
        import importlib
        import config

        importlib.reload(config)

        assert config.settings.DEMUCS_DEVICE == "cuda"

    def test_cors_origins_type(self):
        """Test CORS origins configuration"""
        from config import settings

        if hasattr(settings, "ALLOWED_ORIGINS"):
            assert isinstance(settings.ALLOWED_ORIGINS, (list, tuple, str))

            if isinstance(settings.ALLOWED_ORIGINS, str):
                # If it's a string, it should be "*" or a valid URL
                assert settings.ALLOWED_ORIGINS in [
                    "*"
                ] or settings.ALLOWED_ORIGINS.startswith("http")

    def test_log_level_valid(self):
        """Test log level is valid"""
        from config import settings

        if hasattr(settings, "LOG_LEVEL"):
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            assert settings.LOG_LEVEL.upper() in valid_levels

    def test_task_settings(self):
        """Test task-related settings"""
        from config import settings

        if hasattr(settings, "TASK_TIME_LIMIT"):
            assert isinstance(settings.TASK_TIME_LIMIT, int)
            assert settings.TASK_TIME_LIMIT > 0

        if hasattr(settings, "TASK_SOFT_TIME_LIMIT"):
            assert isinstance(settings.TASK_SOFT_TIME_LIMIT, int)
            assert settings.TASK_SOFT_TIME_LIMIT > 0

            # Soft limit should be less than hard limit
            if hasattr(settings, "TASK_TIME_LIMIT"):
                assert settings.TASK_SOFT_TIME_LIMIT <= settings.TASK_TIME_LIMIT


if __name__ == "__main__":
    pytest.main([__file__])
