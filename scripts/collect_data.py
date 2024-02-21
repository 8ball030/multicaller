#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
#   Copyright 2024 8baller
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
Simple script to collect ohlcv data from the gecko terminal api.

Takes a pool id and collects the data in 1000 row chunks.
"""

import time

import pandas as pd
from geckoterminal_py.client import GeckoTerminalClient


SLEEP_PERIOD = 5
POOL_ID = "0x09d1d767edf8fa23a64c51fa559e0688e526812f"


def get_actual_high(row):
    """Give a row, return the actual high value."""
    a, b, c, d = row["Open"], row["Close"], row["High"], row["Low"]
    return max(a, b, c, d)


def get_actual_low(row):
    """Give a row, return the actual low value."""
    a, b, c, d = row["Open"], row["Close"], row["High"], row["Low"]
    return min(a, b, c, d)


def collect_data(
    pool_id,
    since="2024-01-01 00:00:00Z",
    until="2024-02-28 00:00:00Z",
    limit=1000,
    frequency="5m",
):
    """
    Collect OLAS 5m data

    we will have to chunk the data into 1000 rows

    """

    gt = GeckoTerminalClient()
    done = False
    all_data_df = pd.DataFrame()

    before_timestamp = int(pd.to_datetime(until).timestamp())

    timeout = 0

    while not done:
        df = gt.get_ohlcv_sync(
            "eth", pool_id, frequency, limit=limit, before_timestamp=before_timestamp
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["Date Time"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        all_data_df = pd.concat([all_data_df, df])
        all_data_df = all_data_df.sort_values("timestamp", ascending=True)
        all_data_df = all_data_df.drop_duplicates(subset=["timestamp"], keep="first")

        if len(df) == 0:
            timeout += 1
            if timeout > 5:
                raise Exception("Timeout")
            print("Timeout waiting for ", timeout * SLEEP_PERIOD, " seconds")
            time.sleep(SLEEP_PERIOD * timeout)
            continue

        oldest = all_data_df.timestamp.min()
        before_timestamp = int(oldest.timestamp())
        time.sleep(SLEEP_PERIOD)
        if oldest.timestamp() < pd.to_datetime(since).timestamp():
            done = True
        print(f"Processed Since: {oldest}")

    df = all_data_df[["Date Time", "open", "high", "low", "close", "volume_usd"]]
    df.columns = ["Date Time", "Open", "High", "Low", "Close", "Volume"]

    df["High"] = df.apply(get_actual_high, axis=1)
    df["Low"] = df.apply(get_actual_low, axis=1)
    return df


if __name__ == "__main__":
    print("Collecting OLAS 5m data")
    data = collect_data(POOL_ID)
    data.to_csv("strategies/data/olas_5m.csv", index=False)
    print("Done")
