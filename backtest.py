from .broker import Broker, Long, Short
from .backtest_stats import BacktestStats


class Backtest:
    def __init__(self, df, broker=None):
        self.df = df
        self.broker = broker or Broker()
        self.index = -1
        self.row = None
        self.stats = None

    def next(self):
        raise NotImplementedError

    def run_positions_take_profit_and_stop_loss(self):
        price_gone_up = self.row.Open < self.row.Close
        to_be_closed = []
        for trade in self.broker.positions:
            if isinstance(trade, Long):
                if price_gone_up:
                    if trade.is_take_profit(self.row.Close):
                        to_be_closed.append((trade, trade.take_profit))
                    elif trade.is_stop_loss(self.row.Close):
                        to_be_closed.append((trade, trade.stop_loss))
                else:
                    if trade.is_stop_loss(self.row.Close):
                        to_be_closed.append((trade, trade.stop_loss))
                    elif trade.is_take_profit(self.row.Close):
                        to_be_closed.append((trade, trade.take_profit))
            elif isinstance(trade, Short):
                if price_gone_up:
                    if trade.is_stop_loss(self.row.Close):
                        to_be_closed.append((trade, trade.stop_loss))
                    elif trade.is_take_profit(self.row.Close):
                        to_be_closed.append((trade, trade.take_profit))
                else:
                    if trade.is_take_profit(self.row.Close):
                        to_be_closed.append((trade, trade.take_profit))
                    elif trade.is_stop_loss(self.row.Close):
                        to_be_closed.append((trade, trade.stop_loss))
            else:
                raise ValueError('trade is neither long or short')
        for trade, price in to_be_closed:
            self.broker.close_trade(price, trade, self.row.name, self.broker.maker_fee)

    def run(self, start=-1, end=-1):
        self.index = 0 if start == -1 else start
        end = len(self.df) if end == -1 else end
        assert end > start
        assert end <= len(self.df)
        self.broker.reset()
        while self.index < end:
            self.row = self.df.iloc[self.index]
            self.run_positions_take_profit_and_stop_loss()
            self.next()
            self.index += 1
        if self.broker.positions:
            print(f'no data left to backtest, {len(self.broker.positions)} position{"s" if len(self.broker.positions) > 1 else ""} still open, '
                  f'pretend {"they" if len(self.broker.positions) > 1 else "it"} never existed')
            self.broker.undo_positions()
        self.stats = BacktestStats(self)
        self.stats.do_analysis()
