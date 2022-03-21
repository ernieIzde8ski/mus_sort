# mus_sort

A music sorting script in Python.

## Prerequisites

- Python 3.10
- run `python -m pip install tinytag`

## Usage

I usually git clone the entire project into Music/, but it'll work with just the Python file + relevant script if you don't mind an error line.

- Windows: click mus_sort.bat
- Linux: click mus_sort.sh
- else: `python mus_sort.py`

### Command-Line Arguments

To avoid having to punch in arguments to the terminal, you can use `-M`, `--mode` and `-P`, `--path` arguments the same way.

```text
[ernie@archiso Music]$ python mus_sort.py -P SOULSEEK_DOWNLOADS -M default
Subdirectories here: Folk Rock, Death-Thrash Metal, Hip-Hop, SOULSEEK_DOWNLOADS, ...

Default path: '.'
Default mode: '3'


Selected root: /home/ernie/Music/SOULSEEK_DOWNLOADS
Selected path: /home/ernie/Music/SOULSEEK_DOWNLOADS
Selected modes: remove_empty, rename_dirs

Crust Punk                Amebix                    1987 - Monolith          
Crust Punk                Amebix                    2000 - Arise!            
Crust Punk                Amebix                    1983 - Winter - Beginning of the End
Black-Thrash Metal        Sarcófago                 1989 - Rotting           
Black Metal               Totale Vernichtung        2012 - Die Pechschwarze Artillerie
Power Metal               Secret Sphere             1999 - Mistress of the Shadowlight
Power Metal               Fates Warning             1994 - Night on Bröcken  
Power Metal               Fates Warning             1985 - The Spectre Within
Thrash Metal              Flotsam and Jetsam        1986 - Doomsday for the Deceiver
Hard Rock                 Blue Öyster Cult          1972 - Blue Öyster Cult  
```
