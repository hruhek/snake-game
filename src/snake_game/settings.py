from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

CONFIG_PATH = Path("~/.config/snake-game/settings.json").expanduser()


class SpeedPreset(Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


SPEED_TICK_INTERVALS = {
    SpeedPreset.SLOW: 0.20,
    SpeedPreset.NORMAL: 0.12,
    SpeedPreset.FAST: 0.06,
}


@dataclass(frozen=True)
class Settings:
    speed_preset: SpeedPreset = SpeedPreset.NORMAL
    wrap: bool = False


class SettingsStore:
    def load(self) -> Settings:
        if not CONFIG_PATH.exists():
            return Settings()
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        return Settings(
            speed_preset=SpeedPreset(data["speed_preset"]),
            wrap=data["wrap"],
        )

    def save(self, settings: Settings) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(
                {
                    "speed_preset": settings.speed_preset.value,
                    "wrap": settings.wrap,
                },
                f,
            )
