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
from packages.valory.skills.solana_strategy_evaluator_abci.states.backtesting import BacktestRound
from packages.valory.skills.solana_strategy_evaluator_abci.states.base import (
    Event,
    SynchronizedData,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.final_states import (
    BacktestingFailedRound,
    BacktestingNegativeRound,
    HodlRound,
    InstructionPreparationFailedRound,
    NoMoreSwapsRound,
    StrategyExecutionFailedRound,
    SwapTxPreparedRound,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.prepare_swap import (
    PrepareSwapRound,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.proxy_swap_queue import (
    ProxySwapQueueRound,
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
            - prepare swap proxy server: 3.
            - prepare incomplete swap: 1.
            - prepare incomplete swap proxy server: 3.
            - no orders: 8.
            - error preparing swaps: 6.
            - no majority: 0.
            - round timeout: 0.
        1. PrepareSwapRound
            - instructions prepared: 2.
            - incomplete instructions prepared: 2.
            - no instructions: 8.
            - error preparing instructions: 7.
            - no majority: 1.
            - round timeout: 1.
        2. SwapQueueRound
            - swap tx prepared: 4.
            - swaps queue empty: 5.
            - none: 2.
            - no majority: 2.
            - round timeout: 2.
        3. ProxySwapQueueRound
            - proxy swapped: 3.
            - swaps queue empty: 5.
            - proxy swap failed: 3.
            - no majority: 3.
            - round timeout: 3.
        4. SwapTxPreparedRound
        5. NoMoreSwapsRound
        6. StrategyExecutionFailedRound
        7. InstructionPreparationFailedRound
        8. HodlRound

    Final states: {HodlRound, InstructionPreparationFailedRound, NoMoreSwapsRound, StrategyExecutionFailedRound, SwapTxPreparedRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = StrategyExecRound
    initial_states: Set[AppState] = {StrategyExecRound}
    final_states: Set[AppState] = {
        SwapTxPreparedRound,
        NoMoreSwapsRound,
        StrategyExecutionFailedRound,
        InstructionPreparationFailedRound,
        HodlRound,
        BacktestingNegativeRound,
        BacktestingFailedRound,
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
    transition_function: AbciAppTransitionFunction = {
        StrategyExecRound: {
            Event.PREPARE_SWAP: BacktestRound,
            Event.PREPARE_SWAP_PROXY_SERVER: ProxySwapQueueRound,
            Event.PREPARE_INCOMPLETE_SWAP: BacktestRound,
            Event.PREPARE_INCOMPLETE_SWAP_PROXY_SERVER: ProxySwapQueueRound,
            Event.NO_ORDERS: HodlRound,
            Event.ERROR_PREPARING_SWAPS: StrategyExecutionFailedRound,
            Event.NO_MAJORITY: StrategyExecRound,
            Event.ROUND_TIMEOUT: StrategyExecRound,
        },
        BacktestRound: {
            Event.BACKTEST_POSITIVE: PrepareSwapRound,
            Event.BACKTEST_NEGATIVE: BacktestingNegativeRound,
            Event.BACKTEST_FAILED: BacktestingFailedRound,
            Event.NO_MAJORITY: BacktestRound,
            Event.ROUND_TIMEOUT: BacktestRound,
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
        ProxySwapQueueRound: {
            Event.PROXY_SWAPPED: ProxySwapQueueRound,
            Event.SWAPS_QUEUE_EMPTY: NoMoreSwapsRound,
            Event.PROXY_SWAP_FAILED: ProxySwapQueueRound,
            Event.NO_MAJORITY: ProxySwapQueueRound,
            Event.ROUND_TIMEOUT: ProxySwapQueueRound,
        },
        SwapTxPreparedRound: {},
        NoMoreSwapsRound: {},
        StrategyExecutionFailedRound: {},
        BacktestingNegativeRound: {},
        BacktestingFailedRound: {},
        InstructionPreparationFailedRound: {},
        HodlRound: {},
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        SwapTxPreparedRound: set(),  # TODO: {get_name(SynchronizedData.most_voted_instruction_set)},
        NoMoreSwapsRound: set(),
        StrategyExecutionFailedRound: set(),
        BacktestingNegativeRound: set(),
        BacktestingFailedRound: set(),
        InstructionPreparationFailedRound: set(),
        HodlRound: set(),
    }
