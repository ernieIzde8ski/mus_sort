# Firstly, I would like to say I don't remember who wrote the hidden function,
# but it was probably under the MIT license. I think that makes me clear?
# Secondly, Windows

import ctypes
from pathlib import Path

__all__ = ["REPLACEMENTS", "is_hidden"]

REPLACEMENTS: dict[str, str] = {
    "<": "≺",
    ">": "≻",
    '"': "'",
    "/": "⁄",
    "|": "∣",
    "?": "﹖",
    "*": "⋆",
    "\\": "",
}
"""Character replacements to ensure file names don't break under Windows."""


def is_hidden(p: Path, /):
    resp: int = ctypes.windll.kernel32.GetFileAttributesW(str(p))
    if resp == -1:
        raise OSError
    return resp & 2
