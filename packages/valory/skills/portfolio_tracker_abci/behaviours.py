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

"""This package contains round behaviours of `PortfolioTrackerRoundBehaviour`."""

from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.portfolio_tracker_abci.models import Params
from packages.valory.skills.portfolio_tracker_abci.payloads import PortfolioTrackerPayload
from packages.valory.skills.portfolio_tracker_abci.rounds import PortfolioTrackerAbciApp, PortfolioTrackerRound


class PortfolioTrackerBehaviour(BaseBehaviour):
    """Behaviour responsible for tracking the portfolio of the service."""

    matching_round: Type[AbstractRound] = PortfolioTrackerRound

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)

    def track_portfolio(self) -> Generator:
        """Track the portfolio of the service."""

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            portfolio_hash = yield from self.track_portfolio()
            sender = self.context.agent_address
            payload = PortfolioTrackerPayload(sender, portfolio_hash)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PortfolioTrackerRoundBehaviour(AbstractRoundBehaviour):
    """PortfolioTrackerRoundBehaviour"""

    initial_behaviour_cls = PortfolioTrackerBehaviour
    abci_app_cls = PortfolioTrackerAbciApp
    behaviours: Set[Type[BaseBehaviour]] = [
        PortfolioTrackerBehaviour,
    ]
