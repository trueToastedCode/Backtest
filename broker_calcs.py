def increase_value_with_fee(value, fee):
    return value * (1 + fee)


def lower_value_with_fee(value, fee):
    return value * (1 - fee)


def calc_quantity(price, total):
    return (1 / price) * total


def calc_total(price, quantity):
    return price * quantity


# calculate margin fee based on opening fee and rollover_fee applied to the borrowed hours
def calc_margin_fee(hours, opening_fee, rollover_fee):
    # applying rollover fee stepwise
    # e.g. if rollover_fee was 0.01% per 4 hours:
    # 1. 0 <= hour < 4: no rollover fee
    # 2. 4 <= hour < 8: rollover * 1
    # 3. 8 <= hour < 12: rollover * 2
    # 4. ...
    rollover_fee_count = (hours - (hours % rollover_fee[1])) / rollover_fee[1]
    return opening_fee + rollover_fee[0] * rollover_fee_count


# calculate the total, that if we were to sell it for a price with fee, equals a quantity
def calc_total_for_quantity(price, quantity, fee):
    return quantity / ((1 / price) * (1 - fee))
