#!/usr/bin/env python3
"""
Test BPM detection accuracy against known ground truth values
"""

from pathlib import Path
import sys
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.audio_feature_extraction import create_feature_extractor


def load_ground_truth() -> Dict[str, float]:
    """Load ground truth BPM values from the reference file"""
    ground_truth_file = Path("tests/fixtures/bpm_test_audio/ground_truth.txt")

    if not ground_truth_file.exists():
        print(f"Ground truth file not found: {ground_truth_file}")
        return {}

    ground_truth = {}

    with open(ground_truth_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split(",")
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    bpm = float(parts[1].strip())
                    ground_truth[filename] = bpm

    return ground_truth


def calculate_accuracy_metrics(predicted: float, actual: float) -> Dict[str, float]:
    """Calculate accuracy metrics for BPM prediction"""
    if actual == 0:
        return {
            "error": 0.0,
            "percent_error": 0.0,
            "within_5_percent": False,
            "within_10_percent": False,
        }

    error = abs(predicted - actual)
    percent_error = (error / actual) * 100

    # Check for tempo doubling/halving (common errors)
    doubling_candidates = [
        predicted,
        predicted * 2,
        predicted / 2,
        predicted * 4,
        predicted / 4,
    ]
    best_candidate_error = min(
        abs(candidate - actual) for candidate in doubling_candidates if candidate > 0
    )
    best_candidate_percent = (
        (best_candidate_error / actual) * 100 if actual > 0 else 100
    )

    return {
        "error": error,
        "percent_error": percent_error,
        "best_candidate_error": best_candidate_error,
        "best_candidate_percent": best_candidate_percent,
        "within_5_percent": percent_error <= 5.0,
        "within_10_percent": percent_error <= 10.0,
        "within_5_percent_corrected": best_candidate_percent <= 5.0,
        "within_10_percent_corrected": best_candidate_percent <= 10.0,
    }


def test_single_file(
    extractor, audio_file: Path, expected_bpm: float
) -> Dict[str, any]:
    """Test BPM detection on a single file"""
    print(f"  Testing {audio_file.name} (expected: {expected_bpm} BPM)")

    try:
        # Test both standard and enhanced methods
        result_standard = extractor.extract_features(audio_file)
        standard_bpm = (
            result_standard.get("features", {}).get("tempo", {}).get("bpm", 0)
        )

        # Also test enhanced method directly
        y, sr, metadata = extractor.load_audio(audio_file)
        enhanced_result = extractor.extract_bpm_enhanced(y, sr)
        enhanced_bpm = enhanced_result.get("bpm", 0)

        # Calculate metrics
        standard_metrics = calculate_accuracy_metrics(standard_bpm, expected_bpm)
        enhanced_metrics = calculate_accuracy_metrics(enhanced_bpm, expected_bpm)

        result = {
            "file": audio_file.name,
            "expected_bpm": expected_bpm,
            "standard_bpm": standard_bpm,
            "enhanced_bpm": enhanced_bpm,
            "enhanced_confidence": enhanced_result.get("confidence", 0),
            "standard_accuracy": standard_metrics,
            "enhanced_accuracy": enhanced_metrics,
            "method_results": enhanced_result.get("method_results", {}),
            "alternative_tempos": enhanced_result.get("alternative_tempos", []),
        }

        print(
            f"    Standard: {standard_bpm:.1f} BPM (error: {standard_metrics['percent_error']:.1f}%)"
        )
        print(
            f"    Enhanced: {enhanced_bpm:.1f} BPM (error: {enhanced_metrics['percent_error']:.1f}%, confidence: {enhanced_result.get('confidence', 0):.2f})"
        )

        return result

    except Exception as e:
        print(f"    ❌ Error processing {audio_file.name}: {e}")
        return {"file": audio_file.name, "expected_bpm": expected_bpm, "error": str(e)}


def main():
    """Run BPM accuracy tests"""
    print("🎵 Testing Enhanced BPM Detection Accuracy")
    print("=" * 60)

    # Load ground truth
    ground_truth = load_ground_truth()
    if not ground_truth:
        print("❌ Could not load ground truth data")
        return

    print(f"Loaded ground truth for {len(ground_truth)} files")

    # Create extractor
    extractor = create_feature_extractor(extract_detailed=False, timeout=60)

    # Find test audio files
    test_audio_dir = Path("tests/fixtures/bpm_test_audio")
    if not test_audio_dir.exists():
        print(f"❌ Test audio directory not found: {test_audio_dir}")
        print("Run 'python tests/fixtures/create_test_audio_with_bpm.py' first")
        return

    # Test each file
    results = []

    for audio_file in sorted(test_audio_dir.glob("*.wav")):
        if audio_file.name in ground_truth:
            expected_bpm = ground_truth[audio_file.name]
            result = test_single_file(extractor, audio_file, expected_bpm)
            results.append(result)
        else:
            print(f"  ⚠️  Skipping {audio_file.name} (no ground truth)")

    # Analyze results
    print(f"\n📊 Analysis of {len(results)} test files")
    print("=" * 60)

    valid_results = [r for r in results if "error" not in r]

    if not valid_results:
        print("❌ No valid results to analyze")
        return

    # Standard method statistics
    standard_errors = [r["standard_accuracy"]["percent_error"] for r in valid_results]
    standard_within_10 = sum(
        1 for r in valid_results if r["standard_accuracy"]["within_10_percent"]
    )
    standard_within_5 = sum(
        1 for r in valid_results if r["standard_accuracy"]["within_5_percent"]
    )

    # Enhanced method statistics
    enhanced_errors = [r["enhanced_accuracy"]["percent_error"] for r in valid_results]
    enhanced_within_10 = sum(
        1 for r in valid_results if r["enhanced_accuracy"]["within_10_percent"]
    )
    enhanced_within_5 = sum(
        1 for r in valid_results if r["enhanced_accuracy"]["within_5_percent"]
    )

    # Enhanced method with tempo correction
    enhanced_corrected_within_10 = sum(
        1
        for r in valid_results
        if r["enhanced_accuracy"]["within_10_percent_corrected"]
    )
    enhanced_corrected_within_5 = sum(
        1 for r in valid_results if r["enhanced_accuracy"]["within_5_percent_corrected"]
    )

    print("\n🎯 Standard BPM Detection:")
    print(f"  Mean error: {np.mean(standard_errors):.1f}%")
    print(f"  Median error: {np.median(standard_errors):.1f}%")
    print(
        f"  Within 5%: {standard_within_5}/{len(valid_results)} ({100*standard_within_5/len(valid_results):.1f}%)"
    )
    print(
        f"  Within 10%: {standard_within_10}/{len(valid_results)} ({100*standard_within_10/len(valid_results):.1f}%)"
    )

    print("\n⚡ Enhanced BPM Detection:")
    print(f"  Mean error: {np.mean(enhanced_errors):.1f}%")
    print(f"  Median error: {np.median(enhanced_errors):.1f}%")
    print(
        f"  Within 5%: {enhanced_within_5}/{len(valid_results)} ({100*enhanced_within_5/len(valid_results):.1f}%)"
    )
    print(
        f"  Within 10%: {enhanced_within_10}/{len(valid_results)} ({100*enhanced_within_10/len(valid_results):.1f}%)"
    )

    print("\n🔧 Enhanced with Tempo Correction:")
    print(
        f"  Within 5%: {enhanced_corrected_within_5}/{len(valid_results)} ({100*enhanced_corrected_within_5/len(valid_results):.1f}%)"
    )
    print(
        f"  Within 10%: {enhanced_corrected_within_10}/{len(valid_results)} ({100*enhanced_corrected_within_10/len(valid_results):.1f}%)"
    )

    # Show improvement
    improvement_5 = enhanced_corrected_within_5 - standard_within_5
    improvement_10 = enhanced_corrected_within_10 - standard_within_10

    print(f"\n📈 Improvement:")
    print(f"  +{improvement_5} files within 5% accuracy")
    print(f"  +{improvement_10} files within 10% accuracy")

    # Show worst performing files
    print(f"\n❌ Files with highest error (Enhanced):")
    sorted_results = sorted(
        valid_results,
        key=lambda x: x["enhanced_accuracy"]["percent_error"],
        reverse=True,
    )
    for result in sorted_results[:5]:
        print(
            f"  {result['file']}: {result['enhanced_accuracy']['percent_error']:.1f}% error "
            f"(expected {result['expected_bpm']}, got {result['enhanced_bpm']:.1f})"
        )

    # Show best performing files
    print(f"\n✅ Most accurate results:")
    for result in sorted(
        valid_results, key=lambda x: x["enhanced_accuracy"]["percent_error"]
    )[:5]:
        print(
            f"  {result['file']}: {result['enhanced_accuracy']['percent_error']:.1f}% error "
            f"(expected {result['expected_bpm']}, got {result['enhanced_bpm']:.1f})"
        )

    # Method analysis
    print(f"\n🔍 Method Performance Analysis:")
    method_stats = {
        "standard": [],
        "percussive": [],
        "onset_based": [],
        "tempogram": [],
    }

    for result in valid_results:
        expected = result["expected_bpm"]
        methods = result["method_results"]

        for method_name, predicted in methods.items():
            if predicted > 0 and method_name in method_stats:
                error = abs(predicted - expected) / expected * 100
                method_stats[method_name].append(error)

    for method_name, errors in method_stats.items():
        if errors:
            print(
                f"  {method_name.capitalize()}: {np.mean(errors):.1f}% mean error ({len(errors)} valid results)"
            )
        else:
            print(f"  {method_name.capitalize()}: No valid results")

    # Save detailed results
    results_file = Path("bpm_accuracy_results.csv")
    try:
        df_data = []
        for result in valid_results:
            df_data.append(
                {
                    "file": result["file"],
                    "expected_bpm": result["expected_bpm"],
                    "standard_bpm": result["standard_bpm"],
                    "enhanced_bpm": result["enhanced_bpm"],
                    "enhanced_confidence": result["enhanced_confidence"],
                    "standard_error_percent": result["standard_accuracy"][
                        "percent_error"
                    ],
                    "enhanced_error_percent": result["enhanced_accuracy"][
                        "percent_error"
                    ],
                    "enhanced_corrected_error_percent": result["enhanced_accuracy"][
                        "best_candidate_percent"
                    ],
                }
            )

        df = pd.DataFrame(df_data)
        df.to_csv(results_file, index=False)
        print(f"\n💾 Detailed results saved to: {results_file}")

    except Exception as e:
        print(f"\n⚠️  Could not save results to CSV: {e}")

    print(f"\n🎉 BPM accuracy testing complete!")


if __name__ == "__main__":
    main()
