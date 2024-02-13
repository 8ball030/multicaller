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

"""This module contains the backtesting state of the swap(s)."""

from packages.valory.skills.abstract_round_abci.base import VotingRound, get_name
from packages.valory.skills.solana_strategy_evaluator_abci.payloads import VotingPayload
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import (
    Event,
    SynchronizedData,
)


class BacktestRound(VotingRound):
    """A round in which the agents prepare swap(s) instructions."""

    synchronized_data_class = SynchronizedData
    payload_class = VotingPayload
    done_event = Event.BACKTEST_POSITIVE
    negative_event = Event.BACKTEST_NEGATIVE
    none_event = Event.BACKTEST_FAILED
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_backtesting)
