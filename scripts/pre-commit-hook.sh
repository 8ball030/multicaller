#! /bin/bash

set -e 

tox -e isort,black,pylint,mypy,flake8,safety,bandit -p

echo "Pre-push hook completed successfully."