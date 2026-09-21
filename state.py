import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import date


@dataclass
class BotState:
    day: str = ""
    realized_pnl: float = 0.0
    last_order_id: str = ""
    last_signal_key: str = ""


class StateStore:
    def __init__(self, path: str = "data/bot_state.json"):
        self.path = path

    def load(self) -> BotState:
        try:
            with open(self.path, encoding="utf-8") as handle:
                state = BotState(**json.load(handle))
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            state = BotState()
        if state.day != date.today().isoformat():
            state.day = date.today().isoformat()
            state.realized_pnl = 0.0
        return state

    def save(self, state: BotState) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="bot-state-", dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(asdict(state), handle, indent=2)
                handle.write("\n")
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
