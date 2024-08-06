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

"""This module contains the behaviour for preparing swap(s) instructions."""

from typing import Any, Dict, Generator, List, Optional, Tuple

from packages.eightballer.connections.dcxt import PUBLIC_ID as DCXT_ID
from packages.eightballer.protocols.orders.custom_types import (
    Order,
    OrderSide,
    OrderType,
)
from packages.eightballer.protocols.orders.message import OrdersMessage
from packages.valory.skills.strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.strategy_evaluator_abci.states.prepare_swap import (
    PrepareEvmSwapRound,
    PrepareSwapRound,
)


class PrepareSwapBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents execute the selected strategy and decide on the swap(s)."""

    matching_round = PrepareSwapRound

    def __init__(self, **kwargs: Any):
        """Initialize the swap-preparation behaviour."""
        super().__init__(**kwargs)
        self.incomplete = False

    def setup(self) -> None:
        """Initialize the behaviour."""
        self.context.swap_quotes.reset_retries()
        self.context.swap_instructions.reset_retries()

    def build_quote(
        self, quote_data: Dict[str, str]
    ) -> Generator[None, None, Optional[dict]]:
        """Build the quote."""
        response = yield from self._get_response(self.context.swap_quotes, quote_data)
        return response

    def build_instructions(self, quote: dict) -> Generator[None, None, Optional[dict]]:
        """Build the instructions."""
        content = {
            "quoteResponse": quote,
            "userPublicKey": self.context.agent_address,
        }
        response = yield from self._get_response(
            self.context.swap_instructions,
            dynamic_parameters={},
            content=content,
        )
        return response

    def build_swap_tx(
        self, quote_data: Dict[str, str]
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Build instructions for a swap transaction."""
        quote = yield from self.build_quote(quote_data)
        if quote is None:
            return None
        instructions = yield from self.build_instructions(quote)
        return instructions

    def prepare_instructions(
        self, orders: List[Dict[str, str]]
    ) -> Generator[None, None, Tuple[List[Dict[str, Any]], bool]]:
        """Prepare the instructions for a Swap transaction."""
        instructions = []
        for quote_data in orders:
            swap_instruction = yield from self.build_swap_tx(quote_data)
            if swap_instruction is None:
                self.incomplete = True
            else:
                instructions.append(swap_instruction)

        return instructions, self.incomplete

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.backtested_orders_hash,
            self.prepare_instructions,
            str(self.swap_instructions_filepath),
        )


class PrepareEvmSwapBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents execute the selected strategy and decide on the swap(s)."""

    matching_round = PrepareEvmSwapRound

    def __init__(self, **kwargs: Any):
        """Initialize the swap-preparation behaviour."""
        super().__init__(**kwargs)
        self.incomplete = False
        self._performative_to_dialogue_class = {
            OrdersMessage.Performative.CREATE_ORDER: self.context.orders_dialogues,
        }

    def setup(self) -> None:
        """Initialize the behaviour."""
        self.context.swap_quotes.reset_retries()
        self.context.swap_instructions.reset_retries()

    def build_quote(
        self, quote_data: Dict[str, str]
    ) -> Generator[None, None, Optional[dict]]:
        """Build the quote."""
        response = yield from self._get_response(self.context.swap_quotes, quote_data)
        return response

    def build_instructions(self, quote: dict) -> Generator[None, None, Optional[dict]]:
        """Build the instructions."""
        content = {
            "quoteResponse": quote,
            "userPublicKey": self.context.agent_address,
        }
        response = yield from self._get_response(
            self.context.swap_instructions,
            dynamic_parameters={},
            content=content,
        )
        return response

    def build_swap_tx(
        self, quote_data: Dict[str, str]
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Build instructions for a swap transaction."""
        quote = yield from self.build_quote(quote_data)
        if quote is None:
            return None
        instructions = yield from self.build_instructions(quote)
        return instructions

    def prepare_instructions(
        self, orders: List[Dict[str, str]]
    ) -> Generator[None, None, Tuple[List[Dict[str, Any]], bool]]:
        """Prepare the instructions for a Swap transaction."""
        instructions = []
        for quote_data in orders:
            symbol = f'{quote_data["inputMint"]}/{quote_data["outputMint"]}'
            size = 0.1
            order = Order(
                exchange_id="balancer",
                symbol=symbol,
                amount=size,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
            )

            result = yield from self.get_dcxt_response(
                protocol_performative=OrdersMessage.Performative.CREATE_ORDER,  # type: ignore
                order=order,
            )
            transaction = result.Order.info.get("transaction", None)
            if transaction is None:
                self.incomplete = True
            else:
                instructions.append(transaction)

        return instructions, self.incomplete

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.backtested_orders_hash,
            self.prepare_instructions,
            str(self.swap_instructions_filepath),
        )

    def get_dcxt_response(
        self,
        protocol_performative: OrdersMessage.Performative,
        **kwargs: Any,
    ) -> Generator[None, None, Any]:
        """Get a ccxt response."""
        if protocol_performative not in self._performative_to_dialogue_class:
            raise ValueError(
                f"Unsupported protocol performative {protocol_performative}."
            )
        dialogue_class = self._performative_to_dialogue_class[protocol_performative]

        msg, dialogue = dialogue_class.create(
            counterparty=str(DCXT_ID),
            performative=protocol_performative,
            **kwargs,
        )
        msg._sender = str(self.context.skill_id)  # pylint: disable=protected-access
        response = yield from self._do_request(msg, dialogue)
        return response
