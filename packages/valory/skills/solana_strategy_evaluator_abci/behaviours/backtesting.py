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

"""This module contains the behaviour for backtesting the swap(s)."""

from typing import Generator

from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import VotingPayload
from packages.valory.skills.solana_strategy_evaluator_abci.states.backtesting import (
    BacktestRound,
)


class BacktestBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents backtest the swap(s)."""

    matching_round = BacktestRound

    def backtest(self) -> bool:
        """Backtest the swap(s) and decide whether we should proceed to perform them or not."""
        return True

    def async_act(self) -> Generator:
        """Do the action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            sender = self.context.agent_address
            # TODO fetch the swap(s) and pass them to the `backtest` method
            should_proceed = self.backtest()
            payload = VotingPayload(sender, should_proceed)

        yield from self.finish_behaviour(payload)
