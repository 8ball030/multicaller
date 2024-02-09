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

"""This module contains the behaviour for executing a strategy."""

from copy import deepcopy
from dataclasses import asdict
from typing import Any, Dict, Generator, List, Optional, Tuple, cast

import yaml

from packages.valory.skills.solana_strategy_evaluator_abci.behaviours.base import (
    StrategyEvaluatorBaseBehaviour,
)
from packages.valory.skills.solana_strategy_evaluator_abci.models import (
    AMOUNT_PARAM,
    GetBalance,
    RPCPayload,
    TokenAccounts,
)
from packages.valory.skills.solana_strategy_evaluator_abci.states.strategy_exec import (
    StrategyExecRound,
)


STRATEGY_KEY = "trading_strategy"
PRICE_DATA_KEY = "price_data"
SWAP_DECISION_FIELD = "signal"
BUY_DECISION = "buy"
SELL_DECISION = "sell"
HODL_DECISION = "hold"
AVAILABLE_DECISIONS = (BUY_DECISION, SELL_DECISION, HODL_DECISION)
NO_SWAP_DECISION = {SWAP_DECISION_FIELD: HODL_DECISION}
SUPPORTED_STRATEGY_LOG_LEVELS = ("info", "warning", "error")
SOL = "SOL"
SOL_ADDRESS = "So11111111111111111111111111111111111111112"
DOWNLOADED_PACKAGES_KEY = "downloaded_ipfs_packages"
COMPONENT_YAML_FILENAME = "component.yaml"
ENTRY_POINT_KEY = "entry_point"
CALLABLE_KEY = "callable"
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
INPUT_MINT = "inputMint"
OUTPUT_MINT = "outputMint"


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


class StrategyExecBehaviour(StrategyEvaluatorBaseBehaviour):
    """A behaviour in which the agents execute the selected strategy and decide on the swap(s)."""

    matching_round = StrategyExecRound

    def __init__(self, **kwargs: Any):
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self.sol_balance: Optional[int] = None
        self.sol_balance_after_swaps: Optional[int] = None

    @property
    def get_balance(self) -> GetBalance:
        """Get the `GetBalance` instance."""
        return self.context.get_balance

    @property
    def token_accounts(self) -> TokenAccounts:
        """Get the `TokenAccounts` instance."""
        return self.context.token_accounts

    def strategy_exec(self, strategy_name: str) -> Optional[Dict[str, str]]:
        """Get the executable strategy's contents."""
        return self.context.shared_state.get(DOWNLOADED_PACKAGES_KEY, {}).get(
            strategy_name, None
        )

    def load_custom_component(
        self, serialized_objects: Dict[str, str]
    ) -> Optional[Tuple[str, str, str]]:
        """Load a custom component package.

        :param serialized_objects: the serialized objects.
        :return: the component.yaml, entry_point.py and callable as tuple.
        """
        # the package MUST contain a component.yaml file
        if COMPONENT_YAML_FILENAME not in serialized_objects:
            self.context.logger.error(
                "Invalid component package. "
                f"The package MUST contain a {COMPONENT_YAML_FILENAME}."
            )
            return None
        # load the component.yaml file
        component_yaml = yaml.safe_load(serialized_objects[COMPONENT_YAML_FILENAME])
        if ENTRY_POINT_KEY not in component_yaml or CALLABLE_KEY not in component_yaml:
            self.context.logger.error(
                "Invalid component package. "
                f"The {COMPONENT_YAML_FILENAME} file MUST contain the {ENTRY_POINT_KEY} and {CALLABLE_KEY} keys."
            )
            return None
        # the name of the script that needs to be executed
        entry_point_name = component_yaml[ENTRY_POINT_KEY]
        # load the script
        if entry_point_name not in serialized_objects:
            self.context.logger.error(
                f"Invalid component package. "
                f"The entry point {entry_point_name!r} is not present in the component package."
            )
            return None
        entry_point = serialized_objects[entry_point_name]
        # the method that needs to be called
        callable_method = component_yaml[CALLABLE_KEY]
        return component_yaml, entry_point, callable_method

    def execute_strategy(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute the strategy and return the results."""
        trading_strategy = kwargs.pop(STRATEGY_KEY, None)
        if trading_strategy is None:
            self.context.logger.error(f"No {trading_strategy!r} was given!")
            return NO_SWAP_DECISION

        strategy = self.strategy_exec(trading_strategy)
        if strategy is None:
            self.context.logger.error(
                f"No executable was found for {trading_strategy=}!"
            )
            return NO_SWAP_DECISION

        res = self.load_custom_component(strategy)
        if res is None:
            return NO_SWAP_DECISION

        _component_yaml, strategy_exec, callable_method = res
        if callable_method in globals():
            del globals()[callable_method]

        exec(strategy_exec, globals())  # pylint: disable=W0122  # nosec
        method = globals().get(callable_method, None)
        if method is None:
            self.context.logger.error(
                f"No {callable_method!r} method was found in {trading_strategy} strategy's executable:\n"
                f"{strategy_exec}."
            )
            return NO_SWAP_DECISION

        return method(*args, **kwargs)

    def get_swap_amount(self) -> int:
        """Get the swap amount."""
        if self.params.use_proxy_server:
            api = self.context.tx_settlement_proxy
        else:
            api = self.context.swap_quotes

        return api.parameters.get(AMOUNT_PARAM, 0)

    def unexpected_res_format_err(self, res: Any) -> None:
        """Error log in case of an unexpected format error."""
        self.context.logger.error(
            f"Unexpected response format from {TOKEN_ACCOUNTS_METHOD!r}: {res}"
        )

    def get_native_balance(self) -> Generator[None, None, Optional[int]]:
        """Get the SOL balance of the given address."""
        if self.sol_balance is not None:
            return self.sol_balance

        payload = RPCPayload(BALANCE_METHOD, [self.params.squad_vault])
        response = yield from self._get_response(self.get_balance, {}, asdict(payload))
        self.sol_balance = self.sol_balance_after_swaps = response
        return response

    def get_token_balance(self, token: str) -> Generator[None, None, Optional[int]]:
        """Get the balance of the token corresponding to the given address."""
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
        if amount is None:
            self.unexpected_res_format_err(response)

        try:
            # typing was warning about int(amount), therefore, we first convert to `str` here
            return int(str(amount))
        except ValueError:
            self.unexpected_res_format_err(response)
            return None

    def is_balance_sufficient(
        self, token: str
    ) -> Generator[None, None, Optional[bool]]:
        """Check whether the balance of the given token is enough to perform the swap transaction."""
        if (
            token == SOL_ADDRESS
            and self.sol_balance_after_swaps is not None
            and self.sol_balance_after_swaps <= 0
        ):
            warning = "Preceding trades are expected to use up all the SOL. Not taking any action."
            self.context.logger.warning(warning)
            return False

        sol_before_swap = self.sol_balance_after_swaps
        swap_cost = self.params.expected_swap_tx_cost
        sol_balance = yield from self.get_native_balance()
        self.sol_balance_after_swaps = cast(int, self.sol_balance_after_swaps)
        if sol_balance is None:
            self.context.logger.error("Failed to get balance for SOL!")
            return None
        if swap_cost > self.sol_balance_after_swaps:
            self.context.logger.warning(
                "There is not enough SOL to cover the expected swap tx's cost. "
                f"SOL balance after preceding swaps ({self.sol_balance_after_swaps}) < swap cost ({swap_cost}). "
                f"Not taking any actions."
            )
            return False
        self.sol_balance_after_swaps -= swap_cost

        compared_balance: Optional[int]
        swap_amount = self.get_swap_amount()
        if token == SOL_ADDRESS:
            # do not use the SOL's address to simplify the log messages
            token = SOL
            token_balance = yield from self.get_native_balance()
            compared_balance = self.sol_balance_after_swaps
            self.sol_balance_after_swaps -= swap_amount
        else:
            token_balance = yield from self.get_token_balance(token)
            compared_balance = token_balance

        # the second part of the statement is unnecessary but avoids typing warning
        if token_balance is None or compared_balance is None:
            self.context.logger.error(f"Failed to get balance for {token}!")
            return None

        self.context.logger.info(f"Balance ({token}): {token_balance}.")
        if swap_amount > compared_balance:
            warning = (
                f"There is not enough balance to cover the swap amount ({swap_amount}) "
            )
            if token == SOL:
                preceding_swaps_amount = token_balance - (
                    sol_before_swap or token_balance
                )

                warning += (
                    f"plus the expected swap tx's cost ({swap_cost}) ["
                    f"also taking into account preceding swaps' amount ({preceding_swaps_amount})] "
                )
                # the swap's cost which was subtracted during the first `get_native_balance` call
                # should be included in the swap amount
                self.sol_balance_after_swaps += swap_amount
                swap_amount += swap_cost
                token_balance -= preceding_swaps_amount
            self.sol_balance_after_swaps += swap_cost
            warning += f"({token_balance} < {swap_amount}) for {token!r}. Not taking any actions."
            self.context.logger.warning(warning)
            return False

        self.context.logger.info("Balance is sufficient.")
        return True

    def get_swap_decision(
        self,
        token_data: Any,
    ) -> Optional[str]:
        """Get the swap decision given a token's data."""
        strategy = self.synchronized_data.selected_strategy
        self.context.logger.info(f"Using trading strategy {strategy!r}.")
        # the following are always passed to a strategy script, which may choose to ignore any
        kwargs: Dict[str, Any] = self.params.strategies_kwargs
        kwargs.update(
            {
                STRATEGY_KEY: strategy,
                PRICE_DATA_KEY: token_data,
            }
        )
        results = self.execute_strategy(**kwargs)
        for level in SUPPORTED_STRATEGY_LOG_LEVELS:
            logger = getattr(self.context.logger, level, None)
            if logger is not None:
                for log in results.get(level, []):
                    logger(log)
        decision = results.get(SWAP_DECISION_FIELD, None)
        if decision is None:
            self.context.logger.error(
                f"Required field {SWAP_DECISION_FIELD!r} was not returned by {strategy} strategy."
                "Not taking any actions."
            )
        if decision not in AVAILABLE_DECISIONS:
            self.context.logger.error(
                f"Invalid decision {decision!r} was detected! Expected one of {AVAILABLE_DECISIONS}."
                "Not taking any actions."
            )
            decision = None

        return decision

    def get_token_swap_position(self, decision: str) -> Optional[str]:
        """Get the position of the non-native token in the swap operation."""
        token_swap_position = None

        if decision == BUY_DECISION:
            token_swap_position = OUTPUT_MINT
        elif decision == SELL_DECISION:
            token_swap_position = INPUT_MINT
        elif decision != HODL_DECISION:
            self.context.logger.error(
                f"Unrecognised decision {decision!r} found! Expected one of {AVAILABLE_DECISIONS}."
            )

        return token_swap_position

    def get_orders(
        self, token_data: Dict[str, Any]
    ) -> Generator[None, None, Tuple[List[Dict[str, str]], bool]]:
        """Get a mapping from a string indicating whether to buy or sell, to a list of tokens."""
        # TODO this method is blocking, needs to be run from an aea skill.
        orders: List[Dict[str, str]] = []
        incomplete = False
        for token, data in token_data.items():
            if token == SOL_ADDRESS:
                continue

            decision = self.get_swap_decision(data)
            if decision is None:
                incomplete = True
                continue

            msg = f"Decided to {decision} token with address {token!r}."
            self.context.logger.info(msg)
            quote_data = {INPUT_MINT: SOL_ADDRESS, OUTPUT_MINT: SOL_ADDRESS}
            token_swap_position = self.get_token_swap_position(decision)
            if token_swap_position is None:
                # holding token, no tx to perform
                continue

            quote_data[token_swap_position] = token
            input_token = quote_data[INPUT_MINT]
            enough_tokens = yield from self.is_balance_sufficient(input_token)
            if not enough_tokens:
                incomplete = True
                continue
            orders.append(quote_data)

        # we only yield here to convert this method to a generator, so that it can be used by `get_process_store_act`
        yield
        return orders, incomplete

    def async_act(self) -> Generator:
        """Do the action."""
        yield from self.get_process_store_act(
            self.synchronized_data.data_hash,
            self.get_orders,
            str(self.swap_decision_filepath),
        )
