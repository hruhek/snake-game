from snake_game.settings import Settings, SettingsStore, SpeedPreset


def test_speed_preset_enum():
    assert SpeedPreset.SLOW.value == "slow"
    assert SpeedPreset.NORMAL.value == "normal"
    assert SpeedPreset.FAST.value == "fast"


def test_settings_defaults():
    s = Settings()
    assert s.speed_preset == SpeedPreset.NORMAL
    assert s.wrap is False


def test_settings_frozen():
    s = Settings()
    try:
        s.speed_preset = SpeedPreset.FAST
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass


def test_settings_store_load_creates_default(tmp_path, monkeypatch):
    fake_home = tmp_path / "config" / "snake-game"
    monkeypatch.setenv("HOME", str(tmp_path))
    import snake_game.settings as settings_module

    original = settings_module.CONFIG_PATH
    settings_module.CONFIG_PATH = fake_home / "settings.json"
    try:
        store = SettingsStore()
        result = store.load()
        assert result.speed_preset == SpeedPreset.NORMAL
        assert result.wrap is False
    finally:
        settings_module.CONFIG_PATH = original


def test_settings_store_save_load_round_trip(tmp_path, monkeypatch):
    fake_home = tmp_path / "config" / "snake-game"
    fake_home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path))
    import snake_game.settings as settings_module

    original = settings_module.CONFIG_PATH
    settings_module.CONFIG_PATH = fake_home / "settings.json"
    try:
        store = SettingsStore()
        original_settings = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
        store.save(original_settings)
        loaded = store.load()
        assert loaded == original_settings
    finally:
        settings_module.CONFIG_PATH = original
