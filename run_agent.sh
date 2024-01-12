rm -r solana_trader
find . -empty -type d -delete  # remove empty directories to avoid wrong hashes
autonomy packages lock
autonomy fetch --local --agent valory/solana_trader && cd solana_trader || exit
# if running for the first time, replace the following two lines with: autonomy generate-key solana --add-key
cp "$PWD"/../solana_private_key.txt .  # replace with the path to your solana key
autonomy add-key solana solana_private_key.txt
autonomy issue-certificates
aea -s run
