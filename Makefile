PIP=pip3

init:
	$(PIP) install pipenv --upgrade
	pipenv install --dev --skip-lock


test:
	pipenv run tox


pylint:
	pipenv run pylint -E parrotfish


coverage:
	@echo "Coverage"
	pipenv run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=pydent tests