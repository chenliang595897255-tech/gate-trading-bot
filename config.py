import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def boolean(name: str, default: str = "false") -> bool:
    return env(name, default).lower() in {"1", "true", "yes", "on"}


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
    run_mode: str
    live_confirmation: str
    live_armed: bool
    timeout: int
    news_enabled: bool
    news_max_items: int
    max_quote_age_seconds: int
    min_market_sources: int
    min_confidence: float
    gate_base_url: str

    @classmethod
    def from_env(cls) -> "Config":
        mode = env("RUN_MODE", "paper").lower()
        if mode not in {"paper", "live"}:
            raise ValueError("RUN_MODE must be paper or live")
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
            run_mode=mode,
            live_confirmation=env("LIVE_CONFIRMATION"),
            live_armed=boolean("LIVE_ARMED"),
            timeout=int(env("DATA_TIMEOUT_SECONDS", "10")),
            news_enabled=boolean("NEWS_ENABLED", "true"),
            news_max_items=int(env("NEWS_MAX_ITEMS", "20")),
            max_quote_age_seconds=int(env("MAX_QUOTE_AGE_SECONDS", "30")),
            min_market_sources=int(env("MIN_MARKET_SOURCES", "3")),
            min_confidence=float(env("MIN_SIGNAL_CONFIDENCE", "0.70")),
            gate_base_url=env("GATE_API_BASE_URL", "https://api.gateio.ws").rstrip("/"),
        )

    def live_orders_allowed(self) -> bool:
        return all((
            self.run_mode == "live",
            self.live_armed,
            self.live_confirmation == "I_UNDERSTAND_RISK",
            bool(self.api_key),
            bool(self.api_secret),
        ))
