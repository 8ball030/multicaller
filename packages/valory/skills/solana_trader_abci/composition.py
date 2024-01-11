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

"""This module contains the solana_trader ABCI application."""

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
import packages.valory.skills.registration_abci.rounds as RegistrationAbci
import packages.valory.skills.reset_pause_abci.rounds as ResetAndPauseAbci
import packages.valory.skills.solana_trader_decision_maker_abci.rounds as SolanaTraderDecisionMakerAbci
import packages.valory.skills.market_data_fetcher_abci.rounds as MarketDataFetcherAbci
import packages.valory.skills.solana_strategy_evaluator_abci.rounds as StrategyEvaluatorAbci
# import packages.valory.skills.solana_transaction_settlement_abci.rounds as SolanaTransactionSettlementAbci

abci_app_transition_mapping: AbciAppTransitionMapping = {
    RegistrationAbci.FinishedRegistrationRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    SolanaTraderDecisionMakerAbci.FinishedSolanaTraderDecisionMakerRound: MarketDataFetcherAbci.FetchMarketDataRound,
    SolanaTraderDecisionMakerAbci.FailedSolanaTraderDecisionMakerRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    MarketDataFetcherAbci.FinishedMarketFetchRound: ResetAndPauseAbci.ResetAndPauseRound,  # TODO: StrategyEvaluatorAbci.StrategyExecRound,
    # StrategyEvaluatorAbci.FinishedStrategyEvaluation: SolanaTransactionSettlementAbci.RandomnessTransactionSubmissionRound,   # TODO
    # SolanaTransactionSettlementAbci.FinishedTransactionSubmissionRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,    # TODO
    # SolanaTransactionSettlementAbci.FailedRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,    # TODO
    ResetAndPauseAbci.FinishedResetAndPauseRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    ResetAndPauseAbci.FinishedResetAndPauseErrorRound: RegistrationAbci.RegistrationRound,
}

SolanaTraderAbciApp = chain(
    (
        RegistrationAbci.AgentRegistrationAbciApp,
        SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerAbciApp,
        MarketDataFetcherAbci.MarketDataFetcherAbciApp,
        StrategyEvaluatorAbci.StrategyEvaluatorAbciApp,
        # SolanaTransactionSettlementAbci.SolanaTransactionSettlementAbciApp,  # TODO
        ResetAndPauseAbci.ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
)
