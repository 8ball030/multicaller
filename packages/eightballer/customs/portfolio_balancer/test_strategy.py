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

"""This module contains tests for the trend_following_strategy."""

from datetime import datetime, timedelta

import requests
from packages.eightballer.customs.portfolio_balancer.strategy import run, transform

token = 'OLAS'



def date_range(start_date, end_date, seconds_delta=300):
    """
    Generate a range of dates in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    start = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
    end = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
    current = start
    while current < end:
        yield current.timestamp() * 1000
        current += timedelta(seconds=seconds_delta)

EXAMPLE_MARKETS_DATA = 'https://gateway.autonolas.tech/ipfs/QmSiHSRzUtMQvjDeVomvubR9fwGWMSNDcy9vJAUcaAZaZy/markets.json'
EXAMPLE_PORTFOLIO_DATA = 'https://gateway.autonolas.tech/ipfs/QmWg6cjG2p3QNtNmWXpNZA2nKrQUZvDGZGjQGghk4NxiFQ/portfolio.json'

USDC_ASSET = '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
OLAS_ASSET = '0x54330d28ca3357f294334bdc454a032e7f353416' # USDC is used to price all assets. However this is configurable.

TEST_WEIGHTS = {
    '0x54330d28ca3357f294334bdc454a032e7f353416': 0.5,
    '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913': 0.49,
}

TOKEN_ID_KEY = "token_id"  # nosec B105:hardcoded_password_string

def get_ipfs_data(ipfs_url: str):
    """
    Get the market data.
    """
    return requests.get(ipfs_url).json()


def test_run():
    """
    Test the run function.
    """
    raw_data = get_ipfs_data(EXAMPLE_MARKETS_DATA)
    data = transform(
        **raw_data[OLAS_ASSET],
        )
    
    data = {OLAS_ASSET: data}
    
    portfolio = get_ipfs_data(EXAMPLE_PORTFOLIO_DATA)
    res = run(
        weights=TEST_WEIGHTS,
        portfolio_data=portfolio,
        token_id=OLAS_ASSET,
        **{'transformed_data': data,
           },
    )
    assert res, f'The result: {res} is empty'


    if 'error' in res:
        raise Exception(res['error'])


def test_transform():
    """
    Test the transform function.
    """
    raw_data = get_ipfs_data(EXAMPLE_MARKETS_DATA)
    data = transform(**raw_data[OLAS_ASSET])
    assert data, f'The data: {data} is empty'


