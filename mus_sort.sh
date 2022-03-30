#!/bin/bash
git pull
export PYTHONIOENCODING=utf8
python mus_sort.py $1
read -n 1 -s -r -p "Press any key to continue"
echo -e "\n"
