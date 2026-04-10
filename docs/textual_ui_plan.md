# Textual UI Design Specification

## Overview

The Textual UI provides a terminal-based interface for the Snake game using the Textual framework with Rich text rendering for colored output.

## Visual Design

### Color Palette

| Element       | Color Code | Hex       | Usage                        |
|---------------|------------|-----------|------------------------------|
| Primary Green | `#6ac470`  | 106,196,112 | Snake head, title, running status |
| Body Green    | `#46a05c`  | 70,160,92  | Snake body                   |
| Orange        | `#e6a86c`  | 230,168,108 | Score, paused status         |
| Coral/Food    | `#e67860`  | 230,120,96  | Food item                    |
| Red/Game Over | `#e5584a`  | 229,88,74   | Game over status             |

| Dark BG       | `#16181c`  | 22,24,28    | Board background             |
| Muted Gray    | `#8a8f9a`  | 138,143,154 | Wrap toggle indicator        |

### Layout

```
┌──────────────────────────────────────────────────────┐
│                    SNAKE (Header)                    │
├──────────────────────────────────────────────────────┤
│                      SNAKE                          │
│  ┌──────────────────────────────────────────────┐   │
│  │                                              │   │
│  │                      @@ oo                   │   │
│  │                       **                     │   │
│  │                                              │   │
│  │                                              │   │
│  │                                              │   │
│  │                                              │   │
│  │                                              │   │
│  │                                              │   │
│  └──────────────────────────────────────────────┘   │
│            Score: 0  RUNNING  Wrap: OFF              │
│  arrows/WASD: move | P: pause | R: restart | T:...  │
└──────────────────────────────────────────────────────┘
```

### Components

#### Header
- **Widget:** `Header` (built-in Textual widget)
- **Purpose:** Displays title and key bindings

#### Title
- **Widget:** `Static`
- **ID:** `title`
- **Content:** `SNAKE` in bold green (`#6ac470`)
- **Alignment:** Center

#### Board
- **Widget:** `Static`
- **ID:** `board`
- **Alignment:** Center
- **Background:** Dark (`#16181c`)
- **Content:** ASCII grid with colored snake and food using Rich markup, surrounded by a green (`#46a05c`) box border (`┌─┐│└┘`)

#### Status
- **Widget:** `Static`
- **ID:** `status`
- **Layout:** `Score: X  STATE  Wrap: X`
- **States:**
  - Running: Green state text
  - Paused: Orange state text
  - Game Over: Red state text

#### Controls
- **Widget:** `Static`
- **ID:** `controls`
- **Alignment:** Center
- **Content:** `arrows/WASD: move | P: pause | R: restart | T: wrap | Q: quit`

## CSS Classes

The following CSS classes are defined for status rendering (though Rich inline markup is used in practice):

| Selector | Color | Purpose |
|----------|-------|---------|
| `#status .score` | `#e6a86c` | Score value |
| `#status .state` | `#6ac470` | RUNNING state |
| `#status .state.paused` | `#e6a86c` | PAUSED state |
| `#status .state.gameover` | `#e5584a` | GAME OVER state |
| `#status .wrap` | `#8a8f9a` | Wrap toggle indicator |

A `Footer` rule sets `width: 100%`.

## Rendering

### Board Rendering (`_render_board`)

The board uses Rich `Text` with inline color markup:

- Snake head: `@@` in green (`#6ac470`)
- Snake body: `oo` in darker green (`#46a05c`)
- Food: `**` in coral (`#e67860`)
- Background: `  ` (two spaces) in dark (`#16181c`)
- Border: Box-drawing characters (`┌─┐│└┘`) in green (`#46a05c`)
- Board width: `width * 2` characters (each cell is 2 chars wide)

### Status Rendering (`_render_status`)

Returns a Rich `Text` composed of:
- Score prefix + value in orange
- State text (RUNNING/PAUSED/GAME OVER) in appropriate color
- Wrap status in muted gray

## Key Bindings

| Key      | Action         | Description              |
|----------|----------------|--------------------------|
| `up` / `w` | `move_up`    | Move snake up            |
| `down` / `s` | `move_down` | Move snake down          |
| `left` / `a` | `move_left` | Move snake left          |
| `right` / `d` | `move_right` | Move snake right        |
| `p`      | `pause`        | Toggle pause             |
| `r`      | `restart`      | Restart game             |
| `t`      | `toggle_wrap`  | Toggle wraparound mode   |
| `q`      | `quit_game`    | Quit game                |

## Game Constants

- **Width:** 20 cells
- **Height:** 20 cells
- **Tick Rate:** 0.12 seconds

## Implementation Notes

- Uses `textual.widgets.Header` for built-in header with key hints
- Uses `rich.text.Text` for colored terminal output (inline Rich markup, not CSS classes)
- Board and status are separate widgets updated independently
- Game observer pattern triggers `refresh_view()` on state changes
