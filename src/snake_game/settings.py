from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class SpeedPreset(Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


SPEED_TICK_INTERVALS: dict[SpeedPreset, float] = {
    SpeedPreset.SLOW: 0.20,
    SpeedPreset.NORMAL: 0.12,
    SpeedPreset.FAST: 0.06,
}

DEFAULT_PATH = Path.home() / ".config" / "snake-game" / "settings.json"


@dataclass(frozen=True)
class Settings:
    speed_preset: SpeedPreset = SpeedPreset.NORMAL
    wrap: bool = False


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_PATH

    def load(self) -> Settings:
        if self._path.exists():
            try:
                data: dict[str, Any] = json.loads(self._path.read_text())
                return Settings(
                    speed_preset=SpeedPreset(data["speed_preset"]),
                    wrap=data["wrap"],
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        defaults = Settings()
        self.save(defaults)
        return defaults

    def save(self, settings: Settings) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "speed_preset": settings.speed_preset.value,
            "wrap": settings.wrap,
        }
        self._path.write_text(json.dumps(data, indent=2) + "\n")
