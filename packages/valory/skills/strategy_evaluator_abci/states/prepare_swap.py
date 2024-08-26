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

"""This module contains the swap(s) instructions' preparation state of the strategy evaluator abci app."""

from collections import Counter
from typing import Any, Dict, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppException,
    ABCIAppInternalError,
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    get_name,
)
from packages.valory.skills.strategy_evaluator_abci.payloads import (
    TransactionHashPayload,
    TransactionHashSamePayload,
)
from packages.valory.skills.strategy_evaluator_abci.states.base import (
    Event,
    IPFSRound,
    SynchronizedData,
)


class PrepareSwapRound(IPFSRound):
    """A round in which the agents prepare swap(s) instructions."""

    done_event = Event.INSTRUCTIONS_PREPARED
    incomplete_event = Event.INCOMPLETE_INSTRUCTIONS_PREPARED
    no_hash_event = Event.NO_INSTRUCTIONS
    none_event = Event.ERROR_PREPARING_INSTRUCTIONS
    selection_key = (
        get_name(SynchronizedData.instructions_hash),
        get_name(SynchronizedData.incomplete_instructions),
    )
    collection_key = get_name(SynchronizedData.participant_to_instructions)


class PrepareEvmSwapRound(CollectSameUntilThresholdRound):
    """
    A round in which agents compute the transaction hash.

    This is a special kind of round. It is a mix of collect same and collect different.
    In essence, it collects the same values for the tx hash and different values for the signatures and the data.
    """

    payload_class = TransactionHashPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.TRANSACTION_PREPARED
    none_event = Event.NO_INSTRUCTIONS
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_signature)
    selection_key = get_name(SynchronizedData.most_voted_tx_hash)

    @property
    def payload_values_count(self) -> Counter:
        """Get count of payload values."""
        return Counter(map(lambda p: (p.values[2],), self.payloads))

    @property
    def most_voted_payload_values(
        self,
    ) -> Tuple[Any, ...]:
        """Get the most voted payload values."""
        _, max_votes = self.payload_values_count.most_common()[0]
        if max_votes < self.synchronized_data.consensus_threshold:
            raise ABCIAppInternalError("not enough votes")

        all_payload_values_count = Counter(map(lambda p: p.values, self.payloads))
        most_voted_payload_values, _ = all_payload_values_count.most_common()[0]
        return most_voted_payload_values

    def check_majority_possible(
        self,
        votes_by_participant: Dict[str, BaseTxPayload],
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException,
    ) -> None:
        """
        Overrides the check to only account for the tx hash which should be the same.

        The rest attributes have to be different.

        :param votes_by_participant: a mapping from a participant to its vote
        :param nb_participants: the total number of participants
        :param exception_cls: the class of the exception to raise in case the check fails
        """
        votes_by_participant = {
            participant: TransactionHashSamePayload(
                payload.sender, cast(TransactionHashSamePayload, payload).tx_hash
            )
            for participant, payload in votes_by_participant.items()
        }
        super().check_majority_possible(
            votes_by_participant, nb_participants, exception_cls
        )
