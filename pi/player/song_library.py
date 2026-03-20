import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Song:
    song_id: str
    title: str
    artist: Optional[str] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None
    stem_paths: dict[str, Path] = field(default_factory=dict)


class SongLibrary:
    """Scans the stems directory for available songs."""

    def __init__(self, stems_dir: Path):
        self.stems_dir = Path(stems_dir)
        self.songs: list[Song] = []

    def scan(self) -> list[Song]:
        """Scan the stems directory and return list of available songs."""
        songs_dir = self.stems_dir / "songs"
        if not songs_dir.exists():
            self.songs = []
            return self.songs

        self.songs = []
        for song_path in sorted(songs_dir.iterdir()):
            if not song_path.is_dir():
                continue
            meta_path = song_path / "meta.json"
            if not meta_path.exists():
                continue

            with open(meta_path) as f:
                meta = json.load(f)

            stem_paths = {}
            for stem_type in meta.get("stems", []):
                ogg_path = song_path / f"{stem_type}.ogg"
                if ogg_path.exists():
                    stem_paths[stem_type] = ogg_path

            self.songs.append(Song(
                song_id=meta["song_id"],
                title=meta["title"],
                artist=meta.get("artist"),
                bpm=meta.get("bpm"),
                duration=meta.get("duration"),
                stem_paths=stem_paths,
            ))

        return self.songs
