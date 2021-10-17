from pathlib import Path

from tinytag import TinyTag


accepted_files = tuple(("." + i) for i in ("mp3", "bit", "wav", "wave", "opus",
                                           "flac", "asf", "wma", "mp4", "m4a", "m4b", "aiff", "aif", "aifc"))


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
        root_dir = Path(dir)

    for item in dir.iterdir():
        if item.is_dir():
            sort(item, root_dir)
    if is_album_directory(dir):
        stats = get_album_stats(dir)
        _target_dir = f"{root_dir}/{stats.genre[:30] if (stats.genre and stats.genre != 'Other') else 'UNKNOWN'}/{stats.artist[:30] or 'UNKNOWN'}/"
        album_title = f"{(stats.year[:30] + ' - ') if (stats.year and stats.album) else ''}" \
                      f"{'UNKNOWN,Singles' if not stats.album else stats.album.replace(':', '–')}".strip(
                      )
        print(_target_dir + album_title)
        target_dir = Path(_target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dir = target_dir / album_title
        try:
            dir.rename(target_dir)
        except FileExistsError as e:
            print(f"{e}: Album titled '{album_title} already exists")


def cleanup(dir: Path) -> None:
    if not dir.is_dir():
        return
    [cleanup(subdir) for subdir in dir.iterdir()]
    try:
        dir.rmdir()
    except:
        pass


if __name__ == "__main__":
    dirs = [("./" + str(dir)) for dir in Path(".").iterdir() if dir.is_dir()]
    print(f"Subdirectories here: {', '.join(dirs)}")
    p = Path(input("Path?  "))

    sort(p)
    cleanup(Path(p))
