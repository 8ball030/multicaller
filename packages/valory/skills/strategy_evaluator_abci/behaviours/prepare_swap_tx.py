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

import hashlib
import json
import traceback
from typing import Any, Callable, Dict, Generator, List, Optional, Sized, Tuple, cast

from packages.eightballer.connections.dcxt import PUBLIC_ID as DCXT_ID
from packages.eightballer.protocols.orders.custom_types import (
    Order,
    OrderSide,
    OrderType,
)
from packages.eightballer.protocols.orders.message import OrdersMessage
from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SafeOperation,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.strategy_evaluator_abci.payloads import (
    TransactionHashPayload,
)
from packages.valory.skills.strategy_evaluator_abci.states.prepare_swap import (
    PrepareEvmSwapRound,
    PrepareSwapRound,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import TX_HASH_LENGTH


SAFE_GAS = 0


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

    def prepare_transactions(
        self, orders: List[Dict[str, str]]
    ) -> Generator[None, None, Tuple[List[Dict[str, Any]], bool]]:
        """Prepare the instructions for a Swap transaction."""
        instructions = []
        for quote_data in orders:
            symbol = f'{quote_data["inputMint"]}/{quote_data["outputMint"]}'
            order = Order(
                exchange_id="balancer",
                symbol=symbol,
                amount=self.params.trade_size_in_base_token,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                data=json.dumps(
                    {
                        "safe_contract_address": self.synchronized_data.safe_contract_address,
                    }
                ),
            )

            result = yield from self.get_dcxt_response(
                protocol_performative=OrdersMessage.Performative.CREATE_ORDER,  # type: ignore
                order=order,
            )
            call_data = result.order.data
            try:
                can_create_hash = yield from self._build_safe_tx_hash(
                    vault_address=call_data["vault_address"],
                    chain_id=call_data["chain_id"],
                    call_data=call_data["data"].encode(),
                )
            except Exception as e:
                self.context.logger.error(
                    f"Error building safe tx hash: {traceback.format_exc()} with error {e}"
                )

            if call_data is None:
                self.incomplete = not can_create_hash
            else:
                instructions.append(call_data)

        return instructions, self.incomplete

    def _build_safe_tx_hash(
        self,
        vault_address: str,
        chain_id: int,
        call_data: str,
    ) -> Any:
        """Prepares and returns the safe tx hash for a multisend tx."""
        self.context.logger.info(
            f"Building safe tx hash: safe={self.synchronized_data.safe_contract_address}\n"
            + f"vault={vault_address}\n"
            + f"chain_id={chain_id}\n"
            + f"call_data={call_data}"
        )

        data = cast(bytes, call_data)

        response_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=vault_address,
            value=0,
            data=data,
            safe_tx_gas=SAFE_GAS,
            operation=SafeOperation.DELEGATE_CALL.value,
            ledger_id="ethereum",
        )

        if response_msg.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                "Couldn't get safe tx hash. Expected response performative "
                f"{ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response_msg.performative.value}: {response_msg}."
            )
            return False

        tx_hash = response_msg.state.body.get("tx_hash", None)
        if tx_hash is None or len(tx_hash) != TX_HASH_LENGTH:
            self.context.logger.error(
                "Something went wrong while trying to get the buy transaction's hash. "
                f"Invalid hash {tx_hash!r} was returned."
            )
            return False

        safe_tx_hash = tx_hash[2:]
        self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
        # temp hack:
        payload_string = hash_payload_to_hex(
            safe_tx_hash, 0, SAFE_GAS, vault_address, data
        )
        self.safe_tx_hash = safe_tx_hash
        self.payload_string = payload_string
        self.call_data = call_data
        return True

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.backtested_orders_hash,
            self.prepare_transactions,
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

    def get_process_store_act(
        self,
        hash_: Optional[str],
        process_fn: Callable[[Any], Generator[None, None, Tuple[Sized, bool]]],
        store_filepath: str,
    ) -> Generator:
        """An async act method for getting some data, processing them, and storing the result.

        1. Get some data using the given hash.
        2. Process them using the given fn.
        3. Send them to IPFS using the given filepath as intermediate storage.

        :param hash_: the hash of the data to process.
        :param process_fn: the function to process the data.
        :param store_filepath: path to the file to store the processed data.
        :yield: None
        """
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            data = yield from self.get_from_ipfs(hash_, SupportedFiletype.JSON)
            sender = self.context.agent_address
            yield from self.get_ipfs_hash_payload_content(
                data, process_fn, store_filepath
            )
            signature, data_json = yield from self.get_data_signature(
                self.payload_string
            )

            self.context.logger.info(f"Data json: {data_json}")
            self.context.logger.info(f"Signature: {signature}")
            self.context.logger.info(f"Safe tx hash: {self.safe_tx_hash}")

            payload = TransactionHashPayload(
                sender,
                signature=signature,
                data_json=data_json,
                tx_hash=self.safe_tx_hash,
            )

        yield from self.finish_behaviour(payload)

    def finish_behaviour(self, payload: BaseTxPayload) -> Generator:
        """Finish the behaviour."""
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_data_signature(self, string: str) -> Generator[None, None, Tuple[str, str]]:
        """Get signature for the data."""
        data_bytes = string.encode("ascii")
        hash_bytes = hashlib.sha256(data_bytes).digest()

        signature_hex = yield from self.get_signature(
            hash_bytes, is_deprecated_mode=True
        )
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        self.context.logger.info(f"Data signature: {signature_hex}")
        return signature_hex, string
