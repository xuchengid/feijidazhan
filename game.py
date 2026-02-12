import pygame
import random
import math
import os

# --- 喜庆色彩配置 ---
BG_RED = (60, 10, 10)       # 深朱红背景
GOLD = (255, 215, 0)        # 金色（等级/特效）
FESTIVE_RED = (220, 20, 20)  # 喜庆红（灯笼/敌机）
WHITE = (255, 255, 255)     # 白色（龙马主体）
CYAN = (0, 255, 255)        # 青色（激光）
YELLOW = (255, 255, 100)    # 亮黄（普通子弹）
XP_PURPLE = (200, 100, 255) # 经验条颜色
GREEN = (50, 205, 50)       # 绿色（补给）

WIDTH, HEIGHT = 900, 700
FPS = 60

# 获取资源路径
def get_asset_path(filename):
    """获取资源文件的绝对路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'assets', filename)

# --- 特效类：粒子系统 ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, size=4):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        # 绘制发光粒子
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        # 添加发光效果
        glow_color = (color[0], color[1], color[2], 128)
        pygame.draw.circle(self.image, glow_color, (size//2, size//2), size//2 + 1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = random.uniform(-4, 4)
        self.vel_y = random.uniform(-4, 4)
        self.lifetime = 30
        self.original_lifetime = 30

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.lifetime -= 1
        # 粒子淡出效果
        alpha = int(255 * (self.lifetime / self.original_lifetime))
        if alpha > 0:
            self.image.set_alpha(alpha)
        if self.lifetime <= 0:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 加载龙马图像
        try:
            original_image = pygame.image.load(get_asset_path('longma_player.png')).convert_alpha()
            # 缩放到合适大小
            self.base_image = pygame.transform.smoothscale(original_image, (70, 70))
            self.image = self.base_image.copy()
        except Exception as e:
            print(f"无法加载龙马图像: {e}")
            # 后备方案：绘制简单的龙马造型
            self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, WHITE, (15, 5, 20, 40))
            pygame.draw.line(self.image, GOLD, (25, 5), (15, 0), 3)
            pygame.draw.line(self.image, GOLD, (25, 5), (35, 0), 3)
            self.base_image = self.image.copy()
        
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT - 100))
        
        self.speed = 7
        self.hp = 100
        self.max_hp = 100
        self.shield = 50
        self.max_shield = 50
        self.shield_regen_timer = 0
        self.level = 1
        self.xp = 0
        self.xp_next = 50
        self.bullet_count = 1
        self.fire_rate = 450
        self.is_laser = False
        self.last_shot = 0
        self.engine_particles = []

    def update(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.speed
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.speed
        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        
        self.shield_regen_timer += 1
        if self.shield_regen_timer > 180:
            if self.shield < self.max_shield:
                self.shield = min(self.max_shield, self.shield + 0.3)

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.xp_next = int(50 * (self.level ** 1.5))
            return True
        return False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, is_boss=False):
        super().__init__()
        self.is_boss = is_boss
        
        if is_boss:
            # 加载Boss灯笼图像
            try:
                original_image = pygame.image.load(get_asset_path('lantern_boss.png')).convert_alpha()
                self.image = pygame.transform.smoothscale(original_image, (180, 140))
            except Exception as e:
                print(f"无法加载Boss灯笼图像: {e}")
                # 后备方案
                self.image = pygame.Surface((160, 100), pygame.SRCALPHA)
                pygame.draw.ellipse(self.image, FESTIVE_RED, (10, 10, 140, 80))
                pygame.draw.rect(self.image, GOLD, (10, 10, 140, 80), 4)
            self.hp = 1000 + (player_lvl_ref * 60)
            self.rect = self.image.get_rect(center=(WIDTH//2, -100))
            self.speed = 2
        else:
            # 加载普通灯笼图像
            try:
                original_image = pygame.image.load(get_asset_path('lantern_enemy.png')).convert_alpha()
                self.image = pygame.transform.smoothscale(original_image, (45, 55))
            except Exception as e:
                print(f"无法加载灯笼图像: {e}")
                # 后备方案
                self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
                pygame.draw.ellipse(self.image, FESTIVE_RED, (5, 0, 30, 35))
                pygame.draw.rect(self.image, GOLD, (15, 35, 10, 10))
            self.hp = 1
            self.rect = self.image.get_rect(x=random.randint(50, WIDTH-50), y=-60)
            self.speed = random.uniform(2, 4)
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        if self.is_boss:
            if self.rect.y < 120: self.rect.y += 2
            self.rect.x += self.speed
            if self.rect.left < 0 or self.rect.right > WIDTH: self.speed *= -1
        else:
            self.rect.y += self.speed
            if self.rect.top > HEIGHT: self.kill()

    def shoot(self, enemy_bullets, all_sprites):
        now = pygame.time.get_ticks()
        rate = 2000 if not self.is_boss else 700
        if now - self.last_shot > rate:
            eb = EnemyBullet(self.rect.centerx, self.rect.bottom)
            enemy_bullets.add(eb)
            all_sprites.add(eb)
            self.last_shot = now

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_laser=False):
        super().__init__()
        self.is_laser = is_laser
        if is_laser:
            self.image = pygame.Surface((20, 100), pygame.SRCALPHA)
            # 绘制更华丽的激光
            for i in range(20):
                alpha = 255 - i * 10
                pygame.draw.rect(self.image, (*CYAN[:3], max(0, alpha)), (i//2, 0, 20-i, 100))
            pygame.draw.rect(self.image, WHITE, (8, 0, 4, 100))
            self.damage = 60
        else:
            self.image = pygame.Surface((10, 25), pygame.SRCALPHA)
            # 金色烟花子弹
            pygame.draw.ellipse(self.image, GOLD, (0, 0, 10, 25))
            pygame.draw.ellipse(self.image, YELLOW, (2, 2, 6, 21))
            self.damage = 30
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y -= 18
        if self.rect.bottom < 0: self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        # 绘制烟花弹
        pygame.draw.circle(self.image, FESTIVE_RED, (8, 8), 8)
        pygame.draw.circle(self.image, GOLD, (8, 8), 8, 2)
        pygame.draw.circle(self.image, WHITE, (8, 8), 4)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y += 6
        if self.rect.top > HEIGHT: self.kill()

class Supply(pygame.sprite.Sprite):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        
        # 根据类型加载不同的补给图像
        if kind == 'weapon':
            try:
                original_image = pygame.image.load(get_asset_path('supply_weapon.png')).convert_alpha()
                self.image = pygame.transform.smoothscale(original_image, (40, 40))
            except Exception as e:
                print(f"无法加载武器补给图像: {e}")
                self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.rect(self.image, GOLD, (0, 0, 30, 30), border_radius=5)
                pygame.draw.rect(self.image, WHITE, (0, 0, 30, 30), 2, border_radius=5)
        elif kind == 'heal':
            try:
                original_image = pygame.image.load(get_asset_path('supply_heal.png')).convert_alpha()
                self.image = pygame.transform.smoothscale(original_image, (40, 40))
            except Exception as e:
                print(f"无法加载治疗补给图像: {e}")
                self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.rect(self.image, FESTIVE_RED, (0, 0, 30, 30), border_radius=5)
                pygame.draw.rect(self.image, GOLD, (0, 0, 30, 30), 2, border_radius=5)
        else:  # shield
            try:
                original_image = pygame.image.load(get_asset_path('supply_shield.png')).convert_alpha()
                self.image = pygame.transform.smoothscale(original_image, (40, 40))
            except Exception as e:
                print(f"无法加载护盾补给图像: {e}")
                self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.rect(self.image, CYAN, (0, 0, 30, 30), border_radius=5)
                pygame.draw.rect(self.image, WHITE, (0, 0, 30, 30), 2, border_radius=5)
        
        self.rect = self.image.get_rect(x=random.randint(50, WIDTH-50), y=-40)
        self.glow_timer = 0

    def update(self):
        self.rect.y += 2
        if self.rect.top > HEIGHT: self.kill()
        # 添加发光动画效果
        self.glow_timer += 1

# --- 全局参考与主逻辑 ---
player_lvl_ref = 1

def create_explosion(x, y, color, group, count=15, size=5):
    """创建更华丽的爆炸特效"""
    for _ in range(count):
        p = Particle(x, y, color, random.randint(3, size))
        group.add(p)

def draw_chinese_border(screen, width, height, color=GOLD, thickness=3):
    """绘制中国风边框装饰"""
    # 四角装饰
    corner_size = 30
    for corner_x, corner_y in [(0, 0), (width-corner_size, 0), (0, height-corner_size), (width-corner_size, height-corner_size)]:
        pygame.draw.rect(screen, color, (corner_x, corner_y, corner_size, corner_size), thickness)
        pygame.draw.line(screen, color, (corner_x, corner_y), (corner_x + corner_size//2, corner_y + corner_size//2), 2)
        pygame.draw.line(screen, color, (corner_x + corner_size, corner_y + corner_size), (corner_x + corner_size//2, corner_y + corner_size//2), 2)

def draw_hp_bar(screen, x, y, width, height, current, maximum, bg_color, fill_color, label=""):
    """绘制华丽的血条"""
    # 背景
    pygame.draw.rect(screen, bg_color, (x-2, y-2, width+4, height+4), border_radius=3)
    pygame.draw.rect(screen, (30, 30, 30), (x, y, width, height), border_radius=2)
    
    # 填充
    fill_width = int(width * (current / maximum))
    if fill_width > 0:
        pygame.draw.rect(screen, fill_color, (x, y, fill_width, height), border_radius=2)
        # 高光效果
        highlight = pygame.Surface((fill_width, height//3), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 60))
        screen.blit(highlight, (x, y))
    
    # 边框
    pygame.draw.rect(screen, GOLD, (x, y, width, height), 2, border_radius=2)

def show_upgrade_menu(screen, player):
    upgrading = True
    font = pygame.font.SysFont("SimHei", 32)
    small_font = pygame.font.SysFont("SimHei", 24)
    
    # 华丽的升级界面背景
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((40, 10, 10, 220))
    
    # 绘制装饰边框
    pygame.draw.rect(overlay, GOLD, (WIDTH//2 - 280, 150, 560, 350), 4, border_radius=15)
    pygame.draw.rect(overlay, FESTIVE_RED, (WIDTH//2 - 275, 155, 550, 340), 2, border_radius=12)
    
    while upgrading:
        screen.blit(overlay, (0, 0))
        
        # 标题
        title = font.render(f"🎊 龙马升级 (LV {player.level}) 🎊", True, GOLD)
        title_rect = title.get_rect(center=(WIDTH//2, 190))
        screen.blit(title, title_rect)
        
        # 选项
        options = [
            ("🐉 1. 龙魂觉醒", "增加炮弹数量/射速", WHITE),
            ("💚 2. 祥龙补给", "生命上限+20并回满", (100, 255, 100)),
            ("🛡️ 3. 瑞马护甲", "护盾上限+20", CYAN)
        ]
        
        for i, (title_text, desc_text, color) in enumerate(options):
            y_pos = 260 + i * 70
            title_surf = font.render(title_text, True, color)
            desc_surf = small_font.render(desc_text, True, (200, 200, 200))
            screen.blit(title_surf, (WIDTH//2 - 180, y_pos))
            screen.blit(desc_surf, (WIDTH//2 - 180, y_pos + 30))
        
        # 底部提示
        hint = small_font.render("按数字键选择升级方向", True, (150, 150, 150))
        hint_rect = hint.get_rect(center=(WIDTH//2, 460))
        screen.blit(hint, hint_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    if player.bullet_count < 3: player.bullet_count += 1
                    else: player.fire_rate = max(120, player.fire_rate - 60)
                    upgrading = False
                elif event.key == pygame.K_2:
                    player.max_hp += 20
                    player.hp = player.max_hp
                    upgrading = False
                elif event.key == pygame.K_3:
                    player.max_shield += 20
                    player.shield = player.max_shield
                    upgrading = False

def draw_firework(screen, x, y, frame, color):
    """绘制烟花效果"""
    num_sparks = 12
    for i in range(num_sparks):
        angle = (i * 30 + frame * 3) % 360
        dist = frame * 2
        spark_x = x + math.cos(math.radians(angle)) * dist
        spark_y = y + math.sin(math.radians(angle)) * dist
        spark_size = max(1, 4 - frame // 10)
        pygame.draw.circle(screen, color, (int(spark_x), int(spark_y)), spark_size)

def main():
    global player_lvl_ref
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🎊 龙马精神：新春大作战 🏮")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("SimHei", 24)
    big_font = pygame.font.SysFont("SimHei", 48)
    
    # 加载背景图像
    try:
        bg_image = pygame.image.load(get_asset_path('background.png')).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (WIDTH, HEIGHT))
    except Exception as e:
        print(f"无法加载背景图像: {e}")
        bg_image = None

    player = Player()
    all_sprites = pygame.sprite.Group(player)
    enemies = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    supplies = pygame.sprite.Group()
    boss_group = pygame.sprite.Group()
    particles = pygame.sprite.Group()

    score = 0
    in_boss_fight = False
    next_boss_milestone = 10
    running = True
    frame_count = 0
    fireworks = []  # 存储烟花效果

    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()
        player_lvl_ref = player.level
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # 1. 逻辑生成
        if not in_boss_fight:
            if random.random() < 0.04:
                e = Enemy()
                enemies.add(e)
                all_sprites.add(e)
            if player.level >= next_boss_milestone:
                in_boss_fight = True
                for e in enemies:
                    create_explosion(e.rect.centerx, e.rect.centery, GOLD, particles, 20, 6)
                    e.kill()
                boss = Enemy(is_boss=True)
                boss_group.add(boss)
                all_sprites.add(boss)

        # 2. 玩家开火逻辑
        if pygame.mouse.get_pressed()[0] and now - player.last_shot > player.fire_rate:
            if player.is_laser:
                b = Bullet(player.rect.centerx, player.rect.top, True)
                player_bullets.add(b)
                all_sprites.add(b)
            else:
                offsets = [0] if player.bullet_count==1 else ([-15, 15] if player.bullet_count==2 else [-25, 0, 25])
                for off in offsets:
                    b = Bullet(player.rect.centerx + off, player.rect.top)
                    player_bullets.add(b)
                    all_sprites.add(b)
            player.last_shot = now

        for e in enemies:
            e.shoot(enemy_bullets, all_sprites)
        for b in boss_group:
            b.shoot(enemy_bullets, all_sprites)

        # 3. 碰撞处理
        # 补给
        for s in pygame.sprite.spritecollide(player, supplies, True):
            create_explosion(player.rect.centerx, player.rect.centery, GOLD, particles, 20, 5)
            if s.kind == 'weapon':
                if player.bullet_count >= 3: player.is_laser = True
                else: player.bullet_count += 1
            elif s.kind == 'heal':
                player.hp = min(player.max_hp, player.hp + 50)
            elif s.kind == 'shield':
                player.max_shield += 10
                player.shield = player.max_shield

        # 玩家子弹打击
        for b in player_bullets:
            hits = pygame.sprite.spritecollide(b, enemies, True)
            for hit in hits:
                create_explosion(hit.rect.centerx, hit.rect.centery, FESTIVE_RED, particles, 18, 5)
                score += 10
                if player.gain_xp(35):
                    show_upgrade_menu(screen, player)
                if not b.is_laser: b.kill()
            
            boss_hits = pygame.sprite.spritecollide(b, boss_group, False)
            for boss in boss_hits:
                boss.hp -= b.damage
                create_explosion(b.rect.centerx, b.rect.top, GOLD, particles, 10, 4)
                if not b.is_laser: b.kill()
                if boss.hp <= 0:
                    # Boss死亡大爆炸
                    for _ in range(3):
                        create_explosion(
                            boss.rect.centerx + random.randint(-50, 50),
                            boss.rect.centery + random.randint(-30, 30),
                            GOLD, particles, 25, 7
                        )
                    boss.kill()
                    in_boss_fight = False
                    score += 2000
                    next_boss_milestone += 5
                    # 添加烟花效果
                    fireworks.append({'x': boss.rect.centerx, 'y': boss.rect.centery, 'frame': 0, 'color': GOLD})
                    # 掉落补给
                    ws = Supply('weapon')
                    ws.rect.center = boss.rect.center
                    supplies.add(ws)
                    all_sprites.add(ws)

        # 玩家受损
        if pygame.sprite.spritecollide(player, enemy_bullets, True) or pygame.sprite.spritecollide(player, enemies, True):
            player.shield_regen_timer = 0
            if player.shield > 0:
                player.shield -= 20
                if player.shield < 0:
                    player.hp += player.shield
                    player.shield = 0
            else:
                player.hp -= 20

        # 4. 绘图
        all_sprites.update()
        particles.update()
        
        # 绘制背景
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill(BG_RED)
            # 备用：绘制简单的纸屑效果
            for _ in range(3):
                pygame.draw.circle(screen, GOLD, (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)
        
        # 绘制中国风边框
        draw_chinese_border(screen, WIDTH, HEIGHT, GOLD, 3)
        
        # 绘制烟花
        for fw in fireworks[:]:
            draw_firework(screen, fw['x'], fw['y'], fw['frame'], fw['color'])
            fw['frame'] += 1
            if fw['frame'] > 30:
                fireworks.remove(fw)
        
        all_sprites.draw(screen)
        particles.draw(screen)
        
        # UI - 华丽的血条和护盾条
        draw_hp_bar(screen, 25, 25, 200, 18, player.hp, player.max_hp, (80, 0, 0), (50, 205, 50), "生命")
        draw_hp_bar(screen, 25, 50, 200, 12, player.shield, player.max_shield, (0, 50, 50), CYAN, "护盾")
        
        # 经验条
        pygame.draw.rect(screen, (30, 30, 60), (0, HEIGHT-12, WIDTH, 12))
        xp_width = WIDTH * (player.xp / player.xp_next)
        pygame.draw.rect(screen, XP_PURPLE, (0, HEIGHT-12, xp_width, 12))
        pygame.draw.rect(screen, GOLD, (0, HEIGHT-12, WIDTH, 12), 1)
        
        # 信息显示
        info = font.render(f"🎊 等级: {player.level}  🧧 福分: {score}", True, GOLD)
        screen.blit(info, (25, 75))
        
        # Boss血条
        if in_boss_fight:
            for boss in boss_group:
                boss_hp_width = min(300, boss.hp // 4)
                pygame.draw.rect(screen, (50, 0, 0), (WIDTH//2-150, 15, 300, 20), border_radius=5)
                pygame.draw.rect(screen, FESTIVE_RED, (WIDTH//2-150, 15, boss_hp_width, 20), border_radius=5)
                pygame.draw.rect(screen, GOLD, (WIDTH//2-150, 15, 300, 20), 2, border_radius=5)
                boss_label = font.render("🏮 年兽 Boss 🏮", True, GOLD)
                screen.blit(boss_label, (WIDTH//2 - 70, 40))

        # 游戏结束
        if player.hp <= 0:
            # 显示游戏结束画面
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((40, 10, 10, 200))
            screen.blit(overlay, (0, 0))
            
            game_over = big_font.render("🎊 新春大吉 🎊", True, GOLD)
            score_text = font.render(f"最终福分: {score}", True, WHITE)
            level_text = font.render(f"最终等级: {player.level}", True, WHITE)
            
            screen.blit(game_over, (WIDTH//2 - 120, HEIGHT//2 - 80))
            screen.blit(score_text, (WIDTH//2 - 70, HEIGHT//2))
            screen.blit(level_text, (WIDTH//2 - 70, HEIGHT//2 + 40))
            
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
        else:
            pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
