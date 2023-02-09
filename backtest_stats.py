from datetime import timedelta

import pandas as pd
import plotly.express as px


def make_table_str(table):
    longest_a, longest_b = 0, 0
    for a, b in table:
        if len(a) > longest_a:
            longest_a = len(a)
        if len(b) > longest_b:
            longest_b = len(b)
    return '\n'.join([f'{a}{(longest_a - len(a) + longest_b - len(b)) * " "}        {b}' for a, b in table])


class BacktestStats:
    def __init__(self, backtest, resample_equity_timeframe=None):
        self.resample_equity_timeframe = resample_equity_timeframe
        self.backtest = backtest
        self.period = None
        self.win_rate = None
        self.equity_trades_profit_df = None
        self.equity_trades_profit_fig = None
        self.min_equity = None
        self.max_equity = None
        self.return_perc = None
        self.av_trade_duration = None
        self.min_trade_duration = None
        self.max_trade_duration = None
        self.av_profit_per_trade = None

    def __str__(self):
        return make_table_str([
            ('Period', 'N/A' if self.period is None else str(self.period.round('1s'))),
            ('Final Equity', str(round(self.backtest.broker.equity, 2))),
            ('Min Equity', 'N/A' if self.min_equity is None else str(round(self.min_equity, 2))),
            ('Max Equity', 'N/A' if self.max_equity is None else str(round(self.max_equity, 2))),
            ('Return [%]', 'N/A' if self.return_perc is None else str(round(self.return_perc * 100, 2))),
            ('Win rate [%]', 'N/A' if self.win_rate is None else str(round(self.win_rate * 100, 2))),
            ('Avg. Trade Duration', 'N/A' if self.av_trade_duration is None else str(self.av_trade_duration.round('1s'))),
            ('Min Trade Duration', 'N/A' if self.min_trade_duration is None else str(self.min_trade_duration.round('1s'))),
            ('Max Trade Duration', 'N/A' if self.max_trade_duration is None else str(self.max_trade_duration.round('1s'))),
            ('Trades', str(len(self.backtest.broker.history))),
            ('Avg. Profit Per Trade', 'N/A' if self.av_profit_per_trade is None else str(round(self.av_profit_per_trade, 2)))
        ])

    def do_analysis(self):
        self.period = self.get_period()
        self.win_rate = self.calc_win_rate()
        self.equity_trades_profit_df = self.get_equity_trades_profit_df()
        self.equity_trades_profit_fig = self.get_equity_trades_profit_fig()
        self.min_equity = self.get_min_equity()
        self.max_equity = self.get_max_equity()
        self.return_perc = self.get_return_perc()
        self.av_trade_duration = self.get_av_trade_duration()
        self.min_trade_duration = self.get_min_trade_duration()
        self.max_trade_duration = self.get_max_trade_duration()
        self.av_profit_per_trade = self.get_av_profit_per_trade()

    def get_period(self):
        return self.backtest.df.index[-1] - self.backtest.df.index[0]

    def calc_win_rate(self):
        if not self.backtest.broker.history:
            return
        win_counter = 0
        for trade in self.backtest.broker.history:
            if trade.calc_profit() > 0:
                win_counter += 1
        return win_counter / len(self.backtest.broker.history)

    def get_equity_trades_profit_df(self):
        df = pd.DataFrame()
        df['Datetime'] = self.backtest.df.index
        equity = [self.backtest.broker.initial_equity]
        for trade in self.backtest.broker.history:
            i = self.backtest.df.index.get_loc(trade.close_dt)
            if len(equity) <= i:
                equity.extend([equity[-1]] * (i - len(equity) + 1))
            equity[i] += trade.calc_profit()
        if len(equity) < len(df):
            equity.extend([equity[-1]] * (len(df) - len(equity)))
        df['Equity'] = equity
        return df

    def get_equity_trades_profit_fig(self):
        if self.resample_equity_timeframe:
            df = self.equity_trades_profit_df.copy()
            df.set_index('Datetime', inplace=True)
            df = df.resample(self.resample_equity_timeframe or 'D').agg({'Equity': 'last'})
            df.reset_index(inplace=True)
            return px.line(df, x='Datetime', y="Equity")
        else:
            return px.line(self.equity_trades_profit_df, x='Datetime', y="Equity")

    def get_min_equity(self):
        return self.equity_trades_profit_df.Equity.min()

    def get_max_equity(self):
        return self.equity_trades_profit_df.Equity.max()

    def get_return_perc(self):
        return (self.backtest.broker.equity - self.backtest.broker.initial_equity) / self.backtest.broker.initial_equity

    def get_av_trade_duration(self):
        if not self.backtest.broker.history:
            return
        total_duration = timedelta()
        for trade in self.backtest.broker.history:
            total_duration += trade.get_duration()
        return total_duration / len(self.backtest.broker.history)

    def get_min_trade_duration(self):
        if not self.backtest.broker.history:
            return
        min_duration = self.backtest.broker.history[0].get_duration()
        for trade in self.backtest.broker.history[1:]:
            duration = trade.get_duration()
            if duration < min_duration:
                min_duration = duration
        return min_duration

    def get_max_trade_duration(self):
        if not self.backtest.broker.history:
            return
        max_duration = self.backtest.broker.history[0].get_duration()
        for trade in self.backtest.broker.history[1:]:
            duration = trade.get_duration()
            if duration > max_duration:
                max_duration = duration
        return max_duration

    def get_av_profit_per_trade(self):
        if not self.backtest.broker.history:
            return
        total_profit = 0
        for trade in self.backtest.broker.history:
            total_profit += trade.calc_profit()
        return total_profit / len(self.backtest.broker.history)
