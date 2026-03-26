import pygame
import random
import sys

# --- Constants ---
WINDOW_W = 600
WINDOW_H = 620
GRID_SIZE = 20
COLS = WINDOW_W // GRID_SIZE
ROWS = (WINDOW_H - 60) // GRID_SIZE   # leave room for score bar at top

FPS = 10

# Colors
BG_COLOR       = (15, 17, 26)
GRID_COLOR     = (25, 28, 40)
SNAKE_HEAD     = (80, 220, 140)
SNAKE_BODY     = (50, 170, 100)
SNAKE_OUTLINE  = (30, 120, 70)
FOOD_COLOR     = (230, 80, 80)
FOOD_SHINE     = (255, 160, 160)
SCORE_BG       = (20, 22, 34)
TEXT_COLOR     = (200, 210, 230)
HIGHLIGHT      = (80, 220, 140)
DEAD_COLOR     = (180, 60, 60)
OVERLAY_COLOR  = (10, 12, 20, 200)

# Directions
UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)

SCORE_BAR_H = 60   # pixels reserved at top for score


def draw_grid(surface):
    for x in range(0, WINDOW_W, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, SCORE_BAR_H), (x, WINDOW_H))
    for y in range(SCORE_BAR_H, WINDOW_H, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WINDOW_W, y))


def cell_to_pixel(col, row):
    """Top-left pixel of a grid cell."""
    return col * GRID_SIZE, SCORE_BAR_H + row * GRID_SIZE


def draw_snake(surface, snake, alive):
    for i, (col, row) in enumerate(snake):
        x, y = cell_to_pixel(col, row)
        rect = pygame.Rect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2)

        if i == 0:
            color = SNAKE_HEAD if alive else DEAD_COLOR
        else:
            # gradient: body gets slightly darker near the tail
            t = i / max(len(snake) - 1, 1)
            r = int(SNAKE_BODY[0] * (1 - t * 0.3))
            g = int(SNAKE_BODY[1] * (1 - t * 0.3))
            b = int(SNAKE_BODY[2] * (1 - t * 0.3))
            color = (r, g, b) if alive else DEAD_COLOR

        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, SNAKE_OUTLINE, rect, width=1, border_radius=4)

        # little eyes on head
        if i == 0 and alive:
            eye_r = 2
            ox, oy = 5, 5
            pygame.draw.circle(surface, (10, 10, 10), (x + ox, y + oy), eye_r)
            pygame.draw.circle(surface, (10, 10, 10), (x + GRID_SIZE - ox, y + oy), eye_r)


def draw_food(surface, food, tick):
    col, row = food
    x, y = cell_to_pixel(col, row)
    cx, cy = x + GRID_SIZE // 2, y + GRID_SIZE // 2
    radius = GRID_SIZE // 2 - 2

    # slight pulse using sine of tick
    import math
    pulse = int(2 * math.sin(tick * 0.15))
    pygame.draw.circle(surface, FOOD_COLOR, (cx, cy), radius + pulse)
    # shine dot
    pygame.draw.circle(surface, FOOD_SHINE, (cx - 3, cy - 3), 3)


def draw_score_bar(surface, font_big, font_small, score, high_score):
    pygame.draw.rect(surface, SCORE_BG, (0, 0, WINDOW_W, SCORE_BAR_H))
    pygame.draw.line(surface, GRID_COLOR, (0, SCORE_BAR_H), (WINDOW_W, SCORE_BAR_H), 2)

    score_surf = font_big.render(f"{score}", True, HIGHLIGHT)
    label_surf = font_small.render("SCORE", True, TEXT_COLOR)
    hi_surf    = font_small.render(f"BEST  {high_score}", True, TEXT_COLOR)

    surface.blit(label_surf, (20, 10))
    surface.blit(score_surf, (20, 26))
    surface.blit(hi_surf,    (WINDOW_W - hi_surf.get_width() - 20, 22))


def draw_overlay(surface, font_title, font_body, message, sub):
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))

    title = font_title.render(message, True, HIGHLIGHT)
    hint  = font_body.render(sub, True, TEXT_COLOR)

    surface.blit(title, (WINDOW_W // 2 - title.get_width() // 2,
                         WINDOW_H // 2 - 50))
    surface.blit(hint,  (WINDOW_W // 2 - hint.get_width() // 2,
                         WINDOW_H // 2 + 10))


def spawn_food(snake):
    occupied = set(snake)
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if pos not in occupied:
            return pos


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()

    # Fonts — using a monospace feel; fall back gracefully
    try:
        font_title = pygame.font.SysFont("couriernew", 42, bold=True)
        font_big   = pygame.font.SysFont("couriernew", 28, bold=True)
        font_body  = pygame.font.SysFont("couriernew", 18)
        font_small = pygame.font.SysFont("couriernew", 13)
    except Exception:
        font_title = pygame.font.SysFont(None, 42)
        font_big   = pygame.font.SysFont(None, 28)
        font_body  = pygame.font.SysFont(None, 18)
        font_small = pygame.font.SysFont(None, 13)

    high_score = 0

    # ---- Game state ----
    def reset():
        start_col = COLS // 2
        start_row = ROWS // 2
        snake = [(start_col, start_row),
                 (start_col - 1, start_row),
                 (start_col - 2, start_row)]
        direction = RIGHT
        next_dir  = RIGHT
        food = spawn_food(snake)
        return snake, direction, next_dir, food, 0, True

    snake, direction, next_dir, food, score, alive = reset()
    started = False   # show start screen first
    tick = 0

    while True:
        clock.tick(FPS)
        tick += 1

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if not started or not alive:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        snake, direction, next_dir, food, score, alive = reset()
                        started = True
                    continue

                # direction input — don't allow 180 flip
                if event.key == pygame.K_UP    and direction != DOWN:
                    next_dir = UP
                elif event.key == pygame.K_DOWN  and direction != UP:
                    next_dir = DOWN
                elif event.key == pygame.K_LEFT  and direction != RIGHT:
                    next_dir = LEFT
                elif event.key == pygame.K_RIGHT and direction != LEFT:
                    next_dir = RIGHT
                # WASD support
                elif event.key == pygame.K_w and direction != DOWN:
                    next_dir = UP
                elif event.key == pygame.K_s and direction != UP:
                    next_dir = DOWN
                elif event.key == pygame.K_a and direction != RIGHT:
                    next_dir = LEFT
                elif event.key == pygame.K_d and direction != LEFT:
                    next_dir = RIGHT

        # --- Update ---
        if started and alive:
            direction = next_dir
            head_col, head_row = snake[0]
            dc, dr = direction
            new_head = (head_col + dc, head_row + dr)

            # Wall collision
            if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
                alive = False
                high_score = max(high_score, score)
            # Self collision
            elif new_head in snake[1:]:
                alive = False
                high_score = max(high_score, score)
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 10
                    food = spawn_food(snake)
                else:
                    snake.pop()

        # --- Draw ---
        screen.fill(BG_COLOR)
        draw_grid(screen)
        draw_food(screen, food, tick)
        draw_snake(screen, snake, alive)
        draw_score_bar(screen, font_big, font_small, score, high_score)

        if not started:
            draw_overlay(screen, font_title, font_body,
                         "SNAKE",
                         "Press ENTER or SPACE to start")
        elif not alive:
            draw_overlay(screen, font_title, font_body,
                         "GAME OVER",
                         f"Score: {score}   |   Press ENTER to restart")

        pygame.display.flip()


if __name__ == "__main__":
    main()