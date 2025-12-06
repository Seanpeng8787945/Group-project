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
BASE_FPS = 7 # 基礎FPS
FPS = BASE_FPS  # 當前FPS

# 顏色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)  # 加速狀態和雙倍食物
BLUE = (0, 0, 255)      # 新增藍色用於減速食物

# 方向
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# 獎勵食物類型
class BonusType(Enum):
    STANDARD = 0    # 紅色，+10 分，長度 +1
    DOUBLE_SCORE = 1 # 黃色，+20 分，長度 +1
    SLOW_DOWN = 2   # 藍色，-10 分，遊戲速度暫時減慢

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
            
        # 修正：即使長度為 1，頭撞到自己也不能算撞到尾巴（因為尾巴和頭是同一個點）
        # 這裡的邏輯是正確的：如果新位置在 body_set 中，且不是即將移除的尾巴，則撞到
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
        # 這個方法在新邏輯中不再直接使用，但保留以防萬一
        self.length += 1
        self.score += 10

    def reset(self):
        self.__init__()

    def draw(self, surface):
        for p in self.body:
            rect = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
            # 讓蛇頭和蛇身有點區別
            if p == self.body[0]:
                pygame.draw.rect(surface, (0, 200, 0), rect) # 較深的綠色
            else:
                pygame.draw.rect(surface, GREEN, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    # 擴展後的 Food 類別，現在可以代表所有類型的食物
    def __init__(self, bonus_type=BonusType.STANDARD):
        self.position = (0, 0)
        self.bonus_type = bonus_type
        self.properties = self._get_properties()
        
    def _get_properties(self):
        # 根據食物類型定義屬性
        if self.bonus_type == BonusType.STANDARD:
            # score, color, grow, speed_effect(倍率)
            return {'score': 10, 'color': RED, 'grow': 1, 'speed_multiplier': 1.0}
        elif self.bonus_type == BonusType.DOUBLE_SCORE:
            return {'score': 20, 'color': YELLOW, 'grow': 1, 'speed_multiplier': 1.0}
        elif self.bonus_type == BonusType.SLOW_DOWN:
            # 減速食物扣分，且將速度變為基礎速度的 50%
            return {'score': -10, 'color': BLUE, 'grow': 0, 'speed_multiplier': 0.5} 

    def randomize_position(self, occupied):
        # 隨機選擇未被蛇佔據的格子
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in occupied:
                self.position = pos
                return
            
    def draw(self, surface):
        rect = pygame.Rect((self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE), (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(surface, self.properties['color'], rect)
        pygame.draw.rect(surface, BLACK, rect, 1)

def create_random_food():
    # 決定生成哪種食物（機率）
    r = random.random()
    if r < 0.7:     # 70% 機率是普通食物
        return Food(BonusType.STANDARD)
    elif r < 0.9:   # 20% 機率是雙倍分數食物
        return Food(BonusType.DOUBLE_SCORE)
    else:           # 10% 機率是減速食物
        return Food(BonusType.SLOW_DOWN)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake - WASD to move, CTRL to speed up")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('simhei', 24)
        
        self.snake = Snake()
        
        # 使用新的食物生成函數
        self.food = create_random_food()

        self.state = GameState.RUNNING
        self.is_speeding = False      # 玩家加速狀態
        self.speed_multiplier = 1.8   # 玩家加速倍率 (提高到 1.8 讓差異更明顯)
        self.base_fps = BASE_FPS
        
        # 特殊效果控制
        self.slow_down_active = False # 減速效果是否開啟
        self.slow_down_timer = 0      # 減速效果結束時間
        self.SLOW_DURATION = 5000     # 減速效果持續 5000 毫秒 (5 秒)

        # 速度與計時器
        self.fps = self.base_fps
        self.last_move_time = 0       # 毫秒
        self.move_interval = 1000 // self.fps # 毫秒/步
        
        self.highscore = self.load_highscore()
        # 初始化食物位置，確保不在蛇身上
        self.food.randomize_position(self.snake.body_set)
        
        # 確保初始速度正確
        self.set_speeding(False)
        
    def load_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("highscore", 0)
        except Exception:
            return 0

    def save_highscore(self):
        # 只有在分數高於歷史紀錄時才寫入
        if self.snake.score > self.highscore:
             self.highscore = self.snake.score
        try:
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                json.dump({"highscore": self.highscore}, f)
        except Exception:
            pass

    def set_speeding(self, speeding):
        """
        更新當前遊戲的 FPS 和移動間隔，同時考慮玩家加速和食物減速。
        """
        self.is_speeding = speeding
        
        # 1. 計算基礎 FPS
        calculated_fps = self.base_fps
        
        # 2. 應用玩家加速 (CTRL 鍵)
        if self.is_speeding:
            calculated_fps *= self.speed_multiplier
            
        # 3. 應用食物減速效果
        if self.slow_down_active:
            # 減速食物的 speed_multiplier 是 0.5
            slow_multiplier = self.food.properties.get('speed_multiplier', 1.0) 
            calculated_fps *= slow_multiplier
            
        # 確保 FPS 不會低於 1
        self.fps = max(1, int(calculated_fps)) 
        
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
        is_ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        self.set_speeding(is_ctrl_pressed)

    def restart(self):
        self.snake.reset()
        self.food = create_random_food()
        self.food.randomize_position(self.snake.body_set)
        self.state = GameState.RUNNING
        
        # 重設所有特殊效果
        self.slow_down_active = False
        self.slow_down_timer = 0
        self.set_speeding(False)
        
        self.last_move_time = pygame.time.get_ticks()

    def update_logic(self):
        now = pygame.time.get_ticks()
        
        # --- [START] 特殊食物效果計時器 ---
        if self.slow_down_active and now > self.slow_down_timer:
            self.slow_down_active = False
            self.set_speeding(self.is_speeding) # 重設速度，將減速效果移除
        # --- [END] 特殊食物效果計時器 ---

        # 只在 RUNNING 狀態下更新遊戲邏輯
        if self.state != GameState.RUNNING:
            return

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
            props = self.food.properties
            
            # 處理分數和成長
            self.snake.score += props['score']
            self.snake.length += props['grow']
            
            # 處理特殊效果
            if self.food.bonus_type == BonusType.SLOW_DOWN:
                # 只有在目前沒有減速效果時才觸發新的減速
                if not self.slow_down_active:
                    self.slow_down_active = True
                    self.slow_down_timer = now + self.SLOW_DURATION
            
            # 重新應用速度 (即使用戶沒有按 CTRL，也要更新以應用/移除效果)
            self.set_speeding(self.is_speeding)
            
            # 重新生成食物
            self.food = create_random_food()
            self.food.randomize_position(self.snake.body_set)

    def draw_ui(self):
        # 分數
        score_text = self.font.render(f"SCORE: {self.snake.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # 最高分
        hs_text = self.font.render(f"HIGHSCORE: {self.highscore}", True, WHITE)
        self.screen.blit(hs_text, (10, 40))

        # 加速狀態
        if self.is_speeding:
            speed_text = self.font.render("SPEED BOOST!", True, YELLOW)
            self.screen.blit(speed_text, (WIDTH // 2 - speed_text.get_width() // 2, 10))
            
        # 減速狀態
        if self.slow_down_active:
            # 計算剩餘時間 (秒)
            remaining_time = max(0, self.slow_down_timer - pygame.time.get_ticks()) // 1000 + 1 
            slow_text = self.font.render(f"SLOW! {remaining_time}s", True, BLUE)
            # 放置在加速文本的下方
            self.screen.blit(slow_text, (WIDTH // 2 - slow_text.get_width() // 2, 40))

        # 提示
        controls_text = self.font.render("WASD move, CTRL speed, P pause, R restart, ESC quit", True, WHITE)
        self.screen.blit(controls_text, (WIDTH - controls_text.get_width() - 10, 10))
        
    def draw_grid(self):
        """繪製灰色網格線"""
        grid_color = (50, 50, 50)
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, grid_color, (0, y), (WIDTH, y))

    def draw_gameover(self):
        go_text = self.font.render("GAME OVER! Press R to restart", True, WHITE)
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
            self.draw_grid() # 新增：繪製網格
            
            # 只有在非菜單狀態下才繪製蛇和食物
            if self.state != GameState.MENU:
                self.snake.draw(self.screen)
                self.food.draw(self.screen)
            
            self.draw_ui()

            if self.state == GameState.PAUSED:
                # 繪製半透明覆蓋層
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 128)) 
                self.screen.blit(s, (0, 0))
                
                pause_text = self.font.render("PAUSED (P to resume)", True, WHITE)
                self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))
                
            elif self.state == GameState.GAMEOVER:
                self.draw_gameover()

            pygame.display.update()
            # 渲染 FPS (保持高幀率，讓加速/減速的視覺效果更平滑)
            self.clock.tick(60)

def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
