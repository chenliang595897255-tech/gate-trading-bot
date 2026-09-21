from dataclasses import dataclass, field
from datetime import datetime, timezone
import html
import re
import time
import xml.etree.ElementTree as ET
import requests

USER_AGENT = "gate-trading-bot/2.0 (+https://github.com/chenliang595897255-tech/gate-trading-bot)"


@dataclass
class Snapshot:
    source: str
    price: float | None = None
    change: float | None = None
    volume: float | None = None
    timestamp: float = field(default_factory=time.time)
    headlines: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def healthy(self) -> bool:
        return self.error is None and self.price is not None


def _get_json(url: str, timeout: int):
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


def _number(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _source(name: str, reader) -> Snapshot:
    try:
        price, change, volume = reader()
        if price is None or price <= 0:
            raise ValueError("missing or invalid price")
        return Snapshot(name, price, change, volume)
    except Exception as exc:
        return Snapshot(name, error=f"{type(exc).__name__}: {exc}")


def market_snapshots(pair: str, timeout: int) -> list[Snapshot]:
    base, quote = pair.split("_", 1)
    symbol = base + quote
    coinbase_product = f"{base}-{quote}" if quote != "USDT" else f"{base}-USD"

    def gate():
        item = _get_json(f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}", timeout)[0]
        return _number(item.get("last")), _number(item.get("change_percentage")), _number(item.get("base_volume"))

    def binance():
        item = _get_json(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout)
        return _number(item.get("lastPrice")), _number(item.get("priceChangePercent")), _number(item.get("volume"))

    def kraken():
        # Kraken uses XBT instead of BTC and often uses USD for stablecoin pairs.
        kbase = "XBT" if base == "BTC" else base
        kpair = f"{kbase}{"USD" if quote == "USDT" else quote}"
        result = _get_json(f"https://api.kraken.com/0/public/Ticker?pair={kpair}", timeout)
        item = next(iter(result["result"].values()))
        opening = _number(item["o"])
        last = _number(item["c"][0])
        change = ((last - opening) / opening * 100) if last and opening else None
        return last, change, _number(item["v"][1])

    def coinbase():
        item = _get_json(f"https://api.exchange.coinbase.com/products/{coinbase_product}/stats", timeout)
        opening = _number(item.get("open"))
        last = _number(item.get("last"))
        change = ((last - opening) / opening * 100) if last and opening else None
        return last, change, _number(item.get("volume"))

    return [_source("gate", gate), _source("binance", binance), _source("kraken", kraken), _source("coinbase", coinbase)]


def _clean_title(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    return " ".join(value.split())[:300]


def news_headlines(timeout: int, max_items: int) -> list[Snapshot]:
    feeds = [
        ("coindesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("cointelegraph", "https://cointelegraph.com/rss"),
        ("decrypt", "https://decrypt.co/feed"),
    ]
    output = []
    for source, url in feeds:
        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            titles = [_clean_title(node.text) for node in root.findall(".//item/title") if node.text]
            output.append(Snapshot(source, headlines=titles[:max_items]))
        except Exception as exc:
            output.append(Snapshot(source, headlines=[], error=f"{type(exc).__name__}: {exc}"))
    return output


def source_health(snapshots: list[Snapshot], max_age_seconds: int) -> dict:
    now = time.time()
    healthy = [s for s in snapshots if s.healthy and now - s.timestamp <= max_age_seconds]
    return {
        "total": len(snapshots),
        "healthy": len(healthy),
        "failed": [s.source for s in snapshots if not s.healthy],
        "stale": [s.source for s in snapshots if s.healthy and now - s.timestamp > max_age_seconds],
    }
