from dataclasses import dataclass


@dataclass(frozen=True)
class Balance:
    available: float
    locked: float


@dataclass(frozen=True)
class Position:
    base_available: float
    base_locked: float
    quote_available: float


class RiskGate:
    def __init__(self, max_order_usdt: float, max_position_usdt: float, max_daily_loss_usdt: float):
        self.max_order_usdt = max_order_usdt
        self.max_position_usdt = max_position_usdt
        self.max_daily_loss_usdt = max_daily_loss_usdt

    def check(self, action: str, price: float, position: Position, quote_balance: Balance, realized_pnl: float):
        if price <= 0:
            return False, "invalid price"
        if realized_pnl <= -self.max_daily_loss_usdt:
            return False, "daily loss limit reached"
        position_value = position.base_available * price + position.base_locked * price
        if action == "BUY":
            order_value = min(self.max_order_usdt, self.max_position_usdt - position_value)
            if order_value <= 0:
                return False, "maximum position reached"
            if quote_balance.available < order_value:
                return False, "insufficient quote balance"
        elif action == "SELL" and position.base_available <= 0:
            return False, "no verified available base balance"
        return True, "allowed"

    def order_value(self, position: Position, price: float) -> float:
        return max(0.0, min(self.max_order_usdt, self.max_position_usdt - position.base_available * price))
