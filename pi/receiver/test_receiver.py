import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def stems_dir(tmp_path):
    """Use a temp directory for stem storage during tests."""
    os.environ["WAVDASH_STEMS_DIR"] = str(tmp_path)
    yield tmp_path


@pytest.fixture
def client(stems_dir):
    # Import after setting env var
    from main import app
    return TestClient(app)


def make_ogg_bytes():
    """Return minimal bytes to simulate an OGG file."""
    return b"fake-ogg-data-for-testing"


class TestCreateSong:
    def test_create_song(self, client):
        response = client.post("/api/songs", json={
            "title": "Test Song",
            "artist": "Test Artist",
            "bpm": 120.0,
            "duration": 210.5,
        })
        assert response.status_code == 201
        data = response.json()
        assert "song_id" in data
        assert data["title"] == "Test Song"

    def test_create_song_missing_title(self, client):
        response = client.post("/api/songs", json={
            "artist": "Test Artist",
        })
        assert response.status_code == 422


class TestUploadStem:
    def test_upload_stem(self, client, stems_dir):
        # Create song first
        resp = client.post("/api/songs", json={
            "title": "Test Song",
            "artist": "Test",
            "bpm": 120.0,
            "duration": 200.0,
        })
        song_id = resp.json()["song_id"]

        # Upload a stem
        response = client.post(
            f"/api/songs/{song_id}/stems",
            data={"stem_type": "vocals"},
            files={"file": ("vocals.ogg", make_ogg_bytes(), "audio/ogg")},
        )
        assert response.status_code == 201
        assert response.json()["stem_type"] == "vocals"

        # Verify file exists on disk
        stem_path = stems_dir / "songs" / song_id / "vocals.ogg"
        assert stem_path.exists()

    def test_upload_stem_invalid_type(self, client):
        resp = client.post("/api/songs", json={
            "title": "Test",
            "artist": "Test",
            "bpm": 120.0,
            "duration": 200.0,
        })
        song_id = resp.json()["song_id"]

        response = client.post(
            f"/api/songs/{song_id}/stems",
            data={"stem_type": "invalid"},
            files={"file": ("bad.ogg", make_ogg_bytes(), "audio/ogg")},
        )
        assert response.status_code == 422

    def test_upload_stem_song_not_found(self, client):
        response = client.post(
            "/api/songs/nonexistent/stems",
            data={"stem_type": "vocals"},
            files={"file": ("vocals.ogg", make_ogg_bytes(), "audio/ogg")},
        )
        assert response.status_code == 404


class TestListSongs:
    def test_list_songs_empty(self, client):
        response = client.get("/api/songs")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_songs_with_entries(self, client):
        client.post("/api/songs", json={
            "title": "Song A",
            "artist": "Artist",
            "bpm": 128.0,
            "duration": 180.0,
        })
        client.post("/api/songs", json={
            "title": "Song B",
            "artist": "Artist",
            "bpm": 140.0,
            "duration": 200.0,
        })
        response = client.get("/api/songs")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestDeleteSong:
    def test_delete_song(self, client, stems_dir):
        resp = client.post("/api/songs", json={
            "title": "To Delete",
            "artist": "Test",
            "bpm": 120.0,
            "duration": 200.0,
        })
        song_id = resp.json()["song_id"]

        # Upload a stem so there are files to delete
        client.post(
            f"/api/songs/{song_id}/stems",
            data={"stem_type": "drums"},
            files={"file": ("drums.ogg", make_ogg_bytes(), "audio/ogg")},
        )

        response = client.delete(f"/api/songs/{song_id}")
        assert response.status_code == 200

        # Verify files removed
        assert not (stems_dir / "songs" / song_id).exists()

        # Verify not in listing
        listing = client.get("/api/songs").json()
        assert len(listing) == 0

    def test_delete_nonexistent(self, client):
        response = client.delete("/api/songs/nonexistent")
        assert response.status_code == 404
