# create virtual environment
PATH := .env/bin:$(PATH)

.env:
	virtualenv .env

# install all needed for development
develop: .env
	.env/bin/pip install -e .[full]

coverage: develop
	coverage run --source=pytest_cuke .env/bin/pytest tests
	coverage report -m

docs: .env
	.env/bin/pip install -e .[docs]
	.env/bin/sphinx-build -b html -W --keep-going docs docs/_build/html

test: develop
	tox

coveralls: coverage
	coveralls

# clean the development environment
clean:
	-rm -rf .env
