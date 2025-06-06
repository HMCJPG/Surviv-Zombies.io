# Zombie Survival Arena

This repository contains two versions of a simple zombie survival game:

- **Web Version** (`index.html`) – an HTML5/JavaScript implementation.
- **Python Version** (`zombie_survival.py`) – a Pygame port that can be run locally.

## Running the Python Game

1. Install Python 3 and [Pygame](https://www.pygame.org/). On most systems you can install Pygame with:
   ```bash
   pip install pygame
   ```
2. Launch the game:
   ```bash
   python zombie_survival.py [path_to_map.json]
   ```
   The map argument is optional. If no map is supplied the game generates a random world.

Use **WASD** to move, the mouse to aim and shoot, and press **R** to restart after a game over.

## Map Format

Map files are JSON objects with optional `playerStart`, `rocks`, `walls`, and `trees` fields – similar to the structure used by the web version. See `custom-map.json` for an example.
