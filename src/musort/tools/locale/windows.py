# Firstly, I would like to say I don't remember who wrote the hidden function,
# but it was probably under the MIT license. I think that makes me clear?
# Secondly, Windows

import ctypes
from builtins import WindowsError
from pathlib import Path

REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("<", "≺"),
    (">", "≻"),
    ('"', "'"),
    ("/", "⁄"),
    ("|", "∣"),
    ("?", "﹖"),
    ("*", "⋆"),
    ("\\", ""),
)
"""Character replacements to ensure file names don't break under Windows."""


def is_hidden(p: Path, /):
    resp: int = ctypes.windll.kernel32.GetFileAttributesW(str(p))
    if resp == -1:
        raise WindowsError
    return resp & 2
