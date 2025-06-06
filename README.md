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

## Multiplayer Server

A simple WebSocket server is provided in `server.js` to synchronize players across clients.
Start the server with:

```bash
node server.js
```

The web version will automatically connect to `ws://localhost:8765` when opened in a browser.
For the Python version, simply run the game while the server is running:

```bash
python zombie_survival.py
```

Multiple clients can connect and see each other's position, bullets and zombies.

### Testing the Server

A basic connectivity test is available:

```bash
node tests/connect_test.js
```

This script starts the server and performs a WebSocket handshake to verify it is reachable.
