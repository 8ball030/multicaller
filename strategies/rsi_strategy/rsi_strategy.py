"""
Simple RSI strategy.

Uses the RSI indicator to generate buy and sell signals.
"""
import itertools
from typing import Any, Dict, List, Tuple, Union

import pandas as pd
from pyalgotrade import plotter, strategy
from pyalgotrade.bar import Bar, Bars
from pyalgotrade.barfeed import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.broker.backtesting import TradePercentage
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.strategy.position import Position
from pyalgotrade.technical import cross, ma, rsi


DEFAULT_CSV_FILE = "data.csv"
DEFAULT_BASE_CURRENCY = "USDT"
DEFAULT_MA_PERIOD = 69
DEFAULKT_RISK_FREE_RATE = 0.04  # ether risk free rate
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


def transform(
    price_data: Dict[str, List[Tuple[int, float]]],
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


def prepare_feed(token: str, data: Dict[str, Any]) -> GenericBarFeed:
    """Prepare the data for the strategy."""
    dataset = pd.read_json(
        data,
    )
    dataset.to_csv(DEFAULT_CSV_FILE, index=False)  # pylint: disable=no-member
    feed = GenericBarFeed(Frequency.MINUTE)
    feed.addBarsFromCSV(token, DEFAULT_CSV_FILE)
    return feed


def prepare_strategy(  # pylint: disable=too-many-arguments
    feed: GenericBarFeed,
    token: str,
    entry_sma: int = 200,
    exit_sma: int = 80,
    rsi_period: int = 30,
    overbought_threshold: int = 60,
    oversold_threshold: int = 30,
) -> strategy.BacktestingStrategy:
    """Prepare the strategy."""
    strat = Strategy(
        feed,
        token,
        entry_sma,
        exit_sma,
        rsi_period,
        overbought_threshold,
        oversold_threshold,
    )
    sharpe_analyser = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpe_analyser)
    strat.sharpe_analyser = sharpe_analyser
    commission = TradePercentage(0.003)
    broker = strat.getBroker()
    broker.setCommission(commission)
    return strat


def evaluate(
    transformed_data: Dict[str, Any],
    ma_period: int = DEFAULT_MA_PERIOD,
    plot: bool = False,
) -> Dict[str, Any]:
    """Evaluate the strategy."""
    results = {}
    for token, data in transformed_data.items():
        feed = prepare_feed(token, data)
        strat = prepare_strategy(feed, token, ma_period)
        if plot:
            plt = plotter.StrategyPlotter(strat, True, True, True)
            plt.getInstrumentSubplot(token).addDataSeries(
                "Entry MA", strat.getEntrySMA()
            )
            plt.getInstrumentSubplot(token).addDataSeries("Exit MA", strat.getExitSMA())
            plt.getOrCreateSubplot("Rsi").addDataSeries("RSI", strat.getRSI())
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


def signal(
    transformed_data: Dict[str, Any],
    portfolio_data: Dict[str, Any],
    ma_period: int = DEFAULT_MA_PERIOD,
) -> Dict[str, Any]:
    """Compute the trend following signal"""
    # we return the signal for each token
    results = {}
    cash = portfolio_data.get(DEFAULT_BASE_CURRENCY, 0)
    for token, data in transformed_data.items():
        print(f"Processing signal for {token}")
        feed = prepare_feed(token, data)
        balance = portfolio_data.get(token, 10)
        strat = prepare_strategy(feed, token, ma_period)
        broker = strat.getBroker()
        broker.setCash(cash)
        new_bar = feed.getNextBars()
        close = new_bar.getBar(token).getClose()
        feed.reset()
        broker.setShares(token, balance, close)
        strat.run()
        new_signal = strat.onBars(
            new_bar,
        )
        results[token] = new_signal
    return {"signals": results}


def run(*_args: Any, **kwargs: Any) -> Dict[str, Union[str, List[str]]]:
    """Run the strategy."""
    missing = check_missing_fields(kwargs)
    if len(missing) > 0:
        return {"error": f"Required kwargs {missing} were not provided."}

    kwargs = remove_irrelevant_fields(kwargs)
    return signal(**kwargs)


def optimise(*args, **kwargs) -> Dict[str, Union[str, List[str]]]:  # type: ignore
    """Optimise the strategy."""
    del args, kwargs
    return {"error": "Not implemented"}


class Strategy(
    strategy.BacktestingStrategy
):  # pylint: disable=too-many-instance-attributes
    """The RSI strategy."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        feed: GenericBarFeed,
        instrument: str,
        entrySMA: int,
        exitSMA: int,
        rsiPeriod: int,
        overBoughtThreshold: int,
        overSoldThreshold: int,
    ):
        """Initialise the strategy."""
        super().__init__(feed)
        self.__instrument = instrument
        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)
        self.__priceDS = feed[instrument].getPriceDataSeries()
        self.__entrySMA = ma.SMA(self.__priceDS, entrySMA)
        self.__exitSMA = ma.SMA(self.__priceDS, exitSMA)
        self.__rsi = rsi.RSI(self.__priceDS, rsiPeriod)
        self.__overBoughtThreshold = overBoughtThreshold
        self.__overSoldThreshold = overSoldThreshold
        self.__longPos: Position = None
        self.__shortPos: Position = None

    @property
    def sharpe_analyser(self) -> sharpe.SharpeRatio:
        """Get the sharpe analyser."""
        return self.__sharpe_analyser

    @sharpe_analyser.setter
    def sharpe_analyser(self, value: sharpe.SharpeRatio) -> None:
        """Set the sharpe analyser."""
        self.__sharpe_analyser = value

    def getEntrySMA(self) -> ma.SMA:
        """Get the entry SMA."""
        return self.__entrySMA

    def getExitSMA(self) -> ma.SMA:
        """Get the exit SMA."""
        return self.__exitSMA

    def getRSI(self) -> rsi.RSI:
        """Get the RSI."""
        return self.__rsi

    def onEnterCanceled(self, position: Position) -> None:
        """Handle the enter canceled."""
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            raise AssertionError("Unknown position")

    def onExitOk(self, position: Position) -> None:
        """Handle the exit ok."""
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            raise AssertionError("Unknown position")

    def onExitCanceled(self, position: Position) -> None:
        """Handle the exit canceled. Re-submit it on the next bar."""
        position.exitMarket()

    def onBars(self, bars: Bars) -> Dict[str, str]:
        """Handle the bars."""
        if (
            self.__exitSMA[-1] is None
            or self.__entrySMA[-1] is None
            or self.__rsi[-1] is None
        ):
            return {"signal": "HOLD"}

        new_bar = bars[self.__instrument]
        if self.__longPos is not None:
            if self.exitLongSignal():
                self.__longPos.exitMarket()
                return {"signal": "SELL"}
        else:
            if self.enterLongSignal(new_bar):
                shares = int(
                    self.getBroker().getCash()
                    * 0.9
                    / bars[self.__instrument].getPrice()
                )
                self.__longPos = self.enterLong(self.__instrument, shares, True)
                return {"signal": "BUY"}
        return {"signal": "HOLD"}

    def enterLongSignal(self, new_bar: Bar) -> bool:
        """Check for the long signal."""
        del new_bar
        return self.__rsi[-1] <= self.__overSoldThreshold

    def exitLongSignal(self) -> bool:
        """Check for the exit long signal."""
        return (
            self.__rsi[-1] >= self.__overBoughtThreshold
            and not self.__longPos.exitActive()
            and self.__exitSMA[-1] < self.__entrySMA[-1]
        )

    def enterShortSignal(self, new_bar: Bar) -> bool:
        """Check for the short signal."""
        del new_bar
        return self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

    def exitShortSignal(self) -> bool:
        """Check for the exit short signal."""
        return (
            cross.cross_below(self.__priceDS, self.__exitSMA)
            and not self.__shortPos.exitActive()
        )


def parameters_generator() -> List[Tuple[str, int, int, int, int, int]]:
    """Generate the parameters"""
    instrument = ["token_a"]
    entrySMA = range(5, 8)
    exitSMA = range(5, 8)
    rsiPeriod = range(9, 10)
    overBoughtThreshold = range(90, 92)
    overSoldThreshold = range(15, 17)
    results = list(
        itertools.product(
            instrument,
            entrySMA,
            exitSMA,
            rsiPeriod,
            overBoughtThreshold,
            overSoldThreshold,
        )
    )
    print(f"Length of results: {len(results)}")
    return results
