import logging
import time
import uuid

from config import Config
from data_sources import market_snapshots, news_headlines, source_health
from execution import ExecutionEngine, ExecutionError
from gate_client import GateClient
from risk import Balance, Position, RiskGate
from signal_engine import aggregate
from state import StateStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def balance(accounts, currency):
    for item in accounts:
        if item.get("currency") == currency:
            return Balance(float(item.get("available", 0)), float(item.get("locked", 0)))
    return Balance(0.0, 0.0)


def main():
    config = Config.from_env()
    base, quote = config.pair.split("_", 1)
    gate = GateClient(config.api_key, config.api_secret, config.gate_base_url, config.timeout)
    state_store, state = StateStore(), StateStore().load()
    risk = RiskGate(config.order_usdt, config.max_position_usdt, config.max_daily_loss_usdt)
    executor = ExecutionEngine(gate, config.pair, config.order_poll_seconds, config.order_timeout_seconds, config.max_slippage_percent)

    if config.run_mode == "live" and not config.live_orders_allowed():
        raise SystemExit("Live mode is not armed")

    while True:
        try:
            markets = market_snapshots(config.pair, config.timeout)
            health = source_health(markets, config.max_quote_age_seconds)
            if health["healthy"] < config.min_market_sources:
                logging.error("fail-closed: %s", health)
                time.sleep(config.loop_seconds)
                continue
            news = news_headlines(config.timeout, config.news_max_items) if config.news_enabled else []
            decision = aggregate(markets, news, config.min_market_sources)
            logging.info("decision=%s confidence=%.2f price=%.8f", decision.action, decision.confidence, decision.price)
            if decision.action not in ("BUY", "SELL") or decision.confidence < config.min_confidence:
                time.sleep(config.loop_seconds)
                continue

            if config.run_mode != "live":
                logging.info("PAPER PROPOSAL ONLY: %s", decision.action)
                time.sleep(config.loop_seconds)
                continue

            accounts = gate.accounts()
            base_balance, quote_balance = balance(accounts, base), balance(accounts, quote)
            position = Position(base_balance.available, base_balance.locked, quote_balance.available)
            allowed, reason = risk.check(decision.action, decision.price, position, quote_balance, state.realized_pnl)
            if not allowed:
                logging.warning("risk blocked %s: %s", decision.action, reason)
                time.sleep(config.loop_seconds)
                continue
            open_orders = gate.open_orders(config.pair)
            if len(open_orders) >= config.max_open_orders:
                logging.warning("risk blocked: %s open orders", len(open_orders))
                time.sleep(config.loop_seconds)
                continue

            if decision.action == "BUY":
                value = risk.order_value(position, decision.price)
                amount = value / decision.price
            else:
                amount = position.base_available
            client_id = f"t-bot-{uuid.uuid4().hex[:12]}"
            try:
                confirmed = executor.submit_and_confirm(decision.action.lower(), f"{amount:.8f}", client_id, decision.price)
                state.last_order_id = str(confirmed.get("id", ""))
                state.last_signal_key = f"{decision.action}:{decision.price:.8f}"
                state_store.save(state)
            except ExecutionError:
                logging.exception("execution failed; no state update")
        except Exception:
            logging.exception("cycle failed; fail-closed")
        time.sleep(config.loop_seconds)


if __name__ == "__main__":
    main()
