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

"""This module contains the trader ABCI application."""

import packages.valory.skills.market_data_fetcher_abci.rounds as MarketDataFetcherAbci
import packages.valory.skills.portfolio_tracker_abci.rounds as PortfolioTrackerAbci
import packages.valory.skills.registration_abci.rounds as RegistrationAbci
import packages.valory.skills.reset_pause_abci.rounds as ResetAndPauseAbci
import packages.valory.skills.strategy_evaluator_abci.rounds as StrategyEvaluatorAbci
import packages.valory.skills.trader_decision_maker_abci.rounds as TraderDecisionMakerAbci
import packages.valory.skills.transaction_settlement_abci.rounds as TransactionSettlementAbci
from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)


DECISION_MAKING = TraderDecisionMakerAbci.RandomnessRound
RESET_AND_PAUSE = ResetAndPauseAbci.ResetAndPauseRound


abci_app_transition_mapping: AbciAppTransitionMapping = {
    RegistrationAbci.FinishedRegistrationRound: DECISION_MAKING,
    TraderDecisionMakerAbci.FinishedTraderDecisionMakerRound: MarketDataFetcherAbci.FetchMarketDataRound,
    TraderDecisionMakerAbci.FailedTraderDecisionMakerRound: DECISION_MAKING,
    MarketDataFetcherAbci.FinishedMarketFetchRound: PortfolioTrackerAbci.PortfolioTrackerRound,
    MarketDataFetcherAbci.FailedMarketFetchRound: DECISION_MAKING,
    PortfolioTrackerAbci.FinishedPortfolioTrackerRound: StrategyEvaluatorAbci.StrategyExecRound,
    PortfolioTrackerAbci.FailedPortfolioTrackerRound: DECISION_MAKING,
    StrategyEvaluatorAbci.SwapTxPreparedRound: TransactionSettlementAbci.RandomnessTransactionSubmissionRound,  # TODO
    StrategyEvaluatorAbci.NoMoreSwapsRound: RESET_AND_PAUSE,
    StrategyEvaluatorAbci.StrategyExecutionFailedRound: DECISION_MAKING,
    StrategyEvaluatorAbci.InstructionPreparationFailedRound: DECISION_MAKING,
    StrategyEvaluatorAbci.HodlRound: RESET_AND_PAUSE,
    StrategyEvaluatorAbci.BacktestingNegativeRound: DECISION_MAKING,
    StrategyEvaluatorAbci.BacktestingFailedRound: DECISION_MAKING,
    TransactionSettlementAbci.FinishedTransactionSubmissionRound: DECISION_MAKING,
    TransactionSettlementAbci.FailedRound: DECISION_MAKING,
    ResetAndPauseAbci.FinishedResetAndPauseRound: DECISION_MAKING,
    ResetAndPauseAbci.FinishedResetAndPauseErrorRound: RegistrationAbci.RegistrationRound,
}

TraderAbciApp = chain(
    (
        RegistrationAbci.AgentRegistrationAbciApp,
        TraderDecisionMakerAbci.TraderDecisionMakerAbciApp,
        MarketDataFetcherAbci.MarketDataFetcherAbciApp,
        PortfolioTrackerAbci.PortfolioTrackerAbciApp,
        StrategyEvaluatorAbci.StrategyEvaluatorAbciApp,
        TransactionSettlementAbci.TransactionSubmissionAbciApp,
        # TransactionSettlementAbci.SolanaTransactionSettlementAbciApp,  # TODO
        ResetAndPauseAbci.ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
)
