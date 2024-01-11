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

"""This module contains the shared state for the abci skill of MarketDataFetcherAbciApp."""

from typing import Any, Dict, List

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.market_data_fetcher_abci.rounds import (
    MarketDataFetcherAbciApp,
)


def format_whitelist(token_whitelist: List) -> List:
    """Load the token whitelist into its proper format"""
    fixed_whitelist = []
    for element in token_whitelist:
        token_config = {}
        for i in element.split("&"):
            key, value = i.split("=")
            token_config[key] = value
        fixed_whitelist.append(token_config)
    return fixed_whitelist


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = MarketDataFetcherAbciApp


class Params(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.token_symbol_whitelist: List[Dict] = format_whitelist(
            self._ensure("token_symbol_whitelist", kwargs, List[str])
        )
        self.coingecko_api_key: str = self._ensure("coingecko_api_key", kwargs, str)
        self.coingecko_market_endpoint: str = self._ensure(
            "coingecko_market_endpoint", kwargs, str
        )
        super().__init__(*args, **kwargs)


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
