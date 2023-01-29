from .broker_calcs import *
from .trade import Long, Short


class Broker:
    def __init__(self,
                 equity=1000,
                 # fees example for trading BTC/USD (symbol a/symbol b)
                 maker_fee=0.0016,  # 0.15% maker fee
                 taker_fee=0.0026,  # 0.26% taker fee
                 symbol_a_margin_opening_fee=0.0001,  # 0.01% opening fee
                 symbol_a_margin_rollover_fee=(0.0001, 4),  # 0.01% rollover fee per 4 hours (applies after 4 hours)
                 positions=None,
                 history=None):
        self.initial_equity = equity
        self.equity = equity
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.symbol_a_margin_opening_fee = symbol_a_margin_opening_fee
        self.symbol_a_margin_rollover_fee = symbol_a_margin_rollover_fee
        self.positions = positions or []
        self.history = history or []

    def open_long(self, price, total, open_dt, fee, leverage=1, stop_loss=None, take_profit=None):
        # calculate total of symbol b with leverage and total
        leveraged_total = total * leverage
        # lowering leveraged amount of symbol b with fee
        leveraged_total_with_fee = lower_value_with_fee(leveraged_total, fee)
        # calculate the equivalent amount of symbol a
        leveraged_quantity_with_fee = calc_quantity(price, leveraged_total_with_fee)
        # create long instance, save leveraged total of symbol b
        # and the quantity of symbol a that has been exchanged
        long = Long(leveraged_quantity_with_fee, leveraged_total, open_dt, leverage, stop_loss, take_profit)
        self.positions.append(long)
        self.equity -= total
        return long

    def close_long(self, price, long, close_dt, fee):
        assert isinstance(long, Long)
        # lowering leveraged amount of symbol a with fee
        leveraged_quantity_with_fee = lower_value_with_fee(long.leveraged_quantity, fee)
        # calculate the equivalent amount of symbol b
        leveraged_total_with_fee = calc_total(price, leveraged_quantity_with_fee)
        # close long, save leveraged total of symbol b that has been exchanged back
        long.close(leveraged_total_with_fee, close_dt)
        self.positions.remove(long)
        self.history.append(long)
        self.equity += long.leveraged_total_bought / long.leverage + long.calc_profit()

    def open_short(self, price, total, open_dt, fee, leverage=1, stop_loss=None, take_profit=None):
        # calculate total of symbol a with leverage and total
        leveraged_quantity = calc_quantity(price, total * leverage)
        # lowering leveraged amount of symbol a with fee
        leveraged_quantity_with_fee = lower_value_with_fee(leveraged_quantity, fee)
        # calculate the equivalent amount of symbol b
        leveraged_total_with_fee = calc_total(price, leveraged_quantity_with_fee)
        # create short instance, save leveraged quantity of symbol a
        # and the total of symbol a that has been exchanged
        short = Short(leveraged_quantity, leveraged_total_with_fee, open_dt, leverage, stop_loss, take_profit)
        self.positions.append(short)
        # borrowed money is not available as regular equity, therefore don't change equity
        return short

    def close_short(self, price, short, close_dt, fee):
        assert isinstance(short, Short)
        # calculate the quantity of symbol a that has been borrowed without leverage
        borrowed_quantity = short.leveraged_quantity / short.leverage
        # calculate the margin fee of symbol a based on opening and rollover
        hours = (close_dt - short.open_dt).total_seconds() / 3600
        margin_fee = calc_margin_fee(hours, self.symbol_a_margin_opening_fee, self.symbol_a_margin_rollover_fee)
        # increasing borrowed quantity with the margin fee
        borrowed_quantity_with_fee = increase_value_with_fee(borrowed_quantity, margin_fee)
        # calculate the total of symbol b for the amount of symbol a that needs to be settled
        # do the calculation by asking, what is the amount of symbol b,
        # that if we were to sell it for a price with a fee,
        # equals a quantity of symbol a which has been increased by the margin fee
        quantity_settle = short.leveraged_quantity + borrowed_quantity_with_fee - borrowed_quantity
        total_settle = calc_total_for_quantity(price, quantity_settle, fee)
        # close long, save the amount of symbol b that was needed to settle the position
        short.close(total_settle, close_dt)
        self.positions.remove(short)
        self.history.append(short)
        self.equity += short.calc_profit()

    def close_trade(self, price, trade, close_dt, fee):
        if isinstance(trade, Long):
            self.close_long(price, trade, close_dt, fee)
        elif isinstance(trade, Short):
            self.close_short(price, trade, close_dt, fee)
        else:
            raise ValueError('trade is neither long or short')

    def undo_positions(self):
        for trade in self.positions:
            if isinstance(trade, Long):
                self.equity += trade.leveraged_total_bought / trade.leverage
        self.positions.clear()

    def reset(self):
        self.equity = self.initial_equity
        self.positions.clear()
        self.history.clear()
