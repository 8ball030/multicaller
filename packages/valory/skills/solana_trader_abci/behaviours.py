# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
from packages.valory.skills.solana_trader_decision_maker_abci.behaviours.round_behaviour import (
    SolanaTraderDecisionMakerRoundBehaviour,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.termination_abci.behaviours import (
    BackgroundBehaviour,
    TerminationAbciBehaviours,
)
from packages.valory.skills.solana_trader_abci.composition import SolanaTraderAbciApp
from packages.valory.skills.solana_transaction_settlement_abci.behaviours import (
    SolanaTransactionSettlementRoundBehaviour,
)
from packages.valory.skills.market_data_fetcher_abci.behaviours import (
    MarketDataFetcherRoundBehaviour
)
from packages.valory.skills.strategy_evaluator_abci.behaviours import (
    StrategyEvaluatorRoundBehaviour
)


class SolanaTraderConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the solana_trader."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = SolanaTraderAbciApp

    behaviours: Set[Type[BaseBehaviour]] = {
        *AgentRegistrationRoundBehaviour.behaviours,
        *SolanaTraderDecisionMakerRoundBehaviour.behaviours,
        *MarketDataFetcherRoundBehaviour.behaviours,
        *StrategyEvaluatorRoundBehaviour.behaviours,
        *SolanaTransactionSettlementRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
        *TerminationAbciBehaviours.behaviours,
    }
    background_behaviours_cls = {BackgroundBehaviour}  # type: ignore
