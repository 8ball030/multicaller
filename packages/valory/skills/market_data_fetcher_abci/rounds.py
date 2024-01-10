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
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    DegenerateRound,
    EventToTimeout,
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


class FetchMarketDataRound(AbstractRound):
    """FetchMarketDataRound"""

    payload_class = FetchMarketDataPayload
    payload_attribute = ""  # TODO: update
    synchronized_data_class = SynchronizedData

    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound,
    # CollectSameUntilAllRound, CollectSameUntilThresholdRound,
    # CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound,
    # from packages/valory/skills/abstract_round_abci/base.py
    # or implement the methods

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: FetchMarketDataPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: FetchMarketDataPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class VerifyMarketDataRound(AbstractRound):
    """VerifyMarketDataRound"""

    payload_class = VerifyMarketDataPayload
    payload_attribute = ""  # TODO: update
    synchronized_data_class = SynchronizedData

    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound,
    # CollectSameUntilAllRound, CollectSameUntilThresholdRound,
    # CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound,
    # from packages/valory/skills/abstract_round_abci/base.py
    # or implement the methods

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: VerifyMarketDataPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: VerifyMarketDataPayload) -> None:
        """Process payload."""
        raise NotImplementedError


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
        FetchMarketDataRound: [],
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedMarketFetchRound: [],
    }
