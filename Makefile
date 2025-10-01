.DEFAULT_GOAL := build
SHELL := /usr/bin/env -S bash -O globstar # makes work globs like **/*.py

sync:
	uv sync

build: linter sync test
	make clean
	uv build

publish: build
	UV_PUBLISH_TOKEN=$$(cat .pypi_token) uv publish

test: linter
	PYTHONWARNINGS=ignore PYTHONPATH=. uv -q run pytest -q

init: clean githook
	uv venv -q
	make sync

githook:
	echo -e "#!/bin/sh\nexec uv run -q pre-commit run --hook-stage manual" > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

clean:
	rm -rf .venv **/__pycache__ .python-version dist **/*.egg* *.lock build

linter: format
	uv sync --no-dev -q
	uv run ty check --respect-ignore-files trn/*.py
	uv run ruff check -q --ignore F401 **/*.py

format: sync
	uv run isort -q **/*.py
	uv run ruff format **/*.py

safety:
	uv run safety scan -o bare

readme:
	gsed -i'' '/^> trn --help/,$$d' README.md
	echo '> trn --help' >> README.md
	uv run -q --refresh --with . trn --help >> README.md
	echo '```' >> README.md
