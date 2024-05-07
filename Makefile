install: pyproject.toml poetry.lock
	@poetry install

format: geoip2gcs/
	@poetry run isort $^
	@poetry run black $^

requirements.txt: poetry.lock
	@poetry export -o $@

v$(shell poetry version --short).zip: requirements.txt $(shell find geoip2gcs -name __pycache__ -prune -o -print)
	@rm -f $@
	@zip $@ $^
