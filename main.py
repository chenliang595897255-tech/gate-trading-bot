import logging
import time
from config import Config
from data_sources import market_snapshots, news_headlines, source_health
from gate_client import GateClient
from signal_engine import aggregate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    config = Config.from_env()
    gate = GateClient(config.api_key, config.api_secret, config.gate_base_url, config.timeout)
    if config.run_mode == "live" and not config.live_orders_allowed():
        raise SystemExit("Live mode is not armed: use paper mode unless all live safety flags are deliberate")
    logging.warning("run_mode=%s live_orders_allowed=%s", config.run_mode, config.live_orders_allowed())

    while True:
        try:
            markets = market_snapshots(config.pair, config.timeout)
            health = source_health(markets, config.max_quote_age_seconds)
            logging.info("market_source_health=%s", health)
            news = news_headlines(config.timeout, config.news_max_items) if config.news_enabled else []
            decision = aggregate(markets, news, config.min_market_sources)
            logging.info("decision=%s confidence=%.2f price=%.8f sources=%d rationale=%s", decision.action, decision.confidence, decision.price, decision.sources, decision.rationale)

            if decision.action in ("BUY", "SELL") and decision.confidence >= config.min_confidence:
                if config.run_mode != "live":
                    logging.info("PAPER PROPOSAL ONLY: %s", decision.action)
                elif decision.action == "SELL":
                    logging.error("SELL blocked: exchange reconciliation is required before selling")
                else:
                    amount = f"{config.order_usdt / decision.price:.8f}"
                    order = gate.market_order(config.pair, "buy", amount)
                    logging.warning("LIVE BUY SENT: %s", order)
        except Exception:
            logging.exception("analysis cycle failed; fail-closed")
        time.sleep(config.loop_seconds)


if __name__ == "__main__":
    main()
