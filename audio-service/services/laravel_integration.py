"""
Enhanced Laravel Integration Service
Phase 3: Optimization & Polish - Enhanced callback integration for Laravel
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from models.tempo_models import TempoCallbackData

logger = logging.getLogger(__name__)


class CallbackStatus(Enum):
    """Status values for Laravel callbacks"""

    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CallbackPriority(Enum):
    """Priority levels for callback delivery"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EnhancedCallbackData:
    """Enhanced callback data structure for Laravel integration"""

    # Core task information
    task_id: str
    status: CallbackStatus
    processing_type: str  # "tempo", "features", "stems"

    # Timing information
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None

    # Audio analysis data
    original_analysis: Optional[Dict[str, Any]] = None
    tempo_processing: Optional[Dict[str, Any]] = None

    # File and storage information
    storage_paths: Optional[Dict[str, str]] = None
    public_urls: Optional[Dict[str, str]] = None
    storage_type: Optional[str] = None

    # Error handling
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0

    # Performance metrics
    cache_hit: bool = False
    processing_warnings: Optional[Dict[str, str]] = None
    smart_suggestions: Optional[Dict[str, Any]] = None

    # Laravel-specific metadata
    user_id: Optional[str] = None
    upload_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)

        # Convert datetime objects to ISO format strings
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()

        # Convert enums to values
        data["status"] = self.status.value

        return data


class CallbackDeliveryService:
    """
    Robust callback delivery service with retry logic and Laravel optimization
    """

    def __init__(self, max_retries: int = 3, timeout_seconds: int = 30):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.delivery_stats = {
            "total_attempts": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "average_response_time": 0.0,
        }

    def send_callback(
        self,
        callback_url: str,
        callback_data: EnhancedCallbackData,
        priority: CallbackPriority = CallbackPriority.NORMAL,
    ) -> bool:
        """
        Send callback to Laravel with enhanced error handling and retry logic

        Args:
            callback_url: The Laravel endpoint URL
            callback_data: Enhanced callback data
            priority: Delivery priority (affects retry behavior)

        Returns:
            bool: True if delivery was successful, False otherwise
        """
        if not callback_url:
            logger.warning("No callback URL provided, skipping callback")
            return False

        self.delivery_stats["total_attempts"] += 1
        max_retries = self._get_max_retries_for_priority(priority)

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()

                # Prepare headers optimized for Laravel
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "BeatForge-AudioService/3.0",
                    "X-Callback-Attempt": str(attempt + 1),
                    "X-Callback-Priority": priority.value,
                    "X-Service-Version": "3.0.0",
                    "Accept": "application/json",
                }

                # Add authentication headers if available
                if hasattr(self, "_auth_token") and self._auth_token:
                    headers["Authorization"] = f"Bearer {self._auth_token}"

                # Send the callback
                response = requests.post(
                    callback_url,
                    json=callback_data.to_dict(),
                    headers=headers,
                    timeout=self.timeout_seconds,
                    allow_redirects=True,
                )

                response_time = time.time() - start_time
                self._update_response_time_stats(response_time)

                # Check response status
                if response.status_code in [200, 201, 202]:
                    logger.info(
                        f"✅ Callback delivered successfully to {callback_url} "
                        f"(attempt {attempt + 1}, {response_time:.2f}s)"
                    )

                    self.delivery_stats["successful_deliveries"] += 1

                    # Log response from Laravel for debugging
                    if response.text:
                        try:
                            response_data = response.json()
                            logger.debug(f"Laravel response: {response_data}")
                        except json.JSONDecodeError:
                            logger.debug(
                                f"Laravel response (text): {response.text[:200]}"
                            )

                    return True

                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(
                        f"Callback failed with status {response.status_code}: {error_msg}"
                    )

                    # Don't retry for client errors (4xx), only server errors (5xx)
                    if 400 <= response.status_code < 500:
                        logger.error(
                            f"Client error {response.status_code}, not retrying"
                        )
                        break

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Callback timeout (attempt {attempt + 1}) to {callback_url}"
                )

            except requests.exceptions.ConnectionError:
                logger.warning(
                    f"Connection error (attempt {attempt + 1}) to {callback_url}"
                )

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request error (attempt {attempt + 1}) to {callback_url}: {str(e)}"
                )

            except Exception as e:
                logger.error(
                    f"Unexpected error (attempt {attempt + 1}) sending callback: {str(e)}"
                )

            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                wait_time = min(2**attempt, 30)  # Cap at 30 seconds
                logger.info(f"Retrying callback in {wait_time} seconds...")
                time.sleep(wait_time)

        # All attempts failed
        logger.error(
            f"❌ Failed to deliver callback to {callback_url} after {max_retries + 1} attempts"
        )
        self.delivery_stats["failed_deliveries"] += 1
        return False

    def _get_max_retries_for_priority(self, priority: CallbackPriority) -> int:
        """Get max retries based on priority level"""
        retry_map = {
            CallbackPriority.LOW: 1,
            CallbackPriority.NORMAL: self.max_retries,
            CallbackPriority.HIGH: self.max_retries + 2,
            CallbackPriority.URGENT: self.max_retries + 4,
        }
        return retry_map.get(priority, self.max_retries)

    def _update_response_time_stats(self, response_time: float):
        """Update average response time statistics"""
        current_avg = self.delivery_stats["average_response_time"]
        total_attempts = self.delivery_stats["total_attempts"]

        # Calculate new average
        new_avg = (
            (current_avg * (total_attempts - 1)) + response_time
        ) / total_attempts
        self.delivery_stats["average_response_time"] = new_avg

    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get callback delivery statistics"""
        total = self.delivery_stats["total_attempts"]
        success_rate = (
            (self.delivery_stats["successful_deliveries"] / total * 100)
            if total > 0
            else 0
        )

        return {
            **self.delivery_stats,
            "success_rate_percent": round(success_rate, 2),
            "failure_rate_percent": round(100 - success_rate, 2),
        }


class LaravelIntegrationHelper:
    """
    Helper class for Laravel-specific integration features
    """

    @staticmethod
    def create_tempo_callback_data(
        task_id: str,
        status: CallbackStatus,
        processing_result: Dict[str, Any],
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> EnhancedCallbackData:
        """
        Create enhanced callback data for tempo processing results

        Args:
            task_id: Unique task identifier
            status: Processing status
            processing_result: Result from tempo processing task
            user_metadata: Additional user/Laravel metadata

        Returns:
            EnhancedCallbackData: Enhanced callback data structure
        """
        now = datetime.now()

        # Extract user information from metadata
        user_id = None
        upload_id = None
        project_id = None

        if user_metadata:
            user_id = user_metadata.get("user_id")
            upload_id = user_metadata.get("upload_id")
            project_id = user_metadata.get("project_id")

        # Create enhanced callback data
        callback_data = EnhancedCallbackData(
            task_id=task_id,
            status=status,
            processing_type="tempo",
            started_at=now,
            user_id=user_id,
            upload_id=upload_id,
            project_id=project_id,
            metadata=user_metadata,
        )

        if status == CallbackStatus.COMPLETED and processing_result:
            # Extract processing information
            callback_data.completed_at = now
            callback_data.processing_time = processing_result.get("processing_time")
            callback_data.original_analysis = processing_result.get("original_analysis")
            callback_data.tempo_processing = processing_result.get("tempo_processing")
            callback_data.storage_paths = processing_result.get("output_files", {})
            callback_data.public_urls = processing_result.get("public_urls", {})
            callback_data.storage_type = processing_result.get("storage_type")
            callback_data.smart_suggestions = processing_result.get("smart_suggestions")
            callback_data.processing_warnings = processing_result.get(
                "processing_warnings"
            )

            # Check if this was a cache hit (performance optimization)
            callback_data.cache_hit = "🚀 Cache hit" in str(processing_result)

        elif status == CallbackStatus.FAILED and processing_result:
            # Extract error information
            callback_data.error_message = processing_result.get("error")
            callback_data.error_code = processing_result.get(
                "error_code", "PROCESSING_FAILED"
            )

        return callback_data

    @staticmethod
    def generate_laravel_compatible_urls(
        storage_paths: Dict[str, str], base_url: str, signed_url_expiry_hours: int = 24
    ) -> Dict[str, str]:
        """
        Generate Laravel-compatible URLs for processed audio files

        Args:
            storage_paths: Dictionary of file paths
            base_url: Base URL for the storage service
            signed_url_expiry_hours: Expiry time for signed URLs

        Returns:
            Dict[str, str]: Dictionary of public URLs
        """
        public_urls = {}

        for key, path in storage_paths.items():
            if path:
                # Create Laravel-compatible URL
                public_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

                # Add expiry parameter for signed URLs
                if "?" in public_url:
                    public_url += f"&expires={int(time.time()) + (signed_url_expiry_hours * 3600)}"
                else:
                    public_url += f"?expires={int(time.time()) + (signed_url_expiry_hours * 3600)}"

                public_urls[key] = public_url

        return public_urls

    @staticmethod
    def validate_callback_url(callback_url: str) -> bool:
        """
        Validate that the callback URL is properly formatted and accessible

        Args:
            callback_url: URL to validate

        Returns:
            bool: True if URL appears valid, False otherwise
        """
        if not callback_url:
            return False

        # Basic URL validation
        if not callback_url.startswith(("http://", "https://")):
            logger.warning(f"Invalid callback URL protocol: {callback_url}")
            return False

        # Check for localhost in production (optional warning)
        if "localhost" in callback_url or "127.0.0.1" in callback_url:
            logger.warning(f"Callback URL uses localhost: {callback_url}")

        try:
            # Quick connectivity test (optional, can be disabled for performance)
            response = requests.head(callback_url, timeout=5)
            if response.status_code >= 500:
                logger.warning(
                    f"Callback URL returned server error: {response.status_code}"
                )
                return False

        except requests.exceptions.RequestException:
            # URL might be valid but endpoint not ready, allow it
            logger.debug(f"Could not verify callback URL connectivity: {callback_url}")

        return True


# Global instances
_callback_delivery_service = CallbackDeliveryService()
_laravel_helper = LaravelIntegrationHelper()


def get_callback_delivery_service() -> CallbackDeliveryService:
    """Get the global callback delivery service instance"""
    return _callback_delivery_service


def get_laravel_integration_helper() -> LaravelIntegrationHelper:
    """Get the Laravel integration helper instance"""
    return _laravel_helper


def send_enhanced_callback(
    callback_url: str,
    task_id: str,
    status: CallbackStatus,
    processing_result: Dict[str, Any],
    user_metadata: Optional[Dict[str, Any]] = None,
    priority: CallbackPriority = CallbackPriority.NORMAL,
) -> bool:
    """
    Convenience function to send enhanced callbacks to Laravel

    Args:
        callback_url: Laravel callback endpoint
        task_id: Task identifier
        status: Processing status
        processing_result: Processing result data
        user_metadata: Additional metadata
        priority: Delivery priority

    Returns:
        bool: True if callback was delivered successfully
    """
    if not LaravelIntegrationHelper.validate_callback_url(callback_url):
        logger.error(f"Invalid callback URL: {callback_url}")
        return False

    # Create enhanced callback data
    callback_data = LaravelIntegrationHelper.create_tempo_callback_data(
        task_id, status, processing_result, user_metadata
    )

    # Send the callback
    delivery_service = get_callback_delivery_service()
    return delivery_service.send_callback(callback_url, callback_data, priority)
