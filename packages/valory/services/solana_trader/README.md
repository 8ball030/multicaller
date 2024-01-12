## Solana Trader

A trading service which:
1. Dynamically loads all the available trading strategies implemented as Custom Components. 
2. Selects a strategy to run
3. Fetches the tokens' data required for the strategy
4. Runs the strategy for each pair of tokens
5. Prepares swap instructions based on the decisions of the strategy
6. Submits the transactions on chain
