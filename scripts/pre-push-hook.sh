#! /bin/bash

set -e 

tox -e isort,black,pylint,mypy,flake8,safety,bandit -p

# Run the tests for abci.
tox -e check-packages 
tox -e check-abci-docstrings
tox -e check-handlers
tox -e analyse-service
tox -e check-abciapp-specs



make clean
autonomy packages lock
git add packages
git commit -m 'checkpoint: pre-push-hook at $(date)'

echo "Pre-push hook completed successfully."