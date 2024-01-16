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

"""This module contains the strategy execution state of the strategy evaluator abci app."""

from enum import Enum
from typing import Optional, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    get_name,
)
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import (
    StrategyExecPayload,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import (
    Event,
    SynchronizedData,
)


class StrategyExecRound(CollectSameUntilThresholdRound):
    """A round for executing a strategy."""

    payload_class = StrategyExecPayload
    synchronized_data_class = SynchronizedData
    prepare_swap_event = Event.PREPARE_SWAP
    done_event = prepare_swap_event
    incomplete_swap_event = Event.PREPARE_INCOMPLETE_SWAP
    no_orders_event = Event.NO_ORDERS
    none_event = Event.ERROR_PREPARING_SWAPS
    no_majority_event = Event.NO_MAJORITY
    selection_key = (
        get_name(SynchronizedData.orders_hash),
        get_name(SynchronizedData.incomplete_exec),
    )
    collection_key = get_name(SynchronizedData.participant_to_orders)

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        res = super().end_block()
        if res is None:
            return None

        synced_data, event = cast(Tuple[SynchronizedData, Enum], res)
        if event == self.prepare_swap_event:
            return synced_data, self.get_swap_event(synced_data)
        return synced_data, event

    def get_swap_event(self, synced_data: SynchronizedData) -> Enum:
        """Get the swap event based on the synchronized data."""
        if synced_data.orders_hash is None:
            return self.no_orders_event
        if synced_data.incomplete_exec:
            return self.incomplete_swap_event
        return self.prepare_swap_event
