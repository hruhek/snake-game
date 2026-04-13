import json

from snake_game.settings import SPEED_PRESETS, Settings


def test_default_settings():
    settings = Settings()
    assert settings.speed_preset == "Normal"
    assert settings.wrap is False


def test_speed_presets_contains_expected_keys():
    assert "Slow" in SPEED_PRESETS
    assert "Normal" in SPEED_PRESETS
    assert "Fast" in SPEED_PRESETS


def test_tick_seconds_slow():
    settings = Settings(speed_preset="Slow")
    assert settings.tick_seconds == 0.20


def test_tick_seconds_normal():
    settings = Settings(speed_preset="Normal")
    assert settings.tick_seconds == 0.12


def test_tick_seconds_fast():
    settings = Settings(speed_preset="Fast")
    assert settings.tick_seconds == 0.06


def test_save_and_load(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", tmp_path)

    settings = Settings(speed_preset="Fast", wrap=True)
    settings.save()

    loaded = Settings.load()
    assert loaded.speed_preset == "Fast"
    assert loaded.wrap is True


def test_load_missing_file(tmp_path, monkeypatch):
    settings_file = tmp_path / "nonexistent.json"
    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", tmp_path)

    loaded = Settings.load()
    assert loaded.speed_preset == "Normal"
    assert loaded.wrap is False


def test_load_corrupt_json(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{invalid json")
    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", tmp_path)

    loaded = Settings.load()
    assert loaded.speed_preset == "Normal"
    assert loaded.wrap is False


def test_load_invalid_speed_preset(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    data = {"speed_preset": "Turbo", "wrap": True}
    settings_file.write_text(json.dumps(data))
    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", tmp_path)

    loaded = Settings.load()
    assert loaded.speed_preset == "Normal"
    assert loaded.wrap is True


def test_load_defaults_from_partial_file(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}")
    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", tmp_path)

    loaded = Settings.load()
    assert loaded.speed_preset == "Normal"
    assert loaded.wrap is False


def test_save_handles_mkdir_error(monkeypatch):
    class BadDir:
        def mkdir(self, *a, **kw):
            raise OSError("cannot create")

    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", BadDir())
    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", BadDir())

    settings = Settings(speed_preset="Fast", wrap=True)
    settings.save()


def test_load_handles_read_error(monkeypatch, tmp_path):
    class BadFile:
        def exists(self):
            return True

        def read_text(self):
            raise OSError("cannot read")

    monkeypatch.setattr("snake_game.settings.SETTINGS_FILE", BadFile())
    monkeypatch.setattr("snake_game.settings.SETTINGS_DIR", tmp_path)

    loaded = Settings.load()
    assert loaded.speed_preset == "Normal"
    assert loaded.wrap is False
