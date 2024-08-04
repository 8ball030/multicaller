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

DEFAULT_MA_PERIOD = 20
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_OVERBOUGHT_THRESHOLD = 70
DEFAULT_RSI_OVERSOLD_THRESHOLD = 30

REQUIRED_FIELDS = frozenset({"transformed_data"})
OPTIONAL_FIELDS = frozenset(
    {"ma_period", "rsi_period", "rsi_overbought_threshold", "rsi_oversold_threshold"}
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


def trend_following_signal(
    transformed_data: List[Tuple[int, float]],
    ma_period: int = DEFAULT_MA_PERIOD,
    rsi_period: int = DEFAULT_RSI_PERIOD,
    rsi_overbought_threshold: int = DEFAULT_RSI_OVERBOUGHT_THRESHOLD,
    rsi_oversold_threshold: int = DEFAULT_RSI_OVERSOLD_THRESHOLD,
) -> Dict[str, Union[str, List[str]]]:
    """Compute the trend following signal"""
    prices = [price for _timestamp, price in transformed_data]

    if len(prices) < max(ma_period, rsi_period + 1):
        return {"signal": NA_SIGNAL}

    ma = sum(prices[-ma_period:]) / ma_period

    gains = [
        prices[i] - prices[i - 1]
        for i in range(1, len(prices))
        if prices[i] > prices[i - 1]
    ]
    losses = [
        -1 * (prices[i] - prices[i - 1])
        for i in range(1, len(prices))
        if prices[i] < prices[i - 1]
    ]

    avg_gain = sum(gains) / rsi_period
    avg_loss = sum(losses) / rsi_period

    if avg_loss != 0:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    else:
        rsi = 100

    if prices[-1] > ma and rsi < rsi_overbought_threshold:
        return {"signal": BUY_SIGNAL}

    if prices[-1] < ma and rsi > rsi_oversold_threshold:
        return {"signal": SELL_SIGNAL}

    return {"signal": HOLD_SIGNAL}


def run(*_args: Any, **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": f"Required kwargs {missing} were not provided."}

    kwargs = remove_irrelevant_fields(kwargs)
    return trend_following_signal(**kwargs)


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
    df = pd.DataFrame(
        rows,
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    df = df.resample(default_ohlcv_period).ohlc()
    df.bfill(inplace=True)
    df.reset_index(inplace=True)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df.columns = [
        "Date Time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "vol_1",
        "vol_2",
        "vol_3",
    ]
    df = df.drop(columns=["vol_1", "vol_2", "vol_3"])
    return df.to_json()


def optimise(*args, **kwargs):  # type: ignore
    """Optimise the strategy."""
    del args, kwargs
    return {"results": {}}


def evaluate(*args, **kwargs):  # type: ignore
    """Evaluate the strategy."""
    del args, kwargs
    return {"sharpe_ratio": -10}
