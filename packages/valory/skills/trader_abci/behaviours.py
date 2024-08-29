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

"""This module contains the behaviours for the trader skill."""

from typing import Set, Type

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.market_data_fetcher_abci.behaviours import (
    MarketDataFetcherRoundBehaviour,
)
from packages.valory.skills.portfolio_tracker_abci.behaviours import (
    PortfolioTrackerRoundBehaviour,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.strategy_evaluator_abci.behaviours.round_behaviour import (
    AgentStrategyEvaluatorRoundBehaviour,
)
from packages.valory.skills.trader_abci.composition import TraderAbciApp
from packages.valory.skills.trader_decision_maker_abci.behaviours import (
    TraderDecisionMakerRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)


class TraderConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the trader."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = TraderAbciApp

    behaviours: Set[Type[BaseBehaviour]] = {
        *AgentRegistrationRoundBehaviour.behaviours,
        *TraderDecisionMakerRoundBehaviour.behaviours,
        *MarketDataFetcherRoundBehaviour.behaviours,
        *PortfolioTrackerRoundBehaviour.behaviours,
        *AgentStrategyEvaluatorRoundBehaviour.behaviours,
        *TransactionSettlementRoundBehaviour.behaviours,  # TODO
        *ResetPauseABCIConsensusBehaviour.behaviours,
    }
