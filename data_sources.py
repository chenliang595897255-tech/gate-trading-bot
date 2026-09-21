from dataclasses import dataclass
import time
import xml.etree.ElementTree as ET
import requests


@dataclass
class Snapshot:
    source: str
    price: float | None = None
    change: float | None = None
    headlines: list[str] | None = None
    error: str | None = None


def fetch_json(url: str, timeout: int):
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "gate-trading-bot/1.0"})
    response.raise_for_status()
    return response.json()


def market_snapshots(pair: str, timeout: int) -> list[Snapshot]:
    symbol = pair.replace("_", "")
    results = []
    sources = [
        ("gate", f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"),
        ("binance", f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"),
        ("coinbase", f"https://api.exchange.coinbase.com/products/{symbol.replace('USDT', '-USD')}/ticker"),
    ]
    for name, url in sources:
        try:
            data = fetch_json(url, timeout)
            if name == "gate":
                results.append(Snapshot(name, float(data[0]["last"]), float(data[0].get("change_percentage", 0))))
            elif name == "binance":
                results.append(Snapshot(name, float(data["lastPrice"]), float(data["priceChangePercent"])))
            else:
                results.append(Snapshot(name, float(data["price"]), None))
        except Exception as exc:
            results.append(Snapshot(name, error=str(exc)))
    return results


def news_headlines(timeout: int, max_items: int) -> list[Snapshot]:
    feeds = [
        ("coindesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("cointelegraph", "https://cointelegraph.com/rss"),
    ]
    output = []
    for source, url in feeds:
        try:
            root = ET.fromstring(requests.get(url, timeout=timeout, headers={"User-Agent": "gate-trading-bot/1.0"}).content)
            titles = [node.text.strip() for node in root.findall(".//item/title") if node.text]
            output.append(Snapshot(source, headlines=titles[:max_items]))
        except Exception as exc:
            output.append(Snapshot(source, headlines=[], error=str(exc)))
    return output
