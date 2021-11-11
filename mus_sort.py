from pathlib import Path
import textwrap
from tinytag import TinyTag


accepted_files = tuple(("." + i) for i in ("mp3", "bit", "wav", "wave", "opus",
                                           "flac", "asf", "wma", "mp4", "m4a", "m4b", "aiff", "aif", "aifc"))


def fix_new_path(name: str, *, genre: bool = False) -> str:
    name = textwrap.fill(name.strip(), width=50, placeholder="(...)", max_lines=1).replace(
        ": ", " - ").replace(":", ";").replace("\"", "'").replace("\\", "").replace("/", "")
    return name.replace("|", "")


def is_album_directory(dir: Path) -> (Path or False):
    for item in dir.iterdir():
        if item.suffix.lower() in accepted_files:
            return item
    return False


class AlbumDirStats:
    year: int or None
    genre: str or None
    artist: str or None
    album: str or None

    def __init__(self, dir: Path) -> None:
        self.dir = Path(dir)
        self.year = None
        self.genre = None
        self.artist = None
        self.album = None


def get_album_stats(dir: Path) -> AlbumDirStats:
    resp = AlbumDirStats(dir)
    filepaths = [i for i in dir.iterdir() if i.is_file()
                 and i.suffix.lower() in accepted_files]

    for path in filepaths:
        track = TinyTag.get(path)

        for attr in ("year", "genre", "album", "artist"):
            if getattr(resp, attr, None) is None:
                if (_attr := getattr(track, attr)) is not None:
                    setattr(resp, attr, str(_attr).replace("/", "-") or None)

        if resp.year and resp.genre and resp.album and resp.artist:
            return resp

    return resp


def sort(dir: Path, root_dir: Path = None) -> None:
    if root_dir is None:
        root_dir = dir.resolve()

    for item in dir.iterdir():
        if item.is_dir():
            sort(item, root_dir)
    if is_album_directory(dir):
        if dir.name == ".git":
            return
        stats = get_album_stats(dir)

        genre = stats.genre if (
            stats.genre and stats.genre != "Other") else "UNKNOWN_GENRE"
        artist = stats.artist or "UNKNOWN_ARTIST"
        album = stats.album or "Singles"
        if stats.year:
            album = stats.year + ". " + album
        genre = fix_new_path(genre)
        artist = fix_new_path(artist)
        album = fix_new_path(album)

        print(genre, artist, album)
        target_dir = root_dir / genre / artist
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dir.resolve()

        target_dir = target_dir / album

        try:
            dir.rename(target_dir)
        except FileExistsError as e:
            print(f"{e}: Album titled '{album} already exists")


def cleanup(dir: Path) -> None:
    if dir.name == ".git" or not dir.is_dir():
        return
    [cleanup(subdir) for subdir in dir.iterdir()]
    try:
        dir.rmdir()
    except:
        pass


if __name__ == "__main__":
    dirs = [("./" + str(dir)) for dir in Path(".").iterdir()
            if dir.is_dir() and dir.name != ".git"]
    print(f"Subdirectories here: {', '.join(dirs)}")
    p = Path(input("Path?  "))

    sort(p)
    cleanup(Path(p))
