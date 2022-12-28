help:
	@echo 'usage: make <init|build|upload>'

init: requirements-dev.txt requirements.txt
	python3 -m venv venv
	./venv/bin/pip3 install -r requirements-dev.txt

build: setup.py musort/info.py
	rm -r build/ dist/
	python3 setup.py sdist bdist_wheel

upload: build/ dist/
	twine upload dist/**
