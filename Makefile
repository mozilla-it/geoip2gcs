format: geoupdate.py
	@poetry run isort $^
	@poetry run black $^

requirements.txt: poetry.lock
	@poetry export -o $@
