import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="WavDash Stem Receiver")

VALID_STEM_TYPES = {"vocals", "drums", "bass", "guitar", "piano", "other"}


def get_stems_dir() -> Path:
    d = Path(os.environ.get("WAVDASH_STEMS_DIR", os.path.expanduser("~/wavdash-stems")))
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_songs_index_path() -> Path:
    return get_stems_dir() / "songs.json"


def load_songs_index() -> list[dict]:
    path = get_songs_index_path()
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save_songs_index(songs: list[dict]):
    with open(get_songs_index_path(), "w") as f:
        json.dump(songs, f, indent=2)


class CreateSongRequest(BaseModel):
    title: str
    artist: Optional[str] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None


class CreateSongResponse(BaseModel):
    song_id: str
    title: str
    artist: Optional[str] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None


class StemUploadResponse(BaseModel):
    song_id: str
    stem_type: str
    message: str


@app.post("/api/songs", status_code=201, response_model=CreateSongResponse)
def create_song(req: CreateSongRequest):
    song_id = uuid.uuid4().hex[:12]
    song_dir = get_stems_dir() / "songs" / song_id
    song_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "song_id": song_id,
        "title": req.title,
        "artist": req.artist,
        "bpm": req.bpm,
        "duration": req.duration,
        "stems": [],
    }
    with open(song_dir / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    songs = load_songs_index()
    songs.append({"song_id": song_id, "title": req.title, "artist": req.artist, "bpm": req.bpm, "duration": req.duration})
    save_songs_index(songs)

    return CreateSongResponse(song_id=song_id, **req.model_dump())


@app.post("/api/songs/{song_id}/stems", status_code=201, response_model=StemUploadResponse)
async def upload_stem(
    song_id: str,
    stem_type: str = Form(...),
    file: UploadFile = File(...),
):
    if stem_type not in VALID_STEM_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid stem_type: {stem_type}. Must be one of {VALID_STEM_TYPES}")

    song_dir = get_stems_dir() / "songs" / song_id
    if not song_dir.exists():
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")

    stem_path = song_dir / f"{stem_type}.ogg"
    with open(stem_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update meta.json stems list
    meta_path = song_dir / "meta.json"
    with open(meta_path) as f:
        meta = json.load(f)
    if stem_type not in meta["stems"]:
        meta["stems"].append(stem_type)
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return StemUploadResponse(song_id=song_id, stem_type=stem_type, message="Stem uploaded")


@app.get("/api/songs")
def list_songs():
    return load_songs_index()


@app.delete("/api/songs/{song_id}")
def delete_song(song_id: str):
    song_dir = get_stems_dir() / "songs" / song_id
    if not song_dir.exists():
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")

    shutil.rmtree(song_dir)

    songs = load_songs_index()
    songs = [s for s in songs if s["song_id"] != song_id]
    save_songs_index(songs)

    return {"message": f"Song {song_id} deleted"}
