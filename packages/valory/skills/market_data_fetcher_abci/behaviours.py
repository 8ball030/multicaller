# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This package contains round behaviours of MarketDataFetcherAbciApp."""

import json
import os
from abc import ABC
from typing import Any, Callable, Dict, Generator, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.market_data_fetcher_abci.models import Coingecko, Params
from packages.valory.skills.market_data_fetcher_abci.payloads import (
    TransformedMarketDataPayload,
)
from packages.valory.skills.market_data_fetcher_abci.rounds import (
    FetchMarketDataRound,
    MarketDataFetcherAbciApp,
    MarketDataPayload,
    SynchronizedData,
    TransformMarketDataRound,
)


HTTP_OK = [200, 201]
MAX_RETRIES = 3
MARKETS_FILE_NAME = "markets.json"
TOKEN_ID_FIELD = "coingecko_id"  # nosec: B105:hardcoded_password_string
TOKEN_ADDRESS_FIELD = "address"  # nosec: B105:hardcoded_password_string
UTF8 = "utf-8"
STRATEGY_KEY = "trading_strategy"
ENTRY_POINT_STORE_KEY = "entry_point"
TRANSFORM_CALLABLE_STORE_KEY = "transform_callable"


class MarketDataFetcherBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the market_data_fetcher_abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)

    @property
    def coingecko(self) -> Coingecko:
        """Return the Coingecko."""
        return cast(Coingecko, self.context.coingecko)

    def from_data_dir(self, path: str) -> str:
        """Return the given path appended to the data dir."""
        return os.path.join(self.context.data_dir, path)

    def _request_with_retries(
        self,
        endpoint: str,
        rate_limited_callback: Callable,
        method: str = "GET",
        body: Optional[Any] = None,
        headers: Optional[Dict] = None,
        rate_limited_code: int = 429,
        max_retries: int = MAX_RETRIES,
        retry_wait: int = 0,
    ) -> Generator[None, None, Tuple[bool, Dict]]:
        """Request wrapped around a retry mechanism"""

        self.context.logger.info(f"HTTP {method} call: {endpoint}")
        content = json.dumps(body).encode(UTF8) if body else None

        retries = 0
        while True:
            # Make the request
            response = yield from self.get_http_response(
                method, endpoint, content, headers
            )

            try:
                response_json = json.loads(response.body)
            except json.decoder.JSONDecodeError as exc:
                self.context.logger.error(f"Exception during json loading: {exc}")
                response_json = {"exception": str(exc)}

            if response.status_code == rate_limited_code:
                rate_limited_callback()

            if response.status_code not in HTTP_OK or "exception" in response_json:
                self.context.logger.error(
                    f"Request failed [{response.status_code}]: {response_json}"
                )
                retries += 1
                if retries == max_retries:
                    break
                yield from self.sleep(retry_wait)
                continue

            self.context.logger.info("Request succeeded.")
            return True, response_json

        self.context.logger.error(f"Request failed after {retries} retries.")
        return False, response_json


class FetchMarketDataBehaviour(MarketDataFetcherBaseBehaviour):
    """FetchMarketDataBehaviour"""

    matching_round: Type[AbstractRound] = FetchMarketDataRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            data_hash = yield from self.fetch_markets()
            sender = self.context.agent_address
            payload = MarketDataPayload(sender=sender, data_hash=data_hash)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def fetch_markets(self) -> Generator[None, None, Optional[str]]:
        """Fetch markets from Coingecko and send to IPFS"""

        markets = {}
        headers = {
            "Accept": "application/json",
        }
        if self.coingecko.api_key:
            headers["x-cg-pro-api-key"] = self.coingecko.api_key

        # Get the market data for each token
        for token_data in self.params.token_symbol_whitelist:
            token_id = token_data.get(TOKEN_ID_FIELD, None)
            token_address = token_data.get(TOKEN_ADDRESS_FIELD, None)

            if not token_id or not token_address:
                err = f"Token id or address missing in whitelist's {token_data=}."
                self.context.logger.error(err)
                continue

            warned = False
            while not self.coingecko.rate_limiter.check_and_burn():
                if not warned:
                    self.context.logger.warning(
                        "Rate limiter activated. "
                        "To avoid this in the future, you may consider acquiring a Coingecko API key,"
                        "and updating the `Coingecko` model's overrides.\n"
                        "Cooling down..."
                    )
                warned = True
                yield from self.sleep(self.params.sleep_time)

            if warned:
                self.context.logger.info("Cooldown period passed :)")

            remaining_limit = self.coingecko.rate_limiter.remaining_limit
            remaining_credits = self.coingecko.rate_limiter.remaining_credits
            self.context.logger.info(
                "Local rate limiter's check passed. "
                f"After the call, you will have {remaining_limit=} and {remaining_credits=}."
            )
            success, response_json = yield from self._request_with_retries(
                endpoint=self.coingecko.endpoint.format(token_id=token_id),
                headers=headers,
                rate_limited_code=self.coingecko.rate_limited_code,
                rate_limited_callback=self.coingecko.rate_limited_status_callback,
                retry_wait=self.params.sleep_time,
            )

            # Skip failed markets. The strategy will need to verify market availability
            if not success:
                self.context.logger.error(
                    f"Failed to fetch market data for {token_id}."
                )
                continue

            self.context.logger.info(
                f"Successfully fetched market data for {token_id}."
            )
            # we collect a tuple of the prices and the volumes

            prices = response_json.get(self.coingecko.prices_field, [])
            volumes = response_json.get(self.coingecko.volumes_field, [])
            prices_volumes = {"prices": prices, "volumes": volumes}
            markets[token_address] = prices_volumes

        # Send to IPFS
        data_hash = None
        if markets:
            data_hash = yield from self.send_to_ipfs(
                filename=self.from_data_dir(MARKETS_FILE_NAME),
                obj=markets,
                filetype=SupportedFiletype.JSON,
            )
            self.context.logger.info(
                f"Market file stored in IPFS. Hash is {data_hash}."
            )

        return data_hash


class TransformMarketDataBehaviour(MarketDataFetcherBaseBehaviour):
    """Behaviour to transform the fetched signals."""

    matching_round: Type[AbstractRound] = TransformMarketDataRound

    def strategy_store(self, strategy_name: str) -> Dict[str, str]:
        """Get the stored strategy's files."""
        return self.context.shared_state.get(strategy_name, {})

    def execute_strategy_transformation(
        self, *args: Any, **kwargs: Any
    ) -> Dict[str, Any] | None:
        """Execute the strategy's transform method and return the results."""
        trading_strategy = kwargs.pop(STRATEGY_KEY, None)
        if trading_strategy is None:
            self.context.logger.error(f"No {STRATEGY_KEY!r} was given!")
            return None

        store = self.strategy_store(trading_strategy)
        strategy_exec = store.get(ENTRY_POINT_STORE_KEY, None)
        if strategy_exec is None:
            self.context.logger.error(
                f"No executable was found for {trading_strategy=}! Did the IPFS package downloader load it correctly?"
            )
            return None

        callable_method = store.get(TRANSFORM_CALLABLE_STORE_KEY, None)
        if callable_method is None:
            self.context.logger.error(
                "No transform callable was found in the loaded component! "
                "Did the IPFS package downloader load it correctly?"
            )
            return None

        if callable_method in globals():
            del globals()[callable_method]

        exec(strategy_exec, globals())  # pylint: disable=W0122  # nosec
        method = globals().get(callable_method, None)
        if method is None:
            self.context.logger.error(
                f"No {callable_method!r} method was found in {trading_strategy} strategy's executable:\n"
                f"{strategy_exec}."
            )
            return None
        return method(*args, **kwargs)

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            data_hash = yield from self.transform_data()
            sender = self.context.agent_address
            payload = TransformedMarketDataPayload(
                sender=sender, transformed_data_hash=data_hash
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def transform_data(
        self,
    ) -> Generator[None, None, Optional[str]]:
        """Transform the data to OHLCV format."""
        markets_data = yield from self.get_from_ipfs(
            self.synchronized_data.data_hash, SupportedFiletype.JSON
        )
        markets_data = cast(Dict[str, Dict[str, Any]], markets_data)
        results = {}

        strategy = self.synchronized_data.selected_strategy
        for token_address, market_data in markets_data.items():
            kwargs = {STRATEGY_KEY: strategy, **market_data}
            result = self.execute_strategy_transformation(**kwargs)
            if result is None:
                self.context.logger.error(
                    f"Failed to transform market data for {token_address}."
                )
                continue
            results[token_address] = result['transformed_data']

        data_hash = yield from self.send_to_ipfs(
            filename=self.from_data_dir(MARKETS_FILE_NAME),
            obj=results,
            filetype=SupportedFiletype.JSON,
        )
        return data_hash


class MarketDataFetcherRoundBehaviour(AbstractRoundBehaviour):
    """MarketDataFetcherRoundBehaviour"""

    initial_behaviour_cls = FetchMarketDataBehaviour
    abci_app_cls = MarketDataFetcherAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        FetchMarketDataBehaviour,  # type: ignore
        TransformMarketDataBehaviour,  # type: ignore
    }
