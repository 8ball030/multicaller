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

"""This module contains the trend_following_strategy."""

from typing import Any, Dict, List


BUY_SIGNAL = "buy"
SELL_SIGNAL = "sell"
HOLD_SIGNAL = "hold"
NA_SIGNAL = "insufficient_data"

REQUIRED_FIELDS = ("price_data", "ma_period", "rsi_period")


def check_missing_fields(kwargs: Dict[str, Any]) -> List[str]:
    """Check for missing fields and return them, if any."""
    missing = []
    for field in REQUIRED_FIELDS:
        if kwargs.get(field, None) is None:
            missing.append(field)
    return missing


def remove_irrelevant_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Remove the irrelevant fields from the given kwargs."""
    return {key: value for key, value in kwargs.items() if key in REQUIRED_FIELDS}


def trend_following_signal(
    price_data: List[float], ma_period: int, rsi_period: int
) -> Dict[str, str]:
    """Compute the trend following signal"""
    if len(price_data) < max(ma_period, rsi_period + 1):
        return {"signal": NA_SIGNAL}

    ma = sum(price_data[-ma_period:]) / ma_period

    gains = [
        price_data[i] - price_data[i - 1]
        for i in range(1, len(price_data))
        if price_data[i] > price_data[i - 1]
    ]
    losses = [
        -1 * (price_data[i] - price_data[i - 1])
        for i in range(1, len(price_data))
        if price_data[i] < price_data[i - 1]
    ]

    avg_gain = sum(gains) / rsi_period if gains else 0
    avg_loss = sum(losses) / rsi_period if losses else 0

    if avg_loss != 0:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    else:
        rsi = 100

    if price_data[-1] > ma and rsi < 70:
        return {"signal": BUY_SIGNAL}

    if price_data[-1] < ma and rsi > 30:
        return {"signal": SELL_SIGNAL}

    return {"signal": HOLD_SIGNAL}


def run(*_args, **kwargs) -> Dict[str, str]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": f"Required kwargs {missing} were not provided."}

    kwargs = remove_irrelevant_fields(kwargs)
    return trend_following_signal(**kwargs)
