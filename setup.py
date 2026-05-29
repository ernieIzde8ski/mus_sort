#!/usr/bin/env python3

import re
from collections.abc import Iterable
from pathlib import Path

from setuptools import find_packages, setup  # pyright: ignore[reportUnknownVariableType]

requirements: Iterable[str]
version: str

with open("requirements.txt") as file:
    # we use str.splitlines instead of TextIOWrapper.readlines because it strips trailing newlines
    requirements = file.read().splitlines()

with open("src/musort/info.py") as file:
    # pattern "borrowed" from discord.py (with permission)
    match = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', file.read(), re.MULTILINE
    )
    if match is None:
        raise RuntimeError("couldn't grep __version__ from info file")
    version = match[1]

readme = Path("README.md").read_text()

_ = setup(
    name="musort",
    author="Ernest Izdebski",
    url="https://github.com/ernieIzde8ski/mus_sort",
    version=version,
    packages=find_packages("src"),
    package_dir={"": "src"},
    license="MIT",
    description="A music-sorting package.",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.9.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    entry_points={"console_scripts": ["musort = musort.app:run"]},
)
