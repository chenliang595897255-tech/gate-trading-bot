import logging
import time
from config import Config
from data_sources import market_snapshots, news_headlines
from gate_client import GateClient
from signal_engine import aggregate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    config = Config.from_env()
    gate = GateClient(config.api_key, config.api_secret, config.gate_base_url, config.timeout)
    logging.warning("live_orders_allowed=%s; DRY_RUN=%s", config.live_orders_allowed(), config.dry_run)
    while True:
        try:
            markets = market_snapshots(config.pair, config.timeout)
            news = news_headlines(config.timeout, config.news_max_items) if config.news_enabled else []
            decision = aggregate(markets, news)
            logging.info("decision=%s confidence=%.2f price=%.8f rationale=%s", decision.action, decision.confidence, decision.price, decision.rationale)
            if decision.action in ("BUY", "SELL") and decision.confidence >= 0.70:
                if not config.live_orders_allowed():
                    logging.warning("proposal only; live order blocked: %s", decision.action)
                else:
                    if decision.action == "BUY":
                        amount = f"{config.order_usdt / decision.price:.8f}"
                    else:
                        logging.warning("SELL requires an independently verified local position; no sell was sent")
                        amount = None
                    if amount:
                        order = gate.market_order(config.pair, decision.action.lower(), amount)
                        logging.warning("LIVE ORDER SENT: %s", order)
        except Exception:
            logging.exception("analysis cycle failed")
        time.sleep(config.loop_seconds)


if __name__ == "__main__":
    main()
