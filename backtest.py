from .broker import Broker, Long, Short
from .backtest_stats import BacktestStats


class Backtest:
    def __init__(self,
                 df,
                 broker=None,
                 resample_equity_timeframe='D',
                 enforce_stop_loss_first=True,
                 allow_same_row_exit=False,
                 on_stop_loss=None,
                 on_take_profit=None):
        self.df = df
        self.broker = broker or Broker()
        self.index = -1
        self.row = None
        self.previous_row = None
        self.stats = None
        self.resample_equity_timeframe = resample_equity_timeframe
        self.enforce_stop_loss_first = enforce_stop_loss_first
        self.allow_same_row_exit = allow_same_row_exit
        self.on_stop_loss = on_stop_loss
        self.on_take_profit = on_take_profit

    def next(self):
        raise NotImplementedError

    def run_positions_take_profit_and_stop_loss(self, ignore_positions=None):
        open_is_low = self.row.Open == self.row.Low
        open_is_high = self.row.Open == self.row.High
        open_gone_down = False if self.previous_row is None else self.row.Open < self.previous_row.Close
        open_gone_up = False if self.previous_row is None else self.row.Open > self.previous_row.Close
        to_be_closed = []
        for trade in self.broker.positions:
            if ignore_positions is not None and trade in ignore_positions:
                continue
            if isinstance(trade, Long):
                if self.enforce_stop_loss_first:
                    if trade.is_stop_loss(self.row.Low):
                        to_be_closed.append((trade, trade.stop_loss, 0))
                    elif trade.is_take_profit(self.row.High):
                        to_be_closed.append((trade, trade.take_profit, 1))
                else:
                    if open_gone_down and trade.is_stop_loss(self.row.Open):
                        to_be_closed.append((trade, trade.stop_loss, 0))
                    elif open_is_low:
                        if trade.is_take_profit(self.row.High):
                            to_be_closed.append((trade, trade.take_profit, 1))
                        elif trade.is_stop_loss(self.row.Low):
                            to_be_closed.append((trade, trade.stop_loss, 0))
                    else:
                        if trade.is_stop_loss(self.row.Low):
                            to_be_closed.append((trade, trade.stop_loss, 0))
                        elif trade.is_take_profit(self.row.High):
                            to_be_closed.append((trade, trade.take_profit, 1))
            elif isinstance(trade, Short):
                if self.enforce_stop_loss_first:
                    if trade.is_stop_loss(self.row.High):
                        to_be_closed.append((trade, trade.stop_loss, 0))
                    elif trade.is_take_profit(self.row.Low):
                        to_be_closed.append((trade, trade.take_profit, 1))
                else:
                    if open_gone_up and trade.is_stop_loss(self.row.Open):
                        to_be_closed.append((trade, trade.stop_loss, 0))
                    elif open_is_high:
                        if trade.is_take_profit(self.row.Low):
                            to_be_closed.append((trade, trade.take_profit, 1))
                        elif trade.is_stop_loss(self.row.High):
                            to_be_closed.append((trade, trade.stop_loss, 0))
                    else:
                        if trade.is_stop_loss(self.row.High):
                            to_be_closed.append((trade, trade.stop_loss, 0))
                        elif trade.is_take_profit(self.row.Low):
                            to_be_closed.append((trade, trade.take_profit, 1))
            else:
                raise ValueError('trade is neither long or short')
        for trade, price, close_type in to_be_closed:
            self.broker.close_trade(price, trade, self.row.name, self.broker.maker_fee)
            if to_be_closed == 0:
                if self.on_stop_loss is not None:
                    self.on_stop_loss(trade, price)
            elif self.on_take_profit is not None:
                self.on_take_profit(trade, price)

    def run(self, start=-1, end=-1):
        self.index = 0 if start == -1 else start
        end = len(self.df) if end == -1 else end
        assert end > start
        assert end <= len(self.df)
        self.broker.reset()
        while self.index < end:
            self.row = self.df.iloc[self.index]
            self.run_positions_take_profit_and_stop_loss()
            if self.allow_same_row_exit:
                positions_before = self.broker.positions.copy()
            self.next()
            if self.allow_same_row_exit:
                self.run_positions_take_profit_and_stop_loss(positions_before)
            self.index += 1
            self.previous_row = self.row
        if self.broker.positions:
            print(f'no data left to backtest, {len(self.broker.positions)} position{"s" if len(self.broker.positions) > 1 else ""} still open, '
                  f'pretend {"they" if len(self.broker.positions) > 1 else "it"} never existed')
            self.broker.undo_positions()
        self.stats = BacktestStats(self, self.resample_equity_timeframe)
        self.stats.do_analysis()
