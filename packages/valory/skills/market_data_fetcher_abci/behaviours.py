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
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.market_data_fetcher_abci.models import Params
from packages.valory.skills.market_data_fetcher_abci.rounds import (
    FetchMarketDataPayload,
    FetchMarketDataRound,
    MarketDataFetcherAbciApp,
    SynchronizedData,
    VerifyMarketDataPayload,
    VerifyMarketDataRound,
)


HTTP_OK = [200, 201]
MAX_RETRIES = 3
MARKETS_FILE_NAME = "markets.json"


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

    def from_data_dir(self, path: str) -> str:
        """Return the given path appended to the data dir."""
        return os.path.join(self.context.data_dir, path)

    def _request_with_retries(
        self,
        endpoint,
        method="GET",
        body=None,
        headers=None,
        max_retries=MAX_RETRIES,
        retry_wait=0,
    ):
        """Request wrapped around a retry mechanism"""

        self.context.logger.info(f"HTTP {method} call: {endpoint}")

        kwargs = dict(
            method=method,
            url=endpoint,
        )

        if body:
            kwargs["content"] = json.dumps(body).encode("utf-8")

        if headers:
            kwargs["headers"] = headers

        retries = 0
        response_json = {}

        while retries < max_retries:
            # Make the request
            response = yield from self.get_http_response(**kwargs)

            try:
                response_json = json.loads(response.body)
            except json.decoder.JSONDecodeError as exc:
                self.context.logger.error(f"Exception during json loading: {exc}")
                response_json = {"exception": str(exc)}

            if response.status_code not in HTTP_OK or "exception" in response_json:
                self.context.logger.error(
                    f"Request failed [{response.status_code}]: {response_json}"
                )
                retries += 1
                yield from self.sleep(retry_wait)
                continue
            else:
                self.context.logger.info("Request succeeded")
                return True, response_json

        self.context.logger.error(f"Request failed after {max_retries} retries")
        return False, response_json


class FetchMarketDataBehaviour(MarketDataFetcherBaseBehaviour):
    """FetchMarketDataBehaviour"""

    matching_round: Type[AbstractRound] = FetchMarketDataRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            data_hash = yield from self.fetch_markets()
            sender = self.context.agent_address
            payload = FetchMarketDataPayload(sender=sender, data_hash=data_hash)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def fetch_markets(self):
        """Fetch markets from Coingecko and send to IPFS"""

        markets = {}
        headers = {
            "x-cg-pro-api-key": self.params.coingecko_api_key,
            "Accept": "application/json",
        }

        # Get the market data for each token
        for token_data in self.params.token_symbol_whitelist:
            token_id = token_data.get("coingecko", None)

            if not token_id:
                self.context.logger.error(
                    f"No token_id set for Coingecko in {token_data}"
                )

            success, response_json = yield from self._request_with_retries(
                endpoint=self.params.format(token_id=token_id), headers=headers
            )

            # Skip failed markets. The strategy will need to verify market availability
            if not success:
                self.context.logger.error(f"Failed to fecth market for {token_id}")
                continue

            self.context.logger.info(f"Succesfully fecthed market for {token_id}")

            # We use Jupiter symbol as the market key
            markets[token_data["jupiter"]] = response_json["prices"]

        # Send to IPFS
        data_hash = yield from self.send_to_ipfs(
            filename=self.from_data_dir(MARKETS_FILE_NAME),
            obj=markets,
            filetype=SupportedFiletype.JSON,
        )

        # TODO: handle data_hash=None
        self.context.logger.info(f"Market file stored in IPFS. Hash is {data_hash}")

        return data_hash


class MarketDataFetcherRoundBehaviour(AbstractRoundBehaviour):
    """MarketDataFetcherRoundBehaviour"""

    initial_behaviour_cls = FetchMarketDataBehaviour
    abci_app_cls = MarketDataFetcherAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = [
        FetchMarketDataBehaviour,
    ]
