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

"""This module contains the rounds for the 'solana_trader_decision_maker_abci' skill."""

import json
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    CollectionRound,
    DegenerateRound,
    DeserializedCollection,
    get_name,
)
from packages.valory.skills.solana_trader_decision_maker_abci.payloads import (
    RandomnessPayload,
    SolanaTraderDecisionMakerPayload,
)
from packages.valory.skills.solana_trader_decision_maker_abci.policy import (
    EGreedyPolicy,
)


class Event(Enum):
    """Event enumeration for the SolanaTraderDecisionMakerAbci demo."""

    DONE = "done"
    NONE = "none"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"


@dataclass
class Position:
    """A swap position."""

    from_token: str
    to_token: str
    amount: int

    @classmethod
    def from_json(cls, positions: List[Dict]) -> List["Position"]:
        """Return a list of positions from a JSON representation."""
        return [cls(**position) for position in positions]


class SynchronizedData(BaseSynchronizedData):
    """Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    def _get_deserialized(self, key: str) -> DeserializedCollection:
        """Strictly get a collection and return it deserialized."""
        serialized = self.db.get_strict(key)
        return CollectionRound.deserialize_collection(serialized)

    @property
    def participant_to_decision(self) -> DeserializedCollection:
        """Get the participants to decision."""
        return self._get_deserialized("participant_to_decision")

    @property
    def most_voted_randomness_round(self) -> int:
        """Get the most voted randomness round."""
        round_ = self.db.get_strict("most_voted_randomness_round")
        return int(round_)

    @property
    def selected_strategy(self) -> str:
        """Get the selected strategy."""
        return str(self.db.get_strict("selected_strategy"))

    @property
    def policy(self) -> EGreedyPolicy:
        """Get the policy."""
        policy = self.db.get_strict("policy")
        return EGreedyPolicy(**json.loads(policy))

    @property
    def positions(self) -> List[Position]:
        """Get the swap positions."""
        positions = json.loads(self.db.get_strict("positions"))
        return Position.from_json(positions)


class SolanaTraderDecisionMakerAbstractRound(AbstractRound[Event], ABC):
    """Abstract round for the SolanaTraderDecisionMakerAbci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    def _return_no_majority_event(self) -> Tuple[SynchronizedData, Event]:
        """
        Trigger the `NO_MAJORITY` event.

        :return: the new synchronized data and a `NO_MAJORITY` event
        """
        return self.synchronized_data, Event.NO_MAJORITY


class RandomnessRound(CollectSameUntilThresholdRound):
    """A round for generating randomness."""

    payload_class = RandomnessPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = (
        get_name(SynchronizedData.most_voted_randomness_round),
        get_name(SynchronizedData.most_voted_randomness),
    )


class SolanaTraderDecisionMakerRound(
    CollectSameUntilThresholdRound, SolanaTraderDecisionMakerAbstractRound
):
    """A round for the bets fetching & updating."""

    payload_class = SolanaTraderDecisionMakerPayload
    done_event: Enum = Event.DONE
    none_event: Enum = Event.NONE
    no_majority_event: Enum = Event.NO_MAJORITY
    selection_key = (
        get_name(SynchronizedData.policy),
        get_name(SynchronizedData.positions),
        get_name(SynchronizedData.selected_strategy),
    )
    collection_key = get_name(SynchronizedData.participant_to_decision)
    synchronized_data_class = SynchronizedData


class FinishedSolanaTraderDecisionMakerRound(DegenerateRound, ABC):
    """A round that represents that the ABCI app has finished"""


class FailedSolanaTraderDecisionMakerRound(DegenerateRound, ABC):
    """A round that represents that the ABCI app has failed"""


class SolanaTraderDecisionMakerAbciApp(AbciApp[Event]):
    """SolanaTraderDecisionMakerAbciApp

    Initial round: SolanaTraderDecisionMakerRound

    Initial states: {SolanaTraderDecisionMakerRound}

    Transition states:
        0. SolanaTraderDecisionMakerRound
            - done: 1.
            - none: 2.
            - round timeout: 2.
            - no majority: 2.
        1. FinishedSolanaTraderDecisionMakerRound
        2. FailedSolanaTraderDecisionMakerRound

    Final states: {FailedSolanaTraderDecisionMakerRound, FinishedSolanaTraderDecisionMakerRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RandomnessRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessRound: {
            Event.DONE: SolanaTraderDecisionMakerRound,
            Event.ROUND_TIMEOUT: RandomnessRound,
            Event.NO_MAJORITY: RandomnessRound,
        },
        SolanaTraderDecisionMakerRound: {
            Event.DONE: FinishedSolanaTraderDecisionMakerRound,
            Event.NONE: FailedSolanaTraderDecisionMakerRound,
            Event.ROUND_TIMEOUT: FailedSolanaTraderDecisionMakerRound,
            Event.NO_MAJORITY: FailedSolanaTraderDecisionMakerRound,
        },
        FinishedSolanaTraderDecisionMakerRound: {},
        FailedSolanaTraderDecisionMakerRound: {},
    }
    final_states: Set[AppState] = {
        FinishedSolanaTraderDecisionMakerRound,
        FailedSolanaTraderDecisionMakerRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, Set[str]] = {RandomnessRound: set()}
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedSolanaTraderDecisionMakerRound: {
            get_name(SynchronizedData.selected_strategy),
            get_name(SynchronizedData.most_voted_randomness_round),
            get_name(SynchronizedData.most_voted_randomness),
        },
        FailedSolanaTraderDecisionMakerRound: {
            get_name(SynchronizedData.most_voted_randomness_round),
            get_name(SynchronizedData.most_voted_randomness),
        },
    }
