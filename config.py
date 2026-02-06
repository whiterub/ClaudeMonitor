import json
import os
from dataclasses import dataclass, asdict
from typing import Tuple


CONFIG_DIR = os.path.join(os.getenv("APPDATA", ""), "ClaudeMonitor")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


@dataclass
class Config:
    refresh_interval_seconds: int = 30
    position_x: int = -1
    position_y: int = -1
    opacity: float = 0.9
    show_five_hour: bool = True
    show_seven_day: bool = True
    show_sonnet: bool = True
    ui_size: str = "medium"  # small, medium, large

    @staticmethod
    def load() -> "Config":
        if not os.path.exists(CONFIG_PATH):
            return Config()
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Config(
                refresh_interval_seconds=data.get("refresh_interval_seconds", 30),
                position_x=data.get("position_x", -1),
                position_y=data.get("position_y", -1),
                opacity=data.get("opacity", 0.9),
                show_five_hour=data.get("show_five_hour", True),
                show_seven_day=data.get("show_seven_day", True),
                show_sonnet=data.get("show_sonnet", True),
                ui_size=data.get("ui_size", "medium"),
            )
        except Exception:
            return Config()

    def save(self) -> None:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @property
    def position(self) -> Tuple[int, int]:
        return (self.position_x, self.position_y)

    @position.setter
    def position(self, value: Tuple[int, int]) -> None:
        self.position_x, self.position_y = value
