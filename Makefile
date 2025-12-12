style-check:
	@black --check --diff --color .
	@isort -c .

style-fix:
	@black .
	@isort .

.PHONY: style-check style-fix
