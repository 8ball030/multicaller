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

"""
Tests for the strategy module
"""

import json
import pytest

import random
import pandas as pd



from strategies.sma_strategy import sma_strategy as sma_strategy
from strategies.rsi_strategy import rsi_strategy
from strategies.trend_following_strategy import trend_following_strategy
from unittest import TestCase

import json

import pandas as pd


DEFAULT_OHLCV_PERIOD = "5Min"
DEFAULT_ENCODING = "utf-8"


strategies = [sma_strategy, rsi_strategy, trend_following_strategy]

OHLCV_DATA = "strategies/data/olas_5m.csv"


def read_ohlcv(file_path: str) -> tuple:
    """Helper function to read ohlcv data."""
    df = pd.read_csv(file_path)
    timestamps = pd.to_datetime(df["Date Time"]).tolist()
    prices = df["Close"].tolist()
    volumes = df["Volume"].tolist()
    return timestamps, prices, volumes

@pytest.fixture
def raw_data():
    """Generate raw data for testing."""
    timestamps, prices, volumes = read_ohlcv(OHLCV_DATA)
    TEST_RAW_DATA = {
        "volumes": [(ts, val) for ts, val in zip(timestamps, volumes)],
        "prices": [(ts, val) for ts, val in zip(timestamps, prices)]
    }
    return TEST_RAW_DATA

@pytest.mark.parametrize("func,path", [(read_ohlcv, OHLCV_DATA)])
def test_generate_data(func, path):
    """Test the data generation function."""
    timestamps, prices, volumes = func(path)
    assert len(timestamps) == len(prices) == len(volumes)
    
@pytest.mark.parametrize("strategy", strategies)
def test_evaluate(strategy, raw_data):
    """Test the evaluate function."""
    data = strategy.transform(**raw_data)
    results = strategy.evaluate(**data, plot=False)
    assert "sharpe_ratio" in results

@pytest.mark.parametrize("strategy", strategies)
def test_transform(strategy, raw_data):
    """Test the transform function."""
    data = strategy.transform(**raw_data)
    assert "transformed_data" in data


@pytest.mark.parametrize("strategy", strategies)
def test_run(strategy, raw_data):
    """Test the complete strategy."""
    kwargs = strategy.transform(**raw_data)
    result = strategy.run(**kwargs, portfolio_data={"token_a": 1000, "USDT": 1000})
    assert "error" not in result, f"Error in {strategy.__name__} strategy: {result['error']}"
        
@pytest.mark.parametrize("strategy", strategies)
def test_optimise(strategy, raw_data):
    """Test the optimise function."""
    kwargs = strategy.transform(**raw_data)
    result = strategy.optimise(**kwargs, portfolio_data={"token_a": 1000, "USDT": 1000})
    assert "error" not in result, f"Error in {strategy.__name__} strategy: {result['error']}"
