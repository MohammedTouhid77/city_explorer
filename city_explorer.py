"""
Virtual City Explorer - Interactive Top-Down 2D City
Run: python city_explorer.py
Requires: pip install pygame
"""
import pygame, sys, random, math

# ─── Constants ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 600
TILE = 40
GRID_W, GRID_H = 20, 20
WORLD_W, WORLD_H = GRID_W * TILE, GRID_H * TILE
FPS = 60
MINIMAP_SZ = 160
MINIMAP_PAD = 10
LERP_SPEED = 0.08
WALK_SPEED = 2.0
DRIVE_SPEED = 5.0

# ─── Colors ──────────────────────────────────────────────────────────────────
C_ROAD       = (58, 58, 68)
C_ROAD_LINE  = (200, 200, 200)
C_SIDEWALK   = (180, 180, 175)
C_PARK       = (100, 180, 100)
C_WATER      = (80, 150, 220)
C_BG         = (30, 30, 40)
C_HUD_BG     = (20, 20, 30, 200)
C_HUD_TEXT   = (220, 220, 230)
C_PANEL_BG   = (35, 35, 50)
C_PANEL_BORDER = (80, 140, 255)
C_WHITE      = (255, 255, 255)
C_BLACK      = (0, 0, 0)
C_PLAYER_WALK = (60, 140, 255)
C_PLAYER_DRIVE = (240, 150, 40)
C_HIGHLIGHT  = (255, 255, 180, 90)
C_MINIMAP_BG = (20, 20, 30)
C_MINIMAP_BORDER = (80, 80, 100)

BUILDING_CATALOG = [
    {"name": "City Hospital",     "emoji": "🏥", "type": "Healthcare",  "color": (220, 120, 120), "cap": 300, "staff": 45, "rating": 4.5, "hours": "24/7",       "desc": "A state-of-the-art medical facility providing emergency and specialized care."},
    {"name": "Police Station",    "emoji": "🚔", "type": "Public Safety","color": (120, 140, 200), "cap": 80,  "staff": 32, "rating": 4.1, "hours": "24/7",       "desc": "Keeping SmartVille safe around the clock with rapid response teams."},
    {"name": "Central School",    "emoji": "🏫", "type": "Education",   "color": (230, 210, 100), "cap": 500, "staff": 28, "rating": 4.3, "hours": "7am-4pm",    "desc": "Modern classrooms and labs nurturing the next generation of thinkers."},
    {"name": "Public Library",    "emoji": "📚", "type": "Education",   "color": (180, 160, 120), "cap": 120, "staff": 8,  "rating": 4.7, "hours": "9am-8pm",    "desc": "Thousands of books, free Wi-Fi, and cozy reading nooks for everyone."},
    {"name": "Tech Hub",          "emoji": "💻", "type": "Technology",  "color": (100, 200, 200), "cap": 200, "staff": 22, "rating": 4.6, "hours": "8am-10pm",   "desc": "A buzzing co-working space for startups and innovators."},
    {"name": "Health Clinic",     "emoji": "🩺", "type": "Healthcare",  "color": (200, 140, 140), "cap": 60,  "staff": 12, "rating": 4.0, "hours": "8am-6pm",    "desc": "Walk-in clinic offering primary care and vaccinations."},
    {"name": "Maple Apartments",  "emoji": "🏢", "type": "Residential", "color": (170, 170, 185), "cap": 240, "staff": 5,  "rating": 4.2, "hours": "Always",     "desc": "Comfortable modern living in the heart of SmartVille."},
    {"name": "Golden Restaurant", "emoji": "🍽️","type": "Commercial",  "color": (220, 180, 100), "cap": 80,  "staff": 15, "rating": 4.4, "hours": "10am-11pm",  "desc": "Farm-to-table dining with an ever-changing seasonal menu."},
    {"name": "SmartVille Mall",   "emoji": "🛍️","type": "Commercial",  "color": (200, 160, 200), "cap": 1000,"staff": 60, "rating": 4.1, "hours": "9am-9pm",    "desc": "Three floors of shops, a food court, and a rooftop garden."},
    {"name": "Fire Station",      "emoji": "🚒", "type": "Public Safety","color": (220, 100, 80),  "cap": 40,  "staff": 20, "rating": 4.8, "hours": "24/7",       "desc": "Rapid-response fire and rescue services protecting the city."},
]

# ─── Tile Class ──────────────────────────────────────────────────────────────
class Tile:
    def __init__(self, gx, gy, ttype, building_info=None):
        self.gx, self.gy = gx, gy
        self.ttype = ttype
        self.building_info = building_info
        self.rect = pygame.Rect(gx * TILE, gy * TILE, TILE, TILE)
        self.color = self._pick_color()

    def _pick_color(self):
        if self.ttype == "road":
            return C_ROAD
        if self.ttype == "sidewalk":
            return C_SIDEWALK
        if self.ttype == "park":
            return C_PARK
        if self.ttype == "water":
            return C_WATER
        if self.building_info:
            return self.building_info["color"]
        return (160, 160, 160)

# ─── City Generator ─────────────────────────────────────────────────────────
class City:
    def __init__(self):
        random.seed(42)
        self.tiles = [[None]*GRID_H for _ in range(GRID_W)]
        self._generate()

    def _generate(self):
        road_cols = {0, 5, 10, 15, 19}
        road_rows = {0, 5, 10, 15, 19}

        for x in range(GRID_W):
            for y in range(GRID_H):
                if x in road_cols or y in road_rows:
                    self.tiles[x][y] = Tile(x, y, "road")
                else:
                    self.tiles[x][y] = Tile(x, y, "empty")

        # sidewalks next to roads
        for x in range(GRID_W):
            for y in range(GRID_H):
                if self.tiles[x][y].ttype != "road":
                    adj_road = False
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                            if self.tiles[nx][ny].ttype == "road":
                                adj_road = True; break
                    if adj_road:
                        self.tiles[x][y] = Tile(x, y, "sidewalk")

        # place parks, water, buildings on remaining empty
        for x in range(GRID_W):
            for y in range(GRID_H):
                if self.tiles[x][y].ttype == "empty":
                    r = random.random()
                    if r < 0.12:
                        self.tiles[x][y] = Tile(x, y, "park")
                    elif r < 0.17:
                        self.tiles[x][y] = Tile(x, y, "water")
                    else:
                        info = random.choice(BUILDING_CATALOG).copy()
                        info["cap"] = info["cap"] + random.randint(-20, 20)
                        info["staff"] = max(1, info["staff"] + random.randint(-3, 3))
                        info["rating"] = round(info["rating"] + random.uniform(-0.3, 0.3), 1)
                        info["rating"] = max(1.0, min(5.0, info["rating"]))
                        self.tiles[x][y] = Tile(x, y, "building", info)

    def get_tile(self, gx, gy):
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            return self.tiles[gx][gy]
        return None

    def draw(self, surf, cam):
        # visible tile range
        sx = max(0, int(cam.x) // TILE - 1)
        sy = max(0, int(cam.y) // TILE - 1)
        ex = min(GRID_W, sx + SCREEN_W // TILE + 3)
        ey = min(GRID_H, sy + SCREEN_H // TILE + 3)
        for x in range(sx, ex):
            for y in range(sy, ey):
                t = self.tiles[x][y]
                rx = t.rect.x - int(cam.x)
                ry = t.rect.y - int(cam.y)
                pygame.draw.rect(surf, t.color, (rx, ry, TILE, TILE))
                # road dashes
                if t.ttype == "road":
                    if x not in {0,19} and y not in {0,19}:
                        cx = rx + TILE // 2
                        cy = ry + TILE // 2
                        # horizontal dash
                        pygame.draw.line(surf, C_ROAD_LINE, (rx+4, cy), (rx+TILE-4, cy), 1)
                        # vertical dash
                        pygame.draw.line(surf, C_ROAD_LINE, (cx, ry+4), (cx, ry+TILE-4), 1)
                # building outline
                if t.ttype == "building":
                    pygame.draw.rect(surf, (0,0,0), (rx, ry, TILE, TILE), 1)
                    # small inner detail
                    pygame.draw.rect(surf, tuple(min(255,c+30) for c in t.color), (rx+6, ry+6, TILE-12, TILE-12), 0)
                    pygame.draw.rect(surf, (0,0,0), (rx+6, ry+6, TILE-12, TILE-12), 1)
                # park detail
                if t.ttype == "park":
                    pygame.draw.circle(surf, (60, 140, 60), (rx+TILE//2, ry+TILE//2), 8)
                    pygame.draw.circle(surf, (80, 170, 80), (rx+TILE//2-4, ry+TILE//2-4), 5)
                # water ripple
                if t.ttype == "water":
                    pygame.draw.arc(surf, (120, 190, 250), (rx+5, ry+10, 30, 15), 0, 3.14, 1)
                    pygame.draw.arc(surf, (120, 190, 250), (rx+8, ry+22, 24, 10), 0, 3.14, 1)

# ─── Player ──────────────────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x = WORLD_W / 2.0
        self.y = WORLD_H / 2.0
        self.driving = False

    @property
    def speed(self):
        return DRIVE_SPEED if self.driving else WALK_SPEED

    @property
    def mode_str(self):
        return "Drive" if self.driving else "Walk"

    def toggle_mode(self):
        self.driving = not self.driving

    def update(self, keys):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:   dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:   dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  dx = 1
        if dx and dy:
            dx *= 0.7071; dy *= 0.7071
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(8, min(WORLD_W - 8, self.x))
        self.y = max(8, min(WORLD_H - 8, self.y))

    def draw(self, surf, cam):
        sx = int(self.x - cam.x)
        sy = int(self.y - cam.y)
        if self.driving:
            r = pygame.Rect(sx - 8, sy - 5, 16, 10)
            pygame.draw.rect(surf, C_PLAYER_DRIVE, r, border_radius=3)
            pygame.draw.rect(surf, (200, 120, 20), r, 1, border_radius=3)
        else:
            pygame.draw.circle(surf, C_PLAYER_WALK, (sx, sy), 7)
            pygame.draw.circle(surf, (30, 100, 200), (sx, sy), 7, 1)

    @property
    def tile_pos(self):
        return int(self.x // TILE), int(self.y // TILE)

# ─── Camera ──────────────────────────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, player):
        tx = player.x - SCREEN_W / 2
        ty = player.y - SCREEN_H / 2
        self.x += (tx - self.x) * LERP_SPEED
        self.y += (ty - self.y) * LERP_SPEED

# ─── InfoPanel ───────────────────────────────────────────────────────────────
class InfoPanel:
    def __init__(self):
        self.visible = False
        self.info = None
        self.font = None
        self.sfont = None
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)

    def init_fonts(self, font, sfont):
        self.font = font
        self.sfont = sfont

    def show(self, info):
        if self.visible and self.info and self.info["name"] == info["name"]:
            self.visible = False
            return
        self.info = info
        self.visible = True

    def close(self):
        self.visible = False
        self.info = None

    def handle_click(self, pos):
        if not self.visible:
            return False
        if self.close_rect.collidepoint(pos):
            self.close()
            return True
        if self.panel_rect.collidepoint(pos):
            return True
        return False

    def draw(self, surf):
        if not self.visible or not self.info:
            return
        pw, ph = 340, 260
        px = (SCREEN_W - pw) // 2
        py = (SCREEN_H - ph) // 2
        self.panel_rect = pygame.Rect(px, py, pw, ph)

        # shadow
        shadow = pygame.Surface((pw+6, ph+6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 80))
        surf.blit(shadow, (px-3, py-3))

        # panel bg
        pygame.draw.rect(surf, C_PANEL_BG, self.panel_rect, border_radius=10)
        pygame.draw.rect(surf, C_PANEL_BORDER, self.panel_rect, 2, border_radius=10)

        # accent bar
        pygame.draw.rect(surf, self.info["color"], (px, py, pw, 6), border_radius=3)

        i = self.info
        y = py + 16

        # title
        title = self.font.render(f"{i['emoji']}  {i['name']}", True, C_WHITE)
        surf.blit(title, (px + 18, y)); y += 32

        # type
        tp = self.sfont.render(f"Type: {i['type']}", True, (170, 170, 190))
        surf.blit(tp, (px + 18, y)); y += 24

        # separator
        pygame.draw.line(surf, (60, 60, 80), (px+18, y), (px+pw-18, y), 1); y += 10

        # stats
        stats = [
            f"Capacity: {i['cap']}",
            f"Staff: {i['staff']}",
            f"Rating: {i['rating']}★",
            f"Hours: {i['hours']}",
        ]
        for s in stats:
            t = self.sfont.render(s, True, (200, 200, 210))
            surf.blit(t, (px + 24, y)); y += 22

        y += 6
        pygame.draw.line(surf, (60, 60, 80), (px+18, y), (px+pw-18, y), 1); y += 10

        # description
        desc = i["desc"]
        words = desc.split()
        line = ""
        for w in words:
            test = line + " " + w if line else w
            if self.sfont.size(test)[0] > pw - 40:
                t = self.sfont.render(line, True, (170, 180, 190))
                surf.blit(t, (px + 24, y)); y += 20
                line = w
            else:
                line = test
        if line:
            t = self.sfont.render(line, True, (170, 180, 190))
            surf.blit(t, (px + 24, y))

        # close button
        cx, cy = px + pw - 28, py + 12
        self.close_rect = pygame.Rect(cx - 4, cy - 4, 24, 24)
        pygame.draw.rect(surf, (180, 60, 60), self.close_rect, border_radius=4)
        xt = self.sfont.render("X", True, C_WHITE)
        surf.blit(xt, (cx + 2, cy - 1))

# ─── Minimap ─────────────────────────────────────────────────────────────────
class Minimap:
    def __init__(self, city):
        self.city = city
        self.surf = pygame.Surface((MINIMAP_SZ, MINIMAP_SZ))
        self.rect = pygame.Rect(SCREEN_W - MINIMAP_SZ - MINIMAP_PAD,
                                SCREEN_H - MINIMAP_SZ - MINIMAP_PAD,
                                MINIMAP_SZ, MINIMAP_SZ)
        self._build()

    def _build(self):
        self.surf.fill(C_MINIMAP_BG)
        ts = MINIMAP_SZ / max(GRID_W, GRID_H)
        for x in range(GRID_W):
            for y in range(GRID_H):
                t = self.city.tiles[x][y]
                c = {
                    "road": (80, 80, 90),
                    "sidewalk": (140, 140, 135),
                    "park": (80, 160, 80),
                    "water": (70, 130, 200),
                    "building": (190, 175, 140),
                    "empty": (100, 100, 100),
                }.get(t.ttype, (100, 100, 100))
                pygame.draw.rect(self.surf, c, (x*ts, y*ts, max(1,int(ts)), max(1,int(ts))))

    def draw(self, surf, player):
        surf.blit(self.surf, self.rect)
        pygame.draw.rect(surf, C_MINIMAP_BORDER, self.rect, 2)
        # player dot
        ts = MINIMAP_SZ / max(GRID_W, GRID_H)
        px = self.rect.x + int(player.x / TILE * ts)
        py = self.rect.y + int(player.y / TILE * ts)
        pygame.draw.circle(surf, (255, 80, 80), (px, py), 3)
        pygame.draw.circle(surf, C_WHITE, (px, py), 3, 1)

# ─── Game ────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("SmartVille — Virtual City Explorer")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("segoeui", 18, bold=True)
        self.sfont = pygame.font.SysFont("segoeui", 14)
        self.hfont = pygame.font.SysFont("segoeui", 15)

        self.city = City()
        self.player = Player()
        self.camera = Camera()
        self.panel = InfoPanel()
        self.panel.init_fonts(self.font, self.sfont)
        self.minimap = Minimap(self.city)

        self.hovered_tile = None
        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self._events()
            self._update()
            self._draw()
        pygame.quit()
        sys.exit()

    def _events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.panel.visible:
                        self.panel.close()
                    else:
                        self.running = False
                elif e.key == pygame.K_TAB:
                    self.player.toggle_mode()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.panel.handle_click(e.pos):
                    pass
                else:
                    wx = e.pos[0] + self.camera.x
                    wy = e.pos[1] + self.camera.y
                    gx, gy = int(wx // TILE), int(wy // TILE)
                    t = self.city.get_tile(gx, gy)
                    if t and t.ttype == "building" and t.building_info:
                        self.panel.show(t.building_info)

    def _update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.camera.update(self.player)

        mx, my = pygame.mouse.get_pos()
        wx = mx + self.camera.x
        wy = my + self.camera.y
        gx, gy = int(wx // TILE), int(wy // TILE)
        t = self.city.get_tile(gx, gy)
        self.hovered_tile = t if (t and t.ttype == "building") else None

    def _draw(self):
        self.screen.fill(C_BG)
        self.city.draw(self.screen, self.camera)

        # hover highlight
        if self.hovered_tile:
            t = self.hovered_tile
            rx = t.rect.x - int(self.camera.x)
            ry = t.rect.y - int(self.camera.y)
            hs = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            hs.fill(C_HIGHLIGHT)
            self.screen.blit(hs, (rx, ry))
            pygame.draw.rect(self.screen, (255, 255, 200), (rx, ry, TILE, TILE), 2)

        self.player.draw(self.screen, self.camera)
        self.minimap.draw(self.screen, self.player)
        self._draw_hud()
        self.panel.draw(self.screen)
        pygame.display.flip()

    def _draw_hud(self):
        # top bar
        bar = pygame.Surface((SCREEN_W, 32), pygame.SRCALPHA)
        bar.fill((15, 15, 25, 210))
        self.screen.blit(bar, (0, 0))
        tx, ty = self.player.tile_pos
        fps = int(self.clock.get_fps())
        mode_col = C_PLAYER_DRIVE if self.player.driving else C_PLAYER_WALK
        left = self.hfont.render("SmartVille", True, (120, 180, 255))
        self.screen.blit(left, (12, 7))
        mode_t = self.hfont.render(f"Mode: {self.player.mode_str}", True, mode_col)
        self.screen.blit(mode_t, (160, 7))
        coord = self.hfont.render(f"Tile: ({tx},{ty})", True, C_HUD_TEXT)
        self.screen.blit(coord, (340, 7))
        fpst = self.hfont.render(f"FPS: {fps}", True, (140, 140, 150))
        self.screen.blit(fpst, (SCREEN_W - 80, 7))

        # bottom bar
        bbar = pygame.Surface((SCREEN_W, 28), pygame.SRCALPHA)
        bbar.fill((15, 15, 25, 210))
        self.screen.blit(bbar, (0, SCREEN_H - 28))
        hint = self.sfont.render("WASD: move  |  Tab: toggle mode  |  Click: inspect building  |  Esc: close/quit", True, (150, 150, 160))
        self.screen.blit(hint, (12, SCREEN_H - 23))

# ─── Entry ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
