#!/usr/bin/env python3
"""
Unit tests for task management API endpoints
"""

import json
from pathlib import Path
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from celery_app import celery_app
from main import app
from routes.tasks import get_redis_client, is_task_deleted


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = MagicMock()
    with patch("routes.tasks.redis_client", mock_redis):
        yield mock_redis


@pytest.fixture
def mock_celery_task():
    """Mock Celery task result"""
    mock_task = MagicMock()
    with patch("celery_app.celery_app.AsyncResult") as mock_async_result:
        mock_async_result.return_value = mock_task
        yield mock_task


class TestTaskAPI:
    """Test task management API endpoints"""

    def test_get_task_status_pending(self, client, mock_celery_task, mock_redis):
        """Test getting status of a pending task"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.state = "PENDING"
        mock_redis.exists.return_value = 0  # Task not deleted

        # Test
        response = client.get(f"/task/status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "pending"
        assert "message" in data

    def test_get_task_status_completed(self, client, mock_celery_task, mock_redis):
        """Test getting status of a completed task"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.state = "SUCCESS"
        mock_celery_task.result = {"features": {"tempo": {"bpm": 120}}}
        mock_redis.exists.return_value = 0  # Task not deleted

        # Test
        response = client.get(f"/task/status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "completed"
        assert "result" not in data  # Should not include result by default

    def test_get_task_status_with_result(self, client, mock_celery_task, mock_redis):
        """Test getting status with full result"""
        # Setup
        task_id = "test-task-123"
        mock_result = {
            "features": {"tempo": {"bpm": 120}},
            "metadata": {"duration": 30},
        }
        mock_celery_task.state = "SUCCESS"
        mock_celery_task.result = mock_result
        mock_redis.exists.return_value = 0  # Task not deleted

        # Test
        response = client.get(f"/task/status/{task_id}?include_result=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "completed"
        assert data["result"] == mock_result

    def test_get_task_status_failed(self, client, mock_celery_task, mock_redis):
        """Test getting status of a failed task"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.state = "FAILURE"
        mock_celery_task.info = "Processing error occurred"
        mock_redis.exists.return_value = 0  # Task not deleted

        # Test
        response = client.get(f"/task/status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "failed"
        assert "error" in data

    def test_get_task_status_deleted(self, client, mock_celery_task, mock_redis):
        """Test getting status of a deleted task"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.state = "PENDING"  # Would normally show as pending
        mock_redis.exists.return_value = 1  # Task is marked as deleted

        # Test
        response = client.get(f"/task/status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "deleted"
        assert data["message"] == "Task has been deleted"

    def test_get_task_summary_deleted(self, client, mock_celery_task, mock_redis):
        """Test getting summary of a deleted task"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.state = "PENDING"  # Would normally show as pending
        mock_redis.exists.return_value = 1  # Task is marked as deleted

        # Test
        response = client.get(f"/task/summary/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "deleted"
        assert data["message"] == "Task has been deleted"

    def test_delete_task_success(self, client, mock_celery_task, mock_redis):
        """Test successful task deletion"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.forget = MagicMock()
        mock_redis.setex = MagicMock()

        # Test
        response = client.delete(f"/task/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "deleted"
        assert "removed from backend" in data["message"]

        # Verify methods were called
        mock_celery_task.forget.assert_called_once()
        mock_redis.setex.assert_called_once_with(f"deleted_task:{task_id}", 86400, "1")

    def test_delete_task_redis_failure(self, client, mock_celery_task, mock_redis):
        """Test task deletion when Redis marking fails"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.forget = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis error")

        # Test
        response = client.delete(f"/task/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "deleted"

        # Should still succeed even if Redis marking fails
        mock_celery_task.forget.assert_called_once()

    def test_delete_task_celery_failure(self, client, mock_celery_task, mock_redis):
        """Test task deletion when Celery forget fails"""
        # Setup
        task_id = "test-task-123"
        mock_celery_task.forget.side_effect = Exception("Celery error")

        # Test
        response = client.delete(f"/task/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "error"
        assert "Failed to delete task" in data["error"]

    def test_is_task_deleted_function(self, mock_redis):
        """Test the is_task_deleted helper function"""
        task_id = "test-task-123"

        # Test task not deleted
        mock_redis.exists.return_value = 0
        with patch("routes.tasks.redis_client", mock_redis):
            assert not is_task_deleted(task_id)

        # Test task deleted
        mock_redis.exists.return_value = 1
        with patch("routes.tasks.redis_client", mock_redis):
            assert is_task_deleted(task_id)

        # Test Redis error
        mock_redis.exists.side_effect = Exception("Redis error")
        with patch("routes.tasks.redis_client", mock_redis):
            assert not is_task_deleted(task_id)  # Should return False on error

    def test_is_task_deleted_no_redis(self):
        """Test is_task_deleted when Redis is not available"""
        with patch("routes.tasks.get_redis_client", return_value=None):
            assert not is_task_deleted("test-task-123")

    def test_pending_task_double_check_deleted(
        self, client, mock_celery_task, mock_redis
    ):
        """Test that pending tasks are double-checked for deletion"""
        # Setup - task shows as PENDING and initially not deleted, but then marked as deleted
        task_id = "test-task-123"
        mock_celery_task.state = "PENDING"
        # First call returns 0 (not deleted), second call returns 1 (deleted)
        mock_redis.exists.side_effect = [0, 1]

        # Test
        response = client.get(f"/task/status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "deleted"
        assert data["message"] == "Task has been deleted"

        # Verify Redis was checked twice (once at start, once in PENDING handler)
        assert mock_redis.exists.call_count == 2


def test_integration_delete_then_get_status():
    """Integration test: delete task then check status"""
    client = TestClient(app)
    task_id = "integration-test-123"

    with (
        patch("celery_app.celery_app.AsyncResult") as mock_async_result,
        patch("routes.tasks.redis_client") as mock_redis,
    ):
        mock_task = MagicMock()
        mock_async_result.return_value = mock_task
        mock_task.forget = MagicMock()
        mock_redis.setex = MagicMock()
        mock_redis.exists.return_value = 0

        # Initially task is pending
        mock_task.state = "PENDING"
        response = client.get(f"/task/status/{task_id}")
        assert response.json()["status"] == "pending"

        # Delete the task
        response = client.delete(f"/task/{task_id}")
        assert response.json()["status"] == "deleted"

        # After deletion, mark as deleted in Redis
        mock_redis.exists.return_value = 1

        # Check status again - should now show as deleted
        response = client.get(f"/task/status/{task_id}")
        data = response.json()
        assert data["status"] == "deleted"
        assert data["message"] == "Task has been deleted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
