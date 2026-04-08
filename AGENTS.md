# Agent Notes

## Quick commands

- `make run` / `make run-ui` / `make run-textual`
- `make test` — requires 100% coverage
- `make lint-fix` / `make format`
- `make qa` — format → lint-fix → type-check → test (run before submitting)

Use `uv` for all tooling; never run `python3` directly.

## Public API

Import from `snake_game.game`, not `snake_game.core`. If you add symbols to `core.py`, update the re-export list in `game.py`.

## Docs

- Docs index: `docs/README.md`
- Architecture: `docs/architecture.md`
- Update `docs/troubleshooting.md` if controls/config/timing change.
