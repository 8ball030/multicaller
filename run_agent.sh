rm -r solana_trader
find . -empty -type d -delete  # remove empty directories to avoid wrong hashes
autonomy packages lock
autonomy fetch --local --agent valory/solana_trader && cd solana_trader
cp $PWD/../solana_private_key.txt .
autonomy add-key ethereum solana_private_key.txt
autonomy issue-certificates
aea -s run