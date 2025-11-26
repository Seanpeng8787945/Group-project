
import pygame
import random
import sys
import json
from collections import deque
from enum import Enum

# 初始化
pygame.init()

# 基礎參數
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
BASE_FPS = 10  # 基礎FPS
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

# 最高分檔案
HIGHSCORE_FILE = "snake_highscore.json"

class GameState(Enum):
    MENU = 0
    RUNNING = 1
    PAUSED = 2
    GAMEOVER = 3

class Snake:
    def __init__(self):
        # 使用 deque 管理蛇身（左端為頭）
        self.body = deque()
        start = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.body.appendleft(start)
        self.body_set = set(self.body) # set 做0(1)查詢
        self.direction = RIGHT
        self.next_directions = deque()  # 輸入緩衝
        self.length = 1
        self.score = 0

    def get_head_position(self):
        return self.body[0]

    def queue_turn(self, point):
        # 緩存方向，避免快速按鍵被丟失
        if len(self.next_directions) < 2:
            self.next_directions.append(point)

    def apply_next_direction(self):
        if not self.next_directions:
            return
        point = self.next_directions.popleft()
        # 防止反向移動
        if (point[0] * -1, point[1] * -1) != self.direction:
            self.direction = point

    def move(self):
        #緩衝方向
        self.apply_next_direction()
        
        head = self.get_head_position()
        x, y = self.direction
        new_x = head[0] + dx
        new_y = head[1] + dy
        new_position = (new_x, new_y)

        # 檢查撞牆
        if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
            return False, "WALL"

        # 檢查自撞（尾巴會在非成長時被移除，所以先判斷）
        # 若新位置在 body_set 中且不是尾巴（在下一行會被移除）則自撞
        tail = None
        if len(self.body)>= seld.length:
            tail = self.body[-1]
            
        if new_position in self.body_set and new_positions != tail:
            return False, "SELF"

        # 移動
        self.positions.insert(0, new_position)
        self.body_set.add(new_position)

        # 最大長度限制（超過長度則刪尾）
        if len(self.positions) > self.length:
            removed = self.positions.pop()
            self.body_set.remove(removed)

        return True, "MOVED"

    def grow(self):
        self.length += 1
        self.score += 10

    def reset(self):
        self.__init__()

    def draw(self, surface):
        for p in self.positions:
            rect = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(surface, GREEN, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.randomize_position(set())

    def randomize_position(self, occupied):
        # 隨機選擇未被蛇佔據的格子
        # 若佔據格子過多，改用重試
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in occupied:
                self.position = pos
                return
        
    def draw(self, surface):
        rect = pygame.Rect((self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, RED, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)

class Game:
    def __init__(self):
    self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake - WASD to move, CTRL to speed up")
    self.clock = pygame.time.Clock()
    self.font = pygame.font.SysFont('simhei', 24)
    
    self.snake = Snake()
    self.food = Food()

    self.state = GameState.RUNNING
    self.is_speeding = False # 加速
    self.speed_multiplier = 1.5  # 加速倍率
    self.fps = BASE_FPS
    self.last_move_time = 0  # 毫秒
    self.move_interval = 1000 // self.fps  # 毫秒/步
    self.highscore = self.load_highscore()
    # 初始化食物位置，確保不在蛇身上
    self.food.randomize_position(self.snake.body_set)
    
    def load_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("highscore", 0)
        except Exception:
            return 0

    def save_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                json.dump({"highscore": self.highscore}, f)
        except Exception:
            pass

    def set_speeding(self, speeding):
        self.is_speeding = speeding
        if speeding:
            self.fps = int(self.base_fps * self.speed_multiplier)
        else:
            self.fps = self.base_fps
        # 更新移動間隔（毫秒）
        self.move_interval = max(1, 1000 // self.fps)

    def handle_event(self):
        # 處理事件（鍵盤、視窗）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_highscore()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    self.snake.queue_turn(UP)
                elif event.key == pygame.K_s:
                    self.snake.queue_turn(DOWN)
                elif event.key == pygame.K_a:
                    self.snake.queue_turn(LEFT)
                elif event.key == pygame.K_d:
                    self.snake.queue_turn(RIGHT)
                elif event.key == pygame.K_p:
                    # 暫停切換
                    if self.state == GameState.RUNNING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.RUNNING
                elif event.key == pygame.K_r:
                    # 重開
                    self.restart()
                elif event.key == pygame.K_ESCAPE:
                    self.save_highscore()
                    pygame.quit()
                    sys.exit()
###                    

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
