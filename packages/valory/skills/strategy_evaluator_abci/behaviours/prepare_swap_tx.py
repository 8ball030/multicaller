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

"""This module contains the behaviour for preparing swap(s) instructions."""

from typing import Any, Dict, Generator, List, Optional, Tuple

from packages.valory.skills.strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.strategy_evaluator_abci.states.prepare_swap import (
    PrepareSwapRound,
)


class PrepareSwapBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents execute the selected strategy and decide on the swap(s)."""

    matching_round = PrepareSwapRound

    def __init__(self, **kwargs: Any):
        """Initialize the swap-preparation behaviour."""
        super().__init__(**kwargs)
        self.incomplete = False

    def setup(self) -> None:
        """Initialize the behaviour."""
        self.context.swap_quotes.reset_retries()
        self.context.swap_instructions.reset_retries()

    def build_quote(
        self, quote_data: Dict[str, str]
    ) -> Generator[None, None, Optional[dict]]:
        """Build the quote."""
        response = yield from self._get_response(self.context.swap_quotes, quote_data)
        return response

    def build_instructions(self, quote: dict) -> Generator[None, None, Optional[dict]]:
        """Build the instructions."""
        content = {
            "quoteResponse": quote,
            "userPublicKey": self.context.agent_address,
        }
        response = yield from self._get_response(
            self.context.swap_instructions,
            dynamic_parameters={},
            content=content,
        )
        return response

    def build_swap_tx(
        self, quote_data: Dict[str, str]
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Build instructions for a swap transaction."""
        quote = yield from self.build_quote(quote_data)
        if quote is None:
            return None
        instructions = yield from self.build_instructions(quote)
        return instructions

    def prepare_instructions(
        self, orders: List[Dict[str, str]]
    ) -> Generator[None, None, Tuple[List[Dict[str, Any]], bool]]:
        """Prepare the instructions for a Swap transaction."""
        instructions = []
        for quote_data in orders:
            swap_instruction = yield from self.build_swap_tx(quote_data)
            if swap_instruction is None:
                self.incomplete = True
            else:
                instructions.append(swap_instruction)

        return instructions, self.incomplete

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.backtested_orders_hash,
            self.prepare_instructions,
            str(self.swap_instructions_filepath),
        )
