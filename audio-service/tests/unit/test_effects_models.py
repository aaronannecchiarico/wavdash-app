"""
Unit tests for models.effects_models module
"""

import pytest
import sys
from pathlib import Path
from pydantic import ValidationError
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.effects_models import (
    EffectType, StemType, EffectParameters, CompressorParams, LimiterParams,
    GateParams, ReverbParams, DelayParams, DistortionParams, OverdriveParams,
    ChorusParams, PhaserParams, HighShelfParams, LowShelfParams, LadderFilterParams,
    GainParams, PitchShiftParams, Effect, StemEffectChain, MasterChain,
    EffectsConfiguration, EffectsProcessingRequest, EffectsProcessingResponse,
    EffectsProcessingResult, EffectsCatalogItem, EffectsPreset
)


class TestEffectType:
    """Test cases for EffectType enum"""
    
    def test_effect_type_values(self):
        """Test that all effect types have correct string values"""
        assert EffectType.COMPRESSOR == "compressor"
        assert EffectType.REVERB == "reverb"
        assert EffectType.DELAY == "delay"
        assert EffectType.DISTORTION == "distortion"
        assert EffectType.GAIN == "gain"
    
    def test_effect_type_membership(self):
        """Test effect type membership"""
        assert "compressor" in EffectType
        assert "invalid_effect" not in EffectType


class TestStemType:
    """Test cases for StemType enum"""
    
    def test_stem_type_values(self):
        """Test that all stem types have correct string values"""
        assert StemType.VOCALS == "vocals"
        assert StemType.DRUMS == "drums"
        assert StemType.BASS == "bass"
        assert StemType.OTHER == "other"
        assert StemType.FULL_MIX == "full_mix"


class TestEffectParameters:
    """Test cases for effect parameter classes"""
    
    def test_effect_parameters_base(self):
        """Test base EffectParameters class"""
        params = EffectParameters()
        assert params.enabled == True
        assert params.mix == 1.0
        
        params = EffectParameters(enabled=False, mix=0.5)
        assert params.enabled == False
        assert params.mix == 0.5
    
    def test_effect_parameters_mix_validation(self):
        """Test mix parameter validation"""
        # Valid mix values
        EffectParameters(mix=0.0)
        EffectParameters(mix=0.5)
        EffectParameters(mix=1.0)
        
        # Invalid mix values
        with pytest.raises(ValidationError):
            EffectParameters(mix=-0.1)
        
        with pytest.raises(ValidationError):
            EffectParameters(mix=1.1)
    
    def test_compressor_params(self):
        """Test CompressorParams validation and defaults"""
        params = CompressorParams()
        assert params.threshold_db == -20.0
        assert params.ratio == 4.0
        assert params.attack_ms == 10.0
        assert params.release_ms == 100.0
        assert params.knee_db == 2.0
        assert params.makeup_gain_db == 0.0
        
        # Test custom values
        params = CompressorParams(
            threshold_db=-30.0,
            ratio=8.0,
            attack_ms=5.0,
            release_ms=200.0
        )
        assert params.threshold_db == -30.0
        assert params.ratio == 8.0
    
    def test_compressor_params_validation(self):
        """Test CompressorParams range validation"""
        # Valid ranges
        CompressorParams(threshold_db=-60.0)  # Min
        CompressorParams(threshold_db=0.0)    # Max
        CompressorParams(ratio=1.0)           # Min
        CompressorParams(ratio=20.0)          # Max
        
        # Invalid ranges
        with pytest.raises(ValidationError):
            CompressorParams(threshold_db=-61.0)  # Below min
        
        with pytest.raises(ValidationError):
            CompressorParams(threshold_db=1.0)    # Above max
        
        with pytest.raises(ValidationError):
            CompressorParams(ratio=0.9)           # Below min
        
        with pytest.raises(ValidationError):
            CompressorParams(ratio=21.0)          # Above max
    
    def test_reverb_params(self):
        """Test ReverbParams validation and defaults"""
        params = ReverbParams()
        assert params.room_size == 0.5
        assert params.damping == 0.5
        assert params.wet_level == 0.3
        assert params.dry_level == 1.0
        assert params.width == 1.0
        
        # Test range validation
        with pytest.raises(ValidationError):
            ReverbParams(room_size=-0.1)
        
        with pytest.raises(ValidationError):
            ReverbParams(room_size=1.1)
    
    def test_delay_params(self):
        """Test DelayParams validation and defaults"""
        params = DelayParams()
        assert params.delay_seconds == 0.25
        assert params.feedback == 0.3
        assert params.mix == 0.3
        
        # Test range validation
        with pytest.raises(ValidationError):
            DelayParams(delay_seconds=0.0005)  # Below min
        
        with pytest.raises(ValidationError):
            DelayParams(delay_seconds=2.1)     # Above max
        
        with pytest.raises(ValidationError):
            DelayParams(feedback=0.96)         # Above max
    
    def test_ladder_filter_params(self):
        """Test LadderFilterParams validation"""
        params = LadderFilterParams()
        assert params.cutoff_hz == 1000.0
        assert params.resonance == 0.0
        assert params.drive == 1.0
        assert params.mode == "LPF12"
        
        # Test valid modes
        LadderFilterParams(mode="LPF24")
        LadderFilterParams(mode="HPF12")
        LadderFilterParams(mode="BPF24")
        
        # Test invalid mode
        with pytest.raises(ValidationError):
            LadderFilterParams(mode="INVALID")
    
    def test_gain_params(self):
        """Test GainParams validation"""
        params = GainParams()
        assert params.gain_db == 0.0
        
        # Test range validation
        GainParams(gain_db=-60.0)  # Min
        GainParams(gain_db=60.0)   # Max
        
        with pytest.raises(ValidationError):
            GainParams(gain_db=-61.0)  # Below min
        
        with pytest.raises(ValidationError):
            GainParams(gain_db=61.0)   # Above max
    
    def test_pitch_shift_params(self):
        """Test PitchShiftParams validation"""
        params = PitchShiftParams()
        assert params.semitones == 0.0
        
        # Test range validation
        PitchShiftParams(semitones=-24.0)  # Min
        PitchShiftParams(semitones=24.0)   # Max
        
        with pytest.raises(ValidationError):
            PitchShiftParams(semitones=-25.0)  # Below min
        
        with pytest.raises(ValidationError):
            PitchShiftParams(semitones=25.0)   # Above max


class TestEffect:
    """Test cases for Effect model"""
    
    def test_effect_creation(self):
        """Test creating Effect with valid parameters"""
        effect = Effect(
            type=EffectType.COMPRESSOR,
            name="Vocal Compressor",
            parameters=CompressorParams(threshold_db=-25.0, ratio=6.0),
            order=1
        )
        
        assert effect.type == EffectType.COMPRESSOR
        assert effect.name == "Vocal Compressor"
        assert isinstance(effect.parameters, CompressorParams)
        assert effect.parameters.threshold_db == -25.0
        assert effect.parameters.ratio == 6.0
        assert effect.bypass == False
        assert effect.order == 1
        assert isinstance(effect.id, str)
    
    def test_effect_parameter_validation(self):
        """Test effect parameter type validation"""
        # Valid: Compressor with CompressorParams
        effect = Effect(
            type=EffectType.COMPRESSOR,
            name="Compressor",
            parameters=CompressorParams(),
            order=0
        )
        assert isinstance(effect.parameters, CompressorParams)
        
        # Valid: Reverb with ReverbParams
        effect = Effect(
            type=EffectType.REVERB,
            name="Reverb",
            parameters=ReverbParams(),
            order=0
        )
        assert isinstance(effect.parameters, ReverbParams)
    
    def test_effect_parameter_dict_conversion(self):
        """Test effect parameter validation with dict input"""
        # Should convert dict to proper parameter type
        effect = Effect(
            type=EffectType.COMPRESSOR,
            name="Compressor",
            parameters={"threshold_db": -30.0, "ratio": 8.0},
            order=0
        )
        
        assert isinstance(effect.parameters, CompressorParams)
        assert effect.parameters.threshold_db == -30.0
        assert effect.parameters.ratio == 8.0
    
    def test_effect_unique_id(self):
        """Test that effects get unique IDs"""
        effect1 = Effect(
            type=EffectType.GAIN,
            name="Gain",
            parameters=GainParams(),
            order=0
        )
        
        effect2 = Effect(
            type=EffectType.GAIN,
            name="Gain",
            parameters=GainParams(),
            order=0
        )
        
        assert effect1.id != effect2.id


class TestStemEffectChain:
    """Test cases for StemEffectChain model"""
    
    def test_stem_effect_chain_creation(self):
        """Test creating StemEffectChain"""
        effects = [
            Effect(
                type=EffectType.COMPRESSOR,
                name="Compressor",
                parameters=CompressorParams(),
                order=0
            ),
            Effect(
                type=EffectType.REVERB,
                name="Reverb",
                parameters=ReverbParams(),
                order=1
            )
        ]
        
        chain = StemEffectChain(
            stem=StemType.VOCALS,
            effects=effects,
            volume=1.2,
            pan=0.1,
            mute=False,
            solo=True
        )
        
        assert chain.stem == StemType.VOCALS
        assert len(chain.effects) == 2
        assert chain.volume == 1.2
        assert chain.pan == 0.1
        assert chain.mute == False
        assert chain.solo == True
    
    def test_stem_effect_chain_defaults(self):
        """Test StemEffectChain default values"""
        chain = StemEffectChain(stem=StemType.DRUMS)
        
        assert chain.stem == StemType.DRUMS
        assert chain.effects == []
        assert chain.volume == 1.0
        assert chain.pan == 0.0
        assert chain.mute == False
        assert chain.solo == False
    
    def test_stem_effect_chain_validation(self):
        """Test StemEffectChain parameter validation"""
        # Valid volume range
        StemEffectChain(stem=StemType.BASS, volume=0.0)
        StemEffectChain(stem=StemType.BASS, volume=2.0)
        
        # Invalid volume range
        with pytest.raises(ValidationError):
            StemEffectChain(stem=StemType.BASS, volume=-0.1)
        
        with pytest.raises(ValidationError):
            StemEffectChain(stem=StemType.BASS, volume=2.1)
        
        # Valid pan range
        StemEffectChain(stem=StemType.BASS, pan=-1.0)
        StemEffectChain(stem=StemType.BASS, pan=1.0)
        
        # Invalid pan range
        with pytest.raises(ValidationError):
            StemEffectChain(stem=StemType.BASS, pan=-1.1)
        
        with pytest.raises(ValidationError):
            StemEffectChain(stem=StemType.BASS, pan=1.1)
    
    def test_effect_order_validation(self):
        """Test that effects get sequential order numbers"""
        effects = [
            Effect(
                type=EffectType.COMPRESSOR,
                name="Compressor",
                parameters=CompressorParams(),
                order=5  # This should be overridden
            ),
            Effect(
                type=EffectType.REVERB,
                name="Reverb",
                parameters=ReverbParams(),
                order=10  # This should be overridden
            )
        ]
        
        chain = StemEffectChain(
            stem=StemType.VOCALS,
            effects=effects
        )
        
        # Effects should have sequential order numbers
        assert chain.effects[0].order == 0
        assert chain.effects[1].order == 1


class TestMasterChain:
    """Test cases for MasterChain model"""
    
    def test_master_chain_creation(self):
        """Test creating MasterChain"""
        effects = [
            Effect(
                type=EffectType.LIMITER,
                name="Master Limiter",
                parameters=LimiterParams(),
                order=0
            )
        ]
        
        chain = MasterChain(effects=effects, volume=0.9)
        
        assert len(chain.effects) == 1
        assert chain.volume == 0.9
    
    def test_master_chain_defaults(self):
        """Test MasterChain default values"""
        chain = MasterChain()
        
        assert chain.effects == []
        assert chain.volume == 1.0
    
    def test_master_chain_validation(self):
        """Test MasterChain parameter validation"""
        # Valid volume range
        MasterChain(volume=0.0)
        MasterChain(volume=2.0)
        
        # Invalid volume range
        with pytest.raises(ValidationError):
            MasterChain(volume=-0.1)
        
        with pytest.raises(ValidationError):
            MasterChain(volume=2.1)


class TestEffectsConfiguration:
    """Test cases for EffectsConfiguration model"""
    
    def test_effects_configuration_creation(self):
        """Test creating complete EffectsConfiguration"""
        stem_chains = [
            StemEffectChain(
                stem=StemType.VOCALS,
                effects=[
                    Effect(
                        type=EffectType.COMPRESSOR,
                        name="Vocal Compressor",
                        parameters=CompressorParams(),
                        order=0
                    )
                ]
            ),
            StemEffectChain(
                stem=StemType.DRUMS,
                effects=[
                    Effect(
                        type=EffectType.GATE,
                        name="Drum Gate",
                        parameters=GateParams(),
                        order=0
                    )
                ]
            )
        ]
        
        master_chain = MasterChain(
            effects=[
                Effect(
                    type=EffectType.LIMITER,
                    name="Master Limiter",
                    parameters=LimiterParams(),
                    order=0
                )
            ]
        )
        
        config = EffectsConfiguration(
            stem_chains=stem_chains,
            master_chain=master_chain,
            preset_name="My Preset",
            metadata={"genre": "pop", "version": "1.0"}
        )
        
        assert len(config.stem_chains) == 2
        assert config.stem_chains[0].stem == StemType.VOCALS
        assert config.stem_chains[1].stem == StemType.DRUMS
        assert len(config.master_chain.effects) == 1
        assert config.preset_name == "My Preset"
        assert config.metadata["genre"] == "pop"
    
    def test_effects_configuration_defaults(self):
        """Test EffectsConfiguration default values"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS)
            ]
        )
        
        assert len(config.stem_chains) == 1
        assert isinstance(config.master_chain, MasterChain)
        assert config.preset_name is None
        assert config.metadata == {}
    
    def test_unique_stems_validation(self):
        """Test that stem types can only appear once"""
        stem_chains = [
            StemEffectChain(stem=StemType.VOCALS),
            StemEffectChain(stem=StemType.VOCALS)  # Duplicate
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            EffectsConfiguration(stem_chains=stem_chains)
        
        assert "Each stem type can only appear once" in str(exc_info.value)


class TestEffectsProcessingRequest:
    """Test cases for EffectsProcessingRequest model"""
    
    def test_processing_request_creation(self):
        """Test creating EffectsProcessingRequest"""
        config = EffectsConfiguration(
            stem_chains=[StemEffectChain(stem=StemType.VOCALS)]
        )
        
        request = EffectsProcessingRequest(
            storage_path="/path/to/audio.wav",
            effects_config=config,
            callback_url="http://example.com/callback",
            user_id="user123",
            output_format="mp3",
            separate_stems=False
        )
        
        assert request.storage_path == "/path/to/audio.wav"
        assert isinstance(request.effects_config, EffectsConfiguration)
        assert request.callback_url == "http://example.com/callback"
        assert request.user_id == "user123"
        assert request.output_format == "mp3"
        assert request.separate_stems == False
    
    def test_processing_request_defaults(self):
        """Test EffectsProcessingRequest default values"""
        config = EffectsConfiguration(
            stem_chains=[StemEffectChain(stem=StemType.VOCALS)]
        )
        
        request = EffectsProcessingRequest(
            storage_path="/path/to/audio.wav",
            effects_config=config
        )
        
        assert request.callback_url is None
        assert request.user_id is None
        assert request.output_format == "wav"
        assert request.separate_stems == True
    
    def test_processing_request_output_format_validation(self):
        """Test output format validation"""
        config = EffectsConfiguration(
            stem_chains=[StemEffectChain(stem=StemType.VOCALS)]
        )
        
        # Valid formats
        EffectsProcessingRequest(
            storage_path="/path/to/audio.wav",
            effects_config=config,
            output_format="wav"
        )
        
        EffectsProcessingRequest(
            storage_path="/path/to/audio.wav",
            effects_config=config,
            output_format="mp3"
        )
        
        EffectsProcessingRequest(
            storage_path="/path/to/audio.wav",
            effects_config=config,
            output_format="flac"
        )
        
        # Invalid format
        with pytest.raises(ValidationError):
            EffectsProcessingRequest(
                storage_path="/path/to/audio.wav",
                effects_config=config,
                output_format="ogg"
            )


class TestEffectsProcessingResponse:
    """Test cases for EffectsProcessingResponse model"""
    
    def test_processing_response_creation(self):
        """Test creating EffectsProcessingResponse"""
        response = EffectsProcessingResponse(
            task_id="task-123",
            status="processing",
            message="Effects processing started",
            storage_type="local",
            estimated_completion_time=120
        )
        
        assert response.task_id == "task-123"
        assert response.status == "processing"
        assert response.message == "Effects processing started"
        assert response.storage_type == "local"
        assert response.estimated_completion_time == 120


class TestEffectsProcessingResult:
    """Test cases for EffectsProcessingResult model"""
    
    def test_processing_result_success(self):
        """Test creating successful EffectsProcessingResult"""
        result = EffectsProcessingResult(
            task_id="task-123",
            status="completed",
            output_path="/path/to/processed.wav",
            stems_processed=["vocals", "drums"],
            effects_applied=3,
            processing_time_seconds=45.5,
            quality_score=0.95,
            warnings=["High volume on drums stem"]
        )
        
        assert result.task_id == "task-123"
        assert result.status == "completed"
        assert result.output_path == "/path/to/processed.wav"
        assert result.stems_processed == ["vocals", "drums"]
        assert result.effects_applied == 3
        assert result.processing_time_seconds == 45.5
        assert result.quality_score == 0.95
        assert result.warnings == ["High volume on drums stem"]
        assert result.error is None
    
    def test_processing_result_failure(self):
        """Test creating failed EffectsProcessingResult"""
        result = EffectsProcessingResult(
            task_id="task-123",
            status="failed",
            processing_time_seconds=10.0,
            error="Audio file corrupted"
        )
        
        assert result.task_id == "task-123"
        assert result.status == "failed"
        assert result.output_path is None
        assert result.stems_processed == []
        assert result.effects_applied == 0
        assert result.error == "Audio file corrupted"


class TestEffectsCatalogItem:
    """Test cases for EffectsCatalogItem model"""
    
    def test_catalog_item_creation(self):
        """Test creating EffectsCatalogItem"""
        item = EffectsCatalogItem(
            type=EffectType.COMPRESSOR,
            name="Compressor",
            category="dynamics",
            description="Dynamic range compression",
            parameters={
                "threshold_db": {"min": -60, "max": 0, "default": -20, "unit": "dB"},
                "ratio": {"min": 1, "max": 20, "default": 4, "unit": ":1"}
            },
            tags=["dynamics", "compression"],
            complexity="medium"
        )
        
        assert item.type == EffectType.COMPRESSOR
        assert item.name == "Compressor"
        assert item.category == "dynamics"
        assert item.description == "Dynamic range compression"
        assert "threshold_db" in item.parameters
        assert item.tags == ["dynamics", "compression"]
        assert item.complexity == "medium"
    
    def test_catalog_item_complexity_validation(self):
        """Test complexity level validation"""
        # Valid complexity levels
        EffectsCatalogItem(
            type=EffectType.GAIN,
            name="Gain",
            category="utility",
            description="Volume control",
            parameters={},
            complexity="simple"
        )
        
        EffectsCatalogItem(
            type=EffectType.COMPRESSOR,
            name="Compressor",
            category="dynamics",
            description="Compression",
            parameters={},
            complexity="advanced"
        )
        
        # Invalid complexity level
        with pytest.raises(ValidationError):
            EffectsCatalogItem(
                type=EffectType.GAIN,
                name="Gain",
                category="utility",
                description="Volume control",
                parameters={},
                complexity="expert"
            )


class TestEffectsPreset:
    """Test cases for EffectsPreset model"""
    
    def test_preset_creation(self):
        """Test creating EffectsPreset"""
        config = EffectsConfiguration(
            stem_chains=[StemEffectChain(stem=StemType.VOCALS)]
        )
        
        preset = EffectsPreset(
            name="Vocal Enhancement",
            description="Professional vocal processing",
            category="vocals",
            configuration=config,
            tags=["vocals", "professional"],
            author="Audio Engineer",
            is_public=True,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        assert preset.name == "Vocal Enhancement"
        assert preset.description == "Professional vocal processing"
        assert preset.category == "vocals"
        assert isinstance(preset.configuration, EffectsConfiguration)
        assert preset.tags == ["vocals", "professional"]
        assert preset.author == "Audio Engineer"
        assert preset.is_public == True
        assert preset.created_at == "2024-01-01T00:00:00Z"
        assert preset.updated_at == "2024-01-01T00:00:00Z"


class TestModelSerialization:
    """Test cases for model serialization"""
    
    def test_effect_serialization(self):
        """Test Effect model serialization"""
        effect = Effect(
            type=EffectType.COMPRESSOR,
            name="Compressor",
            parameters=CompressorParams(threshold_db=-25.0),
            order=0
        )
        
        data = effect.model_dump()
        
        assert isinstance(data, dict)
        assert data["type"] == "compressor"
        assert data["name"] == "Compressor"
        assert data["parameters"]["threshold_db"] == -25.0
        assert data["order"] == 0
    
    def test_effects_configuration_serialization(self):
        """Test EffectsConfiguration model serialization"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(
                    stem=StemType.VOCALS,
                    effects=[
                        Effect(
                            type=EffectType.COMPRESSOR,
                            name="Compressor",
                            parameters=CompressorParams(),
                            order=0
                        )
                    ]
                )
            ]
        )
        
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert "stem_chains" in data
        assert "master_chain" in data
        assert data["stem_chains"][0]["stem"] == "vocals"
        assert len(data["stem_chains"][0]["effects"]) == 1
    
    def test_json_serialization(self):
        """Test JSON serialization"""
        effect = Effect(
            type=EffectType.GAIN,
            name="Gain",
            parameters=GainParams(gain_db=3.0),
            order=0
        )
        
        json_str = effect.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "gain" in json_str
        assert "3.0" in json_str


if __name__ == "__main__":
    pytest.main([__file__])