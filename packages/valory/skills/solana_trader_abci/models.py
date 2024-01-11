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

"""Custom objects for the 'solana_trader_abci' application."""

from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.solana_trader_decision_maker_abci.models import SolanaTraderDecisionMakerParams
from packages.valory.skills.solana_trader_decision_maker_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.solana_trader_abci.composition import SolanaTraderAbciApp


from packages.valory.skills.market_data_fetcher_abci.models import (
    Params as MarketDataFetcherAbciParams,
)
from packages.valory.skills.market_data_fetcher_abci.rounds import (
    Event as MarketDataFetcherEvent,
)

from packages.valory.skills.solana_strategy_evaluator_abci.models import (
    Params as StrategyEvaluatorAbciParams,
)
from packages.valory.skills.solana_strategy_evaluator_abci.rounds import (
    Event as StrategyEvaluatorEvent,
)

from packages.valory.skills.solana_trader_decision_maker_abci.models import (
    Params as SolanaTraderDecisionMakerAbciParams,
)
from packages.valory.skills.solana_trader_decision_maker_abci.rounds import (
    Event as DecisionMakingEvent,
)


SolanaTraderDecisionMakerParams = SolanaTraderDecisionMakerAbciParams
MarketDataFetcherParams = MarketDataFetcherAbciParams
StrategyEvaluatorParams = StrategyEvaluatorAbciParams

Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class RandomnessApi(ApiSpecs):
    """A model for randomness api specifications."""




class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = SolanaTraderAbciApp

    def setup(self) -> None:
        """Set up."""
        super().setup()
        SolanaTraderAbciApp.event_to_timeout[
            DecisionMakingEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        SolanaTraderAbciApp.event_to_timeout[
            MarketDataFetcherEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        SolanaTraderAbciApp.event_to_timeout[
            StrategyEvaluatorEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds


class Params(
    SolanaTraderDecisionMakerParams,
    MarketDataFetcherParams,
    StrategyEvaluatorParams,
):
    """A model to represent params for multiple abci apps."""
