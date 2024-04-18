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

import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Set, Tuple, Type, cast

from aea.configurations.constants import _SOLANA_IDENTIFIER

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.portfolio_tracker_abci.models import (
    GetBalance,
    Params,
    RPCPayload,
    TokenAccounts,
)
from packages.valory.skills.portfolio_tracker_abci.payloads import (
    PortfolioTrackerPayload,
)
from packages.valory.skills.portfolio_tracker_abci.rounds import (
    PortfolioTrackerAbciApp,
    PortfolioTrackerRound,
    SynchronizedData,
)


PORTFOLIO_FILENAME = "portfolio.json"
SOL_ADDRESS = "So11111111111111111111111111111111111111112"
BALANCE_METHOD = "getBalance"
TOKEN_ACCOUNTS_METHOD = "getTokenAccountsByOwner"  # nosec
TOKEN_ENCODING = "jsonParsed"  # nosec
TOKEN_AMOUNT_ACCESS_KEYS = (
    "account",
    "data",
    "parsed",
    "info",
    "tokenAmount",
    "amount",
)


def to_content(content: dict) -> bytes:
    """Convert the given content to bytes' payload."""
    return json.dumps(content, sort_keys=True).encode()


def safely_get_from_nested_dict(
    nested_dict: Dict[str, Any], keys: Tuple[str, ...]
) -> Optional[Any]:
    """Get a value safely from a nested dictionary."""
    res = deepcopy(nested_dict)
    for key in keys[:-1]:
        res = res.get(key, {})
        if not isinstance(res, dict):
            return None

    if keys[-1] not in res:
        return None
    return res[keys[-1]]


class PortfolioTrackerBehaviour(BaseBehaviour):
    """Behaviour responsible for tracking the portfolio of the service."""

    matching_round: Type[AbstractRound] = PortfolioTrackerRound

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the strategy evaluator behaviour."""
        super().__init__(**kwargs)
        self.portfolio: Dict[str, int] = {}
        self.portfolio_filepath = Path(self.context.data_dir) / PORTFOLIO_FILENAME

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def get_balance(self) -> GetBalance:
        """Get the `GetBalance` API specs instance."""
        return self.context.get_balance

    @property
    def token_accounts(self) -> TokenAccounts:
        """Get the `TokenAccounts` API specs instance."""
        return self.context.token_accounts

    @property
    def sol_agent_address(self) -> str:
        """Get the agent's Solana address."""
        return self.context.agent_addresses[_SOLANA_IDENTIFIER]

    def _handle_response(
        self,
        api: ApiSpecs,
        res: Optional[dict],
    ) -> Generator[None, None, Optional[Any]]:
        """Handle the response from an API.

        :param api: the `ApiSpecs` instance of the API.
        :param res: the response to handle.
        :return: the response's result, using the given keys. `None` if response is `None` (has failed).
        :yield: None
        """
        if res is None:
            error = f"Could not get a response from {api.api_id!r} API."
            self.context.logger.error(error)
            api.increment_retries()
            yield from self.sleep(api.retries_info.suggested_sleep_time)
            return None

        self.context.logger.info(
            f"Retrieved a response from {api.api_id!r} API: {res}."
        )
        api.reset_retries()
        return res

    def _get_response(
        self,
        api: ApiSpecs,
        dynamic_parameters: Dict[str, str],
        content: Optional[dict] = None,
    ) -> Generator[None, None, Any]:
        """Get the response from an API."""
        specs = api.get_spec()
        specs["parameters"].update(dynamic_parameters)
        if content is not None:
            specs["content"] = to_content(content)

        while not api.is_retries_exceeded():
            res_raw = yield from self.get_http_response(**specs)
            res = api.process_response(res_raw)
            response = yield from self._handle_response(api, res)
            if response is not None:
                return response

        error = f"Retries were exceeded for {api.api_id!r} API."
        self.context.logger.error(error)
        api.reset_retries()
        return None

    def get_native_balance(self, address: str) -> Generator[None, None, Optional[int]]:
        """Get the SOL balance of the given address."""
        payload = RPCPayload(BALANCE_METHOD, [address])
        response = yield from self._get_response(self.get_balance, {}, asdict(payload))
        if response is None:
            self.context.logger.error("Failed to get SOL balance!")
        return response

    def check_balance(self, multisig: bool) -> Generator[None, None, Optional[bool]]:
        """Check whether the balance of the multisig or the agent is above the corresponding threshold."""
        if multisig:
            address = self.params.squad_vault
            theta = self.params.multisig_balance_threshold
            which = "vault"
        else:
            address = self.sol_agent_address
            theta = self.params.agent_balance_threshold
            which = "agent"

        self.context.logger.info(f"Checking the SOl balance of the {which}...")
        balance = yield from self.get_native_balance(address)
        if balance is None:
            return None
        if balance < theta:
            self.context.logger.warning(
                f"The {which}'s SOL balance is below the specified threshold: {balance} < {theta}"
            )
            return False
        self.context.logger.info(f"SOL balance of the {which} is sufficient.")
        if multisig:
            self.portfolio[SOL_ADDRESS] = balance
        return True

    def is_balance_sufficient(self) -> Generator[None, None, Optional[bool]]:
        """Check whether the balance of the multisig and the agent are above the given thresholds."""
        agent_balance = yield from self.check_balance(multisig=False)
        vault_balance = yield from self.check_balance(multisig=True)

        balances = (agent_balance, vault_balance)
        if None in balances:
            return None
        return all(balances)

    def unexpected_res_format_err(self, res: Any) -> None:
        """Error log in case of an unexpected format error."""
        self.context.logger.error(
            f"Unexpected response format from {TOKEN_ACCOUNTS_METHOD!r}: {res}"
        )

    def get_token_balance(self, token: str) -> Generator[None, None, Optional[int]]:
        """Retrieve the balance of the tokens held in the vault."""
        payload = RPCPayload(
            TOKEN_ACCOUNTS_METHOD,
            [
                self.params.squad_vault,
                {"mint": token},
                {"encoding": TOKEN_ENCODING},
            ],
        )
        response = yield from self._get_response(
            self.token_accounts, {}, asdict(payload)
        )
        if response is None:
            return None

        if not isinstance(response, list):
            self.unexpected_res_format_err(response)
            return None

        if len(response) == 0:
            return 0

        value_content = response.pop(0)

        if not isinstance(value_content, dict):
            self.unexpected_res_format_err(response)
            return None

        amount = safely_get_from_nested_dict(value_content, TOKEN_AMOUNT_ACCESS_KEYS)

        try:
            # typing was warning about int(amount), therefore, we first convert to `str` here
            return int(str(amount))
        except ValueError:
            self.unexpected_res_format_err(response)
            return None

    def track_portfolio(self) -> Generator:
        """Track the portfolio of the service."""
        self.context.logger.info("Tracking the portfolio of the service...")
        should_wait = False
        for token in self.params.tracked_tokens:
            self.context.logger.info(f"Tracking {token=}...")

            if token == SOL_ADDRESS:
                # SOL will be populated using a different RPC method, in the `check_balance` method
                continue

            if should_wait:
                # poll in intervals so that we do not get a 429 error code as a response
                yield from self.sleep(self.params.rpc_polling_interval)
            should_wait = True

            balance = yield from self.get_token_balance(token)
            if balance is None:
                self.context.logger.error(
                    f"Portfolio tracking failed! Could not get the vault's balance for {token=}."
                )
                return None
            self.portfolio[token] = balance

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            if self.synchronized_data.is_balance_sufficient is False:
                # wait for some time for the user to take action
                sleep_time = self.params.refill_action_timeout
                self.context.logger.info(
                    f"Waiting for a refill. Checking again in {sleep_time} seconds..."
                )
                yield from self.sleep(sleep_time)

            is_balance_sufficient = yield from self.is_balance_sufficient()
            if is_balance_sufficient is None:
                portfolio_hash = None
            elif not is_balance_sufficient:
                # the value does not matter as the round will transition based on the insufficient balance event
                portfolio_hash = ""
            else:
                yield from self.track_portfolio()
                portfolio_hash = yield from self.send_to_ipfs(
                    str(self.portfolio_filepath),
                    self.portfolio,
                    filetype=SupportedFiletype.JSON,
                )
                if portfolio_hash is None:
                    is_balance_sufficient = None

            sender = self.context.agent_address
            payload = PortfolioTrackerPayload(
                sender, portfolio_hash, is_balance_sufficient
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PortfolioTrackerRoundBehaviour(AbstractRoundBehaviour):
    """PortfolioTrackerRoundBehaviour"""

    initial_behaviour_cls = PortfolioTrackerBehaviour
    abci_app_cls = PortfolioTrackerAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        PortfolioTrackerBehaviour,  # type: ignore
    }
