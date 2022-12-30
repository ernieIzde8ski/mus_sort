# musort

A music-sorting package.

## Installation

From PyPI:

```bash
python -m pip install -U musort
```

From source:

```sh
git clone https://github.com/ernieIzde8ski/mus_sort/tree/module_v2.git mus_sort
cd mus_sort
# just installing
python -m pip install -e .
# building (linux)
make init build
```

## Usage

See `python -m musort --help` for usage.

If found in the present working directory, configuration files named `musort-conf` or
`musort_conf` will be loaded. A sample is provided:

```sh
.
# reorganize by folder and rename tracks
--folder-mode --file-mode
# ignore FileExistsError
--replace-duplicates
# remove emptied directories afterwards
--clean-after
# make sure each artist is not split across multiple folders
--single-genre
```
