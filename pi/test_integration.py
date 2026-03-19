"""
End-to-end integration test.
Starts the receiver, pushes a fake song, verifies it appears in the song library.

Run: cd pi && python test_integration.py
Requires: receiver and player packages installed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import httpx


def main():
    stems_dir = tempfile.mkdtemp(prefix="wavdash-test-")
    os.environ["WAVDASH_STEMS_DIR"] = stems_dir
    print(f"Using temp stems dir: {stems_dir}")

    # Start receiver in background
    receiver = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "9099"],
        cwd=os.path.join(os.path.dirname(__file__), "receiver"),
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for receiver to start
        base_url = "http://127.0.0.1:9099"
        for _ in range(20):
            try:
                httpx.get(f"{base_url}/api/songs", timeout=1)
                break
            except httpx.ConnectError:
                time.sleep(0.5)
        else:
            print("FAIL: Receiver did not start")
            return 1

        print("Receiver started")

        # Create a song
        resp = httpx.post(f"{base_url}/api/songs", json={
            "title": "Integration Test Song",
            "artist": "Test",
            "bpm": 128.0,
            "duration": 200.0,
        })
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        song_id = resp.json()["song_id"]
        print(f"Created song: {song_id}")

        # Upload 6 stems
        for stem_type in ["vocals", "drums", "bass", "guitar", "piano", "other"]:
            resp = httpx.post(
                f"{base_url}/api/songs/{song_id}/stems",
                data={"stem_type": stem_type},
                files={"file": (f"{stem_type}.ogg", b"fake-ogg-data", "audio/ogg")},
            )
            assert resp.status_code == 201, f"Stem upload failed: {resp.status_code}"
        print("Uploaded 6 stems")

        # Verify song listing
        resp = httpx.get(f"{base_url}/api/songs")
        songs = resp.json()
        assert len(songs) == 1
        assert songs[0]["title"] == "Integration Test Song"
        print("Song appears in listing")

        # Verify files on disk
        song_dir = os.path.join(stems_dir, "songs", song_id)
        assert os.path.exists(os.path.join(song_dir, "vocals.ogg"))
        assert os.path.exists(os.path.join(song_dir, "meta.json"))
        with open(os.path.join(song_dir, "meta.json")) as f:
            meta = json.load(f)
        assert len(meta["stems"]) == 6
        print("Files verified on disk")

        # Verify song library scanner picks it up
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "player"))
        from song_library import SongLibrary
        lib = SongLibrary(stems_dir)
        scanned = lib.scan()
        assert len(scanned) == 1
        assert scanned[0].title == "Integration Test Song"
        assert len(scanned[0].stem_paths) == 6
        print("Song library scanner works")

        # Delete song
        resp = httpx.delete(f"{base_url}/api/songs/{song_id}")
        assert resp.status_code == 200
        assert not os.path.exists(song_dir)
        print("Song deleted successfully")

        print("\n=== ALL INTEGRATION TESTS PASSED ===")
        return 0

    finally:
        receiver.terminate()
        receiver.wait()
        shutil.rmtree(stems_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
