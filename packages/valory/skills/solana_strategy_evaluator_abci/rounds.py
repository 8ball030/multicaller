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
    InstructionPreparationFailedRound,
    NoMoreSwapsRound,
    StrategyExecutionFailedRound,
    SwapTxPreparedRound,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.prepare_swap import (
    PrepareSwapRound,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.strategy_exec import (
    StrategyExecRound,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.swap_queue import (
    SwapQueueRound,
)


class StrategyEvaluatorAbciApp(AbciApp[Event]):
    """StrategyEvaluatorAbciApp

    Initial round: StrategyExecRound

    Initial states: {StrategyExecRound}

    Transition states:
        0. StrategyExecRound
            - prepare swap: 1.
            - prepare incomplete swap: 1.
            - no orders: 5.
            - error preparing swaps: 3.
            - no majority: 0.
            - round timeout: 0.
        1. PrepareSwapRound
            - done: 2.
            - none: 4.
            - round timeout: 1.
            - no majority: 1.
        2. SwapTxPreparedRound
        3. StrategyExecutionFailedRound
        4. TxPreparationFailedRound
        5. HodlRound

    Final states: {HodlRound, StrategyExecutionFailedRound, SwapTxPreparedRound, TxPreparationFailedRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = StrategyExecRound
    initial_states: Set[AppState] = {StrategyExecRound}
    transition_function: AbciAppTransitionFunction = {
        StrategyExecRound: {
            Event.PREPARE_SWAP: PrepareSwapRound,
            Event.PREPARE_INCOMPLETE_SWAP: PrepareSwapRound,
            Event.NO_ORDERS: HodlRound,
            Event.ERROR_PREPARING_SWAPS: StrategyExecutionFailedRound,
            Event.NO_MAJORITY: StrategyExecRound,
            Event.ROUND_TIMEOUT: StrategyExecRound,
        },
        PrepareSwapRound: {
            Event.INSTRUCTIONS_PREPARED: SwapQueueRound,
            Event.INCOMPLETE_INSTRUCTIONS_PREPARED: SwapQueueRound,
            Event.NO_INSTRUCTIONS: HodlRound,
            Event.ERROR_PREPARING_INSTRUCTIONS: InstructionPreparationFailedRound,
            Event.NO_MAJORITY: PrepareSwapRound,
            Event.ROUND_TIMEOUT: PrepareSwapRound,
        },
        SwapQueueRound: {
            Event.SWAP_TX_PREPARED: SwapTxPreparedRound,
            Event.SWAPS_QUEUE_EMPTY: NoMoreSwapsRound,
            Event.TX_PREPARATION_FAILED: SwapQueueRound,
            Event.NO_MAJORITY: SwapQueueRound,
            Event.ROUND_TIMEOUT: SwapQueueRound,
        },
        SwapTxPreparedRound: {},
        NoMoreSwapsRound: {},
        StrategyExecutionFailedRound: {},
        InstructionPreparationFailedRound: {},
        HodlRound: {},
    }
    final_states: Set[AppState] = {
        SwapTxPreparedRound,
        NoMoreSwapsRound,
        StrategyExecutionFailedRound,
        InstructionPreparationFailedRound,
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
        SwapTxPreparedRound: set(),  # TODO: {get_name(SynchronizedData.most_voted_instruction_set)},
        NoMoreSwapsRound: set(),
        StrategyExecutionFailedRound: set(),
        InstructionPreparationFailedRound: set(),
        HodlRound: set(),
    }
