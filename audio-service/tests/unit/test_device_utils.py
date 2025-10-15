"""
Unit tests for utils.device_utils module
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.device_utils import (
    get_optimal_device,
    get_device_info,
    setup_device_for_model,
    optimize_for_inference,
    clear_gpu_memory,
    get_memory_usage,
    check_device_compatibility,
)


class TestDeviceUtils:
    """Test cases for device utility functions"""

    def test_get_optimal_device_auto_cpu_fallback(self):
        """Test device detection with CPU fallback"""
        with patch("utils.device_utils.settings") as mock_settings:
            mock_settings.DEMUCS_DEVICE = "auto"

            with patch("torch.cuda.is_available", return_value=False), patch(
                "torch.backends.mps.is_available", return_value=False
            ):

                device = get_optimal_device()
                assert device == "cpu"

    def test_get_optimal_device_manual_setting(self):
        """Test device detection with manual setting"""
        with patch("utils.device_utils.settings") as mock_settings:
            mock_settings.DEMUCS_DEVICE = "cpu"

            device = get_optimal_device()
            assert device == "cpu"

    def test_get_optimal_device_cuda_available(self):
        """Test device detection when CUDA is available"""
        with patch("utils.device_utils.settings") as mock_settings:
            mock_settings.DEMUCS_DEVICE = "auto"

            with patch("torch.cuda.is_available", return_value=True), patch(
                "torch.cuda.device_count", return_value=1
            ):

                device = get_optimal_device()
                assert device == "cuda"

    def test_get_optimal_device_mps_available(self):
        """Test device detection when MPS is available"""
        with patch("utils.device_utils.settings") as mock_settings:
            mock_settings.DEMUCS_DEVICE = "auto"

            with patch("torch.cuda.is_available", return_value=False):
                # Mock MPS availability
                mock_backends = MagicMock()
                mock_backends.mps.is_available.return_value = True

                with patch("torch.backends", mock_backends):
                    device = get_optimal_device()
                    assert device == "mps"

    def test_get_device_info_basic(self):
        """Test getting basic device information"""
        with patch("torch.cuda.is_available", return_value=False), patch(
            "utils.device_utils.get_optimal_device", return_value="cpu"
        ):

            info = get_device_info()

            assert isinstance(info, dict)
            assert "platform" in info
            assert "architecture" in info
            assert "python_version" in info
            assert "torch_version" in info
            assert "optimal_device" in info
            assert "cuda" in info
            assert "mps" in info

            assert info["optimal_device"] == "cpu"
            assert info["cuda"]["available"] == False

    def test_setup_device_for_model_cpu(self):
        """Test setting up model on CPU device"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model

        with patch("torch.device") as mock_torch_device:
            mock_device = MagicMock()
            mock_torch_device.return_value = mock_device

            model, device = setup_device_for_model(mock_model, "cpu")

            mock_torch_device.assert_called_with("cpu")
            mock_model.to.assert_called_with(mock_device)
            assert model == mock_model
            assert device == mock_device

    def test_setup_device_for_model_auto_detection(self):
        """Test setting up model with automatic device detection"""
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model

        with patch("utils.device_utils.get_optimal_device", return_value="cpu"), patch(
            "torch.device"
        ) as mock_torch_device:

            mock_device = MagicMock()
            mock_torch_device.return_value = mock_device

            model, device = setup_device_for_model(mock_model)

            mock_torch_device.assert_called_with("cpu")
            mock_model.to.assert_called_with(mock_device)

    def test_setup_device_for_model_fallback(self):
        """Test device setup with fallback to CPU on error"""
        mock_model = MagicMock()
        mock_model.to.side_effect = [RuntimeError("GPU not available"), mock_model]

        with patch("torch.device") as mock_torch_device:
            mock_gpu_device = MagicMock()
            mock_cpu_device = MagicMock()
            mock_torch_device.side_effect = [mock_gpu_device, mock_cpu_device]

            model, device = setup_device_for_model(mock_model, "cuda")

            # Should try GPU first, then fallback to CPU
            assert mock_torch_device.call_count == 2
            mock_torch_device.assert_any_call("cuda")
            mock_torch_device.assert_any_call("cpu")
            assert device == mock_cpu_device

    def test_optimize_for_inference(self):
        """Test model optimization for inference"""
        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model

        with patch("torch.__version__", "2.1.0"), patch(
            "torch.compile"
        ) as mock_compile:

            mock_compile.return_value = mock_model

            optimized_model = optimize_for_inference(mock_model)

            mock_model.eval.assert_called_once()
            mock_compile.assert_called_once_with(mock_model, mode="reduce-overhead")
            assert optimized_model == mock_model

    def test_optimize_for_inference_old_pytorch(self):
        """Test model optimization with older PyTorch version"""
        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model

        with patch("torch.__version__", "1.13.0"):
            optimized_model = optimize_for_inference(mock_model)

            mock_model.eval.assert_called_once()
            assert optimized_model == mock_model

    def test_optimize_for_inference_compile_error(self):
        """Test model optimization with compile error"""
        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model

        with patch("torch.__version__", "2.1.0"), patch(
            "torch.compile", side_effect=RuntimeError("Compile failed")
        ):

            optimized_model = optimize_for_inference(mock_model)

            mock_model.eval.assert_called_once()
            assert optimized_model == mock_model

    def test_clear_gpu_memory_cuda(self):
        """Test clearing CUDA GPU memory"""
        with patch("torch.cuda.is_available", return_value=True), patch(
            "torch.cuda.empty_cache"
        ) as mock_empty_cache:

            clear_gpu_memory()

            mock_empty_cache.assert_called_once()

    def test_clear_gpu_memory_mps(self):
        """Test clearing MPS GPU memory"""
        mock_backends = MagicMock()
        mock_backends.mps.is_available.return_value = True

        with patch("torch.cuda.is_available", return_value=False), patch(
            "torch.backends", mock_backends
        ), patch("torch.mps.empty_cache") as mock_mps_empty_cache:

            clear_gpu_memory()

            mock_mps_empty_cache.assert_called_once()

    def test_clear_gpu_memory_no_gpu(self):
        """Test clearing GPU memory when no GPU available"""
        with patch("torch.cuda.is_available", return_value=False):
            # Should not raise any errors
            clear_gpu_memory()

    def test_get_memory_usage_cuda(self):
        """Test getting CUDA memory usage"""
        with patch("torch.cuda.is_available", return_value=True), patch(
            "torch.cuda.device_count", return_value=1
        ), patch("torch.cuda.memory_allocated", return_value=1000), patch(
            "torch.cuda.memory_reserved", return_value=2000
        ), patch(
            "torch.cuda.get_device_properties"
        ) as mock_props:

            mock_props.return_value.total_memory = 8000

            usage = get_memory_usage()

            assert isinstance(usage, dict)
            assert "cuda" in usage
            assert "cuda:0" in usage["cuda"]

            cuda_info = usage["cuda"]["cuda:0"]
            assert cuda_info["allocated"] == 1000
            assert cuda_info["reserved"] == 2000
            assert cuda_info["total"] == 8000

    def test_get_memory_usage_mps(self):
        """Test getting MPS memory usage"""
        mock_backends = MagicMock()
        mock_backends.mps.is_available.return_value = True

        with patch("torch.cuda.is_available", return_value=False), patch(
            "torch.backends", mock_backends
        ):

            usage = get_memory_usage()

            assert isinstance(usage, dict)
            assert "mps" in usage
            assert usage["mps"]["available"] == True
            assert usage["mps"]["monitoring"] == "not_supported"

    def test_check_device_compatibility_basic(self):
        """Test basic device compatibility check"""
        with patch("utils.device_utils.get_optimal_device", return_value="cpu"), patch(
            "utils.device_utils.get_device_info"
        ) as mock_device_info:

            mock_device_info.return_value = {
                "platform": "Darwin",
                "architecture": "arm64",
                "mps": {"available": True},
            }

            result = check_device_compatibility()

            assert isinstance(result, dict)
            assert "compatible" in result
            assert "device" in result
            assert "warnings" in result
            assert "recommendations" in result

            assert result["compatible"] == True
            assert result["device"] == "cpu"
            assert isinstance(result["warnings"], list)
            assert isinstance(result["recommendations"], list)

    def test_check_device_compatibility_memory_warning(self):
        """Test device compatibility with memory warning"""
        mock_device_info = {
            "platform": "Linux",
            "cuda": {
                "devices": [
                    {
                        "memory_total": 1000 * 1024 * 1024,  # 1GB
                        "memory_allocated": 800 * 1024 * 1024,  # 800MB used
                    }
                ]
            },
        }

        with patch("utils.device_utils.get_optimal_device", return_value="cuda"), patch(
            "utils.device_utils.get_device_info", return_value=mock_device_info
        ), patch("torch.cuda.is_available", return_value=True):

            result = check_device_compatibility(required_memory_mb=500)

            # Should have warning about low GPU memory
            assert len(result["warnings"]) > 0
            assert any("Low GPU memory" in warning for warning in result["warnings"])
            assert len(result["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
