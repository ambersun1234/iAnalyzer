style-check:
	@black --check --diff --color .
	@isort -c .

style-fix:
	@black .
	@isort .

docker-build:
	@docker build -t ianalyzer .

docker-run:
	@docker run -it --rm ianalyzer --domain ambersuncreates.com --ignore-prefix https://ambersuncreates.com/tags --ignore-prefix https://ambersuncreates.com/categories

.PHONY: style-check style-fix docker-build docker-run
