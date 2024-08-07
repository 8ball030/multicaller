#! /bin/bash

set -e 

tox -e isort,black,pylint,mypy,flake8,safety,bandit -p

# Run the tests for abci.
tox -e check-packages,check-abci-docstrings,check-handlers,analyse-service,check-abciapp-specs


autonomy packages lock
git add packages
echo "Pre-push hook completed successfully."