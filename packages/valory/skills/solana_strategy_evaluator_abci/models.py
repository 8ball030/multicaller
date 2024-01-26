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

"""This module contains the models for the skill."""

from typing import Any, Dict, Iterable, List, Optional

from aea.skills.base import SkillContext

from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.solana_strategy_evaluator_abci.rounds import (
    StrategyEvaluatorAbciApp,
)


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = StrategyEvaluatorAbciApp

    def __init__(self, *args: Any, skill_context: SkillContext, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, skill_context=skill_context, **kwargs)
        self.instructions: Optional[List[Dict[str, Any]]] = None

        if (
            self.context.params.use_proxy_server
            and self.synchronized_data.max_participants != 1
        ):
            raise ValueError("Cannot use proxy server with a multi-agent service!")


def _raise_incorrect_config(key: str, values: Any) -> None:
    """Raise a `ValueError` for incorrect configuration of a nested_list workaround."""
    raise ValueError(
        f"The given configuration for {key!r} is incorrectly formatted: {values}!"
        "The value is expected to be a list of lists that can be represented as a dictionary."
    )


def nested_list_todict_workaround(
    kwargs: Dict,
    key: str,
) -> Dict:
    """Get a nested list from the kwargs and convert it to a dictionary."""
    values = list(kwargs.get(key, []))
    if len(values) == 0:
        raise ValueError(f"No {key!r} specified in agent's configurations: {kwargs}!")
    if any(not issubclass(type(nested_values), Iterable) for nested_values in values):
        _raise_incorrect_config(key, values)
    if any(len(nested_values) % 2 == 1 for nested_values in values):
        _raise_incorrect_config(key, values)
    return {value[0]: value[1] for value in values}


class StrategyEvaluatorParams(BaseParams):
    """Strategy evaluator's parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters' object."""
        self.strategies_kwargs: Dict[str, List[Any]] = nested_list_todict_workaround(
            kwargs, "strategies_kwargs"
        )
        self.use_proxy_server: bool = self._ensure("use_proxy_server", kwargs, bool)
        super().__init__(*args, **kwargs)


class SwapQuotesSpecs(ApiSpecs):
    """A model that wraps ApiSpecs for the Jupiter quotes specifications."""


class SwapInstructionsSpecs(ApiSpecs):
    """A model that wraps ApiSpecs for the Jupiter instructions specifications."""


class TxSettlementProxy(ApiSpecs):
    """A model that wraps ApiSpecs for the Solana transaction settlement proxy server."""
