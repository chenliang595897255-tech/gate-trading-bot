import logging
import time
import uuid

from config import Config
from data_sources import market_snapshots, news_headlines, source_health
from gate_client import GateClient
from risk import Balance, Position, RiskGate
from signal_engine import aggregate
from state import StateStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _balance(accounts, currency: str) -> Balance:
    for item in accounts:
        if item.get("currency") == currency:
            return Balance(float(item.get("available", 0)), float(item.get("locked", 0)))
    return Balance(0.0, 0.0)


def main():
    config = Config.from_env()
    base, quote = config.pair.split("_", 1)
    gate = GateClient(config.api_key, config.api_secret, config.gate_base_url, config.timeout)
    state_store = StateStore()
    state = state_store.load()
    risk = RiskGate(config.order_usdt, config.max_position_usdt, config.max_daily_loss_usdt)

    if config.run_mode == "live" and not config.live_orders_allowed():
        raise SystemExit("Live mode is not armed; use RUN_MODE=paper unless every live safety flag is deliberate")

    logging.warning("run_mode=%s live_orders_allowed=%s", config.run_mode, config.live_orders_allowed())

    while True:
        try:
            markets = market_snapshots(config.pair, config.timeout)
            health = source_health(markets, config.max_quote_age_seconds)
            if health["healthy"] < config.min_market_sources:
                logging.error("fail-closed: insufficient market sources: %s", health)
                time.sleep(config.loop_seconds)
                continue

            news = news_headlines(config.timeout, config.news_max_items) if config.news_enabled else []
            decision = aggregate(markets, news, config.min_market_sources)
            logging.info("decision=%s confidence=%.2f price=%.8f rationale=%s", decision.action, decision.confidence, decision.price, decision.rationale)

            accounts = gate.accounts() if config.run_mode == "live" else []
            position = Position(
                base_available=_balance(accounts, base).available,
                base_locked=_balance(accounts, base).locked,
                quote_available=_balance(accounts, quote).available,
            )
            quote_balance = _balance(accounts, quote)

            if decision.action in ("BUY", "SELL") and decision.confidence >= config.min_confidence:
                allowed, reason = risk.check(decision.action, decision.price, position, quote_balance, state.realized_pnl)
                if not allowed:
                    logging.warning("risk blocked %s: %s", decision.action, reason)
                elif config.run_mode != "live":
                    logging.info("PAPER PROPOSAL ONLY: %s", decision.action)
                elif decision.action == "SELL":
                    amount = f"{position.base_available:.8f}"
                    order = gate.market_order(config.pair, "sell", amount, f"t-bot-{uuid.uuid4().hex[:12]}")
                    state.last_order_id = str(order.get("id", ""))
                    state_store.save(state)
                    logging.warning("LIVE SELL SENT; reconciliation required: %s", order)
                else:
                    value = risk.order_value(position, decision.price)
                    amount = f"{value / decision.price:.8f}"
                    order = gate.market_order(config.pair, "buy", amount, f"t-bot-{uuid.uuid4().hex[:12]}")
                    state.last_order_id = str(order.get("id", ""))
                    state_store.save(state)
                    logging.warning("LIVE BUY SENT; poll order before updating state: %s", order)
        except Exception:
            logging.exception("cycle failed; fail-closed")
        time.sleep(config.loop_seconds)


if __name__ == "__main__":
    main()
