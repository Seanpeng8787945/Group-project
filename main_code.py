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
        new_x = head[0] + x
        new_y = head[1] + y
        new_position = (new_x, new_y)

        # 檢查撞牆
        if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
            return False, "WALL"

        # 檢查自撞（尾巴會在非成長時被移除，所以先判斷）
        # 若新位置在 body_set 中且不是尾巴（在下一行會被移除）則自撞
        tail = None
        if len(self.body)>= self.length:
            tail = self.body[-1]
            
        if new_position in self.body_set and new_position != tail:
            return False, "SELF"

        # 移動
        self.body.appendleft(new_position)
        self.body_set.add(new_position)

        # 最大長度限制（超過長度則刪尾）
        if len(self.body) > self.length:
            removed = self.body.pop()
            self.body_set.remove(removed)

        return True, "MOVED"

    def grow(self):
        self.length += 1
        self.score += 10

    def reset(self):
        self.__init__()

    def draw(self, surface):
        for p in self.body:
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
        self.base_fps = BASE_FPS
        self.fps = self.base_fps
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

    def handle_events(self):
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
                    
        # 持續按鍵（加速）
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            self.set_speeding(True)
        else:
            self.set_speeding(False)

    def restart(self):
        self.snake.reset()
        self.food.randomize_position(self.snake.body_set)
        self.state = GameState.RUNNING
        self.set_speeding(False)
        self.last_move_time = pygame.time.get_ticks()

    def update_logic(self):
        # 只在 RUNNING 狀態下更新遊戲邏輯
        if self.state != GameState.RUNNING:
            return

        now = pygame.time.get_ticks()
        if now - self.last_move_time < self.move_interval:
            return  # 還沒到下一步
        self.last_move_time = now

        ok, reason = self.snake.move()
        if not ok:
            # 遊戲結束
            self.state = GameState.GAMEOVER
            # 更新最高分
            if self.snake.score > self.highscore:
                self.highscore = self.snake.score
                self.save_highscore()
            return

        # 吃到食物?
        if self.snake.get_head_position() == self.food.position:
            self.snake.grow()
            # 重新生成食物（不在蛇身上）
            self.food.randomize_position(self.snake.body_set)

    def draw_ui(self):
        # 分數
        score_text = self.font.render(f"score: {self.snake.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # 最高分
        hs_text = self.font.render(f"highscore: {self.highscore}", True, WHITE)
        self.screen.blit(hs_text, (10, 40))

        # 加速狀態
        if self.is_speeding:
            speed_text = self.font.render("SPEED BOOST!", True, YELLOW)
            self.screen.blit(speed_text, (WIDTH // 2 - speed_text.get_width() // 2, 10))

        # 提示
        controls_text = self.font.render("WASD to move, CTRL to speed up, P pause, R restart", True, WHITE)
        self.screen.blit(controls_text, (WIDTH - controls_text.get_width() - 10, 10))

    def draw_gameover(self):
        go_text = self.font.render("Game Over! Press R to restart", True, WHITE)
        self.screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 20))

    def run(self):
        # 主迴圈：使用高頻率渲染，但邏輯以固定步進更新
        self.last_move_time = pygame.time.get_ticks()
        while True:
            self.handle_events()

            # 更新邏輯（固定步進）
            self.update_logic()


            # 繪製
            self.screen.fill(BLACK)
            self.snake.draw(self.screen)
            self.food.draw(self.screen)
            self.draw_ui()

            if self.state == GameState.PAUSED:
                pause_text = self.font.render("PAUSED (P to resume)", True, WHITE)
                self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))
            elif self.state == GameState.GAMEOVER:
                self.draw_gameover()

            pygame.display.update()
            # 渲染 FPS（不等於邏輯FPS）
            self.clock.tick(60)

def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
