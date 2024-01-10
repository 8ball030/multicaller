# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
from packages.valory.skills.abstract_round_abci.base import BackgroundAppConfig
import packages.valory.skills.registration_abci.rounds as RegistrationAbci
import packages.valory.skills.reset_pause_abci.rounds as ResetAndPauseAbci
import packages.valory.skills.solana_trader_decision_maker_abci.rounds as SolanaTraderDecisionMakerAbci
import packages.valory.skills.market_data_fetcher_abci.rounds as MarketDataFetcherAbci
import packages.valory.skills.strategy_evaluator_abci.rounds as StrategyEvaluatorAbci
import packages.valory.skills.solana_transaction_settlement_abci.rounds as SolanaTransactionSettlementAbci
from packages.valory.skills.termination_abci.rounds import (
    BackgroundRound,
    Event,
    TerminationAbciApp,
)

abci_app_transition_mapping: AbciAppTransitionMapping = {
    RegistrationAbci.FinishedRegistrationRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    SolanaTraderDecisionMakerAbci.FinishedSolanaTraderDecisionMakerRound: MarketDataFetcherAbci.FetchMarketDataRound,
    SolanaTraderDecisionMakerAbci.FailedSolanaTraderDecisionMakerRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    MarketDataFetcherAbci.FinishedMarketFetchRound: StrategyEvaluatorAbci.StrategyExecRound,
    StrategyEvaluatorAbci.FinishedStrategyEvaluation: SolanaTransactionSettlementAbci.RandomnessTransactionSubmissionRound,
    SolanaTransactionSettlementAbci.FinishedTransactionSubmissionRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    SolanaTransactionSettlementAbci.FailedRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    ResetAndPauseAbci.FinishedResetAndPauseRound: SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerRound,
    ResetAndPauseAbci.FinishedResetAndPauseErrorRound: RegistrationAbci.RegistrationRound,
}

termination_config = BackgroundAppConfig(
    round_cls=BackgroundRound,
    start_event=Event.TERMINATE,
    abci_app=TerminationAbciApp,
)

SolanaTraderAbciApp = chain(
    (
        RegistrationAbci.AgentRegistrationAbciApp,
        SolanaTraderDecisionMakerAbci.SolanaTraderDecisionMakerAbciApp,
        MarketDataFetcherAbci.MarketDataFetcherAbciApp,
        StrategyEvaluatorAbci.StrategyEvaluatorAbciApp,
        SolanaTransactionSettlementAbci.SolanaTransactionSettlementAbciApp,
        ResetAndPauseAbci.ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
).add_background_app(termination_config)
