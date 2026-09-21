import argparse
import csv
from dataclasses import dataclass


@dataclass
class Trade:
    side: str
    price: float
    amount: float
    pnl: float = 0.0


def sma(values, period):
    return sum(values[-period:]) / period if len(values) >= period else None


def run_backtest(rows, initial_cash, order_usdt, fee, stop_loss, take_profit):
    cash, base, entry = initial_cash, 0.0, 0.0
    trades, equity_curve = [], []
    closes = []
    for row in rows:
        price = float(row["close"])
        closes.append(price)
        if len(closes) < 21:
            equity_curve.append(cash + base * price)
            continue
        short_now, long_now = sma(closes, 5), sma(closes, 20)
        short_prev, long_prev = sma(closes[:-1], 5), sma(closes[:-1], 20)
        buy = short_prev <= long_prev and short_now > long_now
        sell = short_prev >= long_prev and short_now < long_now
        protective = base > 0 and (price <= entry * (1 - stop_loss) or price >= entry * (1 + take_profit))
        if base == 0 and buy and cash >= order_usdt:
            amount = order_usdt / price
            cash -= order_usdt * (1 + fee)
            base += amount
            entry = price
            trades.append(Trade("BUY", price, amount))
        elif base > 0 and (sell or protective):
            proceeds = base * price * (1 - fee)
            pnl = proceeds - base * entry
            cash += proceeds
            trades.append(Trade("SELL", price, base, pnl))
            base, entry = 0.0, 0.0
        equity_curve.append(cash + base * price)
    if base > 0:
        price = float(rows[-1]["close"])
        proceeds = base * price * (1 - fee)
        trades.append(Trade("SELL_EOD", price, base, proceeds - base * entry))
        cash += proceeds
    return cash, trades, equity_curve


def main():
    parser = argparse.ArgumentParser(description="Offline-only Gate bot backtest")
    parser.add_argument("csv", help="CSV with a close column; no API credentials are used")
    parser.add_argument("--cash", type=float, default=1000)
    parser.add_argument("--order-usdt", type=float, default=20)
    parser.add_argument("--fee", type=float, default=0.001)
    parser.add_argument("--stop-loss", type=float, default=0.02)
    parser.add_argument("--take-profit", type=float, default=0.04)
    args = parser.parse_args()
    with open(args.csv, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if len(rows) < 21 or "close" not in rows[0]:
        raise SystemExit("CSV must contain at least 21 rows and a close column")
    final_cash, trades, curve = run_backtest(rows, args.cash, args.order_usdt, args.fee, args.stop_loss, args.take_profit)
    peak = args.cash
    max_drawdown = 0.0
    for equity in curve:
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak if peak else 0)
    pnls = [trade.pnl for trade in trades if trade.side.startswith("SELL")]
    print(f"initial_cash={args.cash:.2f}")
    print(f"final_cash={final_cash:.2f}")
    print(f"return={(final_cash / args.cash - 1) * 100:.2f}%")
    print(f"trades={len(trades)} closed_trades={len(pnls)}")
    print(f"win_rate={(sum(p > 0 for p in pnls) / len(pnls) * 100) if pnls else 0:.2f}%")
    print(f"max_drawdown={max_drawdown * 100:.2f}%")


if __name__ == "__main__":
    main()
