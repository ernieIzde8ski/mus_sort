#!/bin/bash
python setup.py sdist bdist_wheel && {
    read -r -p "Upload to PyPI? " prompt
    if [[ $prompt == "Y" || $prompt == "y" || $prompt = "" ]]; then
            twine upload dist/**
    fi
}
rm -rf build/ && rm -rf dist/
