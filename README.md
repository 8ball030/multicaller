## Solana trader service

Solana-trader is an autonomous service that performs swaps on [Jupiter](https://jup.ag/). Its workflow is as follows:

1. Retrieve price information on supported tokens from [CoinGecko](https://www.coingecko.com/).
2. Select one strategy from the available ones.
3. Apply the selected strategy to all supported token pairs.
4. Execute the needed swaps.
6. Repeat these steps continuously.

## Prepare the environment

- System requirements:

  - Python `== 3.10`
  - [Poetry](https://python-poetry.org/docs/) `>=1.4.0`
  - [Docker Engine](https://docs.docker.com/engine/install/)
  - [Docker Compose](https://docs.docker.com/compose/install/)

- Clone this repository:

      git clone https://github.com/valory-xyz/solana-trader.git

- Create a development environment:

      poetry install && poetry shell

- Configure the Open Autonomy framework:

      autonomy init --reset --author valory --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"

- Pull packages required to run the service:

      autonomy packages sync --update-packages


## Prepare the keys, the multisig account and export environment variables

You need a **Solana keypair** and a **[Squads](https://v3.squads.so/) address** to run the service.

First, prepare the `keys.json` file with the Gnosis keypair of your agent. (Replace the uppercase placeholders below):

    cat > keys.json << EOF
    [
    {
        "address": "YOUR_AGENT_ADDRESS",
        "private_key": "YOUR_AGENT_PRIVATE_KEY"
    }
    ]
    EOF

Then, create an .env file with the needed environment variables:
```bash
ALL_PARTICIPANTS='["YOUR_AGENT_ADDRESS"]'
```

## Run the service

Once you have configured (exported) the environment variables, you are in position to run the service.

```bash
bash run_service.sh
```