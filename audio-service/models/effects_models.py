"""
Pydantic models for advanced audio effects processing

This module defines the data models for configuring and processing
advanced audio effects chains on individual stems and full mixes.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid


class EffectType(str, Enum):
    """Available audio effect types"""
    # Dynamics
    COMPRESSOR = "compressor"
    LIMITER = "limiter"
    GATE = "gate"
    EXPANDER = "expander"
    
    # EQ & Filters
    HIGH_SHELF = "high_shelf"
    LOW_SHELF = "low_shelf"
    LADDER_FILTER = "ladder_filter"
    PEAK_FILTER = "peak_filter"
    
    # Time-Based
    REVERB = "reverb"
    DELAY = "delay"
    CONVOLUTION = "convolution"
    
    # Modulation
    CHORUS = "chorus"
    PHASER = "phaser"
    FLANGER = "flanger"
    TREMOLO = "tremolo"
    VIBRATO = "vibrato"
    
    # Distortion
    DISTORTION = "distortion"
    OVERDRIVE = "overdrive"
    BITCRUSH = "bitcrush"
    
    # Utility
    GAIN = "gain"
    PITCH_SHIFT = "pitch_shift"


class StemType(str, Enum):
    """Available stem types for processing"""
    VOCALS = "vocals"
    DRUMS = "drums"
    BASS = "bass"
    OTHER = "other"
    FULL_MIX = "full_mix"


class EffectParameters(BaseModel):
    """Base class for effect parameters"""
    enabled: bool = True
    mix: float = Field(default=1.0, ge=0.0, le=1.0, description="Dry/wet mix ratio")


class CompressorParams(EffectParameters):
    """Compressor effect parameters"""
    threshold_db: float = Field(default=-20.0, ge=-60.0, le=0.0, description="Compression threshold in dB")
    ratio: float = Field(default=4.0, ge=1.0, le=20.0, description="Compression ratio")
    attack_ms: float = Field(default=10.0, ge=0.1, le=100.0, description="Attack time in milliseconds")
    release_ms: float = Field(default=100.0, ge=1.0, le=1000.0, description="Release time in milliseconds")
    knee_db: float = Field(default=2.0, ge=0.0, le=10.0, description="Knee width in dB")
    makeup_gain_db: float = Field(default=0.0, ge=-20.0, le=20.0, description="Makeup gain in dB")


class LimiterParams(EffectParameters):
    """Limiter effect parameters"""
    threshold_db: float = Field(default=-3.0, ge=-20.0, le=0.0, description="Limiting threshold in dB")
    release_ms: float = Field(default=50.0, ge=1.0, le=500.0, description="Release time in milliseconds")


class GateParams(EffectParameters):
    """Gate effect parameters"""
    threshold_db: float = Field(default=-40.0, ge=-80.0, le=-10.0, description="Gate threshold in dB")
    ratio: float = Field(default=10.0, ge=2.0, le=100.0, description="Gate ratio")
    attack_ms: float = Field(default=1.0, ge=0.1, le=50.0, description="Attack time in milliseconds")
    release_ms: float = Field(default=100.0, ge=10.0, le=5000.0, description="Release time in milliseconds")


class ReverbParams(EffectParameters):
    """Reverb effect parameters"""
    room_size: float = Field(default=0.5, ge=0.0, le=1.0, description="Room size")
    damping: float = Field(default=0.5, ge=0.0, le=1.0, description="High frequency damping")
    wet_level: float = Field(default=0.3, ge=0.0, le=1.0, description="Wet signal level")
    dry_level: float = Field(default=1.0, ge=0.0, le=1.0, description="Dry signal level")
    width: float = Field(default=1.0, ge=0.0, le=1.0, description="Stereo width")


class DelayParams(EffectParameters):
    """Delay effect parameters"""
    delay_seconds: float = Field(default=0.25, ge=0.001, le=2.0, description="Delay time in seconds")
    feedback: float = Field(default=0.3, ge=0.0, le=0.95, description="Feedback amount")
    mix: float = Field(default=0.3, ge=0.0, le=1.0, description="Dry/wet mix")


class DistortionParams(EffectParameters):
    """Distortion effect parameters"""
    drive_db: float = Field(default=10.0, ge=0.0, le=40.0, description="Drive amount in dB")


class OverdriveParams(EffectParameters):
    """Overdrive effect parameters"""
    drive_db: float = Field(default=5.0, ge=0.0, le=30.0, description="Drive amount in dB")


class ChorusParams(EffectParameters):
    """Chorus effect parameters"""
    rate_hz: float = Field(default=0.5, ge=0.1, le=5.0, description="Modulation rate in Hz")
    depth: float = Field(default=0.25, ge=0.0, le=1.0, description="Modulation depth")
    centre_delay_ms: float = Field(default=7.0, ge=1.0, le=20.0, description="Center delay in milliseconds")
    feedback: float = Field(default=0.0, ge=0.0, le=0.8, description="Feedback amount")


class PhaserParams(EffectParameters):
    """Phaser effect parameters"""
    rate_hz: float = Field(default=0.5, ge=0.1, le=5.0, description="Modulation rate in Hz")
    depth: float = Field(default=0.5, ge=0.0, le=1.0, description="Modulation depth")
    centre_frequency_hz: float = Field(default=1000.0, ge=100.0, le=5000.0, description="Center frequency in Hz")
    feedback: float = Field(default=0.5, ge=0.0, le=0.8, description="Feedback amount")


class HighShelfParams(EffectParameters):
    """High shelf filter parameters"""
    cutoff_frequency_hz: float = Field(default=3000.0, ge=100.0, le=20000.0, description="Cutoff frequency in Hz")
    gain_db: float = Field(default=0.0, ge=-20.0, le=20.0, description="Gain in dB")
    q: float = Field(default=0.7, ge=0.1, le=10.0, description="Q factor")


class LowShelfParams(EffectParameters):
    """Low shelf filter parameters"""
    cutoff_frequency_hz: float = Field(default=300.0, ge=20.0, le=2000.0, description="Cutoff frequency in Hz")
    gain_db: float = Field(default=0.0, ge=-20.0, le=20.0, description="Gain in dB")
    q: float = Field(default=0.7, ge=0.1, le=10.0, description="Q factor")


class LadderFilterParams(EffectParameters):
    """Ladder filter parameters"""
    cutoff_hz: float = Field(default=1000.0, ge=20.0, le=20000.0, description="Cutoff frequency in Hz")
    resonance: float = Field(default=0.0, ge=0.0, le=1.0, description="Resonance amount")
    drive: float = Field(default=1.0, ge=0.1, le=10.0, description="Drive amount")
    mode: str = Field(default="LPF12", description="Filter mode (LPF12, LPF24, HPF12, HPF24, BPF12, BPF24)")

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        valid_modes = ["LPF12", "LPF24", "HPF12", "HPF24", "BPF12", "BPF24"]
        if v not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        return v


class GainParams(EffectParameters):
    """Gain effect parameters"""
    gain_db: float = Field(default=0.0, ge=-60.0, le=60.0, description="Gain in dB")


class PitchShiftParams(EffectParameters):
    """Pitch shift effect parameters"""
    semitones: float = Field(default=0.0, ge=-24.0, le=24.0, description="Pitch shift in semitones")


# Union type for all effect parameter types
EffectParametersUnion = Union[
    CompressorParams,
    LimiterParams,
    GateParams,
    ReverbParams,
    DelayParams,
    DistortionParams,
    OverdriveParams,
    ChorusParams,
    PhaserParams,
    HighShelfParams,
    LowShelfParams,
    LadderFilterParams,
    GainParams,
    PitchShiftParams,
]


class Effect(BaseModel):
    """Individual effect in a processing chain"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    type: EffectType = Field(description="Type of effect")
    name: str = Field(description="User-friendly name")
    parameters: EffectParametersUnion = Field(description="Effect-specific parameters")
    bypass: bool = Field(default=False, description="Whether effect is bypassed")
    order: int = Field(description="Position in effect chain (0-based)")

    @field_validator('parameters', mode='before')
    @classmethod
    def validate_parameters(cls, v, info):
        """Validate that parameters match the effect type"""
        if not info.data or 'type' not in info.data:
            return v
        
        effect_type = info.data['type']
        param_mapping = {
            EffectType.COMPRESSOR: CompressorParams,
            EffectType.LIMITER: LimiterParams,
            EffectType.GATE: GateParams,
            EffectType.REVERB: ReverbParams,
            EffectType.DELAY: DelayParams,
            EffectType.DISTORTION: DistortionParams,
            EffectType.OVERDRIVE: OverdriveParams,
            EffectType.CHORUS: ChorusParams,
            EffectType.PHASER: PhaserParams,
            EffectType.HIGH_SHELF: HighShelfParams,
            EffectType.LOW_SHELF: LowShelfParams,
            EffectType.LADDER_FILTER: LadderFilterParams,
            EffectType.GAIN: GainParams,
            EffectType.PITCH_SHIFT: PitchShiftParams,
        }
        
        expected_type = param_mapping.get(effect_type)
        if expected_type and not isinstance(v, expected_type):
            if isinstance(v, dict):
                return expected_type(**v)
            else:
                raise ValueError(f"Parameters must be of type {expected_type.__name__} for effect type {effect_type}")
        
        return v


class StemEffectChain(BaseModel):
    """Effect chain configuration for a specific stem"""
    stem: StemType = Field(description="Type of stem this chain applies to")
    effects: List[Effect] = Field(default=[], description="List of effects in processing order")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Volume multiplier")
    pan: float = Field(default=0.0, ge=-1.0, le=1.0, description="Pan position (-1 = left, 1 = right)")
    mute: bool = Field(default=False, description="Whether stem is muted")
    solo: bool = Field(default=False, description="Whether stem is soloed")

    @field_validator('effects')
    @classmethod
    def validate_effect_order(cls, v):
        """Ensure effects have sequential order numbers"""
        for i, effect in enumerate(v):
            effect.order = i
        return v


class MasterChain(BaseModel):
    """Master effects chain applied to final mix"""
    effects: List[Effect] = Field(default=[], description="List of master effects in processing order")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Master volume")

    @field_validator('effects')
    @classmethod
    def validate_effect_order(cls, v):
        """Ensure effects have sequential order numbers"""
        for i, effect in enumerate(v):
            effect.order = i
        return v


class EffectsConfiguration(BaseModel):
    """Complete effects configuration for audio processing"""
    stem_chains: List[StemEffectChain] = Field(description="Effect chains for each stem")
    master_chain: MasterChain = Field(default_factory=MasterChain, description="Master effects chain")
    preset_name: Optional[str] = Field(default=None, description="Name of preset if saved")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('stem_chains')
    @classmethod
    def validate_unique_stems(cls, v):
        """Ensure each stem type appears only once"""
        stem_types = [chain.stem for chain in v]
        if len(stem_types) != len(set(stem_types)):
            raise ValueError("Each stem type can only appear once in the configuration")
        return v


class EffectsProcessingRequest(BaseModel):
    """Request model for effects processing"""
    storage_path: str = Field(description="Path to audio file in storage")
    effects_config: EffectsConfiguration = Field(description="Effects configuration to apply")
    callback_url: Optional[str] = Field(default=None, description="URL for processing completion callback")
    user_id: Optional[str] = Field(default=None, description="User ID for file organization")
    output_format: str = Field(default="wav", pattern="^(wav|mp3|flac)$", description="Output audio format")
    separate_stems: bool = Field(default=True, description="Whether to perform stem separation first")


class EffectsProcessingResponse(BaseModel):
    """Response model for effects processing"""
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Processing status")
    message: str = Field(description="Status message")
    storage_type: str = Field(description="Storage system being used")
    estimated_completion_time: Optional[int] = Field(default=None, description="Estimated completion time in seconds")


class EffectsProcessingResult(BaseModel):
    """Result model for completed effects processing"""
    task_id: str = Field(description="Task identifier")
    status: str = Field(description="Final processing status")
    output_path: Optional[str] = Field(default=None, description="Path to processed audio file")
    stems_processed: List[str] = Field(default=[], description="List of stems that were processed")
    effects_applied: int = Field(default=0, description="Total number of effects applied")
    processing_time_seconds: float = Field(description="Total processing time")
    quality_score: Optional[float] = Field(default=None, description="Processing quality score (0-1)")
    warnings: List[str] = Field(default=[], description="Processing warnings")
    error: Optional[str] = Field(default=None, description="Error message if processing failed")


class EffectsCatalogItem(BaseModel):
    """Catalog item describing an available effect"""
    type: EffectType = Field(description="Effect type identifier")
    name: str = Field(description="Human-readable name")
    category: str = Field(description="Effect category")
    description: str = Field(description="Effect description")
    parameters: Dict[str, Dict[str, Any]] = Field(description="Parameter specifications")
    tags: List[str] = Field(default=[], description="Search tags")
    complexity: str = Field(default="medium", description="Complexity level: simple, medium, advanced")

    @field_validator('complexity')
    @classmethod
    def validate_complexity(cls, v):
        valid_levels = ["simple", "medium", "advanced"]
        if v not in valid_levels:
            raise ValueError(f"Complexity must be one of {valid_levels}")
        return v


class EffectsPreset(BaseModel):
    """Preset configuration that can be saved and reused"""
    name: str = Field(description="Preset name")
    description: str = Field(description="Preset description")
    category: str = Field(description="Preset category")
    configuration: EffectsConfiguration = Field(description="Effects configuration")
    tags: List[str] = Field(default=[], description="Search tags")
    author: Optional[str] = Field(default=None, description="Preset author")
    is_public: bool = Field(default=False, description="Whether preset is publicly available")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")