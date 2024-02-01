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

"""This module contains the behaviour for preparing a transaction for the next swap in the queue of instructions."""

import json
from typing import Any, Dict, Generator, List, Optional, cast

from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import (
    SendSwapPayload,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.swap_queue import (
    SwapQueueRound,
)


class SwapQueueBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents prepare a transaction for the next swap in the queue of instructions."""

    matching_round = SwapQueueRound

    @property
    def instructions(self) -> Optional[List[Dict[str, Any]]]:
        """Get the instructions from the shared state."""
        return self.shared_state.instructions

    @instructions.setter
    def instructions(self, instructions: Optional[List[Dict[str, Any]]]) -> None:
        """Set the instructions to the shared state."""
        self.shared_state.instructions = instructions

    def get_instructions(self) -> Generator[None, None, Optional[List[Dict[str, Any]]]]:
        """Get the instructions from IPFS."""
        # only fetch once per new queue and store in the shared state for future reference
        hash_ = self.synchronized_data.instructions_hash
        instructions = yield from self.get_from_ipfs(hash_, SupportedFiletype.JSON)
        if instructions is None:
            sleep_time = self.params.sleep_time
            self.context.logger.error(
                f"Could not get the instructions from IPFS using hash {hash_!r}!"
                f"Retrying in {sleep_time}..."
            )
            self.sleep(sleep_time)

        return cast(Optional[List[Dict[str, Any]]], instructions)

    def get_next_instructions(self) -> Optional[str]:
        """Return the next instructions in priority serialized or `None` if there are no instructions left."""
        if self.instructions is None:
            err = "Instructions were expected to be set. The agent should not have entered this execution path."
            self.context.logger.critical(err)
            return None

        if len(self.instructions) == 0:
            self.context.logger.info("No more instructions to process.")
            self.instructions = None
            return ""

        instructions = self.instructions.pop(0)
        if len(instructions) == 0:
            err = "The next instructions in priority are not correctly set! Skipping them..."
            self.context.logger.error(err)
            return None

        try:
            return json.dumps(instructions)
        except (json.decoder.JSONDecodeError, TypeError):
            err = "The next instructions in priority are not correctly formatted! Skipping them..."
            self.context.logger.error(err)
            return None

    def async_act(self) -> Generator:
        """Do the action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            if self.instructions is None:
                instructions = yield from self.get_instructions()
                if instructions is None:
                    return
                self.instructions = instructions

            payload = SendSwapPayload(
                self.context.agent_address,
                self.get_next_instructions(),
            )

        yield from self.finish_behaviour(payload)
