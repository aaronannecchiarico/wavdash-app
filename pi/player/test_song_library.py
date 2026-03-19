import json
import os
from pathlib import Path

import pytest

from song_library import SongLibrary, Song


@pytest.fixture
def stems_dir(tmp_path):
    """Create a temp stems directory with test songs."""
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()

    # Create two test songs
    for song_id, title in [("abc123", "Test Song A"), ("def456", "Test Song B")]:
        song_path = songs_dir / song_id
        song_path.mkdir()
        meta = {
            "song_id": song_id,
            "title": title,
            "artist": "Test Artist",
            "bpm": 120.0,
            "duration": 180.0,
            "stems": ["vocals", "drums", "bass", "guitar", "piano", "other"],
        }
        with open(song_path / "meta.json", "w") as f:
            json.dump(meta, f)
        # Create dummy stem files
        for stem in meta["stems"]:
            (song_path / f"{stem}.ogg").write_bytes(b"fake-ogg")

    # Write index
    index = [
        {"song_id": "abc123", "title": "Test Song A", "artist": "Test Artist", "bpm": 120.0, "duration": 180.0},
        {"song_id": "def456", "title": "Test Song B", "artist": "Test Artist", "bpm": 120.0, "duration": 180.0},
    ]
    with open(tmp_path / "songs.json", "w") as f:
        json.dump(index, f)

    return tmp_path


class TestSongLibrary:
    def test_scan_songs(self, stems_dir):
        lib = SongLibrary(stems_dir)
        songs = lib.scan()
        assert len(songs) == 2
        assert songs[0].title == "Test Song A"
        assert songs[1].title == "Test Song B"

    def test_song_has_stem_paths(self, stems_dir):
        lib = SongLibrary(stems_dir)
        songs = lib.scan()
        song = songs[0]
        assert "vocals" in song.stem_paths
        assert song.stem_paths["vocals"].exists()

    def test_empty_directory(self, tmp_path):
        lib = SongLibrary(tmp_path)
        songs = lib.scan()
        assert len(songs) == 0

    def test_rescan_detects_new_songs(self, stems_dir):
        lib = SongLibrary(stems_dir)
        songs = lib.scan()
        assert len(songs) == 2

        # Add a new song
        new_dir = stems_dir / "songs" / "ghi789"
        new_dir.mkdir()
        meta = {"song_id": "ghi789", "title": "New Song", "artist": "New", "bpm": 140.0, "duration": 200.0, "stems": ["vocals"]}
        with open(new_dir / "meta.json", "w") as f:
            json.dump(meta, f)
        (new_dir / "vocals.ogg").write_bytes(b"fake")

        songs = lib.scan()
        assert len(songs) == 3
