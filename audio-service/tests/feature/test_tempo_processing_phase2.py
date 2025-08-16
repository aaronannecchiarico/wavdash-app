"""
Feature tests for Phase 2 tempo processing enhancements
Tests the enhanced pedalboard integration, stem-aware processing, and BPM suggestions
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from tasks.tempo_processing import (
    apply_tempo_processing,
    calculate_optimal_tempo_factor,
    get_smart_preset_suggestions,
    validate_tempo_processing_params,
    check_system_compatibility,
    process_stems_individually,
    mix_processed_stems,
    TEMPO_PRESETS
)
from models.tempo_models import TempoPresetEnum


class TestPhase2Enhancements:
    """Test Phase 2 enhanced features"""
    
    def test_bpm_aware_tempo_suggestions(self):
        """Test BPM-aware tempo factor calculation"""
        # Test slow BPM -> speed up suggestion
        slow_bpm = 70
        factor = calculate_optimal_tempo_factor(slow_bpm, "pop")
        assert factor > 1.0  # Should suggest speeding up
        assert 0.25 <= factor <= 4.0  # Within valid range
        
        # Test fast BPM -> slow down suggestion
        fast_bpm = 160
        factor = calculate_optimal_tempo_factor(fast_bpm, "chill")
        assert factor < 1.0  # Should suggest slowing down
        assert 0.25 <= factor <= 4.0  # Within valid range
        
        # Test unknown style returns 1.0
        factor = calculate_optimal_tempo_factor(120, "unknown_style")
        assert factor == 1.0
    
    def test_smart_preset_suggestions(self):
        """Test intelligent preset recommendations"""
        # Test slow BPM suggestions
        suggestions = get_smart_preset_suggestions(65, 180)  # Slow BPM, 3 min track
        assert "speed_up" in suggestions
        assert suggestions["speed_up"]["preset"] == TempoPresetEnum.SPED_UP
        assert "optimal_factor" in suggestions["speed_up"]
        
        # Test fast BPM suggestions
        suggestions = get_smart_preset_suggestions(150, 240)  # Fast BPM, 4 min track
        assert "slow_down" in suggestions
        assert suggestions["slow_down"]["preset"] == TempoPresetEnum.SLOWED_REVERB
        
        # Test long duration suggestions
        suggestions = get_smart_preset_suggestions(120, 400)  # 5+ min track
        assert "time_stretch" in suggestions
        assert suggestions["time_stretch"]["preset"] == TempoPresetEnum.TIME_STRETCHED
        
        # Always includes energetic suggestion
        assert "energetic" in suggestions
        assert suggestions["energetic"]["preset"] == TempoPresetEnum.NIGHTCORE
    
    def test_enhanced_parameter_validation(self):
        """Test enhanced validation with warnings"""
        # Valid parameters - no warnings
        warnings = validate_tempo_processing_params(1.0, 0.0, 180)
        assert len(warnings) == 0
        
        # Extreme slow tempo - should warn
        warnings = validate_tempo_processing_params(0.4, 0.0, 180)
        assert "tempo_extreme_slow" in warnings
        
        # Extreme fast tempo - should warn
        warnings = validate_tempo_processing_params(2.5, 0.0, 180)
        assert "tempo_extreme_fast" in warnings
        
        # Large pitch shift - should warn
        warnings = validate_tempo_processing_params(1.0, 10.0, 180)
        assert "pitch_extreme" in warnings
        
        # Long duration - should warn
        warnings = validate_tempo_processing_params(1.0, 0.0, 700)
        assert "long_duration" in warnings
        
        # Short duration - should warn
        warnings = validate_tempo_processing_params(1.0, 0.0, 8)
        assert "short_duration" in warnings
        
        # Aggressive processing - should warn
        warnings = validate_tempo_processing_params(2.0, 6.0, 180)
        assert "aggressive_processing" in warnings
        
        # Invalid parameters - should raise
        with pytest.raises(ValueError):
            validate_tempo_processing_params(5.0, 0.0, 180)  # tempo too high
        
        with pytest.raises(ValueError):
            validate_tempo_processing_params(1.0, 15.0, 180)  # pitch too high
    
    def test_system_compatibility_check(self):
        """Test system compatibility checking"""
        compatibility = check_system_compatibility()
        
        # Should have required fields
        assert "pedalboard_available" in compatibility
        assert "librosa_version" in compatibility
        assert "numpy_version" in compatibility
        assert "system_info" in compatibility
        assert "recommendations" in compatibility
        
        # Should be boolean
        assert isinstance(compatibility["pedalboard_available"], bool)
        
        # Should have recommendations if pedalboard not available
        if not compatibility["pedalboard_available"]:
            assert any("pedalboard" in rec.lower() for rec in compatibility["recommendations"])
    
    def test_stem_aware_processing(self):
        """Test stem-aware audio processing"""
        # Create mock audio data for different stems
        sample_rate = 44100
        duration = 1.0  # 1 second
        samples = int(sample_rate * duration)
        
        stems_data = {
            "vocals": np.random.normal(0, 0.1, samples).astype(np.float32),
            "drums": np.random.normal(0, 0.1, samples).astype(np.float32),
            "bass": np.random.normal(0, 0.1, samples).astype(np.float32),
            "other": np.random.normal(0, 0.1, samples).astype(np.float32)
        }
        
        preset_config = TEMPO_PRESETS[TempoPresetEnum.NIGHTCORE]
        
        # Process stems individually
        processed_stems = process_stems_individually(
            stems_data, sample_rate, preset_config, 
            1.3, 4.0, False, True
        )
        
        # Should return processed data for each stem
        assert len(processed_stems) == len(stems_data)
        for stem_name in stems_data.keys():
            assert stem_name in processed_stems
            assert isinstance(processed_stems[stem_name], np.ndarray)
            assert len(processed_stems[stem_name]) > 0
    
    def test_stem_mixing(self):
        """Test intelligent stem mixing"""
        # Create mock processed stems
        samples = 44100  # 1 second
        processed_stems = {
            "vocals": np.random.normal(0, 0.1, samples).astype(np.float32),
            "drums": np.random.normal(0, 0.1, samples).astype(np.float32),
            "bass": np.random.normal(0, 0.1, samples).astype(np.float32),
            "other": np.random.normal(0, 0.1, samples).astype(np.float32)
        }
        
        # Test default mixing
        mixed = mix_processed_stems(processed_stems)
        assert isinstance(mixed, np.ndarray)
        assert len(mixed) == samples
        assert mixed.dtype == np.float32
        
        # Should normalize if needed
        assert np.max(np.abs(mixed)) <= 1.0
        
        # Test custom mixing weights
        custom_weights = {"vocals": 1.5, "drums": 0.5, "bass": 1.0, "other": 0.7}
        mixed_custom = mix_processed_stems(processed_stems, custom_weights)
        assert isinstance(mixed_custom, np.ndarray)
        assert len(mixed_custom) == samples
        
        # Test with empty stems - should raise error
        with pytest.raises(ValueError):
            mix_processed_stems({})
    
    @patch('tasks.tempo_processing.PEDALBOARD_AVAILABLE', False)
    def test_fallback_processing_without_pedalboard(self):
        """Test graceful fallback when pedalboard is not available"""
        # Create test audio
        sample_rate = 44100
        duration = 0.5  # 0.5 seconds
        samples = int(sample_rate * duration)
        audio_data = np.random.normal(0, 0.1, samples).astype(np.float32)
        
        # Should work without pedalboard
        result = apply_tempo_processing(
            audio_data, sample_rate, 1.5, 2.0, False, True
        )
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) > 0
    
    def test_enhanced_preset_configurations(self):
        """Test Phase 2 enhanced preset configurations"""
        # Check that all presets have enhanced configurations
        for preset_name, config in TEMPO_PRESETS.items():
            assert "effects" in config
            assert "description" in config
            assert isinstance(config["effects"], list)
            
            # Check for enhanced settings
            if "reverb" in config["effects"]:
                assert "reverb_settings" in config
            if "compression" in config["effects"]:
                assert "compression_settings" in config
            if "chorus" in config["effects"]:
                assert "chorus_settings" in config
        
        # Verify specific enhancements
        nightcore = TEMPO_PRESETS[TempoPresetEnum.NIGHTCORE]
        assert "compression" in nightcore["effects"]
        assert "chorus" in nightcore["effects"]
        assert "compression_settings" in nightcore
        assert "chorus_settings" in nightcore
        
        slowed_reverb = TEMPO_PRESETS[TempoPresetEnum.SLOWED_REVERB]
        assert "compression" in slowed_reverb["effects"]
        assert "compression_settings" in slowed_reverb


@pytest.mark.integration
class TestTempoProcessingIntegration:
    """Integration tests for tempo processing with enhanced features"""
    
    def test_full_processing_pipeline_with_suggestions(self):
        """Test complete processing pipeline with BPM analysis and suggestions"""
        # Create test audio with known characteristics
        sample_rate = 44100
        duration = 2.0  # 2 seconds
        samples = int(sample_rate * duration)
        
        # Generate a simple sine wave for testing
        t = np.linspace(0, duration, samples)
        frequency = 440  # A note
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5
        
        # Mock BPM detection to return a known value
        with patch('librosa.beat.tempo') as mock_tempo:
            mock_tempo.return_value = np.array([120.0])
            
            # Test the complete workflow that would happen in the task
            original_bpm = 120.0
            smart_suggestions = get_smart_preset_suggestions(original_bpm, duration)
            processing_warnings = validate_tempo_processing_params(1.3, 2.0, duration)
            
            # Apply processing
            processed_audio = apply_tempo_processing(
                audio_data, sample_rate, 1.3, 2.0, False, False,
                TEMPO_PRESETS[TempoPresetEnum.SPED_UP]
            )
            
            # Verify results
            assert isinstance(processed_audio, np.ndarray)
            assert processed_audio.dtype == np.float32
            assert len(smart_suggestions) > 0
            assert isinstance(processing_warnings, dict)
    
    def test_error_recovery_scenarios(self):
        """Test error handling and recovery in various scenarios"""
        from tasks.tempo_processing import handle_processing_error
        
        # Test ValueError handling
        error = ValueError("Invalid tempo_factor: 5.0")
        error_info = handle_processing_error(error, "test context")
        
        assert error_info["error_type"] == "ValueError"
        assert "tempo_factor" in error_info["error_message"]
        assert len(error_info["recovery_suggestions"]) > 0
        assert any("tempo_factor" in suggestion for suggestion in error_info["recovery_suggestions"])
        
        # Test ImportError handling  
        error = ImportError("No module named 'pedalboard'")
        error_info = handle_processing_error(error, "test context")
        
        assert error_info["error_type"] == "ImportError"
        assert len(error_info["recovery_suggestions"]) > 0
        assert any("pedalboard" in suggestion for suggestion in error_info["recovery_suggestions"])