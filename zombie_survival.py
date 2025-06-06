import pygame
import math
import random
import json
import os
import sys

# Screen dimensions
import socket, base64, hashlib, struct
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# World dimensions (large world like the JS version)
WORLD_WIDTH = 20000
WORLD_HEIGHT = 20000

PLAYER_SPEED = 2
BULLET_SPEED = 5
FIRE_RATE = 500  # milliseconds
MAGAZINE_SIZE = 6
RELOAD_TIME = 2000

class WebSocketClient:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.sock = None
        self.id = None

    def connect(self):
        s = socket.create_connection((self.host, self.port))
        key = base64.b64encode(os.urandom(16)).decode()
        headers = (
            f"GET / HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.send(headers.encode())
        resp = s.recv(1024)
        if b"101" not in resp:
            s.close()
            raise ConnectionError("WebSocket handshake failed")
        s.setblocking(False)
        self.sock = s

    def send(self, data):
        if not self.sock:
            return
        payload = json.dumps(data).encode()
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(length)
        elif length < 65536:
            header.append(126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(127)
            header.extend(struct.pack(">Q", length))
        self.sock.sendall(header + payload)

    def recv(self):
        if not self.sock:
            return None
        try:
            first = self.sock.recv(2)
            if not first:
                return None
            _, b2 = first
            length = b2 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self.sock.recv(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self.sock.recv(8))[0]
            mask = self.sock.recv(4)
            data = bytearray(self.sock.recv(length))
            for i in range(length):
                data[i] ^= mask[i % 4]
            return json.loads(data.decode())
        except BlockingIOError:
            return None
        except Exception:
            return None

ROCK_RADIUS = 45


def load_map(path):
    """Load map data from JSON file if available."""
    if not path or not os.path.exists(path):
        return [], [], [], {'x': WORLD_WIDTH // 2, 'y': WORLD_HEIGHT // 2}

    with open(path, 'r') as f:
        data = json.load(f)

    rocks = [{
        'x': r['x'],
        'y': r['y'],
        'hp': r.get('hp', 8)
    } for r in data.get('rocks', [])]

    walls = [w for w in data.get('walls', [])]
    trees = [t for t in data.get('trees', [])]
    player_start = data.get('playerStart', {'x': WORLD_WIDTH // 2, 'y': WORLD_HEIGHT // 2})
    return rocks, walls, trees, player_start


def spawn_world_objects():
    """Generate random world objects similar to the JS version."""
    rocks = [{
        'x': random.random() * WORLD_WIDTH,
        'y': random.random() * WORLD_HEIGHT,
        'hp': 8
    } for _ in range(300)]

    walls = [{
        'x': random.random() * WORLD_WIDTH,
        'y': random.random() * WORLD_HEIGHT,
        'width': 200 if random.random() > 0.5 else 40,
        'height': 40 if random.random() > 0.5 else 200
    } for _ in range(50)]

    trees = [{
        'x': random.random() * WORLD_WIDTH,
        'y': random.random() * WORLD_HEIGHT,
        'radius': 240,
        'hp': 5
    } for _ in range(200)]

    return rocks, walls, trees


def main(map_path=None):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Load map
    rocks, walls, trees, player_start = load_map(map_path)
    if not rocks and not walls and not trees:
        rocks, walls, trees = spawn_world_objects()

    player = {
        'x': player_start['x'],
        'y': player_start['y'],
        'radius': 20,
        'hp': 100,
        'angle': 0
    }

    bullets = []
    enemies = []

    last_shot = 0
    bullets_fired = 0
    is_reloading = False
    reload_timer = 0

    wave = 1
    zombies_killed = 0
    zombies_to_next_wave = random.randint(10, 15)
    score = 0
    game_over = False
    spawn_timer = 0

    other_players = {}
    net = WebSocketClient()
    try:
        net.connect()
    except Exception as e:
        print("Network disabled:", e)
        net = None
    def spawn_enemy():
        buffer = 400
        side = random.randint(0, 3)
        if side == 0:
            x = player['x'] + random.random() * SCREEN_WIDTH - SCREEN_WIDTH / 2
            y = player['y'] - buffer
        elif side == 1:
            x = player['x'] + buffer
            y = player['y'] + random.random() * SCREEN_HEIGHT - SCREEN_HEIGHT / 2
        elif side == 2:
            x = player['x'] + random.random() * SCREEN_WIDTH - SCREEN_WIDTH / 2
            y = player['y'] + buffer
        else:
            x = player['x'] - buffer
            y = player['y'] + random.random() * SCREEN_HEIGHT - SCREEN_HEIGHT / 2

        r = random.random()
        if r < 0.6:
            enemy = {'x': x, 'y': y, 'radius': 25, 'speed': 1.0, 'hp': 1}
        elif r < 0.85:
            enemy = {'x': x, 'y': y, 'radius': 20, 'speed': 2.0, 'hp': 1}
        elif r < 0.9:
            enemy = {'x': x, 'y': y, 'radius': 40, 'speed': 3.0, 'hp': 0.5}
        else:
            enemy = {'x': x, 'y': y, 'radius': 35, 'speed': 0.6, 'hp': 3}
        enemies.append(enemy)

    def is_blocked(x, y):
        for r in rocks:
            d = math.hypot(r['x'] - x, r['y'] - y)
            if d < ROCK_RADIUS + player['radius']:
                return True
        for w in walls:
            if (x + player['radius'] > w['x'] and x - player['radius'] < w['x'] + w['width'] and
                    y + player['radius'] > w['y'] and y - player['radius'] < w['y'] + w['height']):
                return True
        for t in trees:
            d = math.hypot(t['x'] - x, t['y'] - y)
            if d < t['radius'] * 0.25 + player['radius']:
                return True
        return False

    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
                # restart
                player['hp'] = 100
                player['x'] = WORLD_WIDTH // 2
                player['y'] = WORLD_HEIGHT // 2
                score = 0
                bullets.clear()
                enemies.clear()
                game_over = False
                wave = 1
                zombies_killed = 0
                zombies_to_next_wave = random.randint(10, 15)

        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        player['angle'] = math.atan2(my - SCREEN_HEIGHT / 2, mx - SCREEN_WIDTH / 2)

        if net:
            net.send({"type": "state", "player": player, "bullets": bullets, "zombies": enemies})
            msg = net.recv()
            if msg and msg.get("type") == "world":
                other_players = msg["world"]["players"]
                enemies = msg["world"]["zombies"]
                bullets = msg["world"]["bullets"]
                if net.id is None:
                    net.id = msg["id"]
        if not game_over:
            new_x = player['x']
            new_y = player['y']
            if keys[pygame.K_w]:
                new_y -= PLAYER_SPEED
            if keys[pygame.K_s]:
                new_y += PLAYER_SPEED
            if keys[pygame.K_a]:
                new_x -= PLAYER_SPEED
            if keys[pygame.K_d]:
                new_x += PLAYER_SPEED

            if not is_blocked(new_x, player['y']):
                player['x'] = new_x
            if not is_blocked(player['x'], new_y):
                player['y'] = new_y

            if pygame.mouse.get_pressed()[0]:
                now = pygame.time.get_ticks()
                if not is_reloading and now - last_shot >= FIRE_RATE:
                    muzzle_x = player['x'] + math.cos(player['angle']) * (player['radius'] + 15)
                    muzzle_y = player['y'] + math.sin(player['angle']) * (player['radius'] + 15)
                    bullets.append({
                        'x': muzzle_x,
                        'y': muzzle_y,
                        'dx': math.cos(player['angle']) * BULLET_SPEED,
                        'dy': math.sin(player['angle']) * BULLET_SPEED
                    })
                    last_shot = now
                    bullets_fired += 1
                    if bullets_fired >= MAGAZINE_SIZE:
                        is_reloading = True
                        reload_timer = RELOAD_TIME

            if is_reloading:
                reload_timer -= dt
                if reload_timer <= 0:
                    is_reloading = False
                    bullets_fired = 0

            # update bullets
            for b in bullets[:]:
                b['x'] += b['dx']
                b['y'] += b['dy']
                if b['x'] < -1000 or b['x'] > WORLD_WIDTH + 1000 or b['y'] < -1000 or b['y'] > WORLD_HEIGHT + 1000:
                    bullets.remove(b)
                    continue
                hit = False
                for r in rocks:
                    if math.hypot(r['x'] - b['x'], r['y'] - b['y']) < ROCK_RADIUS + 4:
                        r['hp'] -= 1
                        bullets.remove(b)
                        if r['hp'] <= 0:
                            rocks.remove(r)
                        hit = True
                        break
                if hit:
                    continue
                for t in trees:
                    if math.hypot(t['x'] - b['x'], t['y'] - b['y']) < t['radius'] + 4:
                        t['hp'] -= 1
                        bullets.remove(b)
                        if t['hp'] <= 0:
                            trees.remove(t)
                        hit = True
                        break

            # update enemies
            spawn_timer += dt
            if spawn_timer >= 1000:
                spawn_timer = 0
                spawn_enemy()

            for e in enemies[:]:
                dx = player['x'] - e['x']
                dy = player['y'] - e['y']
                dist = math.hypot(dx, dy)
                blocked = False
                for r in rocks:
                    if math.hypot(e['x'] - r['x'], e['y'] - r['y']) < e['radius'] + ROCK_RADIUS:
                        blocked = True
                        break
                for w in walls:
                    if (e['x'] + e['radius'] > w['x'] and e['x'] - e['radius'] < w['x'] + w['width'] and
                            e['y'] + e['radius'] > w['y'] and e['y'] - e['radius'] < w['y'] + w['height']):
                        blocked = True
                        break
                if not blocked and dist > 0:
                    e['x'] += (dx / dist) * e['speed']
                    e['y'] += (dy / dist) * e['speed']

                if dist < e['radius'] + player['radius']:
                    enemies.remove(e)
                    player['hp'] -= 10
                    if player['hp'] <= 0:
                        game_over = True
                    continue

                for b in bullets[:]:
                    if math.hypot(e['x'] - b['x'], e['y'] - b['y']) < e['radius'] + 4:
                        e['hp'] -= 1
                        bullets.remove(b)
                        if e['hp'] <= 0:
                            enemies.remove(e)
                            score += 10
                            zombies_killed += 1
                            if zombies_killed >= zombies_to_next_wave:
                                wave += 1
                                zombies_killed = 0
                                zombies_to_next_wave = random.randint(10, 15)
                        break

        camera_x = player['x'] - SCREEN_WIDTH // 2
        camera_y = player['y'] - SCREEN_HEIGHT // 2
        screen.fill((34, 165, 47))

        # Draw world bounds background
        map_left = max(0, -camera_x)
        map_top = max(0, -camera_y)
        map_right = min(WORLD_WIDTH - camera_x, SCREEN_WIDTH)
        map_bottom = min(WORLD_HEIGHT - camera_y, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (34, 165, 47), (map_left, map_top, map_right - map_left, map_bottom - map_top))

        for t in trees:
            tx = t['x'] - camera_x
            ty = t['y'] - camera_y
            # canopy
            pygame.draw.circle(screen, (34, 139, 34), (int(tx), int(ty)), int(t['radius']), 0)
            # trunk
            pygame.draw.circle(screen, (92, 64, 51), (int(tx), int(ty)), int(t['radius'] * 0.25))

        for w in walls:
            rect = pygame.Rect(w['x'] - camera_x, w['y'] - camera_y, w['width'], w['height'])
            pygame.draw.rect(screen, (139, 90, 43), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

        for r in rocks:
            pygame.draw.circle(screen, (100, 100, 100), (int(r['x'] - camera_x), int(r['y'] - camera_y)), ROCK_RADIUS)
            pygame.draw.circle(screen, (0, 0, 0), (int(r['x'] - camera_x), int(r['y'] - camera_y)), ROCK_RADIUS, 1)

        for b in bullets:
            pygame.draw.circle(screen, (255, 165, 0), (int(b['x'] - camera_x), int(b['y'] - camera_y)), 4)
        for pid, p in other_players.items():
            if net and net.id == int(pid):
                continue
            pygame.draw.circle(screen, (0, 0, 255), (int(p["x"] - camera_x), int(p["y"] - camera_y)), player["radius"])

        for e in enemies:
            color = (0, 255, 0)
            if e['speed'] > 1.5 and e['radius'] <= 20:
                color = (255, 255, 0)
            elif e['radius'] >= 35 and e['speed'] < 1:
                color = (128, 0, 128)
            elif e['radius'] >= 40:
                color = (255, 255, 255)
            pygame.draw.circle(screen, color, (int(e['x'] - camera_x), int(e['y'] - camera_y)), int(e['radius']))
            pygame.draw.circle(screen, (0, 0, 0), (int(e['x'] - camera_x), int(e['y'] - camera_y)), int(e['radius']), 1)

        # Draw player
        player_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.circle(screen, (218, 178, 140), player_center, player['radius'])
        gun_rect = pygame.Rect(0, 0, 30, 10)
        gun_rect.center = player_center
        gun_surf = pygame.Surface(gun_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(gun_surf, (0, 0, 0), gun_surf.get_rect(), border_radius=4)
        rotated = pygame.transform.rotate(gun_surf, -math.degrees(player['angle']))
        rot_rect = rotated.get_rect(center=player_center)
        screen.blit(rotated, rot_rect.topleft)
        pygame.draw.circle(screen, (0, 0, 0), player_center, player['radius'], 2)

        # UI
        font = pygame.font.SysFont(None, 24)
        pygame.draw.rect(screen, (255, 0, 0), (20, 20, 200, 20))
        pygame.draw.rect(screen, (50, 205, 50), (20, 20, max(0, 200 * (player['hp'] / 100)), 20))
        pygame.draw.rect(screen, (0, 0, 0), (20, 20, 200, 20), 1)
        score_surf = font.render(f"Score: {score}", True, (255, 255, 255))
        wave_surf = font.render(f"Wave: {wave}", True, (255, 255, 255))
        screen.blit(score_surf, (20, 50))
        screen.blit(wave_surf, (20, 80))
        if is_reloading:
            reload_surf = font.render("RELOADING...", True, (255, 255, 0))
            screen.blit(reload_surf, (SCREEN_WIDTH // 2 - reload_surf.get_width() // 2, SCREEN_HEIGHT - 50))
        if game_over:
            over_font = pygame.font.SysFont(None, 48)
            over_surf = over_font.render("Game Over", True, (255, 255, 255))
            over_rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(over_surf, over_rect)
            score_surf = over_font.render(f"Score: {score}", True, (255, 255, 255))
            score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(score_surf, score_rect)
            info_surf = font.render("Press R to restart", True, (255, 255, 255))
            info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            screen.blit(info_surf, info_rect)

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    map_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(map_file)

