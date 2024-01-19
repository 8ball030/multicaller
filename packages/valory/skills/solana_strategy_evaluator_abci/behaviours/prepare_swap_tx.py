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

import json
from typing import Any, Dict, Generator, List, Optional, Tuple

from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.strategy_exec import (
    AVAILABLE_DECISIONS,
    BUY_DECISION,
    HODL_DECISION,
    SELL_DECISION,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.prepare_swap import (
    PrepareSwapRound,
)


SOL = "So11111111111111111111111111111111111111112"


def to_content(content: dict) -> bytes:
    """Convert the given content to bytes' payload."""
    return json.dumps(content, sort_keys=True).encode()


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

    def _handle_response(
        self,
        api: ApiSpecs,
        res: Optional[dict],
    ) -> Optional[Any]:
        """Handle the response from an API.

        :param api: the `ApiSpecs` instance of the API.
        :param res: the response to handle.
        :return: the response's result, using the given keys. `None` if response is `None` (has failed).
        """
        if res is None:
            error = f"Could not get a response from {api.api_id!r} API."
            self.context.logger.error(error)
            api.increment_retries()
            return None

        self.context.logger.info(
            f"Retrieved a response from {api.api_id!r} API: {res}."
        )
        api.reset_retries()
        return res

    def _get_response(
        self,
        api: ApiSpecs,
        dynamic_parameters: Dict[str, str],
        content: Optional[Dict[str, str]] = None,
    ) -> Generator[None, None, Optional[dict]]:
        """Get the response from an API."""
        specs = api.get_spec()
        specs["parameters"].update = dynamic_parameters
        if content is not None:
            specs["content"] = to_content(content)

        while not api.is_retries_exceeded():
            res_raw = yield from self.get_http_response(**specs)
            res = api.process_response(res_raw)
            response = self._handle_response(api, res)
            if response is not None:
                return response

        error = f"Retries were exceeded for {api.api_id!r} API."
        self.context.logger.error(error)
        api.reset_retries()
        return None

    def build_quote(
        self, from_token: str, to_token: str
    ) -> Generator[None, None, Optional[dict]]:
        """Build the quote."""
        params = {"inputMint": from_token, "outputMint": to_token}
        response = yield from self._get_response(self.context.swap_quotes, params)
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
        self, from_token: str, to_token: str
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Build instructions for a swap transaction."""
        quote = yield from self.build_quote(from_token, to_token)
        if quote is None:
            return None
        instructions = yield from self.build_instructions(quote)
        return instructions

    def get_token_swap_position(self, decision: str) -> Optional[str]:
        """Get the position of the non-native token in the swap operation."""
        token_swap_position = None

        if decision == BUY_DECISION:
            token_swap_position = "to_token"  # nosec hardcoded_password_string
        elif decision == SELL_DECISION:
            token_swap_position = "from_token"  # nosec hardcoded_password_string
        elif decision != HODL_DECISION:
            self.context.logger.error(
                f"Unrecognised decision {decision!r} found! Expected one of {AVAILABLE_DECISIONS}."
            )
            self.incomplete = True

        return token_swap_position

    def prepare_instructions(
        self, orders: Dict[str, List[str]]
    ) -> Generator[None, None, Tuple[List[Dict[str, Any]], bool]]:
        """Prepare the instructions for a Swap transaction."""
        instructions = []
        for decision, tokens in orders.items():
            token_swap_position = self.get_token_swap_position(decision)
            if token_swap_position is None:
                continue

            quote_data = {"from_token": SOL, "to_token": SOL}
            for token in tokens:
                if token == SOL:
                    continue
                quote_data[token_swap_position] = token
                swap_instruction = yield from self.build_swap_tx(**quote_data)
                if swap_instruction is None:
                    self.incomplete = True
                else:
                    instructions.append(swap_instruction)

        return instructions, self.incomplete

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.orders_hash,
            self.prepare_instructions,
            str(self.swap_instructions_filepath),
        )
