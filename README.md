<p align="center">
   <img src="./docs/images/solana-trader-logo.svg" width=300>
</p>

<h1 align="center" style="margin-bottom: 0;">
    Solana Trader Service
    <br /><sub>An autonomous trader service on Jupiter</sub>
    <br />
    <a href="https://github.com/valory-xyz/solana-trader/blob/main/LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/github/license/valory-xyz/solana-trader"></a>
    <a href="https://docs.docker.com/compose/"><img alt="Deployment: Docker Compose" src="https://img.shields.io/badge/deployment-Docker%20Compose-blue"></a>
    <a href="https://pypi.org/project/open-autonomy/"><img alt="Framework: Open Autonomy" src="https://img.shields.io/badge/framework-Open%20Autonomy-blueviolet"></a>
    <!-- <a href="https://github.com/valory-xyz/open-operator/releases/latest">
    <img alt="Latest release" src="https://img.shields.io/github/v/release/valory-xyz/open-operator"></a> -->
</h1>

The Solana Trader is an autonomous service built with the [Open Autonomy framework](https://docs.autonolas.network/open-autonomy/) which automatically execute token swaps on Solana's swap aggregator [Jupiter](https://jup.ag/).

## How it works

The service continuously runs the following loop:

1. Retrieve price information on supported tokens from [CoinGecko](https://www.coingecko.com/).
2. Select one strategy from the available ones.
3. Apply the selected strategy to all supported token pairs.
4. Execute the needed swaps.

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

## Build a custom strategy

Trading strategies are located on the `./strategies` folder within the repository. Each strategy is defined as a package contianing a `component.yaml` configuration file and a number of additional python files which encode the business logic of the strategy. The `component.yaml` configuration file must define:

1. `entry_point`: The name of the file which contains the main entry point of the strategy.
2. `callable`: Name of the entry point method (typically `run`).

The outline of the main entry point method of a strategy is as follows:

```python
def run(*_args: Any, **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
    # Read and process the required arguments for this strategy, e.g.,
    result = _process(price_data array, ...)

    # Return the strategy output as a JSON object, e.g.,
    if result > 0:
        return {"signal": "buy"}
    elif result < 0:
        return {"signal": "sell"}
    
    return {"signal": "hold"}
```

You can take a look at the [trend following strategy](./strategies/trend_following_strategy/trend_following_strategy.py) as an example.

In order to use your strategy, you must:

1. Push the package to the IPFS

    ```bash
    cd strategies/your_strategy
    autonomy ipfs add

    > Processing package: /.../solana-trader/strategies/your_strategy
    > Added: `your_strategy`, hash is <your_strategy_hash>
    ```

2. Override the environment variable `FILE_HASH_TO_ID` to include your strategy:

    ```bash
    export FILE_HASH_TO_ID=[["<your_strategy_hash>", ["your_strategy"]], ..., ["bafybeiav273ufxg6743rzxkxpx7vzl742prjovngflxlugawxfkz6dhfhi",["follow_trend_strategy"]]]
    ``````

    Alternatively, you can also modify the parameter `file_hash_to_id` in the file [`service.yaml`](./packages/valory/services/solana_trader/service.yaml).

3. Run your service.
