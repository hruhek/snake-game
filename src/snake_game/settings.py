from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SPEED_PRESETS: dict[str, float] = {
    "Slow": 0.20,
    "Normal": 0.12,
    "Fast": 0.06,
}

SETTINGS_DIR = Path.home() / ".config" / "snake-game"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


@dataclass
class Settings:
    speed_preset: str = "Normal"
    wrap: bool = False

    @property
    def tick_seconds(self) -> float:
        return SPEED_PRESETS[self.speed_preset]

    def save(self) -> None:
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            data = {"speed_preset": self.speed_preset, "wrap": self.wrap}
            SETTINGS_FILE.write_text(json.dumps(data))
        except OSError:
            pass

    @classmethod
    def load(cls) -> Settings:
        if not SETTINGS_FILE.exists():
            return cls()
        try:
            data = json.loads(SETTINGS_FILE.read_text())
            speed_preset = data.get("speed_preset", "Normal")
            wrap = data.get("wrap", False)
            if speed_preset not in SPEED_PRESETS:
                speed_preset = "Normal"
            return cls(speed_preset=speed_preset, wrap=wrap)
        except (json.JSONDecodeError, OSError):
            return cls()
