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

"""This module contains the base functionality for the rounds of the decision-making abci app."""

from enum import Enum

from packages.valory.skills.abstract_round_abci.base import (
    CollectionRound,
    DeserializedCollection,
)
from packages.valory.skills.market_data_fetcher_abci.rounds import (
    SynchronizedData as MarketFetcherSyncedData,
)
from packages.valory.skills.solana_trader_decision_maker_abci.rounds import (
    SynchronizedData as DecisionMakerSyncedData,
)

# TODO replace with Solana tx settlement
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSyncedData,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    HODL = "hodl"
    PREPARE_SWAP = "prepare_swap"
    TX_PREPARATION_FAILED = "none"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"


class SynchronizedData(
    DecisionMakerSyncedData, MarketFetcherSyncedData, TxSettlementSyncedData
):
    """Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    def _get_deserialized(self, key: str) -> DeserializedCollection:
        """Strictly get a collection and return it deserialized."""
        serialized = self.db.get_strict(key)
        return CollectionRound.deserialize_collection(serialized)

    @property
    def swaps_hash(self) -> str:
        """Get the hash of the swaps' data."""
        return str(self.db.get_strict("swaps_hash"))

    @property
    def participant_to_swaps(self) -> DeserializedCollection:
        """Get the participants to swaps."""
        return self._get_deserialized("participant_to_swaps")

    @property
    def participant_to_instructions(self) -> DeserializedCollection:
        """Get the participants to swap(s) instructions."""
        return self._get_deserialized("participant_to_instructions")
