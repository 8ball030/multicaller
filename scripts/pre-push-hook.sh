#! /bin/bash

set -e 

# We assume we have run linters and tests locally in the pre-commit hook.
# tox -e isort,black,pylint,mypy,flake8,safety,bandit -p 

# Run the tests for abci.
tox -e check-hash,check-packages,check-abci-docstrings,check-handlers,analyse-service,check-abciapp-specs


tomte check-copyright --author valory --exclude-part abci --exclude-part http_client --exclude-part ipfs --exclude-part ledger --exclude-part p2p_libp2p_client --exclude-part gnosis_safe_proxy_factory --exclude-part multisend --exclude-part gnosis_safe --exclude-part service_registry --exclude-part protocols --exclude-part abstract_abci --exclude-part abstract_round_abci --exclude-part registration_abci --exclude-part reset_pause_abci --exclude-part solana_transaction_settlement_abci --exclude-part transaction_settlement_abci

autonomy packages lock
echo "Pre-push hook completed successfully."
# Check if there are any changes to packages/packages.json

function check_changes() {
    if [ -n "$(git status --porcelain)" ]; then
        echo "Changes detected in packages/packages.json. Please run 'autonomy packages lock' and push again."
        exit 1
    fi
}

make clean-pyc && autonomy push-all