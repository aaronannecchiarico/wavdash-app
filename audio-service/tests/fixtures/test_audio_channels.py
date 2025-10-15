#!/usr/bin/env python3
"""
Quick test to verify audio channel conversion logic for Demucs
"""

import numpy as np


def test_channel_conversion():
    """Test the channel conversion logic we added"""
    print("🧪 Testing Audio Channel Conversion Logic")
    print("=" * 50)

    # Test case 1: Mono audio (1D array)
    print("\\n1. Testing mono audio (1D):")
    y_mono = np.random.randn(44100)  # 1 second of mono audio
    print(f"   Original shape: {y_mono.shape}")

    # Apply our conversion logic
    if len(y_mono.shape) == 1:
        # Convert mono to stereo by duplicating the channel
        y_stereo = np.stack([y_mono, y_mono])  # Shape: [2, samples]
        y_stereo = y_stereo[None, :]  # Add batch dimension: [1, 2, samples]

    print(f"   Converted shape: {y_stereo.shape}")
    print(
        f"   Expected: (1, 2, 44100) ✅"
        if y_stereo.shape == (1, 2, 44100)
        else "   ❌ Wrong shape"
    )

    # Test case 2: Already stereo (2D array)
    print("\\n2. Testing stereo audio (2D - channels first):")
    y_stereo_orig = np.random.randn(2, 44100)  # 2-channel audio
    print(f"   Original shape: {y_stereo_orig.shape}")

    # Apply our conversion logic
    y = y_stereo_orig
    if y.shape[0] > y.shape[1]:  # If samples x channels, transpose
        y = y.T
    y_stereo = y[None, :]  # Add batch dimension: [1, channels, samples]

    # Ensure exactly 2 channels for Demucs
    if y_stereo.shape[1] == 1:
        # Duplicate mono to stereo
        y_stereo = np.repeat(y_stereo, 2, axis=1)
    elif y_stereo.shape[1] > 2:
        # Take only first 2 channels if more than stereo
        y_stereo = y_stereo[:, :2, :]

    print(f"   Converted shape: {y_stereo.shape}")
    print(
        f"   Expected: (1, 2, 44100) ✅"
        if y_stereo.shape == (1, 2, 44100)
        else "   ❌ Wrong shape"
    )

    # Test case 3: Samples x channels format
    print("\\n3. Testing samples x channels format:")
    y_samples_channels = np.random.randn(44100, 2)  # samples x channels
    print(f"   Original shape: {y_samples_channels.shape}")

    # Apply our conversion logic
    y = y_samples_channels
    if y.shape[0] > y.shape[1]:  # If samples x channels, transpose
        y = y.T
    y_stereo = y[None, :]  # Add batch dimension: [1, channels, samples]

    print(f"   After transpose and batch: {y_stereo.shape}")
    print(
        f"   Expected: (1, 2, 44100) ✅"
        if y_stereo.shape == (1, 2, 44100)
        else "   ❌ Wrong shape"
    )

    # Test case 4: Multi-channel (> 2 channels)
    print("\\n4. Testing multi-channel audio (5 channels):")
    y_multi = np.random.randn(5, 44100)  # 5-channel audio
    print(f"   Original shape: {y_multi.shape}")

    # Apply our conversion logic
    y = y_multi
    if y.shape[0] > y.shape[1]:  # If samples x channels, transpose
        y = y.T
    y_stereo = y[None, :]  # Add batch dimension: [1, channels, samples]

    # Ensure exactly 2 channels for Demucs
    if y_stereo.shape[1] == 1:
        y_stereo = np.repeat(y_stereo, 2, axis=1)
    elif y_stereo.shape[1] > 2:
        # Take only first 2 channels if more than stereo
        y_stereo = y_stereo[:, :2, :]

    print(f"   Converted shape: {y_stereo.shape}")
    print(
        f"   Expected: (1, 2, 44100) ✅"
        if y_stereo.shape == (1, 2, 44100)
        else "   ❌ Wrong shape"
    )

    print("\\n🎉 All channel conversion tests completed!")
    print("\\n💡 This logic ensures Demucs always gets stereo input:")
    print("   • Mono audio → duplicated to stereo")
    print("   • Stereo audio → passed through")
    print("   • Multi-channel → first 2 channels used")
    print("   • Always batch dimension [1, 2, samples] for Demucs")


if __name__ == "__main__":
    test_channel_conversion()
