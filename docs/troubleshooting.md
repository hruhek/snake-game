# Troubleshooting

## Common issues

- If the pygame window does not appear, confirm pygame is installed and your environment allows GUI windows.
- If the Textual UI does not launch, confirm `textual` is installed and run in a terminal that supports interactive TUI updates.

## Configuration and settings

Settings are stored in `~/.config/snake-game/settings.json` and persist across app restarts.

### Game speed

- **Slow**: tick interval 0.20 seconds
- **Normal**: tick interval 0.12 seconds (default)
- **Fast**: tick interval 0.06 seconds

Configurable in the Options screen (keys 1/2/3).

### Wrap-around

- Default: OFF
- Configurable in the Options screen (key W to toggle).
- Wrap-around mode uses `WraparoundGameFactory`; standard mode uses `GameFactory`.

### Pygame UI

Source: `src/snake_game/pygame_ui.py`

- Grid size: `Game(width=20, height=20)`
- Tick rate: determined by `Settings.speed_preset`
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`

### Textual UI

Source: `src/snake_game/textual_ui.py`

- Grid size: `WIDTH = 20`, `HEIGHT = 20`
- Tick rate: determined by `Settings.speed_preset`

## Controls

### Menu screen

| Key        | Action          |
|------------|-----------------|
| 1 / Enter  | Start New Game  |
| 2          | Options         |
| 3 / Esc / Q| Exit           |

### Options screen

| Key        | Action          |
|------------|-----------------|
| 1          | Speed: Slow     |
| 2          | Speed: Normal   |
| 3          | Speed: Fast     |
| W          | Toggle Wrap     |
| Esc / Enter| Back to Menu   |

### Game screen

| Key        | Action          |
|------------|-----------------|
| Arrows/WASD| Move           |
| P          | Pause           |
| R          | Restart         |
| Esc        | Back to Menu    |
| Q          | Quit            |