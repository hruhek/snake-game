# Troubleshooting

## Common issues

- If the terminal UI does not respond to arrow keys, try using WASD or ensure the terminal supports curses input.
- If the pygame window does not appear, confirm pygame is installed and your environment allows GUI windows.
- If the Textual UI does not launch, confirm `textual` is installed and run in a terminal that supports interactive TUI updates.

## Configuration and settings

### Terminal UI (curses)

Source: `src/snake_game/cli.py`

- Grid size: `Game(width=20, height=15)`
- Tick rate: `tick_seconds = 0.12`
- Wrap-around: toggled at runtime with `T` (default: OFF)

### Pygame UI

Source: `src/snake_game/pygame_ui.py`

- Grid size: `Game(width=20, height=15)`
- Tick rate: `TICK_SECONDS = 0.12`
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`
- Wrap-around: toggled at runtime with `T` (default: OFF)

### Textual UI

Source: `src/snake_game/textual_ui.py`

- Grid size: `WIDTH = 20`, `HEIGHT = 15`
- Tick rate: `TICK_SECONDS = 0.12`
- Wrap-around: toggled at runtime with `T` (default: OFF)
