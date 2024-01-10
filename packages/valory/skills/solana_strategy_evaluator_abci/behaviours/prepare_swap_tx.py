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

"""This module contains the behaviour for preparing a swap transaction."""

import json
from typing import Any, Dict, Generator, List, Optional

from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import (
    PrepareSwapPayload,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.prepare_swap import (
    PrepareSwapRound,
)


class PrepareSwapBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents execute the selected strategy and decide on the swap(s)."""

    matching_round = PrepareSwapRound

    def build_swap_tx(self, swap: str):
        """Build instructions for a swap transaction."""
        # TODO

    def prepare_instructions(
        self, swaps: List[str]
    ) -> Generator[None, None, Optional[List[Dict[str, Any]]]]:
        """Prepare the instructions for a Swap transaction."""
        instructions = []
        for swap in swaps:
            swap_instruction = yield from self.build_swap_tx(swap)
            instructions.append(swap_instruction)
        return instructions

    def async_act(self) -> Generator:
        """Do the action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            swaps = yield from self.get_from_ipfs(
                self.synchronized_data.swaps_hash, SupportedFiletype.JSON
            )
            instructions = self.prepare_instructions(swaps)
            serialized_instructions = None
            if instructions is not None:
                serialized_instructions = json.dumps(instructions)
            payload = PrepareSwapPayload(
                self.context.agent_address, serialized_instructions
            )

        yield from self.finish_behaviour(payload)
