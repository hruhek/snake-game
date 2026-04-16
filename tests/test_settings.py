import json
from pathlib import Path

import pytest

from snake_game.settings import (
    SPEED_TICK_INTERVALS,
    Settings,
    SettingsStore,
    SpeedPreset,
)


class TestSpeedPreset:
    def test_values(self):
        assert SpeedPreset.SLOW.value == "slow"
        assert SpeedPreset.NORMAL.value == "normal"
        assert SpeedPreset.FAST.value == "fast"


class TestSpeedTickIntervals:
    def test_mapping(self):
        assert SPEED_TICK_INTERVALS[SpeedPreset.SLOW] == 0.20
        assert SPEED_TICK_INTERVALS[SpeedPreset.NORMAL] == 0.12
        assert SPEED_TICK_INTERVALS[SpeedPreset.FAST] == 0.06


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.speed_preset == SpeedPreset.NORMAL
        assert s.wrap is False

    def test_custom_values(self):
        s = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
        assert s.speed_preset == SpeedPreset.FAST
        assert s.wrap is True

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.wrap = True


class TestSettingsStore:
    def test_load_returns_defaults_when_file_absent(self, tmp_path: Path):
        store = SettingsStore(path=tmp_path / "missing.json")
        s = store.load()
        assert s == Settings()

    def test_save_then_load(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        store = SettingsStore(path=path)
        original = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
        store.save(original)
        loaded = store.load()
        assert loaded == original

    def test_load_creates_file_with_defaults(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        store = SettingsStore(path=path)
        store.load()
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["speed_preset"] == "normal"
        assert data["wrap"] is False

    def test_save_creates_parent_directory(self, tmp_path: Path):
        path = tmp_path / "nested" / "dir" / "settings.json"
        store = SettingsStore(path=path)
        store.save(Settings())
        assert path.exists()

    def test_load_handles_corrupt_file(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        path.write_text("not json{")
        store = SettingsStore(path=path)
        s = store.load()
        assert s == Settings()
