"""
Unit tests for services.tempo_presets module
"""

from pathlib import Path
import sys

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.tempo_models import TempoPresetConfig, TempoPresetEnum
from services.tempo_presets import TempoPresetsService, get_tempo_presets_service


class TestTempoPresetsService:
    """Test cases for TempoPresetsService"""

    def setup_method(self):
        """Set up test instance"""
        self.service = TempoPresetsService()

    def test_get_preset_valid(self):
        """Test getting valid preset configurations"""
        preset = self.service.get_preset(TempoPresetEnum.SPED_UP)

        assert preset is not None
        assert preset.name == "Sped Up"
        assert preset.tempo_factor == 1.25
        assert preset.pitch_shift_semitones == 3.0
        assert preset.preserve_pitch is False
        assert "pitch_shift" in preset.effects
        assert "brightness_boost" in preset.effects

    def test_get_preset_slowed_reverb(self):
        """Test getting slowed reverb preset configuration"""
        preset = self.service.get_preset(TempoPresetEnum.SLOWED_REVERB)

        assert preset is not None
        assert preset.name == "Slowed + Reverb"
        assert preset.tempo_factor == 0.75
        assert preset.pitch_shift_semitones == -2.0
        assert preset.preserve_pitch is False
        assert "reverb" in preset.effects
        assert preset.reverb_settings is not None
        assert preset.reverb_settings["wet_level"] == 0.3
        assert preset.reverb_settings["room_size"] == 0.4

    def test_get_preset_nightcore(self):
        """Test getting nightcore preset configuration"""
        preset = self.service.get_preset(TempoPresetEnum.NIGHTCORE)

        assert preset is not None
        assert preset.name == "Nightcore"
        assert preset.tempo_factor == 1.4
        assert preset.pitch_shift_semitones == 4.0
        assert "compression" in preset.effects

    def test_get_preset_time_stretched(self):
        """Test getting time stretched preset configuration"""
        preset = self.service.get_preset(TempoPresetEnum.TIME_STRETCHED)

        assert preset is not None
        assert preset.name == "Time Stretched"
        assert preset.tempo_factor == 0.8
        assert preset.pitch_shift_semitones == 0.0
        assert preset.preserve_pitch is True
        assert "time_stretch" in preset.effects

    def test_get_preset_chopped_screwed(self):
        """Test getting chopped & screwed preset configuration"""
        preset = self.service.get_preset(TempoPresetEnum.CHOPPED_SCREWED)

        assert preset is not None
        assert preset.name == "Chopped & Screwed"
        assert preset.tempo_factor == 0.6
        assert preset.pitch_shift_semitones == -3.0
        assert "low_pass_filter" in preset.effects
        assert preset.filter_settings is not None

    def test_get_preset_invalid(self):
        """Test getting preset with invalid enum returns None"""
        # This would require creating an invalid enum value, which is not possible
        # with proper enum usage, so we'll test the None case differently
        preset = self.service._presets.get("invalid_preset")
        assert preset is None

    def test_get_all_presets(self):
        """Test getting all presets"""
        all_presets = self.service.get_all_presets()

        assert len(all_presets) == 5  # Should have 5 predefined presets
        assert TempoPresetEnum.SPED_UP in all_presets
        assert TempoPresetEnum.SLOWED_REVERB in all_presets
        assert TempoPresetEnum.NIGHTCORE in all_presets
        assert TempoPresetEnum.CHOPPED_SCREWED in all_presets
        assert TempoPresetEnum.TIME_STRETCHED in all_presets

        # Ensure all presets are valid TempoPresetConfig objects
        for preset_enum, preset_config in all_presets.items():
            assert isinstance(preset_config, TempoPresetConfig)
            assert preset_config.name
            assert 0.25 <= preset_config.tempo_factor <= 4.0
            assert -12.0 <= preset_config.pitch_shift_semitones <= 12.0

    def test_get_preset_info(self):
        """Test getting preset information for API responses"""
        info = self.service.get_preset_info(TempoPresetEnum.SLOWED_REVERB)

        assert info is not None
        assert info["name"] == "Slowed + Reverb"
        assert info["tempo_factor"] == 0.75
        assert info["pitch_shift_semitones"] == -2.0
        assert info["preserve_pitch"] is False
        assert "reverb" in info["effects"]
        assert "reverb_settings" in info
        assert info["reverb_settings"]["wet_level"] == 0.3

    def test_get_all_presets_info(self):
        """Test getting all presets information for API responses"""
        all_info = self.service.get_all_presets_info()

        assert len(all_info) == 5
        assert "sped_up" in all_info
        assert "slowed_reverb" in all_info
        assert "nightcore" in all_info
        assert "chopped_screwed" in all_info
        assert "time_stretched" in all_info

        # Check that each preset info has required fields
        for preset_key, preset_info in all_info.items():
            assert "name" in preset_info
            assert "tempo_factor" in preset_info
            assert "pitch_shift_semitones" in preset_info
            assert "preserve_pitch" in preset_info
            assert "effects" in preset_info

    def test_apply_preset_to_params_with_defaults(self):
        """Test applying preset values when parameters are at defaults"""
        result = self.service.apply_preset_to_params(
            TempoPresetEnum.SPED_UP,
            tempo_factor=1.0,  # Default value
            pitch_shift_semitones=0.0,  # Default value
            preserve_pitch=False,  # Default value
            add_reverb=False,  # Default value
        )

        assert result["tempo_factor"] == 1.25  # From preset
        assert result["pitch_shift_semitones"] == 3.0  # From preset
        assert result["preserve_pitch"] is False  # From preset
        assert result["add_reverb"] is False  # Preset doesn't have reverb
        assert result["effects"] == ["pitch_shift", "brightness_boost"]

    def test_apply_preset_to_params_with_custom_values(self):
        """Test applying preset values when parameters are not at defaults"""
        result = self.service.apply_preset_to_params(
            TempoPresetEnum.SPED_UP,
            tempo_factor=2.0,  # Custom value
            pitch_shift_semitones=5.0,  # Custom value
            preserve_pitch=True,  # Custom value
            add_reverb=True,  # Custom value
        )

        assert result["tempo_factor"] == 2.0  # Keep custom value
        assert result["pitch_shift_semitones"] == 5.0  # Keep custom value
        assert result["preserve_pitch"] is True  # Keep custom value
        assert result["add_reverb"] is True  # Keep custom value

    def test_apply_preset_to_params_reverb_preset(self):
        """Test applying reverb preset values"""
        result = self.service.apply_preset_to_params(
            TempoPresetEnum.SLOWED_REVERB, add_reverb=False  # Default value
        )

        assert result["add_reverb"] is True  # Should be True because preset has reverb
        assert result["reverb_settings"] is not None
        assert result["reverb_settings"]["wet_level"] == 0.3

    def test_calculate_final_bpm_custom(self):
        """Test calculating final BPM for custom preset"""
        final_bpm = self.service.calculate_final_bpm(120.0, TempoPresetEnum.CUSTOM, 1.5)
        assert final_bpm == 180.0  # 120 * 1.5

    def test_calculate_final_bpm_preset_with_pitch_change(self):
        """Test calculating final BPM for preset that changes pitch"""
        final_bpm = self.service.calculate_final_bpm(120.0, TempoPresetEnum.SPED_UP)
        assert final_bpm == 150.0  # 120 * 1.25

    def test_calculate_final_bpm_time_stretched(self):
        """Test calculating final BPM for time stretched preset"""
        final_bpm = self.service.calculate_final_bpm(
            120.0, TempoPresetEnum.TIME_STRETCHED
        )
        assert final_bpm == 120.0  # Should remain the same due to pitch preservation

    def test_get_preset_description(self):
        """Test getting preset descriptions"""
        description = self.service.get_preset_description(TempoPresetEnum.CUSTOM)
        assert "Custom tempo/pitch settings" in description

        description = self.service.get_preset_description(TempoPresetEnum.SPED_UP)
        assert "chipmunk effect" in description

        description = self.service.get_preset_description(TempoPresetEnum.SLOWED_REVERB)
        assert "reverb effect" in description

        description = self.service.get_preset_description(TempoPresetEnum.NIGHTCORE)
        assert "High-energy" in description

        description = self.service.get_preset_description(
            TempoPresetEnum.CHOPPED_SCREWED
        )
        assert "Houston hip-hop" in description

        description = self.service.get_preset_description(
            TempoPresetEnum.TIME_STRETCHED
        )
        assert "preserving the original pitch" in description


class TestTempoPresetsServiceGlobal:
    """Test the global tempo presets service instance"""

    def test_get_tempo_presets_service(self):
        """Test that global service instance is returned consistently"""
        service1 = get_tempo_presets_service()
        service2 = get_tempo_presets_service()

        assert service1 is service2  # Should be the same instance
        assert isinstance(service1, TempoPresetsService)

    def test_global_service_has_presets(self):
        """Test that global service has all expected presets"""
        service = get_tempo_presets_service()
        all_presets = service.get_all_presets()

        assert len(all_presets) >= 5  # Should have at least the 5 default presets

        # Verify all expected presets are present
        expected_presets = [
            TempoPresetEnum.SPED_UP,
            TempoPresetEnum.SLOWED_REVERB,
            TempoPresetEnum.NIGHTCORE,
            TempoPresetEnum.CHOPPED_SCREWED,
            TempoPresetEnum.TIME_STRETCHED,
        ]

        for expected_preset in expected_presets:
            assert expected_preset in all_presets
            preset = service.get_preset(expected_preset)
            assert preset is not None
            assert isinstance(preset, TempoPresetConfig)
