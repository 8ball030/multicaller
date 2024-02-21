"""
Base Strategy utils.

Used to read data from coingecko and ohlcv files.
"""

import json

import pandas as pd


DEFAULT_ENCODING = "utf-8"


def read_coingecko(file_path: str) -> tuple:
    """Helper function to read coingecko data."""
    data = {}
    with open(file_path, "r", encoding=DEFAULT_ENCODING) as f:
        data = json.loads(f.read())
    timestamps = list(map(lambda x: x[0], data["prices"]))
    prices = list(map(lambda x: x[1], data["prices"]))
    volumes = list(map(lambda x: x[1], data["total_volumes"]))
    return timestamps, prices, volumes


def read_ohlcv(file_path: str) -> tuple:
    """Helper function to read ohlcv data."""
    df = pd.read_csv(file_path)
    timestamps = pd.to_datetime(df["Date Time"]).tolist()
    prices = df["Close"].tolist()
    volumes = df["Volume"].tolist()
    return timestamps, prices, volumes
