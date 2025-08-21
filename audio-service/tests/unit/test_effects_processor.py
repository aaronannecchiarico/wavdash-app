"""
Unit tests for services.effects_processor module
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.effects_processor import (
    EffectsProcessor, EffectsProcessingError, get_effects_processor
)
from models.effects_models import (
    EffectType, StemType, Effect, StemEffectChain, MasterChain,
    EffectsConfiguration, CompressorParams, ReverbParams, DelayParams,
    DistortionParams, GainParams, LimiterParams, GateParams, PitchShiftParams,
    HighShelfParams, LowShelfParams, LadderFilterParams, ChorusParams,
    PhaserParams, OverdriveParams
)


class TestEffectsProcessor:
    """Test cases for EffectsProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = EffectsProcessor()
        
        # Sample audio data for testing
        self.sample_rate = 44100
        self.audio_length = int(0.1 * self.sample_rate)  # 0.1 seconds
        self.sample_audio = np.random.uniform(-0.5, 0.5, self.audio_length).astype(np.float32)
        
        # Sample stems dictionary
        self.sample_stems = {
            "vocals": np.random.uniform(-0.5, 0.5, self.audio_length).astype(np.float32),
            "drums": np.random.uniform(-0.5, 0.5, self.audio_length).astype(np.float32),
            "bass": np.random.uniform(-0.5, 0.5, self.audio_length).astype(np.float32),
            "other": np.random.uniform(-0.5, 0.5, self.audio_length).astype(np.float32)
        }
    
    def test_processor_initialization(self):
        """Test EffectsProcessor initialization"""
        processor = EffectsProcessor()
        assert processor is not None
        assert hasattr(processor, 'logger')
    
    def test_is_available(self):
        """Test availability checking"""
        # This will depend on whether pedalboard is actually available
        availability = self.processor.is_available()
        assert isinstance(availability, bool)
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    @patch('services.effects_processor.Pedalboard')
    def test_create_pedalboard_from_effects_empty(self, mock_pedalboard):
        """Test creating pedalboard from empty effects list"""
        result = self.processor.create_pedalboard_from_effects([])
        assert result is None
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    @patch('services.effects_processor.Pedalboard')
    @patch('services.effects_processor.Compressor')
    def test_create_pedalboard_from_effects_single(self, mock_compressor, mock_pedalboard):
        """Test creating pedalboard from single effect"""
        mock_compressor_instance = Mock()
        mock_compressor.return_value = mock_compressor_instance
        mock_pedalboard_instance = Mock()
        mock_pedalboard.return_value = mock_pedalboard_instance
        
        effects = [
            Effect(
                type=EffectType.COMPRESSOR,
                name="Compressor",
                parameters=CompressorParams(threshold_db=-25.0, ratio=6.0),
                order=0
            )
        ]
        
        result = self.processor.create_pedalboard_from_effects(effects)
        
        # Verify compressor was created with correct parameters
        mock_compressor.assert_called_once_with(
            threshold_db=-25.0,
            ratio=6.0,
            attack_ms=10.0,
            release_ms=100.0
        )
        
        # Verify pedalboard was created with the compressor
        mock_pedalboard.assert_called_once_with([mock_compressor_instance])
        assert result == mock_pedalboard_instance
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    @patch('services.effects_processor.Pedalboard')
    def test_create_pedalboard_bypassed_effects(self, mock_pedalboard):
        """Test creating pedalboard with bypassed effects"""
        effects = [
            Effect(
                type=EffectType.COMPRESSOR,
                name="Compressor",
                parameters=CompressorParams(),
                bypass=True,  # This effect should be skipped
                order=0
            )
        ]
        
        result = self.processor.create_pedalboard_from_effects(effects)
        
        # Should return None since all effects are bypassed
        assert result is None
        mock_pedalboard.assert_not_called()
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_create_pedalboard_effect_order(self):
        """Test that effects are ordered correctly"""
        with patch('services.effects_processor.Pedalboard') as mock_pedalboard, \
             patch.object(self.processor, '_create_pedalboard_effect') as mock_create_effect:
            
            mock_effect1 = Mock()
            mock_effect2 = Mock()
            mock_create_effect.side_effect = [mock_effect1, mock_effect2]
            
            effects = [
                Effect(
                    type=EffectType.COMPRESSOR,
                    name="Compressor",
                    parameters=CompressorParams(),
                    order=1  # Second in order
                ),
                Effect(
                    type=EffectType.GAIN,
                    name="Gain",
                    parameters=GainParams(),
                    order=0  # First in order
                )
            ]
            
            self.processor.create_pedalboard_from_effects(effects)
            
            # Verify effects were created in correct order (0, then 1)
            assert mock_create_effect.call_count == 2
            call_args = [call[0][0] for call in mock_create_effect.call_args_list]
            assert call_args[0].order == 0  # Gain effect (order 0) first
            assert call_args[1].order == 1  # Compressor effect (order 1) second
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', False)
    def test_create_pedalboard_unavailable(self):
        """Test behavior when pedalboard is unavailable"""
        result = self.processor.create_pedalboard_from_effects([
            Effect(
                type=EffectType.GAIN,
                name="Gain",
                parameters=GainParams(),
                order=0
            )
        ])
        
        assert result is None
    
    def test_create_pedalboard_effect_compressor(self):
        """Test creating compressor effect"""
        with patch('services.effects_processor.Compressor') as mock_compressor:
            mock_compressor_instance = Mock()
            mock_compressor.return_value = mock_compressor_instance
            
            effect = Effect(
                type=EffectType.COMPRESSOR,
                name="Compressor",
                parameters=CompressorParams(
                    threshold_db=-30.0,
                    ratio=8.0,
                    attack_ms=5.0,
                    release_ms=200.0
                ),
                order=0
            )
            
            result = self.processor._create_pedalboard_effect(effect)
            
            mock_compressor.assert_called_once_with(
                threshold_db=-30.0,
                ratio=8.0,
                attack_ms=5.0,
                release_ms=200.0
            )
            assert result == mock_compressor_instance
    
    def test_create_pedalboard_effect_reverb(self):
        """Test creating reverb effect"""
        with patch('services.effects_processor.Reverb') as mock_reverb:
            mock_reverb_instance = Mock()
            mock_reverb.return_value = mock_reverb_instance
            
            effect = Effect(
                type=EffectType.REVERB,
                name="Reverb",
                parameters=ReverbParams(
                    room_size=0.8,
                    damping=0.3,
                    wet_level=0.4,
                    dry_level=0.9,
                    width=0.7
                ),
                order=0
            )
            
            result = self.processor._create_pedalboard_effect(effect)
            
            mock_reverb.assert_called_once_with(
                room_size=0.8,
                damping=0.3,
                wet_level=0.4,
                dry_level=0.9,
                width=0.7
            )
            assert result == mock_reverb_instance
    
    def test_create_pedalboard_effect_delay(self):
        """Test creating delay effect"""
        with patch('services.effects_processor.Delay') as mock_delay:
            mock_delay_instance = Mock()
            mock_delay.return_value = mock_delay_instance
            
            effect = Effect(
                type=EffectType.DELAY,
                name="Delay",
                parameters=DelayParams(
                    delay_seconds=0.5,
                    feedback=0.4,
                    mix=0.3
                ),
                order=0
            )
            
            result = self.processor._create_pedalboard_effect(effect)
            
            mock_delay.assert_called_once_with(
                delay_seconds=0.5,
                feedback=0.4,
                mix=0.3
            )
            assert result == mock_delay_instance
    
    def test_create_pedalboard_effect_ladder_filter(self):
        """Test creating ladder filter effect"""
        with patch('services.effects_processor.LadderFilter') as mock_filter:
            mock_filter_instance = Mock()
            mock_filter.return_value = mock_filter_instance
            
            # Mock the Mode enum
            mock_mode = Mock()
            mock_filter.Mode = Mock()
            mock_filter.Mode.LPF24 = mock_mode
            
            effect = Effect(
                type=EffectType.LADDER_FILTER,
                name="Filter",
                parameters=LadderFilterParams(
                    cutoff_hz=2000.0,
                    resonance=0.5,
                    drive=1.5,
                    mode="LPF24"
                ),
                order=0
            )
            
            result = self.processor._create_pedalboard_effect(effect)
            
            mock_filter.assert_called_once_with(
                mode=mock_mode,
                cutoff_hz=2000.0,
                resonance=0.5,
                drive=1.5
            )
            assert result == mock_filter_instance
    
    def test_create_pedalboard_effect_unsupported(self):
        """Test creating unsupported effect type"""
        # Create a mock effect with a type that doesn't exist in our processor
        effect = Mock()
        effect.type = "unsupported_effect"
        
        result = self.processor._create_pedalboard_effect(effect)
        assert result is None
    
    def test_create_pedalboard_effect_error_handling(self):
        """Test error handling in effect creation"""
        with patch('services.effects_processor.Compressor') as mock_compressor:
            mock_compressor.side_effect = Exception("Pedalboard error")
            
            effect = Effect(
                type=EffectType.COMPRESSOR,
                name="Compressor",
                parameters=CompressorParams(),
                order=0
            )
            
            result = self.processor._create_pedalboard_effect(effect)
            assert result is None
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', False)
    def test_process_stems_with_effects_unavailable(self):
        """Test processing when pedalboard is unavailable"""
        config = EffectsConfiguration(
            stem_chains=[StemEffectChain(stem=StemType.VOCALS)]
        )
        
        with pytest.raises(EffectsProcessingError, match="Pedalboard not available"):
            self.processor.process_stems_with_effects(
                self.sample_stems, config, self.sample_rate
            )
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_process_stems_with_effects_no_effects(self):
        """Test processing stems with no effects"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS),
                StemEffectChain(stem=StemType.DRUMS)
            ]
        )
        
        with patch.object(self.processor, '_process_single_stem') as mock_process_stem, \
             patch.object(self.processor, '_mix_stems') as mock_mix_stems:
            
            mock_process_stem.side_effect = lambda audio, chain, sr: audio * chain.volume
            mock_mix_stems.return_value = self.sample_audio
            
            result = self.processor.process_stems_with_effects(
                self.sample_stems, config, self.sample_rate
            )
            
            assert isinstance(result, np.ndarray)
            assert result.dtype == np.float32
            assert mock_process_stem.call_count == 2
            mock_mix_stems.assert_called_once()
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_process_stems_with_effects_muted_stem(self):
        """Test processing with muted stem"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS, mute=True),
                StemEffectChain(stem=StemType.DRUMS)
            ]
        )
        
        with patch.object(self.processor, '_mix_stems') as mock_mix_stems:
            mock_mix_stems.return_value = self.sample_audio
            
            result = self.processor.process_stems_with_effects(
                self.sample_stems, config, self.sample_rate
            )
            
            # Check that processed stems includes zeros for muted vocal
            call_args = mock_mix_stems.call_args[0][0]  # First argument (processed_stems)
            vocals_processed = call_args.get('vocals')
            
            if vocals_processed is not None:
                # Should be all zeros for muted stem
                assert np.allclose(vocals_processed, 0.0)
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_process_stems_with_effects_master_chain(self):
        """Test processing with master effects chain"""
        master_chain = MasterChain(
            effects=[
                Effect(
                    type=EffectType.LIMITER,
                    name="Limiter",
                    parameters=LimiterParams(),
                    order=0
                )
            ],
            volume=0.8
        )
        
        config = EffectsConfiguration(
            stem_chains=[StemEffectChain(stem=StemType.VOCALS)],
            master_chain=master_chain
        )
        
        with patch.object(self.processor, 'create_pedalboard_from_effects') as mock_create_board, \
             patch.object(self.processor, '_process_single_stem') as mock_process_stem, \
             patch.object(self.processor, '_mix_stems') as mock_mix_stems:
            
            mock_master_board = Mock()
            mock_master_board.return_value = self.sample_audio * 0.9
            mock_create_board.return_value = mock_master_board
            
            mock_process_stem.return_value = self.sample_audio
            mock_mix_stems.return_value = self.sample_audio
            
            result = self.processor.process_stems_with_effects(
                self.sample_stems, config, self.sample_rate
            )
            
            # Verify master chain was applied
            mock_create_board.assert_called_with(master_chain.effects)
            mock_master_board.assert_called_once_with(self.sample_audio, self.sample_rate)
            
            # Result should be clipped and converted to float32
            assert isinstance(result, np.ndarray)
            assert result.dtype == np.float32
            assert np.all(result >= -1.0) and np.all(result <= 1.0)
    
    def test_process_single_stem_no_effects(self):
        """Test processing single stem without effects"""
        chain = StemEffectChain(stem=StemType.VOCALS, volume=0.8)
        
        result = self.processor._process_single_stem(
            self.sample_audio, chain, self.sample_rate
        )
        
        expected = self.sample_audio * 0.8
        assert np.allclose(result, expected)
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_process_single_stem_with_effects(self):
        """Test processing single stem with effects"""
        effects = [
            Effect(
                type=EffectType.GAIN,
                name="Gain",
                parameters=GainParams(gain_db=3.0),
                order=0
            )
        ]
        
        chain = StemEffectChain(
            stem=StemType.VOCALS,
            effects=effects,
            volume=1.0
        )
        
        with patch.object(self.processor, 'create_pedalboard_from_effects') as mock_create_board:
            mock_pedalboard = Mock()
            mock_pedalboard.return_value = self.sample_audio * 1.5  # Simulated effect processing
            mock_create_board.return_value = mock_pedalboard
            
            result = self.processor._process_single_stem(
                self.sample_audio, chain, self.sample_rate
            )
            
            mock_create_board.assert_called_once_with(effects)
            mock_pedalboard.assert_called_once()
            
            # Should return the processed audio
            expected = (self.sample_audio * 1.5) * chain.volume
            assert np.allclose(result, expected)
    
    def test_process_single_stem_effect_error(self):
        """Test error handling in single stem processing"""
        effects = [
            Effect(
                type=EffectType.GAIN,
                name="Gain",
                parameters=GainParams(),
                order=0
            )
        ]
        
        chain = StemEffectChain(stem=StemType.VOCALS, effects=effects)
        
        with patch.object(self.processor, 'create_pedalboard_from_effects') as mock_create_board:
            mock_pedalboard = Mock()
            mock_pedalboard.side_effect = Exception("Processing error")
            mock_create_board.return_value = mock_pedalboard
            
            result = self.processor._process_single_stem(
                self.sample_audio, chain, self.sample_rate
            )
            
            # Should fall back to original audio
            expected = self.sample_audio * chain.volume
            assert np.allclose(result, expected)
    
    def test_mix_stems_empty(self):
        """Test mixing empty stems dictionary"""
        config = EffectsConfiguration(stem_chains=[])
        
        result = self.processor._mix_stems({}, config)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 0
    
    def test_mix_stems_normal(self):
        """Test mixing normal stems"""
        processed_stems = {
            "vocals": np.ones(100) * 0.5,
            "drums": np.ones(100) * 0.3
        }
        
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS),
                StemEffectChain(stem=StemType.DRUMS)
            ]
        )
        
        result = self.processor._mix_stems(processed_stems, config)
        
        expected = np.ones(100) * (0.5 + 0.3)  # Sum of both stems
        assert np.allclose(result, expected)
    
    def test_mix_stems_solo_mode(self):
        """Test mixing with solo mode"""
        processed_stems = {
            "vocals": np.ones(100) * 0.5,
            "drums": np.ones(100) * 0.3,
            "bass": np.ones(100) * 0.2
        }
        
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS, solo=True),  # Solo
                StemEffectChain(stem=StemType.DRUMS),
                StemEffectChain(stem=StemType.BASS)
            ]
        )
        
        result = self.processor._mix_stems(processed_stems, config)
        
        # Should only include vocals (solo'd stem)
        expected = np.ones(100) * 0.5
        assert np.allclose(result, expected)
    
    def test_mix_stems_muted(self):
        """Test mixing with muted stems"""
        processed_stems = {
            "vocals": np.ones(100) * 0.5,
            "drums": np.zeros(100),  # Muted stem (processed as zeros)
            "bass": np.ones(100) * 0.2
        }
        
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS),
                StemEffectChain(stem=StemType.DRUMS, mute=True),
                StemEffectChain(stem=StemType.BASS)
            ]
        )
        
        result = self.processor._mix_stems(processed_stems, config)
        
        # Should include vocals and bass, but not drums
        expected = np.ones(100) * (0.5 + 0.2)
        assert np.allclose(result, expected)
    
    def test_mix_stems_length_mismatch(self):
        """Test mixing stems with different lengths"""
        processed_stems = {
            "vocals": np.ones(100) * 0.5,
            "drums": np.ones(150) * 0.3  # Different length
        }
        
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS),
                StemEffectChain(stem=StemType.DRUMS)
            ]
        )
        
        result = self.processor._mix_stems(processed_stems, config)
        
        # Should use minimum length (100)
        assert len(result) == 100
        expected = np.ones(100) * (0.5 + 0.3)
        assert np.allclose(result, expected)
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_get_supported_effects(self):
        """Test getting supported effects catalog"""
        effects = self.processor.get_supported_effects()
        
        assert isinstance(effects, list)
        assert len(effects) > 0
        
        # Check structure of first effect
        effect = effects[0]
        assert "type" in effect
        assert "name" in effect
        assert "category" in effect
        assert "description" in effect
        assert "parameters" in effect
        assert "complexity" in effect
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', False)
    def test_get_supported_effects_unavailable(self):
        """Test getting supported effects when pedalboard unavailable"""
        effects = self.processor.get_supported_effects()
        assert effects == []
    
    def test_validate_configuration_simple(self):
        """Test configuration validation with simple config"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(
                    stem=StemType.VOCALS,
                    effects=[
                        Effect(
                            type=EffectType.GAIN,
                            name="Gain",
                            parameters=GainParams(gain_db=3.0),
                            order=0
                        )
                    ],
                    volume=1.0
                )
            ]
        )
        
        is_valid, warnings = self.processor.validate_configuration(config)
        
        assert is_valid == True
        assert len(warnings) == 0
    
    def test_validate_configuration_high_effect_count(self):
        """Test configuration validation with high effect count"""
        # Create many effects to trigger warning
        effects = []
        for i in range(15):
            effects.append(
                Effect(
                    type=EffectType.GAIN,
                    name=f"Gain {i}",
                    parameters=GainParams(),
                    order=i
                )
            )
        
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS, effects=effects),
                StemEffectChain(stem=StemType.DRUMS, effects=effects[:10])
            ]
        )
        
        is_valid, warnings = self.processor.validate_configuration(config)
        
        assert len(warnings) > 0
        assert any("High effect count" in warning for warning in warnings)
    
    def test_validate_configuration_high_volume(self):
        """Test configuration validation with high volume"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS, volume=1.8)  # High volume
            ],
            master_chain=MasterChain(volume=1.3)  # High master volume
        )
        
        is_valid, warnings = self.processor.validate_configuration(config)
        
        assert len(warnings) >= 2  # Both stem and master volume warnings
        assert any("High volume" in warning for warning in warnings)
        assert any("High master volume" in warning for warning in warnings)
    
    def test_validate_configuration_multiple_distortion(self):
        """Test configuration validation with multiple distortion effects"""
        effects = [
            Effect(
                type=EffectType.DISTORTION,
                name="Distortion 1",
                parameters=DistortionParams(),
                order=0
            ),
            Effect(
                type=EffectType.OVERDRIVE,
                name="Overdrive",
                parameters=OverdriveParams(),
                order=1
            ),
            Effect(
                type=EffectType.DISTORTION,
                name="Distortion 2",
                parameters=DistortionParams(),
                order=2
            )
        ]
        
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS, effects=effects)
            ]
        )
        
        is_valid, warnings = self.processor.validate_configuration(config)
        
        assert len(warnings) > 0
        assert any("Multiple distortion effects" in warning for warning in warnings)
    
    def test_validate_configuration_solo_mute_conflict(self):
        """Test configuration validation with solo/mute conflict"""
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(stem=StemType.VOCALS, solo=True),
                StemEffectChain(stem=StemType.DRUMS, mute=True)
            ]
        )
        
        is_valid, warnings = self.processor.validate_configuration(config)
        
        assert len(warnings) > 0
        assert any("Both solo and mute are active" in warning for warning in warnings)


class TestEffectsProcessorGlobal:
    """Test cases for global processor functions"""
    
    def test_get_effects_processor_singleton(self):
        """Test that get_effects_processor returns singleton instance"""
        processor1 = get_effects_processor()
        processor2 = get_effects_processor()
        
        assert processor1 is processor2
        assert isinstance(processor1, EffectsProcessor)


class TestEffectsProcessorIntegration:
    """Integration tests for effects processor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = EffectsProcessor()
        self.sample_rate = 44100
        self.audio_length = int(0.1 * self.sample_rate)
        
        # Create deterministic test audio
        self.test_stems = {
            "vocals": np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, self.audio_length)).astype(np.float32),
            "drums": np.sin(2 * np.pi * 220 * np.linspace(0, 0.1, self.audio_length)).astype(np.float32) * 0.5,
            "bass": np.sin(2 * np.pi * 110 * np.linspace(0, 0.1, self.audio_length)).astype(np.float32) * 0.3,
            "other": np.sin(2 * np.pi * 880 * np.linspace(0, 0.1, self.audio_length)).astype(np.float32) * 0.2
        }
    
    @patch('services.effects_processor.PEDALBOARD_AVAILABLE', True)
    def test_full_processing_pipeline_mock(self):
        """Test full processing pipeline with mocked pedalboard"""
        # Create a realistic effects configuration
        config = EffectsConfiguration(
            stem_chains=[
                StemEffectChain(
                    stem=StemType.VOCALS,
                    effects=[
                        Effect(
                            type=EffectType.COMPRESSOR,
                            name="Vocal Compressor",
                            parameters=CompressorParams(threshold_db=-25.0, ratio=4.0),
                            order=0
                        ),
                        Effect(
                            type=EffectType.REVERB,
                            name="Vocal Reverb",
                            parameters=ReverbParams(room_size=0.3, wet_level=0.2),
                            order=1
                        )
                    ],
                    volume=1.2
                ),
                StemEffectChain(
                    stem=StemType.DRUMS,
                    effects=[
                        Effect(
                            type=EffectType.GATE,
                            name="Drum Gate",
                            parameters=GateParams(threshold_db=-35.0),
                            order=0
                        )
                    ],
                    volume=0.9
                )
            ],
            master_chain=MasterChain(
                effects=[
                    Effect(
                        type=EffectType.LIMITER,
                        name="Master Limiter",
                        parameters=LimiterParams(threshold_db=-1.0),
                        order=0
                    )
                ],
                volume=0.95
            )
        )
        
        # Mock all pedalboard effects to return modified audio
        with patch.object(self.processor, '_create_pedalboard_effect') as mock_create_effect:
            
            def mock_effect_processing(audio, sample_rate):
                # Simulate effect processing by slightly modifying the audio
                return audio * 0.9
            
            mock_effect = Mock()
            mock_effect.side_effect = mock_effect_processing
            mock_create_effect.return_value = mock_effect
            
            with patch('services.effects_processor.Pedalboard') as mock_pedalboard:
                mock_pedalboard.return_value = mock_effect
                
                result = self.processor.process_stems_with_effects(
                    self.test_stems, config, self.sample_rate
                )
        
        # Verify result properties
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == self.audio_length
        assert np.all(result >= -1.0) and np.all(result <= 1.0)  # Clipped output
        
        # Verify some processing occurred (result different from simple mix)
        simple_mix = sum(self.test_stems.values())
        assert not np.allclose(result, simple_mix)


if __name__ == "__main__":
    pytest.main([__file__])