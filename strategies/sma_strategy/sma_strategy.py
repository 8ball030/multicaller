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

import itertools
from typing import Any, Dict, List, Union

import pandas as pd
from pyalgotrade import plotter, strategy
from pyalgotrade.bar import Bars
from pyalgotrade.barfeed import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.broker.backtesting import TradePercentage
from pyalgotrade.optimizer import local
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.strategy.position import Position
from pyalgotrade.technical import ma, stoch


DEFAULKT_RISK_FREE_RATE = 0.04  # ether risk free rate
DEFAULT_BASE_CURRENCY = "USDT"
DEFAULT_CSV_FILE = "data.csv"


BUY_SIGNAL = "buy"
SELL_SIGNAL = "sell"
HOLD_SIGNAL = "hold"
NA_SIGNAL = "insufficient_data"

DEFAULT_MA_PERIOD = 69
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_OVERBOUGHT_THRESHOLD = 70
DEFAULT_RSI_OVERSOLD_THRESHOLD = 30

REQUIRED_FIELDS = frozenset({"transformed_data", "portfolio_data"})
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


class Strategy(
    strategy.BacktestingStrategy
):  # pylint: disable=too-many-instance-attributes
    """A simple moving average crossover strategy."""

    def __init__(self, feed: GenericBarFeed, instrument: str, smaPeriod: int) -> None:
        """Initialize the strategy."""
        super().__init__(feed)
        self.__instrument = instrument
        self.__position: Position = None
        # We'll use adjusted close values instead of regular close values.
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__sma = ma.SMA(self.__prices, smaPeriod)
        self.__lma = ma.SMA(self.__prices, smaPeriod * 2)
        self.__stoch = stoch.StochasticOscillator(feed[instrument], 100)

    @property
    def sharpe_analyser(self) -> sharpe.SharpeRatio:
        """Get the sharpe analyser."""
        return self.__sharpe_analyser

    @sharpe_analyser.setter
    def sharpe_analyser(self, value: sharpe.SharpeRatio) -> None:
        """Set the sharpe analyser."""
        self.__sharpe_analyser = value

    def getSMA(self) -> ma.SMA:
        """Get the simple moving average."""
        return self.__sma

    def getLMA(self) -> ma.SMA:
        """Get the long moving average."""
        return self.__lma

    def getStoch(self) -> stoch.StochasticOscillator:
        """Get the Stochastic Oscillator."""
        return self.__stoch

    def onEnterCanceled(self, position: Position) -> None:
        """Handle the enter canceled."""
        self.__position = None

    def onExitOk(self, position: Position) -> None:
        """Handle the exit ok."""
        self.__position = None

    def onExitCanceled(self, position: Position) -> None:
        """Handle the exit canceled."""
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars: Bars) -> Dict[str, str]:
        """Handle the bars."""
        close = bars[self.__instrument].getClose()
        prices = self.__prices
        lma, sma, stoc = self.__lma, self.__sma, self.__stoch
        print(f"Close: {close}, LMA: {lma[-1]}, SMA: {sma[-1]}, Stoch: {stoc[-1]}")
        if not lma[-1] or not sma[-1] or not prices[-1] or not stoc[-1]:
            return {"signal": HOLD_SIGNAL}

        if self.__position is None:
            if all(
                [
                    prices[-1] > lma[-1],
                    sma[-1] > lma[-1],
                    stoc[-1] > 60,
                ]
            ):
                shares = int(
                    self.getBroker().getCash()
                    * 0.95
                    / bars[self.__instrument].getPrice()
                )
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
                return {"signal": BUY_SIGNAL}
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and all(
            [prices[-1] < sma[-1], stoc[-1] < 50]
        ):
            self.__position.exitMarket()
            return {"signal": SELL_SIGNAL}
        return {"signal": HOLD_SIGNAL}


def trend_following_signal(  # pylint: disable=too-many-arguments, too-many-locals
    transformed_data: Dict[str, Any],
    portfolio_data: Dict[str, Any],
    ma_period: int = DEFAULT_MA_PERIOD,
    rsi_period: int = DEFAULT_RSI_PERIOD,
    rsi_overbought_threshold: int = DEFAULT_RSI_OVERBOUGHT_THRESHOLD,
    rsi_oversold_threshold: int = DEFAULT_RSI_OVERSOLD_THRESHOLD,
) -> Dict[str, Any]:
    """Compute the trend following signal"""
    results = {}
    cash = portfolio_data.get(DEFAULT_BASE_CURRENCY, 0)
    for token, data in transformed_data.items():
        print(f"Processing signal for {token}")
        feed = prepare_feed(token, data)
        balance = portfolio_data.get(token, 10)
        strat = prepare_strategy(
            feed,
            token,
            ma_period=ma_period,
            rsi_period=rsi_period,
            overbought_threshold=rsi_overbought_threshold,
            oversold_threshold=rsi_oversold_threshold,
        )

        broker = strat.getBroker()
        broker.setCash(cash)
        bars = feed.getNextBars()
        close = bars.getBar(token).getClose()
        feed.reset()
        broker.setShares(token, balance, close)
        strat.run()
        signal = strat.onBars(
            bars,
        )
        results[token] = signal
    return {"signals": results}


def transform(
    price_data: Dict[str, Any],
    default_ohlcv_period: str = "5Min",
) -> Dict[str, Any]:
    """Transform the data."""
    results = {}
    for token_address, market_data in price_data.items():
        df = pd.DataFrame(market_data, columns=["timestamp", "price"])
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
        ]
        df["Volume"] = 10000000
        results[token_address] = df.to_json(index=False)
    return {"transformed_data": results}


def evaluate(
    transformed_data: Dict[str, Any],
    ma_period: int = DEFAULT_MA_PERIOD,
    plot: bool = False,
) -> Dict[str, Any]:
    """Evaluate the strategy."""
    results = {}
    for token, data in transformed_data.items():
        feed = prepare_feed(token, data)
        strat = prepare_strategy(feed, token, ma_period=ma_period)
        if plot:
            plt = plotter.StrategyPlotter(strat, True, True, True)
            plt.getInstrumentSubplot(token).addDataSeries("sma", strat.getSMA())
            plt.getInstrumentSubplot(token).addDataSeries("lma", strat.getLMA())
            plt.getOrCreateSubplot("Stoch").addDataSeries("stoch", strat.getStoch())
        strat.run()
        if plot:
            plt.plot()
        token_strategy_sharpe = strat.sharpe_analyser.getSharpeRatio(
            DEFAULKT_RISK_FREE_RATE
        )
        results[token] = {"sharpe_ratio": token_strategy_sharpe}
    average_sharpe = sum([result["sharpe_ratio"] for result in results.values()]) / len(
        results
    )
    print(f"Average Sharpe Ratio: {average_sharpe}")
    return {"sharpe_ratio": average_sharpe}


def prepare_feed(token: str, data: Dict[str, Any]) -> GenericBarFeed:
    """Prepare the data for the strategy."""
    dataset: pd.DataFrame = pd.read_json(
        data,
    )
    dataset.to_csv(DEFAULT_CSV_FILE, index=False)  # pylint: disable=no-member
    feed = GenericBarFeed(Frequency.MINUTE)
    feed.addBarsFromCSV(token, DEFAULT_CSV_FILE)
    return feed


def prepare_strategy(feed: GenericBarFeed, token: str, **kwargs) -> Strategy:  # type: ignore
    """Prepare the strategy."""
    strat = Strategy(feed, token, **kwargs)
    sharpe_analyser = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpe_analyser)
    strat.sharpe_analyser = sharpe_analyser
    commission = TradePercentage(0.003)
    broker = strat.getBroker()
    broker.setCommission(commission)
    return strat


def run(*_args: Any, **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": f"Required kwargs {missing} were not provided."}

    kwargs = remove_irrelevant_fields(kwargs)
    return trend_following_signal(**kwargs)


def parameters_generator() -> itertools.product:
    """Genethe parameters."""
    return itertools.product(range(10, 100, 10), range(10, 100, 10))


def optimise(*_args: Any, **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
    """Optimise the strategy."""
    fn = "strategies/data/olas_5m.csv"
    feed = GenericBarFeed(Frequency.MINUTE)
    feed.addBarsFromCSV(
        "AAPL",
        fn,
    )
    print("Optimising...")
    print(kwargs)
    results = local.run(Strategy, feed, parameters_generator())
    return results
