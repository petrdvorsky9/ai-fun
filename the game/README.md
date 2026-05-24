# PIKA QUEST  —  A Pokemon GBC-style Adventure

A top-down RPG built entirely in Python + Pygame, visually inspired by
**Pokemon Yellow** and **Pokemon Silver** on the Game Boy Color.

## How to run

```powershell
pip install pygame
python game.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move |
| Enter / Space / Z | Interact (talk to NPCs, read signs) |
| Escape | Quit |

## What's in the game

- **Pallet Town** — a scrollable GBC-style town map (40 × 36 tiles)
- **6 buildings** — Pokemon Center, Poke Mart, Gym, 3 houses (each with a coloured roof)
- **4 NPCs** — Prof. Oak, a Girl, a Fisher, a Hiker — each with multi-page dialogue
- **4 sign posts** — readable with Enter
- **Terrain variety** — grass, paths, trees, tall grass, flowers, sand beach, animated lake
- **Animated player sprite** — drawn from coloured rectangles, 4 directions, walking animation
- **GBC dialog box** — typewriter reveal, speaker name tab, flashing page arrow
- **Title screen** — animated walking sprite, starfield, logo

## Visual style

All graphics are drawn procedurally with `pygame.draw` primitives —
no external image files needed.  The colour palette is hand-matched to
the Pokemon Silver / Yellow GBC palette (greens, tans, water blues,
red roofs, pixel-style character sprites).
