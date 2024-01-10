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

"""This package contains the rounds of MarketDataFetcherAbciApp."""

from enum import Enum
from typing import Dict, FrozenSet, Set, Optional, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    CollectSameUntilThresholdRound,
    AppState,
    BaseSynchronizedData,
    DegenerateRound,
    EventToTimeout,
    get_name,
    DeserializedCollection,
    BaseSynchronizedData
)

from packages.valory.skills.market_data_fetcher_abci.payloads import (
    FetchMarketDataPayload,
    VerifyMarketDataPayload,
)


class Event(Enum):
    """MarketDataFetcherAbciApp Events"""

    DONE = "done"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def participant_to_fetching(self) -> DeserializedCollection:
        """Get the participants to market fetching."""
        return self._get_deserialized("participant_to_fetching")


class FetchMarketDataRound(CollectSameUntilThresholdRound):
    """FetchMarketDataRound"""

    payload_class = FetchMarketDataPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    selection_key = (
        get_name(SynchronizedData.market_hash),
    )
    collection_key = get_name(SynchronizedData.participant_to_fetching)


class VerifyMarketDataRound(CollectSameUntilThresholdRound):
    """VerifyMarketDataRound"""

    payload_class = VerifyMarketDataPayload
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            return self.synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class FinishedMarketFetchRound(DegenerateRound):
    """FinishedMarketFetchRound"""


class MarketDataFetcherAbciApp(AbciApp[Event]):
    """MarketDataFetcherAbciApp"""

    initial_round_cls: AppState = FetchMarketDataRound
    initial_states: Set[AppState] = {FetchMarketDataRound}
    transition_function: AbciAppTransitionFunction = {
        FetchMarketDataRound: {
            Event.DONE: VerifyMarketDataRound,
            Event.NO_MAJORITY: FetchMarketDataRound,
            Event.ROUND_TIMEOUT: FetchMarketDataRound
        },
        VerifyMarketDataRound: {
            Event.DONE: FinishedMarketFetchRound,
            Event.NO_MAJORITY: FetchMarketDataRound,
            Event.ROUND_TIMEOUT: FetchMarketDataRound
        },
        FinishedMarketFetchRound: {}
    }
    final_states: Set[AppState] = {FinishedMarketFetchRound}
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
    db_pre_conditions: Dict[AppState, Set[str]] = {
        FetchMarketDataRound: set(),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedMarketFetchRound: set(),
    }
