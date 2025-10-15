"""
Tests for improved tempo file naming conventions and callback data structure
"""

import pytest
from datetime import datetime
from pathlib import Path

# Import the functions we're testing
from tasks.tempo_processing import (
    generate_tempo_filename,
    build_tempo_file_path,
    calculate_processing_quality_score,
    get_processing_warnings,
)


class TestTempoFileNaming:
    """Test the improved tempo filename generation"""

    def test_nightcore_preset_filename(self):
        """Test filename generation for nightcore preset"""
        filename = generate_tempo_filename(
            original_filename="my-song.mp3",
            preset="nightcore",
            tempo_factor=1.4,
            pitch_shift_semitones=4.0,
        )

        expected = "my-song_tempo_nightcore-140-pitch+4.wav"
        assert filename == expected

    def test_sped_up_preset_filename(self):
        """Test filename generation for sped up preset"""
        filename = generate_tempo_filename(
            original_filename="test-track.wav",
            preset="sped_up",
            tempo_factor=1.25,
            pitch_shift_semitones=3.0,
        )

        expected = "test-track_tempo_sped-up-125-pitch+3.wav"
        assert filename == expected

    def test_slowed_reverb_preset_filename(self):
        """Test filename generation for slowed reverb preset"""
        filename = generate_tempo_filename(
            original_filename="chill-song.flac",
            preset="slowed_reverb",
            tempo_factor=0.75,
            pitch_shift_semitones=-2.0,
        )

        expected = "chill-song_tempo_slowed-reverb-75-pitch-2.wav"
        assert filename == expected

    def test_chopped_screwed_preset_filename(self):
        """Test filename generation for chopped & screwed preset"""
        filename = generate_tempo_filename(
            original_filename="hip-hop-track.m4a",
            preset="chopped_screwed",
            tempo_factor=0.6,
            pitch_shift_semitones=-3.0,
        )

        expected = "hip-hop-track_tempo_chopped-screwed-60-pitch-3.wav"
        assert filename == expected

    def test_time_stretched_preset_filename(self):
        """Test filename generation for time stretched preset"""
        filename = generate_tempo_filename(
            original_filename="vocal-track.ogg",
            preset="time_stretched",
            tempo_factor=0.8,
            pitch_shift_semitones=0.0,
        )

        expected = "vocal-track_tempo_time-stretched-80.wav"
        assert filename == expected

    def test_custom_preset_filename(self):
        """Test filename generation for custom preset"""
        filename = generate_tempo_filename(
            original_filename="custom-audio.wav",
            preset="custom",
            tempo_factor=1.15,
            pitch_shift_semitones=0.0,
        )

        expected = "custom-audio_tempo_custom-115.wav"
        assert filename == expected

    def test_custom_with_pitch_shift(self):
        """Test custom preset with pitch shift"""
        filename = generate_tempo_filename(
            original_filename="test.mp3",
            preset="custom",
            tempo_factor=1.0,
            pitch_shift_semitones=5.0,
        )

        expected = "test_tempo_custom-100-pitch+5.wav"
        assert filename == expected

    def test_negative_pitch_shift_formatting(self):
        """Test that negative pitch shifts are formatted correctly"""
        filename = generate_tempo_filename(
            original_filename="test.mp3",
            preset="custom",
            tempo_factor=1.0,
            pitch_shift_semitones=-7.0,
        )

        expected = "test_tempo_custom-100-pitch-7.wav"
        assert filename == expected

    def test_zero_pitch_shift_not_included(self):
        """Test that zero pitch shift is not included in filename"""
        filename = generate_tempo_filename(
            original_filename="test.mp3",
            preset="custom",
            tempo_factor=1.2,
            pitch_shift_semitones=0.0,
        )

        expected = "test_tempo_custom-120.wav"
        assert filename == expected

    def test_complex_filename_with_spaces(self):
        """Test filename with spaces and special characters"""
        filename = generate_tempo_filename(
            original_filename="My Song - Artist Name (2023).mp3",
            preset="nightcore",
            tempo_factor=1.3,
            pitch_shift_semitones=2.5,
        )

        expected = "My Song - Artist Name (2023)_tempo_nightcore-130-pitch+2.wav"
        assert filename == expected


class TestTempoFilePath:
    """Test the improved tempo file path construction"""

    def test_build_tempo_file_path_current_date(self):
        """Test file path building with current date"""
        test_date = datetime(2025, 8, 17, 14, 30, 0)

        path = build_tempo_file_path(
            user_id="123",
            upload_date=test_date,
            filename="song_tempo_nightcore-140.wav",
        )

        expected = "processed/123/2025/08/17/song_tempo_nightcore-140.wav"
        assert path == expected

    def test_build_tempo_file_path_different_date(self):
        """Test file path building with different date"""
        test_date = datetime(2024, 12, 1, 9, 15, 30)

        path = build_tempo_file_path(
            user_id="456", upload_date=test_date, filename="track_tempo_sped-up-125.wav"
        )

        expected = "processed/456/2024/12/01/track_tempo_sped-up-125.wav"
        assert path == expected

    def test_build_tempo_file_path_string_user_id(self):
        """Test file path building with string user ID"""
        test_date = datetime(2025, 1, 5, 12, 0, 0)

        path = build_tempo_file_path(
            user_id="user_789",
            upload_date=test_date,
            filename="audio_tempo_custom-80.wav",
        )

        expected = "processed/user_789/2025/01/05/audio_tempo_custom-80.wav"
        assert path == expected


class TestProcessingQualityScore:
    """Test the processing quality score calculation"""

    def test_perfect_quality_score(self):
        """Test perfect quality score with no warnings and fast processing"""
        score = calculate_processing_quality_score(
            processing_warnings=[],
            processing_time=30.0,
            audio_duration=180.0,  # 3 minutes
            cache_hit=False,
        )

        assert score == 1.0

    def test_quality_score_with_warnings(self):
        """Test quality score reduction with warnings"""
        warnings = [
            "Very fast tempo may cause audio artifacts",
            "Large pitch shifts may cause unnatural sound",
        ]

        score = calculate_processing_quality_score(
            processing_warnings=warnings,
            processing_time=30.0,
            audio_duration=180.0,
            cache_hit=False,
        )

        # Should be reduced by 0.2 (2 warnings * 0.1 each)
        assert score == 0.8

    def test_quality_score_with_slow_processing(self):
        """Test quality score reduction with slow processing"""
        score = calculate_processing_quality_score(
            processing_warnings=[],
            processing_time=600.0,  # 10 minutes
            audio_duration=180.0,  # 3 minutes (ratio = 3.33)
            cache_hit=False,
        )

        # Should be reduced by 0.133 (3.33 - 2.0) * 0.1 = 0.133, capped at 0.2
        expected_penalty = min((600.0 / 180.0 - 2.0) * 0.1, 0.2)
        expected_score = 1.0 - expected_penalty
        assert abs(score - expected_score) < 0.01

    def test_quality_score_cache_hit_no_time_penalty(self):
        """Test that cache hits don't get time penalties"""
        score = calculate_processing_quality_score(
            processing_warnings=[],
            processing_time=600.0,  # Very slow
            audio_duration=180.0,
            cache_hit=True,  # But it was cached
        )

        # Should be perfect since it was cached
        assert score == 1.0

    def test_quality_score_max_warnings_penalty(self):
        """Test maximum warnings penalty"""
        warnings = ["warning"] * 10  # 10 warnings

        score = calculate_processing_quality_score(
            processing_warnings=warnings,
            processing_time=30.0,
            audio_duration=180.0,
            cache_hit=False,
        )

        # Should be reduced by max 0.3 (capped at 30%)
        assert score == 0.7

    def test_quality_score_minimum_bound(self):
        """Test that quality score doesn't go below 0"""
        warnings = ["warning"] * 20  # Many warnings

        score = calculate_processing_quality_score(
            processing_warnings=warnings,
            processing_time=3600.0,  # Very slow
            audio_duration=60.0,
            cache_hit=False,
        )

        # Should not go below 0
        assert score >= 0.0


class TestProcessingWarnings:
    """Test the processing warnings generation"""

    def test_no_warnings_normal_params(self):
        """Test no warnings for normal parameters"""
        warnings = get_processing_warnings(
            tempo_factor=1.2, pitch_shift_semitones=2.0, audio_duration=180.0
        )

        assert warnings == []

    def test_slow_tempo_warning(self):
        """Test warning for very slow tempo"""
        warnings = get_processing_warnings(
            tempo_factor=0.3, pitch_shift_semitones=0.0, audio_duration=180.0
        )

        assert len(warnings) == 1
        assert "Very slow tempo may cause audio artifacts" in warnings

    def test_fast_tempo_warning(self):
        """Test warning for very fast tempo"""
        warnings = get_processing_warnings(
            tempo_factor=2.5, pitch_shift_semitones=0.0, audio_duration=180.0
        )

        assert len(warnings) == 1
        assert "Very fast tempo may cause audio artifacts" in warnings

    def test_large_pitch_shift_warning(self):
        """Test warning for large pitch shifts"""
        warnings = get_processing_warnings(
            tempo_factor=1.0, pitch_shift_semitones=10.0, audio_duration=180.0
        )

        assert len(warnings) == 1
        assert "Large pitch shifts may cause unnatural sound" in warnings

    def test_long_duration_warning(self):
        """Test warning for long audio files"""
        warnings = get_processing_warnings(
            tempo_factor=1.0,
            pitch_shift_semitones=0.0,
            audio_duration=700.0,  # > 10 minutes
        )

        assert len(warnings) == 1
        assert "Long audio files may take significant processing time" in warnings

    def test_short_duration_warning(self):
        """Test warning for very short audio files"""
        warnings = get_processing_warnings(
            tempo_factor=1.0,
            pitch_shift_semitones=0.0,
            audio_duration=5.0,  # < 10 seconds
        )

        assert len(warnings) == 1
        assert "Very short audio may not benefit from tempo processing" in warnings

    def test_aggressive_processing_warning(self):
        """Test warning for aggressive combined processing"""
        warnings = get_processing_warnings(
            tempo_factor=1.8,  # High tempo
            pitch_shift_semitones=6.0,  # Large pitch shift
            audio_duration=180.0,
        )

        assert len(warnings) == 1
        assert "Combining high tempo and pitch changes may degrade quality" in warnings

    def test_multiple_warnings(self):
        """Test multiple warnings for problematic parameters"""
        warnings = get_processing_warnings(
            tempo_factor=2.5,  # Very fast tempo
            pitch_shift_semitones=10.0,  # Large pitch shift
            audio_duration=5.0,  # Very short
        )

        assert len(warnings) == 4  # All warnings should be present
        expected_warnings = [
            "Very fast tempo may cause audio artifacts",
            "Large pitch shifts may cause unnatural sound",
            "Very short audio may not benefit from tempo processing",
            "Combining high tempo and pitch changes may degrade quality",
        ]

        for expected in expected_warnings:
            assert expected in warnings


class TestFilenameExamples:
    """Test real-world filename examples to ensure they match expected patterns"""

    def test_real_world_examples(self):
        """Test examples that match the specification"""
        examples = [
            {
                "input": {
                    "original_filename": "my-song.mp3",
                    "preset": "sped_up",
                    "tempo_factor": 1.25,
                    "pitch_shift_semitones": 0.0,
                },
                "expected": "my-song_tempo_sped-up-125.wav",
            },
            {
                "input": {
                    "original_filename": "my-song.mp3",
                    "preset": "slowed_reverb",
                    "tempo_factor": 0.75,
                    "pitch_shift_semitones": -2.0,
                },
                "expected": "my-song_tempo_slowed-reverb-75-pitch-2.wav",
            },
            {
                "input": {
                    "original_filename": "track.wav",
                    "preset": "nightcore",
                    "tempo_factor": 1.4,
                    "pitch_shift_semitones": 4.0,
                },
                "expected": "track_tempo_nightcore-140-pitch+4.wav",
            },
        ]

        for example in examples:
            actual = generate_tempo_filename(**example["input"])
            assert (
                actual == example["expected"]
            ), f"Expected {example['expected']}, got {actual}"
