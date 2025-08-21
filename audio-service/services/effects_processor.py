"""
Advanced Effects Processing Service

Provides comprehensive audio effects processing using pedalboard
with support for individual stem processing and advanced routing.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from models.effects_models import (
    Effect, EffectType, EffectsConfiguration, StemEffectChain, MasterChain,
    CompressorParams, LimiterParams, GateParams, ReverbParams, DelayParams,
    DistortionParams, OverdriveParams, ChorusParams, PhaserParams,
    HighShelfParams, LowShelfParams, LadderFilterParams, GainParams, PitchShiftParams
)

logger = logging.getLogger(__name__)

# Import pedalboard with fallback handling
try:
    from pedalboard import (
        Pedalboard, Compressor, Limiter, Gate, Reverb, Delay, Distortion,
        Chorus, Phaser, HighShelfFilter, LowShelfFilter, LadderFilter,
        Gain, PitchShift, Mix
    )
    PEDALBOARD_AVAILABLE = True
    logger.info("Pedalboard available - enhanced effects processing enabled")
except ImportError:
    PEDALBOARD_AVAILABLE = False
    logger.warning("Pedalboard not available - effects processing disabled")
    
    # Create dummy classes for type annotations when pedalboard is not available
    class Pedalboard:
        pass
    class Compressor:
        pass
    class Limiter:
        pass
    class Gate:
        pass
    class Reverb:
        pass
    class Delay:
        pass
    class Distortion:
        pass
    class Chorus:
        pass
    class Phaser:
        pass
    class HighShelfFilter:
        pass
    class LowShelfFilter:
        pass
    class LadderFilter:
        pass
    class Gain:
        pass
    class PitchShift:
        pass
    class Mix:
        pass


class EffectsProcessingError(Exception):
    """Exception raised during effects processing"""
    pass


class EffectsProcessor:
    """
    Advanced effects processing engine using pedalboard
    
    Handles individual stem processing, effects chain creation,
    and final mixing with master effects.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if not PEDALBOARD_AVAILABLE:
            self.logger.warning("Pedalboard not available - effects processing will be limited")
    
    def is_available(self) -> bool:
        """Check if effects processing is available"""
        return PEDALBOARD_AVAILABLE
    
    def create_pedalboard_from_effects(self, effects: List[Effect]) -> Optional[Pedalboard]:
        """
        Create a Pedalboard instance from a list of Effect configurations
        
        Args:
            effects: List of Effect objects in processing order
            
        Returns:
            Pedalboard instance or None if no effects or pedalboard unavailable
        """
        if not PEDALBOARD_AVAILABLE:
            self.logger.warning("Cannot create pedalboard - pedalboard library not available")
            return None
            
        if not effects:
            return None
        
        # Filter out bypassed effects and sort by order
        active_effects = [effect for effect in effects if not effect.bypass]
        active_effects.sort(key=lambda x: x.order)
        
        if not active_effects:
            return None
        
        pedalboard_effects = []
        
        for effect in active_effects:
            try:
                pb_effect = self._create_pedalboard_effect(effect)
                if pb_effect:
                    pedalboard_effects.append(pb_effect)
                    self.logger.debug(f"Added effect: {effect.name} ({effect.type})")
            except Exception as e:
                self.logger.error(f"Failed to create effect {effect.name}: {str(e)}")
                continue
        
        if pedalboard_effects:
            return Pedalboard(pedalboard_effects)
        else:
            return None
    
    def _create_pedalboard_effect(self, effect: Effect):
        """
        Convert an Effect model to a pedalboard effect instance
        
        Args:
            effect: Effect configuration
            
        Returns:
            Pedalboard effect instance
        """
        params = effect.parameters
        
        try:
            if effect.type == EffectType.COMPRESSOR:
                return Compressor(
                    threshold_db=params.threshold_db,
                    ratio=params.ratio,
                    attack_ms=params.attack_ms,
                    release_ms=params.release_ms
                )
            
            elif effect.type == EffectType.LIMITER:
                return Limiter(
                    threshold_db=params.threshold_db,
                    release_ms=params.release_ms
                )
            
            elif effect.type == EffectType.GATE:
                return Gate(
                    threshold_db=params.threshold_db,
                    ratio=params.ratio,
                    attack_ms=params.attack_ms,
                    release_ms=params.release_ms
                )
            
            elif effect.type == EffectType.REVERB:
                return Reverb(
                    room_size=params.room_size,
                    damping=params.damping,
                    wet_level=params.wet_level,
                    dry_level=params.dry_level,
                    width=params.width
                )
            
            elif effect.type == EffectType.DELAY:
                return Delay(
                    delay_seconds=params.delay_seconds,
                    feedback=params.feedback,
                    mix=params.mix
                )
            
            elif effect.type == EffectType.DISTORTION:
                return Distortion(
                    drive_db=params.drive_db
                )
            
            elif effect.type == EffectType.OVERDRIVE:
                # Overdrive is similar to distortion but with lower drive
                return Distortion(
                    drive_db=params.drive_db
                )
            
            elif effect.type == EffectType.CHORUS:
                return Chorus(
                    rate_hz=params.rate_hz,
                    depth=params.depth,
                    centre_delay_ms=params.centre_delay_ms,
                    feedback=params.feedback
                )
            
            elif effect.type == EffectType.PHASER:
                return Phaser(
                    rate_hz=params.rate_hz,
                    depth=params.depth,
                    centre_frequency_hz=params.centre_frequency_hz,
                    feedback=params.feedback
                )
            
            elif effect.type == EffectType.HIGH_SHELF:
                return HighShelfFilter(
                    cutoff_frequency_hz=params.cutoff_frequency_hz,
                    gain_db=params.gain_db,
                    q=params.q
                )
            
            elif effect.type == EffectType.LOW_SHELF:
                return LowShelfFilter(
                    cutoff_frequency_hz=params.cutoff_frequency_hz,
                    gain_db=params.gain_db,
                    q=params.q
                )
            
            elif effect.type == EffectType.LADDER_FILTER:
                # Map mode string to LadderFilter mode enum
                mode_mapping = {
                    "LPF12": LadderFilter.Mode.LPF12,
                    "LPF24": LadderFilter.Mode.LPF24,
                    "HPF12": LadderFilter.Mode.HPF12,
                    "HPF24": LadderFilter.Mode.HPF24,
                    "BPF12": LadderFilter.Mode.BPF12,
                    "BPF24": LadderFilter.Mode.BPF24,
                }
                mode = mode_mapping.get(params.mode, LadderFilter.Mode.LPF12)
                
                return LadderFilter(
                    mode=mode,
                    cutoff_hz=params.cutoff_hz,
                    resonance=params.resonance,
                    drive=params.drive
                )
            
            elif effect.type == EffectType.GAIN:
                return Gain(
                    gain_db=params.gain_db
                )
            
            elif effect.type == EffectType.PITCH_SHIFT:
                return PitchShift(
                    semitones=params.semitones
                )
            
            else:
                self.logger.warning(f"Unsupported effect type: {effect.type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating {effect.type} effect: {str(e)}")
            return None
    
    def process_stems_with_effects(
        self,
        stems: Dict[str, np.ndarray],
        effects_config: EffectsConfiguration,
        sample_rate: int
    ) -> np.ndarray:
        """
        Process separated stems with individual effects chains and mix the result
        
        Args:
            stems: Dictionary of stem name -> audio data
            effects_config: Complete effects configuration
            sample_rate: Audio sample rate
            
        Returns:
            Final mixed audio as numpy array
        """
        if not PEDALBOARD_AVAILABLE:
            raise EffectsProcessingError("Pedalboard not available - cannot process effects")
        
        self.logger.info(f"Processing {len(stems)} stems with effects")
        
        processed_stems = {}
        
        # Process each stem with its configured effects chain
        for stem_chain in effects_config.stem_chains:
            stem_name = stem_chain.stem.value
            
            if stem_name not in stems:
                self.logger.warning(f"Stem '{stem_name}' not found in provided stems")
                continue
            
            # Skip muted stems
            if stem_chain.mute:
                self.logger.debug(f"Stem '{stem_name}' is muted - skipping")
                processed_stems[stem_name] = np.zeros_like(stems[stem_name])
                continue
            
            # Process stem with effects
            processed_audio = self._process_single_stem(
                stems[stem_name], 
                stem_chain, 
                sample_rate
            )
            
            processed_stems[stem_name] = processed_audio
        
        # Mix processed stems
        mixed_audio = self._mix_stems(processed_stems, effects_config)
        
        # Apply master effects chain
        if effects_config.master_chain.effects:
            self.logger.debug("Applying master effects chain")
            master_board = self.create_pedalboard_from_effects(effects_config.master_chain.effects)
            if master_board:
                mixed_audio = master_board(mixed_audio, sample_rate)
        
        # Apply master volume
        mixed_audio *= effects_config.master_chain.volume
        
        # Ensure proper format and clipping protection
        mixed_audio = np.clip(mixed_audio, -1.0, 1.0).astype(np.float32)
        
        self.logger.info("Effects processing completed successfully")
        return mixed_audio
    
    def _process_single_stem(
        self,
        audio_data: np.ndarray,
        stem_chain: StemEffectChain,
        sample_rate: int
    ) -> np.ndarray:
        """
        Process a single stem with its effects chain
        
        Args:
            audio_data: Raw audio data for the stem
            stem_chain: Effects chain configuration for this stem
            sample_rate: Audio sample rate
            
        Returns:
            Processed audio data
        """
        stem_name = stem_chain.stem.value
        processed_audio = audio_data.copy()
        
        # Apply effects chain if present
        if stem_chain.effects:
            self.logger.debug(f"Applying {len(stem_chain.effects)} effects to '{stem_name}'")
            
            pedalboard = self.create_pedalboard_from_effects(stem_chain.effects)
            if pedalboard:
                try:
                    # Ensure audio is in correct format for pedalboard
                    if processed_audio.ndim > 1:
                        # Convert to mono for processing
                        processed_audio = np.mean(processed_audio, axis=0)
                    
                    # Apply effects
                    processed_audio = pedalboard(processed_audio, sample_rate)
                    
                    # Ensure output is 1D
                    if processed_audio.ndim > 1:
                        processed_audio = processed_audio.flatten()
                        
                except Exception as e:
                    self.logger.error(f"Error processing effects for '{stem_name}': {str(e)}")
                    # Fall back to original audio
                    processed_audio = audio_data.copy()
        
        # Apply volume adjustment
        processed_audio *= stem_chain.volume
        
        # Apply panning (for future stereo support)
        # TODO: Implement stereo panning when stereo processing is added
        
        return processed_audio
    
    def _mix_stems(
        self,
        processed_stems: Dict[str, np.ndarray],
        effects_config: EffectsConfiguration
    ) -> np.ndarray:
        """
        Mix processed stems into final audio
        
        Args:
            processed_stems: Dictionary of processed stem audio
            effects_config: Effects configuration (for solo handling)
            
        Returns:
            Mixed audio
        """
        if not processed_stems:
            self.logger.warning("No processed stems to mix")
            return np.array([])
        
        # Handle solo mode - if any stems are soloed, only mix those
        solo_stems = [chain for chain in effects_config.stem_chains if chain.solo]
        if solo_stems:
            self.logger.debug(f"Solo mode: only mixing {len(solo_stems)} stems")
            active_stem_names = {chain.stem.value for chain in solo_stems}
        else:
            # Mix all non-muted stems
            muted_stems = {chain.stem.value for chain in effects_config.stem_chains if chain.mute}
            active_stem_names = {name for name in processed_stems.keys() if name not in muted_stems}
        
        # Filter to active stems
        active_stems = {name: audio for name, audio in processed_stems.items() 
                       if name in active_stem_names and audio is not None}
        
        if not active_stems:
            self.logger.warning("No active stems to mix")
            return np.array([])
        
        # Determine the length for mixing (use shortest stem to avoid issues)
        min_length = min(len(audio) for audio in active_stems.values())
        
        # Sum all active stems
        mixed_audio = np.zeros(min_length, dtype=np.float32)
        
        for stem_name, stem_audio in active_stems.items():
            if len(stem_audio) > 0:
                # Trim to minimum length and add to mix
                trimmed_audio = stem_audio[:min_length]
                mixed_audio += trimmed_audio
                self.logger.debug(f"Mixed stem '{stem_name}' (length: {len(trimmed_audio)})")
        
        return mixed_audio
    
    def get_supported_effects(self) -> List[Dict[str, Any]]:
        """
        Get list of supported effects with their parameter specifications
        
        Returns:
            List of effect specifications
        """
        if not PEDALBOARD_AVAILABLE:
            return []
        
        return [
            {
                "type": EffectType.COMPRESSOR,
                "name": "Compressor",
                "category": "dynamics",
                "description": "Dynamic range compression",
                "complexity": "medium",
                "parameters": {
                    "threshold_db": {"min": -60.0, "max": 0.0, "default": -20.0, "unit": "dB"},
                    "ratio": {"min": 1.0, "max": 20.0, "default": 4.0, "unit": ":1"},
                    "attack_ms": {"min": 0.1, "max": 100.0, "default": 10.0, "unit": "ms"},
                    "release_ms": {"min": 1.0, "max": 1000.0, "default": 100.0, "unit": "ms"},
                    "knee_db": {"min": 0.0, "max": 10.0, "default": 2.0, "unit": "dB"},
                    "makeup_gain_db": {"min": -20.0, "max": 20.0, "default": 0.0, "unit": "dB"}
                }
            },
            {
                "type": EffectType.REVERB,
                "name": "Reverb",
                "category": "time_based",
                "description": "Reverberation effect",
                "complexity": "medium",
                "parameters": {
                    "room_size": {"min": 0.0, "max": 1.0, "default": 0.5, "unit": ""},
                    "damping": {"min": 0.0, "max": 1.0, "default": 0.5, "unit": ""},
                    "wet_level": {"min": 0.0, "max": 1.0, "default": 0.3, "unit": ""},
                    "dry_level": {"min": 0.0, "max": 1.0, "default": 1.0, "unit": ""},
                    "width": {"min": 0.0, "max": 1.0, "default": 1.0, "unit": ""}
                }
            },
            {
                "type": EffectType.DELAY,
                "name": "Delay",
                "category": "time_based",
                "description": "Echo delay effect",
                "complexity": "simple",
                "parameters": {
                    "delay_seconds": {"min": 0.001, "max": 2.0, "default": 0.25, "unit": "s"},
                    "feedback": {"min": 0.0, "max": 0.95, "default": 0.3, "unit": ""},
                    "mix": {"min": 0.0, "max": 1.0, "default": 0.3, "unit": ""}
                }
            },
            {
                "type": EffectType.DISTORTION,
                "name": "Distortion",
                "category": "distortion",
                "description": "Harmonic distortion",
                "complexity": "simple",
                "parameters": {
                    "drive_db": {"min": 0.0, "max": 40.0, "default": 10.0, "unit": "dB"}
                }
            },
            {
                "type": EffectType.CHORUS,
                "name": "Chorus",
                "category": "modulation",
                "description": "Chorus modulation effect",
                "complexity": "medium",
                "parameters": {
                    "rate_hz": {"min": 0.1, "max": 5.0, "default": 0.5, "unit": "Hz"},
                    "depth": {"min": 0.0, "max": 1.0, "default": 0.25, "unit": ""},
                    "centre_delay_ms": {"min": 1.0, "max": 20.0, "default": 7.0, "unit": "ms"},
                    "feedback": {"min": 0.0, "max": 0.8, "default": 0.0, "unit": ""}
                }
            },
            {
                "type": EffectType.HIGH_SHELF,
                "name": "High Shelf EQ",
                "category": "eq_filter",
                "description": "High frequency shelf filter",
                "complexity": "simple",
                "parameters": {
                    "cutoff_frequency_hz": {"min": 100.0, "max": 20000.0, "default": 3000.0, "unit": "Hz"},
                    "gain_db": {"min": -20.0, "max": 20.0, "default": 0.0, "unit": "dB"},
                    "q": {"min": 0.1, "max": 10.0, "default": 0.7, "unit": ""}
                }
            },
            {
                "type": EffectType.GAIN,
                "name": "Gain",
                "category": "utility",
                "description": "Volume adjustment",
                "complexity": "simple",
                "parameters": {
                    "gain_db": {"min": -60.0, "max": 60.0, "default": 0.0, "unit": "dB"}
                }
            }
        ]
    
    def validate_configuration(self, config: EffectsConfiguration) -> Tuple[bool, List[str]]:
        """
        Validate an effects configuration for potential issues
        
        Args:
            config: Effects configuration to validate
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check for excessive processing load
        total_effects = sum(len(chain.effects) for chain in config.stem_chains)
        total_effects += len(config.master_chain.effects)
        
        if total_effects > 20:
            warnings.append(f"High effect count ({total_effects}) may cause performance issues")
        
        # Check for problematic effect combinations
        for chain in config.stem_chains:
            distortion_count = sum(1 for effect in chain.effects 
                                 if effect.type in [EffectType.DISTORTION, EffectType.OVERDRIVE])
            if distortion_count > 2:
                warnings.append(f"Multiple distortion effects on {chain.stem.value} may cause excessive noise")
        
        # Check volume levels
        for chain in config.stem_chains:
            if chain.volume > 1.5:
                warnings.append(f"High volume ({chain.volume:.1f}) on {chain.stem.value} may cause clipping")
        
        if config.master_chain.volume > 1.2:
            warnings.append(f"High master volume ({config.master_chain.volume:.1f}) may cause clipping")
        
        # Check solo/mute conflicts
        solo_count = sum(1 for chain in config.stem_chains if chain.solo)
        mute_count = sum(1 for chain in config.stem_chains if chain.mute)
        
        if solo_count > 0 and mute_count > 0:
            warnings.append("Both solo and mute are active - solo takes precedence")
        
        is_valid = len(warnings) == 0 or all("may cause" in w for w in warnings)
        
        return is_valid, warnings


# Global processor instance
_processor_instance = None


def get_effects_processor() -> EffectsProcessor:
    """Get the global effects processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = EffectsProcessor()
    return _processor_instance