import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    pair: str
    order_usdt: float
    max_position_usdt: float
    max_daily_loss_usdt: float
    stop_loss_percent: float
    take_profit_percent: float
    loop_seconds: int
    dry_run: bool
    live_enabled: bool
    live_confirmation: str
    timeout: int
    news_enabled: bool
    news_max_items: int
    gate_base_url: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            api_key=env("GATE_API_KEY"),
            api_secret=env("GATE_API_SECRET"),
            pair=env("TRADING_PAIR", "BTC_USDT"),
            order_usdt=float(env("ORDER_USDT", "20")),
            max_position_usdt=float(env("MAX_POSITION_USDT", "100")),
            max_daily_loss_usdt=float(env("MAX_DAILY_LOSS_USDT", "50")),
            stop_loss_percent=float(env("STOP_LOSS_PERCENT", "0.02")),
            take_profit_percent=float(env("TAKE_PROFIT_PERCENT", "0.04")),
            loop_seconds=int(env("LOOP_SECONDS", "300")),
            dry_run=env("DRY_RUN", "true").lower() == "true",
            live_enabled=env("LIVE_TRADING_ENABLED", "false").lower() == "true",
            live_confirmation=env("LIVE_CONFIRMATION"),
            timeout=int(env("DATA_TIMEOUT_SECONDS", "10")),
            news_enabled=env("NEWS_ENABLED", "true").lower() == "true",
            news_max_items=int(env("NEWS_MAX_ITEMS", "20")),
            gate_base_url=env("GATE_API_BASE_URL", "https://api.gateio.ws").rstrip("/"),
        )

    def live_orders_allowed(self) -> bool:
        return (
            not self.dry_run
            and self.live_enabled
            and self.live_confirmation == "I_UNDERSTAND_RISK"
            and bool(self.api_key)
            and bool(self.api_secret)
        )
