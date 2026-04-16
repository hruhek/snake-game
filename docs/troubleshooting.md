# Troubleshooting

## Common issues

- If the pygame window does not appear, confirm pygame is installed and your environment allows GUI windows.
- If the Textual UI does not launch, confirm `textual` is installed and run in a terminal that supports interactive TUI updates.

## Configuration and settings

Settings are stored in `~/.config/snake-game/settings.json` and managed via the Options screen (Textual) or Options state (Pygame).

### Settings fields

- `speed_preset`: `"slow"`, `"normal"` (default), or `"fast"` — controls tick interval (0.20s, 0.12s, 0.06s)
- `wrap`: `true` or `false` (default) — enables wrap-around movement

### Pygame UI

Source: `src/snake_game/pygame_ui.py`

- Grid size: `Game(width=20, height=20)`
- Tick rate: from `SPEED_TICK_INTERVALS[settings.speed_preset]`
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`
- Wrap-around: from `Settings.wrap` (set in Options state)
- States: MENU → PLAYING / OPTIONS; PLAYING → GAME_OVER → MENU

### Textual UI

Source: `src/snake_game/textual_ui.py`

- Grid size: `WIDTH = 20`, `HEIGHT = 20`
- Tick rate: from `SPEED_TICK_INTERVALS[settings.speed_preset]`
- Wrap-around: from `Settings.wrap` (set in Options screen, persisted via `SettingsStore`)
- Controls: arrows/WASD to move, P to pause, R to restart, Esc to return to menu
- Screens: MenuScreen → GameScreen / OptionsScreen; GameOverOverlay on death (auto-returns after 2s)