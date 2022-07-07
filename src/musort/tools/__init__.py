import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tinytag import TinyTag

from .clargparser import ClargParser, clargs
from .locale import REPLACEMENTS, is_hidden


Errors: list[tuple[Exception, str | None]] = []


def log_error(exc: Exception, path: Path | None = None, level: int = logging.ERROR):
    posix = path.as_posix() if path is not None else None
    Errors.append((exc, posix))
    if posix:
        logging.log(level, "The following error occured while handling a path:", posix)
    logging.log(level, f"{exc.__class__.__name__}")


def is_ok(p: Path, /):
    """Checks if a given path is processable with current clargs in mind."""
    if not clargs.hidden and is_hidden(p):
        return False
    elif not clargs.symlinks and p.is_symlink():
        return False
    elif p.name.lower() in clargs.ignored_paths:
        return False
    return True


def iterdir(dir: Path, /) -> Iterable[Path]:
    for p in dir.iterdir():
        if is_ok(p):
            yield p


class cache:
    _genre: dict[str, str | None] = {}
    """Mapping of artist name to genre. Unused if --single-genre is disabled."""

    @classmethod
    def genre(cls, artist: str, default: str | None):
        """Retrieve an item from the cache."""
        if not clargs.single_genre:
            return default
        artist = artist.lower()
        if artist in cls._genre:
            return cls._genre[artist]
        cls._genre[artist] = default
        return default


@dataclass
class MusicFile:
    """Contains music file information."""

    tags: TinyTag
    """Where data is pulled from."""
    path: Path
    """Path to the file."""

    genre: str | None = None
    artist: str | None = None
    album: str | None = None
    year: str | None = None
    title: str | None = None
    """Name of the track."""
    track: int | None = None
    """Track number."""

    @classmethod
    def from_path(cls, path: Path, /):
        """Constructs an instance of MusicFile from a path to a music file."""
        tags = TinyTag.get(path)
        artist = tags.albumartist or tags.artist
        genre = cache.genre(artist, default=tags.genre) if clargs.single_genre else tags.genre
        track = int(tags.track) if tags.track and tags.track.isnumeric() else None
        return cls(
            tags=tags,
            path=path,
            genre=genre,
            artist=artist,
            album=tags.album,
            year=tags.year,
            title=tags.title,
            track=track,
        )

    _FILE_SUFFIXES = {
        ".mp1",
        ".mp2",
        ".mp3",
        ".oga",
        ".ogg",
        ".opus",
        ".wav",
        ".flac",
        ".wma",
        ".m4b",
        ".m4a",
        ".m4r",
        ".mp4",
        ".aiff",
        ".aifc",
        ".aif",
        ".afc",
    }
    """Accepted file suffixes, as per `TinyTag._get_parser_for_filename`."""

    @classmethod
    def is_music(cls, path: Path):
        return path.is_file() and path.suffix.lower() in cls._FILE_SUFFIXES

    @staticmethod
    def prepare_component(tag: str | None, default="UNKNOWN", max_size=70):
        """Prepare a TinyTag component for being used as a file path."""
        if not tag:
            return default
        # sometimes a genre tag is actually multiple genres split by semicolons
        resp = tag.split(";")[0].strip()
        # remove characters that result in invalid filenames
        for s0, s1 in REPLACEMENTS:
            resp.replace(s0, s1)
        # reducing the length of the string
        # the default being 70 is absolutely arbitrary
        return textwrap.fill(resp, width=max_size, placeholder="(…)", max_lines=1)

    def get_new_dir(self, target: Path = clargs.target, /) -> Path:
        genre = self.prepare_component(self.genre, default="UNKNOWN_GENRE")
        artist = self.prepare_component(self.artist, default="UNKNOWN_ARTIST")
        album = self.prepare_component(self.album, default="UNKNOWN_ALBUM")
        if self.year:
            album = f"{self.prepare_component(self.year)} - {album}"
        return target / genre / artist / album

    def get_new_name(self) -> str:
        track = (str(self.track) if self.track else "").zfill(2)
        title = self.prepare_component(self.title, default="UNKNOWN_TRACK")
        return f"{track} - {title}"

    def get_new_path(self, target: Path = clargs.target) -> Path:
        """Shorthand for `MusicFile.get_new_dir(target) / MusicFile.get_new_name()`"""
        return self.get_new_dir(target) / self.get_new_name()
