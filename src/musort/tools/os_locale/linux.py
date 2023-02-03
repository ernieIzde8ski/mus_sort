from pathlib import Path


REPLACEMENTS: dict[str, str] = {"/": "⁄"}
"""Character replacements to ensure file names don't break under Linux."""


def is_hidden(p: Path, /):
    return p.name.startswith(".")
