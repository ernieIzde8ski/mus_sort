#!/usr/bin/env python3

from pathlib import Path
import re
from typing import Iterable
from setuptools import find_packages, setup

requirements: Iterable[str]
with open("requirements.txt", "r") as file:
    # we use str.splitlines instead of TextIOWrapper.readlines because it strips trailing newlines
    requirements = file.read().splitlines()

with open("src/musort/info.py", "r") as file:
    # pattern "borrowed" from discord.py (with permission)
    version: str = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', file.read(), re.MULTILINE)[1]  # type: ignore

readme = Path("README.md").read_text()

setup(
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
    scripts=["musort"],
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
)
