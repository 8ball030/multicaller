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

"""This module contains the behaviours for the 'solana_trader_decision_maker_abci' skill."""

import json
import os.path
from abc import ABC
from json import JSONDecodeError
from typing import Any, Generator, Iterator, List, Set, Tuple, Type

from aea.helpers.ipfs.base import IPFSHashOnly

from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.solana_trader_decision_maker_abci.rounds import (
    SolanaTraderDecisionMakerAbciApp,
    SolanaTraderDecisionMakerRound,
)
from packages.valory.skills.solana_trader_decision_maker_abci.payloads import (
    SolanaTraderDecisionMakerPayload,
)


class SolanaTraderDecisionMakerBehaviour(BaseBehaviour, ABC):

    def async_act(self) -> Generator:
        """Do the action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
             payload = SolanaTraderDecisionMakerPayload(self.context.agent_address, "OK")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
            self.set_done()


class SolanaTraderDecisionMakerRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the SolanaTraderDecisionMakerBehaviour."""

    initial_behaviour_cls = SolanaTraderDecisionMakerBehaviour
    abci_app_cls = SolanaTraderDecisionMakerAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        SolanaTraderDecisionMakerBehaviour,  # type: ignore
    }
