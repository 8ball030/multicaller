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

"""This module contains the decision receiving state of the strategy evaluator abci app."""

from packages.valory.skills.abstract_round_abci.base import (
    CollectSameUntilThresholdRound,
    get_name,
)
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import (
    SendSwapPayload,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import (
    Event,
    SynchronizedData,
)


class PrepareSwapRound(CollectSameUntilThresholdRound):
    """A round in which the agents prepare swap(s) transaction."""

    payload_class = SendSwapPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.TX_PREPARATION_FAILED
    no_majority_event = Event.NO_MAJORITY
    # TODO replace with `most_voted_instruction_set` when solana tx settlement is ready
    # selection_key = get_name(SynchronizedData.most_voted_tx_hash)  noqa: E800
    collection_key = get_name(SynchronizedData.participant_to_instructions)
