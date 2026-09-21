from dataclasses import dataclass
from statistics import mean
from data_sources import Snapshot


@dataclass(frozen=True)
class Decision:
    action: str
    confidence: float
    price: float
    rationale: str


def aggregate(snapshots: list[Snapshot], headlines: list[Snapshot]) -> Decision:
    valid = [item for item in snapshots if item.price is not None]
    if not valid:
        raise RuntimeError("No market data source is available")
    price = mean(item.price for item in valid)
    changes = [item.change for item in valid if item.change is not None]
    momentum = mean(changes) if changes else 0.0
    agreement = sum(1 for item in valid if item.price and abs(item.price - price) / price < 0.01) / len(valid)
    # News is deliberately informational here; do not infer trading direction from headlines alone.
    news_count = sum(len(item.headlines or []) for item in headlines)
    if momentum > 0.5 and agreement >= 0.66:
        action = "BUY"
    elif momentum < -0.5 and agreement >= 0.66:
        action = "SELL"
    else:
        action = "HOLD"
    confidence = min(1.0, max(0.0, 0.5 * agreement + 0.5 * min(abs(momentum) / 2, 1)))
    return Decision(action, confidence, price, f"sources={len(valid)}, agreement={agreement:.2f}, momentum={momentum:.2f}%, headlines={news_count}")
