
import pygame
import random
import sys

# 初始化
pygame.init()

# 基礎參數
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
BASE_FPS = 10  # 改為基礎FPS
FPS = BASE_FPS  # 當前FPS

# 顏色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)  # 新增黃色用於加速狀態顯示

# 方向
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.length = 1
        self.score = 0

    def get_head_position(self):
        return self.positions[0]

    def turn(self, point):
        # 防止反向移動
        if (point[0] * -1, point[1] * -1) != self.direction:
            self.direction = point

    def move(self):
        head = self.get_head_position()
        x, y = self.direction
        new_x = head[0] + x
        new_y = head[1] + y
        new_position = (new_x, new_y)

        # 檢查撞牆
        if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
            return False

        # 檢查自撞
        if new_position in self.positions:
            return False

        self.positions.insert(0, new_position)

        # 最大長度限制
        if len(self.positions) > self.length:
            self.positions.pop()

        return True

    def grow(self):
        self.length += 1
        self.score += 10

    def draw(self, surface):
        for p in self.positions:
            rect = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, GREEN, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.randomize_position()

    def randomize_position(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))

    def draw(self, surface):
        rect = pygame.Rect((self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, RED, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake - WASD to move, CTRL to speed up")
    clock = pygame.time.Clock()

    snake = Snake()
    food = Food()

    font = pygame.font.SysFont('simhei', 24)

    # 加速相關變數
    is_speeding = False
    speed_multiplier = 1.2  # 加速倍率

    while True:
        # 檢查按鍵狀態（持續按壓）
        keys = pygame.key.get_pressed()

        # CTRL鍵加速（左CTRL或右CTRL）
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            FPS = int(BASE_FPS * speed_multiplier)
            is_speeding = True
        else:
            FPS = BASE_FPS
            is_speeding = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    snake.turn(UP)
                elif event.key == pygame.K_s:
                    snake.turn(DOWN)
                elif event.key == pygame.K_a:
                    snake.turn(LEFT)
                elif event.key == pygame.K_d:
                    snake.turn(RIGHT)
                elif event.key == pygame.K_r:
                    # 重開
                    snake = Snake()
                    food.randomize_position()
                    # 重置加速狀態
                    FPS = BASE_FPS
                    is_speeding = False

        if not snake.move():
            # 結束
            game_over_text = font.render("Gameover ! (press R restart)", True, WHITE)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2))
            pygame.display.update()

            # 等重開
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        waiting = False
                        snake = Snake()
                        food.randomize_position()
                        # 重置加速狀態
                        FPS = BASE_FPS
                        is_speeding = False
            continue

        # 吃到食物?
        if snake.get_head_position() == food.position:
            snake.grow()
            food.randomize_position()
            # 食物不生成在蛇身上
            while food.position in snake.positions:
                food.randomize_position()

        screen.fill(BLACK)
        snake.draw(screen)
        food.draw(screen)

        # 計分
        score_text = font.render(f"score: {snake.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # 顯示加速狀態
        if is_speeding:
            speed_text = font.render("SPEED BOOST!", True, YELLOW)
            screen.blit(speed_text, (WIDTH//2 - speed_text.get_width()//2, 40))

        # 提示
        controls_text = font.render("WASD to move, CTRL to speed up, R to restart", True, WHITE)
        screen.blit(controls_text, (WIDTH - controls_text.get_width() - 10, 10))

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()