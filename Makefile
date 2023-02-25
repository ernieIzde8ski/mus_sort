help:
	@echo 'usage: make <init|build|upload>'

init: requirements-dev.txt requirements.txt
	-rm -r venv/
	-rm -r .git/hooks/*
	python3 -m venv venv
	./venv/bin/pip3 install -r requirements-dev.txt
	ln -rs .git-hooks/* .git/hooks/

build: setup.py src/musort/info.py
	-rm -r build/ dist/
	python3 setup.py sdist bdist_wheel

upload: build/ dist/
	twine upload dist/**
