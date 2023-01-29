class Trade:
    def __init__(self, leveraged_quantity, leverage, leveraged_total_sold, leveraged_total_bought, open_dt,
                 close_dt, stop_loss, take_profit):
        self.leveraged_quantity = leveraged_quantity
        assert leverage >= 1
        self.leverage = leverage
        self.leveraged_total_sold = leveraged_total_sold
        self.leveraged_total_bought = leveraged_total_bought
        self.open_dt = open_dt
        self.close_dt = close_dt
        self.stop_loss = stop_loss
        self.take_profit = take_profit

    def is_stop_loss(self, _):
        raise NotImplementedError

    def is_take_profit(self, _):
        raise NotImplementedError

    def calc_profit(self):
        return self.leveraged_total_sold - self.leveraged_total_bought

    def close(self, total_sold, close_dt):
        raise NotImplementedError

    def get_duration(self):
        return self.close_dt - self.open_dt


class Long(Trade):
    def __init__(self, leveraged_quantity, leveraged_total_bought, open_dt, leverage=1,
                 stop_loss=None, take_profit=None, leveraged_total_sold=None, close_dt=None):
        super(Long, self).__init__(leveraged_quantity, leverage, leveraged_total_sold, leveraged_total_bought,
                                   open_dt, close_dt, stop_loss, take_profit)
        if self.stop_loss is not None and self.take_profit is not None:
            assert self.take_profit > self.stop_loss

    def close(self, leveraged_total_sold, close_dt):
        self.leveraged_total_sold = leveraged_total_sold
        self.close_dt = close_dt

    def is_stop_loss(self, low):
        return self.stop_loss is not None and low <= self.stop_loss

    def is_take_profit(self, high):
        return self.take_profit is not None and high >= self.take_profit


class Short(Trade):
    def __init__(self, leveraged_quantity, leveraged_total_sold, open_dt, leverage=1,
                 stop_loss=None, take_profit=None, leveraged_total_bought=None, close_dt=None):
        super(Short, self).__init__(leveraged_quantity, leverage, leveraged_total_sold, leveraged_total_bought,
                                    open_dt, close_dt, stop_loss, take_profit)
        if self.stop_loss is not None and self.take_profit is not None:
            assert self.stop_loss > self.take_profit

    def close(self, leveraged_total_bought, close_dt):
        self.leveraged_total_bought = leveraged_total_bought
        self.close_dt = close_dt

    def is_stop_loss(self, high):
        return self.stop_loss is not None and high >= self.stop_loss

    def is_take_profit(self, low):
        return self.take_profit is not None and low <= self.take_profit
