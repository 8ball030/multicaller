"""
Volume weighted average price (VWAP) strategy.

This strategy is based on the VWAP indicator and it's designed to trade a single instrument.

"""
import itertools

from pyalgotrade import plotter, strategy
from pyalgotrade.bar import Bars
from pyalgotrade.barfeed import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.broker.backtesting import TradePercentage
from pyalgotrade.optimizer import local
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.strategy.position import Position
from pyalgotrade.technical import vwap


def parameters_generator() -> itertools.product:
    """Generate parameters for the strategy."""
    instrument = ["token_a"]
    vwapWindowSize = range(5, 50)
    threshold = [f / 1e4 for f in range(5, 20, 1)]

    return itertools.product(instrument, vwapWindowSize, threshold)


class VWAPMomentum(strategy.BacktestingStrategy):
    """VWAPMomentum strategy."""

    def __init__(
        self,
        feed: GenericBarFeed,
        instrument: str,
        vwapWindowSize: int,
        threshold: float,
    ) -> None:
        """Initialize the VWAPMomentum strategy."""
        super().__init__(feed)
        self.__instrument = instrument
        self.__vwap = vwap.VWAP(feed[instrument], vwapWindowSize)
        self.__threshold = threshold
        self.__longPos = None
        self.__shortPos = None

    def getVWAP(self) -> vwap.VWAP:
        """Get the VWAP."""
        return self.__vwap

    def onBars(self, bars: Bars) -> None:
        """Handle the bars."""
        vwap_now = self.__vwap[-1]
        if vwap_now is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        price = bars[self.__instrument].getClose()

        can_afford = self.getBroker().getCash()

        to_buy = can_afford / price

        if price > vwap_now * (1 + self.__threshold) and not shares:
            self.marketOrder(self.__instrument, to_buy * 0.99)
        elif price < vwap_now * (1 - self.__threshold) and shares:
            self.marketOrder(self.__instrument, -shares)

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
        """Handle the exit canceled."""
        # If the exit was canceled, re-submit it.
        position.exitMarket()


def main(plot: bool, optimize: bool = False) -> None:
    """Runs the VWAPMomentum strategy."""
    instrument = "AAPL"
    vwapWindowSize = 25
    threshold = 0.005

    fn = "../data/olas_5m.csv"

    feed = GenericBarFeed(Frequency.MINUTE)
    feed.addBarsFromCSV(
        "AAPL",
        fn,
    )

    strat = VWAPMomentum(feed, instrument, vwapWindowSize, threshold)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    broker = strat.getBroker()
    broker.setCash(100)

    commission = TradePercentage(0.003)
    broker.setCommission(commission)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("vwap", strat.getVWAP())

    strat.run()

    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))
    if plot:
        plt.plot()

    if optimize:
        local.run(VWAPMomentum, feed, parameters_generator())


if __name__ == "__main__":
    main(False, True)
