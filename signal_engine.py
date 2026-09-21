from dataclasses import dataclass
from statistics import median
from data_sources import Snapshot


@dataclass(frozen=True)
class Decision:
    action: str
    confidence: float
    price: float
    rationale: str
    sources: int


def aggregate(snapshots: list[Snapshot], headlines: list[Snapshot], min_sources: int = 3) -> Decision:
    valid = [item for item in snapshots if item.healthy and item.price and item.price > 0]
    if len(valid) < min_sources:
        raise RuntimeError(f"insufficient healthy market sources: {len(valid)}/{min_sources}")

    price = median(item.price for item in valid)
    changes = [item.change for item in valid if item.change is not None]
    momentum = sum(changes) / len(changes) if changes else 0.0
    dispersion = max(abs(item.price - price) / price for item in valid)
    agreement = max(0.0, 1.0 - min(dispersion / 0.01, 1.0))
    news_count = sum(len(item.headlines) for item in headlines)
    failed_news = sum(1 for item in headlines if item.error)

    if agreement >= 0.75 and momentum > 0.5:
        action = "BUY"
    elif agreement >= 0.75 and momentum < -0.5:
        action = "SELL"
    else:
        action = "HOLD"

    momentum_score = min(abs(momentum) / 2, 1)
    confidence = min(1.0, 0.6 * agreement + 0.4 * momentum_score)
    rationale = (
        f"market_sources={len(valid)}, median_price={price:.8f}, "
        f"dispersion={dispersion * 100:.3f}%, momentum={momentum:.2f}%, "
        f"news={news_count}, failed_news={failed_news}"
    )
    return Decision(action, confidence, price, rationale, len(valid))
