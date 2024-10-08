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

"""This module contains the trend_following_strategy."""

from typing import Any, Dict, List, Tuple, Union

import pandas as pd


BUY_SIGNAL = "buy"
SELL_SIGNAL = "sell"
HOLD_SIGNAL = "hold"
NA_SIGNAL = "insufficient_data"

MIN_SELL_WEIGHT = 0.05


DEFAULT_WEIGHTS = {
    "0x54330d28ca3357f294334bdc454a032e7f353416": 0.5,
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": 0.5,
}

DEFAULT_ASSET_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

REQUIRED_FIELDS = frozenset(
    {
        "transformed_data", 
        "portfolio_data",
        "token_id",
    }
)
OPTIONAL_FIELDS = frozenset(
    {

        "weights",
        "asset_address",
    }
)
ALL_FIELDS = REQUIRED_FIELDS.union(OPTIONAL_FIELDS)


def check_missing_fields(kwargs: Dict[str, Any]) -> List[str]:
    """Check for missing fields and return them, if any."""
    missing = []
    for field in REQUIRED_FIELDS:
        if kwargs.get(field, None) is None:
            missing.append(field)
    return missing


def remove_irrelevant_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Remove the irrelevant fields from the given kwargs."""
    return {key: value for key, value in kwargs.items() if key in ALL_FIELDS}


def balance(
    transformed_data: List[Tuple[int, float]],
    portfolio_data: Dict[str, float],
    weights: Dict[str, float] = None,
    token_id: str = None,
) -> Dict[str, Union[str, List[str]]]:
    """Compute the trend following signal"""
    if weights is None:
        print("Weights not provided. Using default weights.")
        weights = DEFAULT_WEIGHTS

    def get_asset_price(asset: str) -> float:
        """Get the price of the asset."""
        return pd.DataFrame(transformed_data[token_id.lower()],).sort_values('timestamp').iloc[0].price

    actual_values = {
        asset: get_asset_price(asset) * amount for asset, amount in portfolio_data.items() if asset in weights
    }

    toal_value = sum(actual_values.values())

    actual_weights = {
        asset: value / toal_value for asset, value in actual_values.items()
    }

    

    diffs = {asset: actual_weights[asset] - weights[asset] for asset in weights}

    signal = HOLD_SIGNAL
    if token_id not in diffs:
        signal = HOLD_SIGNAL
    elif diffs[token_id] > 0 + MIN_SELL_WEIGHT:
        signal = SELL_SIGNAL
    elif diffs[token_id] < 0 - MIN_SELL_WEIGHT:
        signal = BUY_SIGNAL

    print(f"Signal for token {token_id}: {signal}")
    return {"signal": signal}


def run(*_args: Any, **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": f"Required kwargs {missing} were not provided."}

    kwargs = remove_irrelevant_fields(kwargs)
    return balance(**kwargs)


def transform(
    prices: List[Tuple[int, float]],
    volumes: List[Tuple[int, float]],
    default_ohlcv_period: str = "5Min",
) -> Dict[str, Any]:
    """Transform the data into an ohlcv dataframe."""
    rows = []
    for values in zip(prices, volumes):
        row = {
            "timestamp": values[0][0],
            "price": values[0][1],
            "Volume": values[1][1],
        }
        rows.append(row)
    return rows



def optimise(*args, **kwargs):  # type: ignore
    """Optimise the strategy."""
    del args, kwargs
    return {"results": {}}


def evaluate(*args, **kwargs):  # type: ignore
    """Evaluate the strategy."""
    del args, kwargs
    return {"sharpe_ratio": -10.0}
