

strategy=$(echo $1)

if ["$strategy" == ""]; then
    echo "Please provide a strategy as an argument."
    exit 1
fi


echo "Running agent with strategy: $strategy"

function get_strategy_hash() {
    strategy=$1
    echo $strategy
    hash=$(cat packages/packages.json | jq -r '.dev."custom/eightballer/portfolio_balancer/0.1.0"')
    echo $hash

    if [ "$hash" == "null" ]; then
        echo "Strategy not found in packages.json"
        exit 1
    fi

}


get_strategy_hash $strategy

export SKILL_IPFS_PACKAGE_DOWNLOADER_MODELS_PARAMS_ARGS_FILE_HASH_TO_I=$hash
# We create a a new var with the 
echo $SKILL_IPFS_PACKAGE_DOWNLOADER_MODELS_PARAMS_ARGS_FILE_HASH_TO_I

# We make a stringtemplate 


rm -r solana_trader
find . -empty -type d -delete  # remove empty directories to avoid wrong hashes
autonomy packages lock
python scripts/update_aea_strategy_hash.py packages/valory/agents/solana_trader/aea-config.yaml $hash
autonomy packages lock
autonomy push-all

autonomy fetch --local --agent valory/solana_trader && cd solana_trader || exit
# if running for the first time, replace the following two lines with: autonomy generate-key solana --add-key
cp "$PWD"/../ethereum_private_key.txt .  # replace with the path to your ethereum key
autonomy add-key ethereum ethereum_private_key.txt
cp "$PWD"/../solana_private_key.txt .  # replace with the path to your solana key
autonomy add-key solana solana_private_key.txt
autonomy issue-certificates
# aea -s install
aea -s run
