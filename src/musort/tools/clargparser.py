import logging
import sys
from pathlib import Path

from tap import ArgumentError, Tap

from .. import info

DEFAULT_IGNORED = (".git", "itunes")


class ClargParser(Tap):
    dirs: list[Path]
    """Folder to sort from."""
    target: Path
    """Folder sorted into.
    If not present, defaults to the folder containing the first config file found, or the
    folder being sorted from if no config files were found."""

    folder_mode: bool = False
    """Sort by moving entire folders around at a time. Useful if your music is already sorted per-album."""
    file_mode: bool = False
    """Sort by moving individual music files around. Highly disrecommended if your metadata is
    inconsistent, or if you don't want to risk leaving album covers and the like behind.

    Alternatively, when used in conjunction with folder-mode, files are renamed within their folders.
    """

    level: int = logging.INFO
    """Logging level. Accepts names from the logging module, eg 'debug' or 'info'."""
    ignored_paths: set[str] = set()
    """Ignored file/folder names. Case insensitive."""

    hidden: bool = False
    """Operate through hidden files & folders."""
    symlinks: bool = False
    """Operate through symlinks. Untested, so probably buggy."""

    clean_after: bool = False
    """Delete empty folders afterwards."""
    replace_duplicates: bool = False
    """Replace existing paths upon FileExistsError. If artist or album is None, the replacement is ignored."""
    single_genre: bool = False
    """Force any given artist to stay in one genre folder."""
    use_dashes: bool = False
    """Replace slashes with dashes in paths."""


    def _load_from_config_files(self, config_files: list[str] | None):
        "override to save config file list to a private attribute"
        self.config_files: list[str] = config_files if config_files else list()
        return super()._load_from_config_files(config_files=config_files)

    @staticmethod
    def _get_level(name: str):
        """Get logging level from a string."""
        if name.isnumeric():
            num = int(name)
            if num in logging._levelToName:
                return num
        else:
            name = name.upper()
            if name in logging._nameToLevel:
                return logging._nameToLevel[name]
        raise ValueError(f"Name '{name}' is not a valid level!")

    def configure(self) -> None:
        self.add_argument(
            "-V", "--version", action="version", version=f"musort v{info.__version__}"
        )

        # making the first argument positional, the second unrequired
        self.add_argument("dirs", nargs='+')
        self.add_argument("-T", "--target", required=False)

        # logging module weirdness
        self.add_argument("-l", "--level", type=self._get_level, choices=(logging._levelToName))

        # providing aliases
        self.add_argument("-i", "--ignored_paths")
        self.add_argument("-H", "--hidden")
        self.add_argument("-C", "--clean_after")
        self.add_argument("-S", "--single_genre")

    def process_args(self) -> None:
        # ensure given directories exist
        if not self.dirs:
            raise ArgumentError(None, "")
        if self.target is None:
            if self.config_files:
                self.target = Path(self.config_files[0]).parent
            else:
                self.target = self.dirs[0]

        if not self.target.is_dir():
            raise ArgumentError(
                None, "target parameter must be a valid directory! got: " + str(self.target)
            )

        # making case insensitive
        self.ignored_paths = {*(i.lower() for i in self.ignored_paths), *DEFAULT_IGNORED}

        # ensure at least one sort method is chosen
        if not (self.file_mode or self.folder_mode):
            raise ArgumentError(None, "Either --file-mode or --folder-mode should be active")


_VALID_CONFIGS = ("musort_conf", "musort-conf", "musort.txt", "mus_sort.txt")


def find_config_file(folder: Path = Path.cwd()) -> Path | None:
    for config_name in _VALID_CONFIGS:
        path = folder / config_name
        if path.is_file():
            return path

    # for root directory, path.parent == path
    if folder.parent != folder:
        return find_config_file(folder.parent)


config = find_config_file()
clargs = ClargParser(
    underscores_to_dashes=True,
    config_files=[str(config)] if config else None,
    epilog=(
        "This program sorts folders based on ID3 data. "
        "So, if the tags on your music are unruly, "
        "it's probably best to sort that out first."
    ),
).parse_args()

logging.basicConfig(level=clargs.level, stream=sys.stdout)

logging.debug(f"current command-line arguments:\n{clargs}")
