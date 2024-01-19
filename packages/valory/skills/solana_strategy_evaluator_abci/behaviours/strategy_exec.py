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

"""This module contains the behaviour for executing a strategy."""

from typing import Any, Dict, Generator, List, Optional, Tuple

from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.strategy_exec import (
    StrategyExecRound,
)


STRATEGY_KEY = "trading_strategy"
PRICE_DATA_KEY = "price_data"
SWAP_DECISION_FIELD = "signal"
BUY_DECISION = "buy"
SELL_DECISION = "sell"
HODL_DECISION = "hold"
AVAILABLE_DECISIONS = (BUY_DECISION, SELL_DECISION, HODL_DECISION)
NO_SWAP_DECISION = {SWAP_DECISION_FIELD: HODL_DECISION}
SUPPORTED_STRATEGY_LOG_LEVELS = ("info", "warning", "error")


class StrategyExecBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents execute the selected strategy and decide on the swap(s)."""

    matching_round = StrategyExecRound

    def strategy_exec(self, strategy_name: str) -> Optional[Tuple[str, str]]:
        """Get the executable strategy's contents."""
        return self.shared_state["downloaded_ipfs_packages"].get(strategy_name, None)

    def execute_strategy(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute the strategy and return the results."""
        trading_strategy = kwargs.pop(STRATEGY_KEY, None)
        if trading_strategy is None:
            self.context.logger.error(f"No {trading_strategy!r} was given!")
            return NO_SWAP_DECISION

        strategy = self.strategy_exec(trading_strategy)
        if strategy is None:
            self.context.logger.error(
                f"No executable was found for {trading_strategy=}!"
            )
            return NO_SWAP_DECISION

        strategy_exec, callable_method = strategy
        if callable_method in globals():
            del globals()[callable_method]

        exec(strategy_exec, globals())  # pylint: disable=W0122  # nosec
        method = globals().get(callable_method, None)
        if method is None:
            self.context.logger.error(
                f"No {callable_method!r} method was found in {trading_strategy} strategy's executable:\n"
                f"{strategy_exec}."
            )
            return NO_SWAP_DECISION

        return method(*args, **kwargs)

    def get_swap_decision(
        self,
        token_data: Any,
    ) -> Optional[str]:
        """Get the swap decision given a token's data."""
        strategy = self.synchronized_data.selected_strategy
        self.context.logger.info(f"Using trading strategy {strategy!r}.")
        # the following are always passed to a strategy script, which may choose to ignore any
        kwargs: Dict[str, Any] = self.params.strategies_kwargs
        kwargs.update(
            {
                STRATEGY_KEY: strategy,
                PRICE_DATA_KEY: token_data,
            }
        )
        results = self.execute_strategy(**kwargs)
        for level in SUPPORTED_STRATEGY_LOG_LEVELS:
            logger = getattr(self.context.logger, level, None)
            if logger is not None:
                for log in results.get(level, []):
                    logger(log)
        decision = results.get(SWAP_DECISION_FIELD, None)
        if decision is None:
            self.context.logger.error(
                f"Required field {SWAP_DECISION_FIELD!r} was not returned by {strategy} strategy."
                "Not taking any actions."
            )
        if decision not in AVAILABLE_DECISIONS:
            self.context.logger.error(
                f"Invalid decision {decision!r} was detected! Expected one of {AVAILABLE_DECISIONS}."
                "Not taking any actions."
            )
            decision = None

        return decision

    def get_orders(
        self, token_data: Dict[str, Any]
    ) -> Generator[None, None, Tuple[Dict[str, List[str]], bool]]:
        """Get a mapping from a string indicating whether to buy or sell, to a list of tokens."""
        # TODO this method is blocking, needs to be run from an aea skill.
        orders: Dict[str, List[str]] = {
            decision: [] for decision in AVAILABLE_DECISIONS
        }
        incomplete = False
        for token, data in token_data.items():
            decision = self.get_swap_decision(data)
            if decision is None:
                incomplete = True
                continue
            orders[decision].append(token)

        # we only yield here to convert this method to a generator, so that it can be used by `get_process_store_act`
        yield
        return orders, incomplete

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.data_hash,
            self.get_orders,
            str(self.swap_decision_filepath),
        )
