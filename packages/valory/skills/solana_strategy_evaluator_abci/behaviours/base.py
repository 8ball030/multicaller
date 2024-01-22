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
from typing import Any, Callable, Generator, Optional, Sized, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.solana_strategy_evaluator_abci.models import (
    SharedState,
    StrategyEvaluatorParams,
)
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import (
    IPFSHashPayload,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import (
    SynchronizedData,
)


SWAP_DECISION_FILENAME = "swap_decision.json"
SWAP_INSTRUCTIONS_FILENAME = "swap_instructions.json"


def wei_to_native(wei: int) -> float:
    """Convert WEI to native token."""
    return wei / 10**18


class StrategyEvaluatorBaseBehaviour(BaseBehaviour, ABC):
    """Represents the base class for the strategy evaluation FSM behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the strategy evaluator behaviour."""
        super().__init__(**kwargs)
        self.swap_decision_filepath = (
            Path(self.context.data_dir) / SWAP_DECISION_FILENAME
        )
        self.swap_instructions_filepath = (
            Path(self.context.data_dir) / SWAP_INSTRUCTIONS_FILENAME
        )
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

    def get_process_store_act(
        self,
        hash_: str,
        process_fn: Callable[[Any], Generator[None, None, Tuple[Sized, bool]]],
        store_filepath: str,
    ) -> Generator:
        """An async act method for getting some data, processing them, and storing the result.

        1. Get some data using the given hash.
        2. Process them using the given fn.
        3. Send them to IPFS using the given filepath as intermediate storage.

        :param hash_: the hash of the data to process.
        :param process_fn: the function to process the data.
        :param store_filepath: path to the file to store the processed data.
        :return: None
        :yield: None
        """
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            data = yield from self.get_from_ipfs(hash_, SupportedFiletype.JSON)
            if data is None:
                self.context.logger.error(
                    f"Could not get the data from IPFS using hash {hash_!r}!"
                )
                self.sleep(self.params.sleep_time)
                return

            processed, incomplete = yield from process_fn(data)
            n_processed: Optional[int] = len(processed)
            if n_processed == 0:
                processed_hash = None
                if incomplete:
                    status = n_processed = None
            else:
                processed_hash = yield from self.send_to_ipfs(
                    store_filepath,
                    processed,
                    filetype=SupportedFiletype.JSON,
                )
                status = incomplete

            payload = IPFSHashPayload(
                self.context.agent_address, processed_hash, status, n_processed
            )

        yield from self.finish_behaviour(payload)

    def finish_behaviour(self, payload: BaseTxPayload) -> Generator:
        """Finish the behaviour."""
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()
