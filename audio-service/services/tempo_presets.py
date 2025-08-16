"""
Tempo Processing Presets Service
Centralized management of tempo processing presets and configurations
"""

import logging
from typing import Dict, Any, Optional
from models.tempo_models import TempoPresetEnum, TempoPresetConfig

logger = logging.getLogger(__name__)


class TempoPresetsService:
    """Service for managing tempo processing presets"""
    
    def __init__(self):
        self._presets = self._load_default_presets()
    
    def _load_default_presets(self) -> Dict[TempoPresetEnum, TempoPresetConfig]:
        """Load default preset configurations"""
        return {
            TempoPresetEnum.SPED_UP: TempoPresetConfig(
                name="Sped Up",
                tempo_factor=1.25,
                pitch_shift_semitones=3.0,
                preserve_pitch=False,
                effects=["pitch_shift", "brightness_boost"]
            ),
            TempoPresetEnum.SLOWED_REVERB: TempoPresetConfig(
                name="Slowed + Reverb",
                tempo_factor=0.75,
                pitch_shift_semitones=-2.0,
                preserve_pitch=False,
                effects=["pitch_shift", "reverb"],
                reverb_settings={
                    "wet_level": 0.3,
                    "room_size": 0.4,
                    "damping": 0.5
                }
            ),
            TempoPresetEnum.NIGHTCORE: TempoPresetConfig(
                name="Nightcore",
                tempo_factor=1.4,
                pitch_shift_semitones=4.0,
                preserve_pitch=False,
                effects=["pitch_shift", "brightness_boost", "compression"]
            ),
            TempoPresetEnum.CHOPPED_SCREWED: TempoPresetConfig(
                name="Chopped & Screwed",
                tempo_factor=0.6,
                pitch_shift_semitones=-3.0,
                preserve_pitch=False,
                effects=["pitch_shift", "low_pass_filter"],
                filter_settings={
                    "cutoff_hz": 5000.0,
                    "resonance": 0.7
                }
            ),
            TempoPresetEnum.TIME_STRETCHED: TempoPresetConfig(
                name="Time Stretched",
                tempo_factor=0.8,
                pitch_shift_semitones=0.0,
                preserve_pitch=True,
                effects=["time_stretch"]
            )
        }
    
    def get_preset(self, preset_enum: TempoPresetEnum) -> Optional[TempoPresetConfig]:
        """Get a preset configuration by enum"""
        return self._presets.get(preset_enum)
    
    def get_all_presets(self) -> Dict[TempoPresetEnum, TempoPresetConfig]:
        """Get all available presets"""
        return self._presets.copy()
    
    def get_preset_info(self, preset_enum: TempoPresetEnum) -> Optional[Dict[str, Any]]:
        """Get preset information in a format suitable for API responses"""
        preset = self.get_preset(preset_enum)
        if not preset:
            return None
        
        info = {
            "name": preset.name,
            "tempo_factor": preset.tempo_factor,
            "pitch_shift_semitones": preset.pitch_shift_semitones,
            "preserve_pitch": preset.preserve_pitch,
            "effects": preset.effects,
        }
        
        # Add effect-specific settings
        if preset.reverb_settings:
            info["reverb_settings"] = preset.reverb_settings
        if preset.filter_settings:
            info["filter_settings"] = preset.filter_settings
            
        return info
    
    def get_all_presets_info(self) -> Dict[str, Dict[str, Any]]:
        """Get all presets information for API responses"""
        result = {}
        for preset_enum, preset_config in self._presets.items():
            result[preset_enum.value] = self.get_preset_info(preset_enum)
        return result
    
    def apply_preset_to_params(
        self, 
        preset_enum: TempoPresetEnum,
        tempo_factor: float = 1.0,
        pitch_shift_semitones: float = 0.0,
        preserve_pitch: bool = False,
        add_reverb: bool = False
    ) -> Dict[str, Any]:
        """
        Apply preset values to parameters, using preset values only if 
        the parameter is at its default value
        """
        preset = self.get_preset(preset_enum)
        if not preset:
            return {
                "tempo_factor": tempo_factor,
                "pitch_shift_semitones": pitch_shift_semitones,
                "preserve_pitch": preserve_pitch,
                "add_reverb": add_reverb,
                "effects": []
            }
        
        # Apply preset values only if parameters are at defaults
        final_tempo_factor = preset.tempo_factor if tempo_factor == 1.0 else tempo_factor
        final_pitch_shift = preset.pitch_shift_semitones if pitch_shift_semitones == 0.0 else pitch_shift_semitones
        final_preserve_pitch = preset.preserve_pitch if not preserve_pitch else preserve_pitch
        final_add_reverb = "reverb" in preset.effects if not add_reverb else add_reverb
        
        return {
            "tempo_factor": final_tempo_factor,
            "pitch_shift_semitones": final_pitch_shift,
            "preserve_pitch": final_preserve_pitch,
            "add_reverb": final_add_reverb,
            "effects": preset.effects,
            "reverb_settings": preset.reverb_settings,
            "filter_settings": preset.filter_settings
        }
    
    def calculate_final_bpm(
        self, 
        original_bpm: float, 
        preset_enum: TempoPresetEnum,
        tempo_factor: Optional[float] = None
    ) -> float:
        """Calculate final BPM after applying preset"""
        if preset_enum == TempoPresetEnum.CUSTOM:
            return original_bpm * (tempo_factor or 1.0)
        
        preset = self.get_preset(preset_enum)
        if not preset:
            return original_bpm
        
        if preset.preserve_pitch:
            return original_bpm  # Time stretching doesn't change perceived BPM
        else:
            return original_bpm * preset.tempo_factor
    
    def get_preset_description(self, preset_enum: TempoPresetEnum) -> str:
        """Get a human-readable description of what the preset does"""
        descriptions = {
            TempoPresetEnum.CUSTOM: "Custom tempo/pitch settings",
            TempoPresetEnum.SPED_UP: "Faster tempo with higher pitch (chipmunk effect)",
            TempoPresetEnum.SLOWED_REVERB: "Slower tempo with lower pitch and dreamy reverb effect",
            TempoPresetEnum.NIGHTCORE: "High-energy style with fast tempo, high pitch, and increased brightness",
            TempoPresetEnum.CHOPPED_SCREWED: "Houston hip-hop style with slow tempo, low pitch, and filtered sound",
            TempoPresetEnum.TIME_STRETCHED: "Tempo change while preserving the original pitch"
        }
        return descriptions.get(preset_enum, "Unknown preset")


# Global instance
tempo_presets_service = TempoPresetsService()


def get_tempo_presets_service() -> TempoPresetsService:
    """Get the global tempo presets service instance"""
    return tempo_presets_service