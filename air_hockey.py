import pygame
import sys
import math
import random

pygame.init()

# ---------------- CONSTANTS ----------------
WIDTH = 1000
HEIGHT = 600
FPS = 60

PUCK_RADIUS = 10
PADDLE_RADIUS = 30
MAX_SCORE = 7

PUCK_FRICTION = 0.995
GOAL_HEIGHT = 160
BARRIER = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 25)
BLUE = (80, 160, 255)
RED = (255, 80, 80)
ICE = (170, 210, 255)
YELLOW = (255, 220, 100)
GREEN = (120, 255, 120)
PURPLE = (210, 120, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Air Hockey")

clock = pygame.time.Clock()

font_big = pygame.font.SysFont("arial", 70, bold=True)
font_med = pygame.font.SysFont("arial", 36, bold=True)
font_small = pygame.font.SysFont("arial", 22)

screen_shake = 0
rink_glow = 0


# ---------------- PARTICLES ----------------
class Particle:
    def __init__(self, x, y, color=YELLOW):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 10)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 40)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)


# ---------------- POWERUPS ----------------
class PowerUp:
    def __init__(self):
        self.x = random.randint(200, WIDTH - 200)
        self.y = random.randint(120, HEIGHT - 120)
        self.type = random.choice(["speed", "big", "slow"])
        self.radius = 15
        self.life = 600

    def update(self):
        self.life -= 1

    def draw(self):
        color = {"speed": GREEN, "big": PURPLE, "slow": YELLOW}[self.type]
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)


# ---------------- PUCK ----------------
class Puck:
    def __init__(self):
        self.trail = []
        self.spin = 0
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.vx = random.choice([-7, 7])
        self.vy = random.uniform(-3, 3)
        self.spin = 0
        self.trail.clear()

    def move(self):
        self.x += self.vx
        self.y += self.vy

        # Physics
        self.vy += self.spin * 0.02
        self.vx *= PUCK_FRICTION
        self.vy *= PUCK_FRICTION
        self.spin *= 0.98

        # --- TOP/BOTTOM BARRIERS ---
        if self.y <= BARRIER + PUCK_RADIUS:
            self.y = BARRIER + PUCK_RADIUS
            self.vy *= -1
            self.spin *= -1
        elif self.y >= HEIGHT - BARRIER - PUCK_RADIUS:
            self.y = HEIGHT - BARRIER - PUCK_RADIUS
            self.vy *= -1
            self.spin *= -1

        # --- SIDE WALLS & GOAL LOGIC ---
        goal_top = (HEIGHT - GOAL_HEIGHT) / 2
        goal_bottom = goal_top + GOAL_HEIGHT

        # Left Side
        if self.x <= PUCK_RADIUS:
            if not (goal_top < self.y < goal_bottom):
                self.x = PUCK_RADIUS
                self.vx *= -1

        # Right Side
        if self.x >= WIDTH - PUCK_RADIUS:
            if not (goal_top < self.y < goal_bottom):
                self.x = WIDTH - PUCK_RADIUS
                self.vx *= -1

        self.trail.append((self.x, self.y))
        if len(self.trail) > 14:
            self.trail.pop(0)

    def draw(self):
        for i, pos in enumerate(self.trail):
            size = int(PUCK_RADIUS * (i / 14))
            pygame.draw.circle(screen, (100, 100, 120), (int(pos[0]), int(pos[1])), size)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), PUCK_RADIUS)


# ---------------- PADDLE ----------------
class Paddle:
    def __init__(self, x, y, color, controls=None, ai=False, difficulty="medium"):
        self.x = x
        self.y = y
        self.color = color
        self.controls = controls
        self.ai = ai
        self.difficulty = difficulty
        self.radius = PADDLE_RADIUS
        self.speed = 7
        self.prev_x, self.prev_y = x, y
        self.power_timer = 0

    def move(self, keys, puck):
        self.prev_x, self.prev_y = self.x, self.y
        if self.ai:
            self.ai_move(puck)
        else:
            if keys[self.controls["up"]]: self.y -= self.speed
            if keys[self.controls["down"]]: self.y += self.speed
            if keys[self.controls["left"]]: self.x -= self.speed
            if keys[self.controls["right"]]: self.x += self.speed
        self.restrict()

        if self.power_timer > 0:
            self.power_timer -= 1
        else:
            self.radius, self.speed = PADDLE_RADIUS, 7

    def restrict(self):
        self.y = max(BARRIER + self.radius, min(HEIGHT - BARRIER - self.radius, self.y))
        if self.x < WIDTH / 2:
            self.x = max(self.radius, min(WIDTH / 2 - self.radius, self.x))
        else:
            self.x = max(WIDTH / 2 + self.radius, min(WIDTH - self.radius, self.x))

    def ai_move(self, puck):
        reaction = {"easy": 3, "medium": 5, "hard": 8}[self.difficulty]
        # Only move if puck is on AI's side
        if puck.x > WIDTH / 2 - 50:
            target_y = puck.y + (puck.vy * 5)
            if target_y > self.y:
                self.y += reaction
            elif target_y < self.y:
                self.y -= reaction
        self.restrict()

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


# ---------------- UTILS ----------------
def puck_collision(puck, paddle):
    global screen_shake
    dx, dy = puck.x - paddle.x, puck.y - paddle.y
    dist = math.hypot(dx, dy)
    if dist < PUCK_RADIUS + paddle.radius:
        angle = math.atan2(dy, dx)
        paddle_vx, paddle_vy = paddle.x - paddle.prev_x, paddle.y - paddle.prev_y
        speed = 10 + math.hypot(paddle_vx, paddle_vy)
        puck.vx = math.cos(angle) * speed
        puck.vy = math.sin(angle) * speed
        puck.spin = paddle_vy * 2
        screen_shake = 8


def draw_rink():
    global rink_glow
    rink_glow = (rink_glow + 2) % 360
    glow = math.sin(math.radians(rink_glow)) * 30 + 30
    screen.fill(ICE)
    pygame.draw.line(screen, RED, (WIDTH / 2, 0), (WIDTH / 2, HEIGHT), 4)
    pygame.draw.circle(screen, (255, 100 + int(glow), 100), (WIDTH // 2, HEIGHT // 2), 80, 5)

    goal_top = (HEIGHT - GOAL_HEIGHT) / 2
    pygame.draw.rect(screen, BLACK, (0, goal_top, 10, GOAL_HEIGHT))
    pygame.draw.rect(screen, BLACK, (WIDTH - 10, goal_top, 10, GOAL_HEIGHT))
    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, BARRIER))
    pygame.draw.rect(screen, BLACK, (0, HEIGHT - BARRIER, WIDTH, BARRIER))


def draw_score(s1, s2):
    text = font_big.render(f"{s1}   {s2}", True, (50, 50, 50))
    screen.blit(text, (WIDTH // 2 - 75, 30))


# ---------------- MENUS ----------------
def start_menu():
    while True:
        screen.fill(BLACK)
        title = font_big.render("ULTIMATE AIR HOCKEY", True, WHITE)
        m1 = font_med.render("1 - Two Players", True, BLUE)
        m2 = font_med.render("2 - Player vs Robot", True, RED)
        screen.blit(title, (WIDTH // 2 - 350, 150))
        screen.blit(m1, (WIDTH // 2 - 150, 320))
        screen.blit(m2, (WIDTH // 2 - 170, 370))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return "2P", "medium"
                if event.key == pygame.K_2: return difficulty_menu()


def difficulty_menu():
    while True:
        screen.fill(BLACK)
        t = font_big.render("Select Difficulty", True, WHITE)
        e, m, h = font_med.render("1 - Easy", True, GREEN), font_med.render("2 - Medium", True,
                                                                            YELLOW), font_med.render("3 - Hard", True,
                                                                                                     RED)
        screen.blit(t, (WIDTH // 2 - 220, 150));
        screen.blit(e, (WIDTH // 2 - 80, 320));
        screen.blit(m, (WIDTH // 2 - 100, 370));
        screen.blit(h, (WIDTH // 2 - 80, 420))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return "AI", "easy"
                if event.key == pygame.K_2: return "AI", "medium"
                if event.key == pygame.K_3: return "AI", "hard"


# ---------------- GAME LOOP ----------------
def game_loop(mode, difficulty):
    global screen_shake
    puck = Puck()
    p1 = Paddle(120, HEIGHT // 2, BLUE, {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d})
    if mode == "AI":
        p2 = Paddle(WIDTH - 120, HEIGHT // 2, RED, ai=True, difficulty=difficulty)
    else:
        p2 = Paddle(WIDTH - 120, HEIGHT // 2, RED,
                    {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT})

    score1, score2 = 0, 0
    particles, powerups = [], []
    spawn_timer = 0
    paused = False

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: paused = not paused
                if paused and event.key == pygame.K_r: return  # Restart
                if paused and event.key == pygame.K_m: return "menu"

        if paused:
            t = font_big.render("PAUSED", True, WHITE)
            screen.blit(t, (WIDTH // 2 - 120, HEIGHT // 2 - 40))
            pygame.display.update()
            continue

        p1.move(keys, puck);
        p2.move(keys, puck)
        puck.move()
        puck_collision(puck, p1);
        puck_collision(puck, p2)

        # Scoring Logic
        goal_top = (HEIGHT - GOAL_HEIGHT) / 2
        scored = False
        if puck.x < 0:
            score2 += 1;
            scored = True;
            color = RED
        elif puck.x > WIDTH:
            score1 += 1;
            scored = True;
            color = BLUE

        if scored:
            screen_shake = 15
            for _ in range(50): particles.append(Particle(puck.x, puck.y, color))
            # Goal Animation
            for _ in range(30):
                draw_rink();
                puck.draw();
                p1.draw();
                p2.draw()
                txt = font_big.render("GOAL!", True, color)
                screen.blit(txt, (WIDTH // 2 - 100, HEIGHT // 2 - 50))
                pygame.display.update()
                clock.tick(FPS)
            puck.reset()

        # Powerups
        spawn_timer += 1
        if spawn_timer > 600:
            powerups.append(PowerUp());
            spawn_timer = 0

        # Draw Everything
        draw_rink()
        puck.draw();
        p1.draw();
        p2.draw()
        draw_score(score1, score2)

        for p in particles[:]:
            p.update();
            p.draw()
            if p.life <= 0: particles.remove(p)

        for pw in powerups[:]:
            pw.update();
            pw.draw()
            if math.hypot(puck.x - pw.x, puck.y - pw.y) < PUCK_RADIUS + pw.radius:
                if pw.type == "speed":
                    puck.vx *= 1.8
                elif pw.type == "big":
                    p1.radius = 50; p1.power_timer = 400
                elif pw.type == "slow":
                    p2.speed = 3; p2.power_timer = 400
                powerups.remove(pw)

        if screen_shake > 0:
            screen_shake -= 1
            screen.scroll(random.randint(-5, 5), random.randint(-5, 5))

        # Win Condition
        if score1 >= MAX_SCORE or score2 >= MAX_SCORE:
            winner = "BLUE WINS!" if score1 > score2 else "RED WINS!"
            while True:
                draw_rink()
                t = font_big.render(winner, True, YELLOW)
                retry = font_small.render("Press SPACE for Menu", True, BLACK)
                screen.blit(t, (WIDTH // 2 - 200, HEIGHT // 2 - 50))
                screen.blit(retry, (WIDTH // 2 - 100, HEIGHT // 2 + 40))
                pygame.display.update()
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: return "menu"
                    if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        pygame.display.update()


# ---------------- START ----------------
while True:
    mode, difficulty = start_menu()
    result = game_loop(mode, difficulty)
    if result == "menu": continue
