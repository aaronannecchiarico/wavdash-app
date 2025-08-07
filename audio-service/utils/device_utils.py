"""
Device detection and management utilities
"""

import torch
import platform
import logging
from config import settings

logger = logging.getLogger(__name__)


def get_optimal_device():
    """
    Automatically detect the best available device for computation
    
    Returns:
        str: Device string ('cuda', 'mps', or 'cpu')
    """
    if settings.DEMUCS_DEVICE.lower() != "auto":
        return settings.DEMUCS_DEVICE.lower()
    
    # Check for CUDA (NVIDIA GPUs)
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        logger.info(f"CUDA detected with {device_count} GPU(s)")
        return "cuda"
    
    # Check for MPS (Apple Silicon)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        logger.info("Apple MPS (Metal Performance Shaders) detected")
        return "mps"
    
    # Fallback to CPU
    logger.info("Using CPU for computation")
    return "cpu"


def get_device_info():
    """
    Get detailed information about available compute devices
    
    Returns:
        dict: Device information
    """
    info = {
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'torch_version': torch.__version__,
        'optimal_device': get_optimal_device()
    }
    
    # CUDA information
    if torch.cuda.is_available():
        info['cuda'] = {
            'available': True,
            'version': torch.version.cuda,
            'device_count': torch.cuda.device_count(),
            'devices': [
                {
                    'name': torch.cuda.get_device_name(i),
                    'memory_total': torch.cuda.get_device_properties(i).total_memory,
                    'memory_allocated': torch.cuda.memory_allocated(i),
                    'memory_cached': torch.cuda.memory_reserved(i)
                }
                for i in range(torch.cuda.device_count())
            ]
        }
    else:
        info['cuda'] = {'available': False}
    
    # MPS information
    if hasattr(torch.backends, 'mps'):
        info['mps'] = {
            'available': torch.backends.mps.is_available(),
            'built': torch.backends.mps.is_built()
        }
    else:
        info['mps'] = {'available': False, 'built': False}
    
    return info


def setup_device_for_model(model, device=None):
    """
    Setup model on the optimal device
    
    Args:
        model: PyTorch model
        device: Specific device to use (optional)
    
    Returns:
        tuple: (model, device)
    """
    if device is None:
        device = get_optimal_device()
    
    try:
        device_obj = torch.device(device)
        model = model.to(device_obj)
        logger.info(f"Model moved to device: {device}")
        return model, device_obj
    except Exception as e:
        logger.warning(f"Failed to move model to {device}, falling back to CPU: {e}")
        device_obj = torch.device("cpu")
        model = model.to(device_obj)
        return model, device_obj


def optimize_for_inference(model):
    """
    Optimize model for inference
    
    Args:
        model: PyTorch model
    
    Returns:
        model: Optimized model
    """
    try:
        # Set to evaluation mode
        model.eval()
        
        # Try to compile if using PyTorch 2.0+
        if hasattr(torch, 'compile') and torch.__version__ >= "2.0":
            try:
                model = torch.compile(model, mode='reduce-overhead')
                logger.info("Model compiled with torch.compile")
            except Exception as e:
                logger.warning(f"Failed to compile model: {e}")
        
        return model
    except Exception as e:
        logger.error(f"Error optimizing model: {e}")
        return model


def clear_gpu_memory():
    """Clear GPU memory cache"""
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("CUDA cache cleared")
        
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            torch.mps.empty_cache()
            logger.info("MPS cache cleared")
            
    except Exception as e:
        logger.warning(f"Failed to clear GPU memory: {e}")


def get_memory_usage():
    """
    Get current memory usage information
    
    Returns:
        dict: Memory usage information
    """
    usage = {}
    
    try:
        if torch.cuda.is_available():
            usage['cuda'] = {}
            for i in range(torch.cuda.device_count()):
                device_name = f"cuda:{i}"
                usage['cuda'][device_name] = {
                    'allocated': torch.cuda.memory_allocated(i),
                    'reserved': torch.cuda.memory_reserved(i),
                    'total': torch.cuda.get_device_properties(i).total_memory
                }
        
        # MPS doesn't have direct memory monitoring
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            usage['mps'] = {'available': True, 'monitoring': 'not_supported'}
            
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
    
    return usage


def check_device_compatibility(required_memory_mb=None):
    """
    Check if the current device setup is compatible for audio processing
    
    Args:
        required_memory_mb: Minimum required memory in MB
    
    Returns:
        dict: Compatibility information
    """
    result = {
        'compatible': True,
        'device': get_optimal_device(),
        'warnings': [],
        'recommendations': []
    }
    
    device_info = get_device_info()
    
    # Check memory requirements
    if required_memory_mb and torch.cuda.is_available():
        for device in device_info.get('cuda', {}).get('devices', []):
            available_mb = (device['memory_total'] - device['memory_allocated']) / (1024 * 1024)
            if available_mb < required_memory_mb:
                result['warnings'].append(
                    f"Low GPU memory: {available_mb:.0f}MB available, {required_memory_mb}MB required"
                )
                result['recommendations'].append("Consider using CPU mode or reducing batch size")
    
    # Platform-specific recommendations
    if device_info['platform'] == 'Darwin' and device_info['architecture'] == 'arm64':
        if not device_info['mps']['available']:
            result['warnings'].append("MPS not available on Apple Silicon")
            result['recommendations'].append("Upgrade to macOS 12.3+ for MPS support")
    
    return result