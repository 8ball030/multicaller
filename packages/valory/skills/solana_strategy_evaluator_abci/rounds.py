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

"""This module contains the rounds for the strategy evaluator."""

from typing import Dict, Set

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    get_name,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import (
    Event,
    SynchronizedData,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.final_states import (
    HodlRound,
    SwapTxPreparedRound,
    TxPreparationFailed,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.prepare_swap import (
    PrepareSwapRound,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.strategy_exec import (
    StrategyExecRound,
)


class StrategyEvaluatorAbciApp(AbciApp[Event]):
    """StrategyEvaluatorAbciApp

    Initial round: TBD

    Initial states: {TBD}

    Transition states:
        0. TBD

    Final states: {TBD}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = StrategyExecRound
    initial_states: Set[AppState] = {StrategyExecRound}
    transition_function: AbciAppTransitionFunction = {
        StrategyExecRound: {
            Event.PREPARE_SWAP: PrepareSwapRound,
            Event.HODL: HodlRound,
            Event.NO_MAJORITY: StrategyExecRound,
            Event.ROUND_TIMEOUT: StrategyExecRound,
        },
        PrepareSwapRound: {
            Event.DONE: SwapTxPreparedRound,
            Event.TX_PREPARATION_FAILED: TxPreparationFailed,
            Event.ROUND_TIMEOUT: PrepareSwapRound,
            Event.NO_MAJORITY: PrepareSwapRound,
        },
        SwapTxPreparedRound: {},
        TxPreparationFailed: {},
        HodlRound: {},
    }
    final_states: Set[AppState] = {
        SwapTxPreparedRound,
        TxPreparationFailed,
        HodlRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, Set[str]] = {
        StrategyExecRound: {
            get_name(SynchronizedData.selected_strategy),
            get_name(SynchronizedData.data_hash),
        },
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        # TODO replace with `most_voted_instruction_set`
        SwapTxPreparedRound: set(),  # TODO: {get_name(SynchronizedData.most_voted_tx_hash)},
        TxPreparationFailed: set(),
        HodlRound: set(),
    }
