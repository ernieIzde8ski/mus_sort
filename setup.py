import pathlib
import re
from typing import Iterable
from setuptools import find_packages, setup

requirements: Iterable[str]
with open("requirements.txt") as file:
    requirements = [i for i in file.read().splitlines() if not i.startswith("-")]

version: str
with open("musort/info.py") as file:
    # pattern "borrowed" from discord.py (with permission)
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', file.read(), re.MULTILINE)[1]


readme = pathlib.Path("README.md").read_text()


setup(
    name="musort",
    author="Ernest Izdebski",
    url="https://github.com/ernieIzde8ski/mus_sort",
    version=version,
    packages=find_packages(),
    license="MIT",
    description="A music-sorting package.",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=list(requirements),
    python_requires=">=3.9.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
