#!/usr/bin/env python3
"""
Generate test audio files with known BPM values for testing enhanced BPM detection
"""

import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def create_metronome_click(
    sample_rate: int = 22050, frequency: float = 1000, duration: float = 0.05
) -> np.ndarray:
    """Create a metronome click sound"""
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples)

    # Sharp attack with exponential decay
    envelope = np.exp(-t * 20)
    click = 0.5 * envelope * np.sin(2 * np.pi * frequency * t)

    return click


def create_drum_hit(sample_rate: int = 22050, duration: float = 0.1) -> np.ndarray:
    """Create a simple drum hit sound"""
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples)

    # Low frequency component (kick)
    kick = 0.7 * np.exp(-t * 30) * np.sin(2 * np.pi * 60 * t)

    # High frequency component (snare)
    snare_noise = 0.3 * np.exp(-t * 50) * np.random.normal(0, 1, samples)
    snare_tone = 0.2 * np.exp(-t * 25) * np.sin(2 * np.pi * 200 * t)

    drum_hit = kick + snare_noise + snare_tone

    # Normalize
    drum_hit = drum_hit / np.max(np.abs(drum_hit)) * 0.8

    return drum_hit


def create_musical_phrase(
    bpm: float, sample_rate: int = 22050, duration: float = 8.0
) -> np.ndarray:
    """Create a musical phrase with consistent BPM"""
    total_samples = int(sample_rate * duration)
    audio = np.zeros(total_samples)

    # Calculate beat timing
    beat_duration = 60.0 / bpm  # seconds per beat
    beats_in_duration = int(duration / beat_duration)

    # Create different instruments
    kick = create_drum_hit(sample_rate, 0.1)
    snare = create_drum_hit(sample_rate, 0.08) * 0.7
    hihat = create_metronome_click(sample_rate, 8000, 0.02) * 0.4

    for beat in range(beats_in_duration):
        beat_time = beat * beat_duration
        beat_sample = int(beat_time * sample_rate)

        # Ensure we don't exceed array bounds
        if beat_sample + len(kick) > len(audio):
            break

        # Add kick on beats 1 and 3
        if beat % 4 in [0, 2]:
            end_sample = min(beat_sample + len(kick), len(audio))
            audio[beat_sample:end_sample] += kick[: end_sample - beat_sample]

        # Add snare on beats 2 and 4
        if beat % 4 in [1, 3]:
            end_sample = min(beat_sample + len(snare), len(audio))
            audio[beat_sample:end_sample] += snare[: end_sample - beat_sample]

        # Add hi-hat on every beat
        end_sample = min(beat_sample + len(hihat), len(audio))
        audio[beat_sample:end_sample] += hihat[: end_sample - beat_sample]

        # Add off-beat hi-hats for faster tempos
        if bpm > 100:
            offbeat_sample = int((beat_time + beat_duration / 2) * sample_rate)
            if offbeat_sample + len(hihat) <= len(audio):
                end_sample = min(offbeat_sample + len(hihat), len(audio))
                audio[offbeat_sample:end_sample] += (
                    hihat[: end_sample - offbeat_sample] * 0.6
                )

    # Add some harmonic content (bass line)
    t = np.linspace(0, duration, total_samples)
    # Simple bass pattern following the chord progression
    bass_freq = 80  # Low E
    for beat in range(beats_in_duration // 4):  # Change chord every 4 beats
        start_time = beat * 4 * beat_duration
        end_time = (beat + 1) * 4 * beat_duration
        mask = (t >= start_time) & (t < end_time)

        # Vary bass note
        if beat % 4 == 0:
            freq = bass_freq  # E
        elif beat % 4 == 1:
            freq = bass_freq * 1.25  # A
        elif beat % 4 == 2:
            freq = bass_freq * 1.33  # G
        else:
            freq = bass_freq * 1.5  # B

        bass_line = (
            0.3
            * np.sin(2 * np.pi * freq * t)
            * np.exp(-((t - start_time) % beat_duration) * 8)
        )
        audio += bass_line * mask

    # Normalize
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * 0.9

    return audio


def create_complex_rhythm(
    bpm: float, sample_rate: int = 22050, duration: float = 8.0
) -> np.ndarray:
    """Create more complex rhythmic patterns that might confuse basic algorithms"""
    total_samples = int(sample_rate * duration)
    audio = np.zeros(total_samples)

    beat_duration = 60.0 / bpm
    sixteenth_duration = beat_duration / 4

    # Create sounds
    kick = create_drum_hit(sample_rate, 0.12)
    snare = create_drum_hit(sample_rate, 0.08) * 0.8
    hihat = create_metronome_click(sample_rate, 10000, 0.015) * 0.3

    # Complex pattern over 2 bars (8 beats)
    pattern_duration = 8 * beat_duration
    num_patterns = int(duration / pattern_duration)

    for pattern in range(num_patterns):
        pattern_start = pattern * pattern_duration

        # Kick pattern (syncopated)
        kick_beats = [0, 1.5, 3, 4.5, 6.5, 7.5]  # Beat positions
        for beat_pos in kick_beats:
            sample_pos = int((pattern_start + beat_pos * beat_duration) * sample_rate)
            if sample_pos + len(kick) <= len(audio):
                end_sample = min(sample_pos + len(kick), len(audio))
                audio[sample_pos:end_sample] += kick[: end_sample - sample_pos]

        # Snare on 2 and 4
        snare_beats = [2, 4, 6]
        for beat_pos in snare_beats:
            sample_pos = int((pattern_start + beat_pos * beat_duration) * sample_rate)
            if sample_pos + len(snare) <= len(audio):
                end_sample = min(sample_pos + len(snare), len(audio))
                audio[sample_pos:end_sample] += snare[: end_sample - sample_pos]

        # Hi-hat pattern (16th notes with accents)
        for sixteenth in range(32):  # 8 beats * 4 sixteenths
            if sixteenth % 4 == 0:  # On beat
                volume = 0.6
            elif sixteenth % 2 == 0:  # Off beat
                volume = 0.4
            else:  # Sixteenth notes
                volume = 0.2

            sample_pos = int(
                (pattern_start + sixteenth * sixteenth_duration) * sample_rate
            )
            if sample_pos + len(hihat) <= len(audio):
                end_sample = min(sample_pos + len(hihat), len(audio))
                audio[sample_pos:end_sample] += (
                    hihat[: end_sample - sample_pos] * volume
                )

    # Add melodic content to make it more musical
    t = np.linspace(0, duration, total_samples)
    melody_freq = 440  # A4
    melody = (
        0.2
        * np.sin(2 * np.pi * melody_freq * t)
        * (np.sin(2 * np.pi * t / beat_duration) ** 2)
    )
    audio += melody

    # Normalize
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * 0.9

    return audio


def main():
    """Generate test audio files with known BPM values"""
    output_dir = Path("tests/fixtures/bpm_test_audio")
    output_dir.mkdir(exist_ok=True)

    sample_rate = 22050
    duration = 10.0  # 10 seconds

    # Test BPM values covering different ranges
    test_bpms = [
        (60, "slow_ballad"),
        (80, "moderate_slow"),
        (100, "moderate"),
        (120, "standard_pop"),
        (140, "upbeat_dance"),
        (160, "fast_electronic"),
        (180, "very_fast"),
    ]

    print("Generating test audio files with known BPM values...")

    for bpm, description in test_bpms:
        print(f"Creating {description} at {bpm} BPM...")

        # Simple rhythmic pattern
        simple_audio = create_musical_phrase(bpm, sample_rate, duration)
        simple_path = output_dir / f"{description}_{bpm}bpm_simple.wav"
        sf.write(simple_path, simple_audio, sample_rate)
        print(f"  ✅ Created: {simple_path}")

        # Complex rhythmic pattern
        complex_audio = create_complex_rhythm(bpm, sample_rate, duration)
        complex_path = output_dir / f"{description}_{bpm}bpm_complex.wav"
        sf.write(complex_path, complex_audio, sample_rate)
        print(f"  ✅ Created: {complex_path}")

    # Create some edge cases
    print("\nCreating edge case test files...")

    # Very short audio (BPM detection challenge)
    short_audio = create_musical_phrase(120, sample_rate, 2.0)
    short_path = output_dir / "short_120bpm.wav"
    sf.write(short_path, short_audio, sample_rate)
    print(f"  ✅ Created short file: {short_path}")

    # Tempo doubling/halving test cases
    # Create 120 BPM that might be detected as 60 or 240
    doubling_audio = create_musical_phrase(120, sample_rate, duration)
    # Emphasize every other beat to potentially confuse algorithms
    beat_duration = 60.0 / 120
    t = np.linspace(0, duration, len(doubling_audio))
    emphasis = 1 + 0.3 * np.sin(2 * np.pi * t / (beat_duration * 2))
    doubling_audio *= emphasis
    doubling_path = output_dir / "tempo_doubling_120bpm.wav"
    sf.write(doubling_path, doubling_audio, sample_rate)
    print(f"  ✅ Created tempo doubling test: {doubling_path}")

    # Mixed meter (compound time)
    # 12/8 feel but 4/4 time signature (triplet feel)
    triplet_audio = create_musical_phrase(
        90, sample_rate, duration
    )  # 90 BPM with triplet subdivision
    triplet_path = output_dir / "triplet_feel_90bpm.wav"
    sf.write(triplet_path, triplet_audio, sample_rate)
    print(f"  ✅ Created triplet feel: {triplet_path}")

    print(
        f"\n🎉 Generated {len(list(output_dir.glob('*.wav')))} test audio files in {output_dir}"
    )
    print("\nFiles created:")
    for wav_file in sorted(output_dir.glob("*.wav")):
        print(f"  - {wav_file.name}")

    # Create a reference file with ground truth
    reference_file = output_dir / "ground_truth.txt"
    with open(reference_file, "w") as f:
        f.write("# Ground Truth BPM Values for Test Audio Files\n")
        f.write("# Format: filename,expected_bpm,description\n\n")

        for bpm, description in test_bpms:
            f.write(
                f"{description}_{bpm}bpm_simple.wav,{bpm},Simple rhythmic pattern\n"
            )
            f.write(
                f"{description}_{bpm}bpm_complex.wav,{bpm},Complex rhythmic pattern\n"
            )

        f.write(f"short_120bpm.wav,120,Short duration (2 seconds)\n")
        f.write(f"tempo_doubling_120bpm.wav,120,Potential tempo doubling confusion\n")
        f.write(f"triplet_feel_90bpm.wav,90,Compound time feel\n")

    print(f"  - {reference_file.name} (ground truth reference)")


if __name__ == "__main__":
    main()
