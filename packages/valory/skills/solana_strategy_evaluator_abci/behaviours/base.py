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

"""This module contains the base behaviour for the 'solana_strategy_evaluator_abci' skill."""

from abc import ABC
from pathlib import Path
from typing import Any, Generator, cast

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.solana_strategy_evaluator_abci.models import (
    SharedState,
)
from packages.valory.skills.solana_strategy_evaluator_abci.models import StrategyEvaluatorParams
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import SynchronizedData

SWAP_DECISION_FILENAME = "swap_decision.json"


def wei_to_native(wei: int) -> float:
    """Convert WEI to native token."""
    return wei / 10 ** 18


class StrategyEvaluatorBaseBehaviour(BaseBehaviour, ABC):
    """Represents the base class for the strategy evaluation FSM behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the bet placement behaviour."""
        super().__init__(**kwargs)
        self.swap_decision_filepath = Path(self.context.data_dir) / SWAP_DECISION_FILENAME
        self.token_balance = 0
        self.wallet_balance = 0

    @property
    def params(self) -> StrategyEvaluatorParams:
        """Return the params."""
        return cast(StrategyEvaluatorParams, self.context.params)

    @property
    def shared_state(self) -> SharedState:
        """Get the shared state."""
        return cast(SharedState, self.context.state)

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return SynchronizedData(super().synchronized_data.db)

    def finish_behaviour(self, payload: BaseTxPayload) -> Generator:
        """Finish the behaviour."""
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()
