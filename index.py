import pygame
import sys
import random
import math
import json
import os
from datetime import datetime

# 🔊 CONFIGURAÇÃO DE ÁUDIO
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# ----- CONFIG -----
GRID_SIZE = 150
BASE_CELL_SIZE = 60
MIN_ZOOM = 0.2
MAX_ZOOM = 2
ZOOM_SPEED = 0.1

# ===== Configuração do mapa orgânico =====
MAP_RADIUS = GRID_SIZE // 2
CENTER_X = GRID_SIZE // 2
CENTER_Y = GRID_SIZE // 2
NOISE_STRENGTH = 0.5
WATER_COLOR = (64, 164, 223)
SAND_COLOR = (238, 214, 175)
GRASS_COLOR = (124, 238, 124)  # Verde claro

# ===== Configurações de UI =====
FULLSCREEN = True

if FULLSCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
else:
    SCREEN_WIDTH = 1000
    SCREEN_HEIGHT = 700
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("City Builder")

clock = pygame.time.Clock()

# Fontes
font_large = pygame.font.Font(None, 36)
font_medium = pygame.font.Font(None, 24)
font_small = pygame.font.Font(None, 18)

# Cores modernas para UI
COLORS = {
    'primary': (52, 152, 219),      # Azul
    'success': (46, 204, 113),       # Verde
    'warning': (241, 196, 15),       # Amarelo
    'danger': (231, 76, 60),         # Vermelho
    'dark': (44, 62, 80),            # Azul escuro
    'light': (236, 240, 241),        # Cinza claro
    'gold': (241, 196, 15),          # Dourado
    'panel': (52, 73, 94, 200),       # Painel semi-transparente
    'construction': (241, 196, 15, 200),  # Amarelo para construção
}

# Adicione esta função na seção de configurações, depois das cores
def get_water_color(distance_from_center, max_distance):
    # Cores da água (RGB)
    SHALLOW_WATER = (64, 164, 223)      # Azul claro (perto da costa)
    DEEP_WATER = (20, 40, 80)           # Azul escuro (longe da costa)
    
    # Calcula o fator de profundidade (0 = costa, 1 = mais longe)
    depth_factor = min(1.0, (distance_from_center - (MAP_RADIUS - 5)) / 10)
    depth_factor = max(0, min(1, depth_factor))
    
    # Interpola entre as cores
    r = int(SHALLOW_WATER[0] + (DEEP_WATER[0] - SHALLOW_WATER[0]) * depth_factor)
    g = int(SHALLOW_WATER[1] + (DEEP_WATER[1] - SHALLOW_WATER[1]) * depth_factor)
    b = int(SHALLOW_WATER[2] + (DEEP_WATER[2] - SHALLOW_WATER[2]) * depth_factor)
    
    return (r, g, b)

# ----- SONS ----- (substitua a seção existente)
pygame.mixer.set_num_channels(32)  # Aumenta o número de canais disponíveis

build_sound = pygame.mixer.Sound("sound/build.wav")
break_sound = pygame.mixer.Sound("sound/breaking.wav")
button_sound = pygame.mixer.Sound("sound/button.wav")
build_finish_sound = pygame.mixer.Sound("sound/build-finish.wav")
cutting_sound = pygame.mixer.Sound("sound/cutting.wav") 
falling_tree_sound = pygame.mixer.Sound("sound/falling-tree.wav") 

build_sound.set_volume(0.5)
break_sound.set_volume(0.5)
button_sound.set_volume(1.0)
build_finish_sound.set_volume(1.0)
cutting_sound.set_volume(3)
falling_tree_sound.set_volume(0.4)

# ----- IMAGENS DOS PRÉDIOS (tamanho original) -----
building_images_original = {}

building_images_original["Casa"] = pygame.image.load("assets/casa.png").convert_alpha()
building_images_original["Predio"] = pygame.image.load("assets/predio.png").convert_alpha()
building_images_original["Lojinha"] = pygame.image.load("assets/loja-game.png").convert_alpha()
building_images_original["Shopping"] = pygame.image.load("assets/shopping-game.png").convert_alpha()
building_images_original["Factory"] = pygame.image.load("assets/factory-game.png").convert_alpha()
building_images_original["School"] = pygame.image.load("assets/school.png").convert_alpha()
building_images_original["Mall"] = pygame.image.load("assets/mall.png").convert_alpha()

try:
    oil_gen_img = pygame.image.load("assets/GeradorPetroleo.png").convert_alpha()
except:
    oil_gen_img = pygame.Surface((BASE_CELL_SIZE, BASE_CELL_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(oil_gen_img, (40, 60, 100), (0, 0, BASE_CELL_SIZE, BASE_CELL_SIZE))
    pygame.draw.circle(oil_gen_img, (255, 140, 0), (BASE_CELL_SIZE//2, BASE_CELL_SIZE//2), BASE_CELL_SIZE//4)
    print("Arquivo assets/gerador-petroleo.png não encontrado. Usando fallback.")
building_images_original["Gerador de petróleo"] = oil_gen_img

try:
    mina_img = pygame.image.load("assets/mina.png").convert_alpha()
except:
    mina_img = pygame.Surface((BASE_CELL_SIZE, BASE_CELL_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(mina_img, (100, 100, 110), (0, 0, BASE_CELL_SIZE, BASE_CELL_SIZE))
    print("Arquivo assets/mina.png não encontrado. Usando fallback.")
building_images_original["Mina"] = mina_img

# ===== NOVO: Configuração do FPS =====
show_fps = True
fps_update_time = 0
fps_counter = 0
fps_display = "0"

# ----- IMAGENS DAS ÁRVORES (tamanho original) -----
tree_images_original = []
for i in range(1, 6):
    try:
        img = pygame.image.load(f"assets/tree{i}.png").convert_alpha()
        tree_images_original.append(img)
    except:
        print(f"Arquivo assets/tree{i}.png não encontrado. Usando fallback.")
        fallback = pygame.Surface((BASE_CELL_SIZE, BASE_CELL_SIZE), pygame.SRCALPHA)
        colors = [(34,139,34), (0,100,0), (50,150,50), (80,180,80), (100,200,100)]
        pygame.draw.rect(fallback, colors[i-1], (0, 0, BASE_CELL_SIZE, BASE_CELL_SIZE))
        pygame.draw.circle(fallback, (101,67,33), (BASE_CELL_SIZE//2, BASE_CELL_SIZE-10), 10)
        tree_images_original.append(fallback)

# ----- ÍCONES DE RECURSOS -----
ICON_SIZE = (35, 35)

try:
    wood_icon = pygame.image.load("assets/logs.png").convert_alpha()
    wood_icon = pygame.transform.scale(wood_icon, ICON_SIZE)
except:
    wood_icon = pygame.Surface(ICON_SIZE)
    wood_icon.fill((139, 69, 19))
    print("Arquivo assets/logs.png não encontrado. Usando fallback.")

try:
    money_icon = pygame.image.load("assets/nota.png").convert_alpha()
    money_icon = pygame.transform.scale(money_icon, ICON_SIZE)
except:
    money_icon = pygame.Surface(ICON_SIZE)
    money_icon.fill((0, 255, 0))
    print("Arquivo assets/nota.png não encontrado. Usando fallback.")

try:
    population_icon = pygame.image.load("assets/population.png").convert_alpha()
    population_icon = pygame.transform.scale(population_icon, ICON_SIZE)
except:
    population_icon = pygame.Surface(ICON_SIZE)
    population_icon.fill((255, 215, 0))
    print("Arquivo assets/population.png não encontrado. Usando fallback.")

try:
    oil_icon = pygame.image.load("assets/petroleo.png").convert_alpha()
    oil_icon = pygame.transform.scale(oil_icon, ICON_SIZE)
except:
    oil_icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
    oil_icon.fill((30, 30, 30))
    pygame.draw.circle(oil_icon, (255, 140, 0), (ICON_SIZE[0]//2, ICON_SIZE[1]//2), ICON_SIZE[0]//3)
    print("Arquivo assets/petroleo.png não encontrado. Usando fallback.")

try:
    stone_icon = pygame.image.load("assets/pedra.png").convert_alpha()
    stone_icon = pygame.transform.scale(stone_icon, ICON_SIZE)
except:
    stone_icon = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
    stone_icon.fill((80, 80, 90))
    pygame.draw.polygon(stone_icon, (190, 190, 200), [(ICON_SIZE[0]//2, 4), (ICON_SIZE[0]-4, ICON_SIZE[1]-4), (4, ICON_SIZE[1]-4)])
    print("Arquivo assets/pedra.png não encontrado. Usando fallback.")

try:
    rock_img = pygame.image.load("assets/pedra.png").convert_alpha()
except:
    rock_img = None
    print("Arquivo assets/pedra.png não encontrado. Rocks usarão fallback.")

# ===== IMAGEM DO BOT =====
try:
    bot_image = pygame.image.load("assets/bot.png").convert_alpha()
    bot_image = pygame.transform.scale(bot_image, (80, 80))
except Exception as e:
    bot_image = pygame.Surface((80, 80), pygame.SRCALPHA)
    pygame.draw.circle(bot_image, (255, 50, 50), (40, 40), 35)
    pygame.draw.rect(bot_image, (200, 200, 200), (25, 30, 30, 35))

# ===== NOVO: Carregar cursores personalizados =====
CURSOR_SIZE = (32, 32)  # Tamanho do cursor

try:
    axe_cursor = pygame.image.load("assets/axe.png").convert_alpha()
    axe_cursor = pygame.transform.scale(axe_cursor, CURSOR_SIZE)
except:
    axe_cursor = pygame.Surface(CURSOR_SIZE)
    axe_cursor.fill((255, 0, 0))
    print("Arquivo assets/axe.png não encontrado. Usando fallback.")

try:
    hammer_cursor = pygame.image.load("assets/hammer.png").convert_alpha()
    hammer_cursor = pygame.transform.scale(hammer_cursor, CURSOR_SIZE)
except:
    hammer_cursor = pygame.Surface(CURSOR_SIZE)
    hammer_cursor.fill((128, 128, 128))
    print("Arquivo assets/hammer.png não encontrado. Usando fallback.")

try:
    pickaxe_cursor = pygame.image.load("assets/picareta.png").convert_alpha()
    pickaxe_cursor = pygame.transform.scale(pickaxe_cursor, CURSOR_SIZE)
except:
    pickaxe_cursor = pygame.Surface(CURSOR_SIZE)
    pickaxe_cursor.fill((100, 70, 30))
    print("Arquivo assets/picareta.png não encontrado. Usando fallback.")

# Ícone para botões de ferramenta (usa o mesmo asset do martelo por enquanto)
tool_button_icon = pygame.transform.scale(hammer_cursor, (20, 20))

# Mostra o cursor padrão do sistema (ainda desenharemos o customizado por cima)
pygame.mouse.set_visible(True)
# ================================================

# ===== Classe Button para botões estilizados =====
class Button:
    def __init__(self, x, y, width, height, text, color=COLORS['primary'], 
                 text_color=(255,255,255), icon=None, border_radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.icon = icon
        self.border_radius = border_radius
        self.hovered = False
        self.active = False
        
    def draw(self, surface):
        color = self.color
        if self.active:
            color = tuple(min(c + 30, 255) for c in self.color[:3])
        elif self.hovered:
            color = tuple(min(c + 20, 255) for c in self.color[:3])
        
        # Desenha sombra
        shadow_rect = self.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(surface, (0,0,0,50), shadow_rect, border_radius=self.border_radius)
        
        # Desenha botão
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, (255,255,255,30), self.rect, width=2, border_radius=self.border_radius)
        
        # Desenha ícone se houver
        text_x = self.rect.centerx
        if self.icon:
            icon_rect = self.icon.get_rect()
            icon_rect.center = (self.rect.x + 25, self.rect.centery)
            surface.blit(self.icon, icon_rect)
            text_x = self.rect.x + 45
        
        # Desenha texto
        text_surf = font_medium.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(text_x, self.rect.centery))
        surface.blit(text_surf, text_rect)

# ===== Classe Panel para painéis estilizados =====
class Panel:
    def __init__(self, x, y, width, height, color=COLORS['panel'], border_radius=15):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.border_radius = border_radius
        
    def draw(self, surface):
        # Desenha sombra
        shadow_rect = self.rect.copy()
        shadow_rect.y += 5
        pygame.draw.rect(surface, (0,0,0,30), shadow_rect, border_radius=self.border_radius)
        
        # Desenha painel
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, self.color, s.get_rect(), border_radius=self.border_radius)
        surface.blit(s, self.rect)
        
        # Desenha borda
        pygame.draw.rect(surface, (255,255,255,50), self.rect, width=2, border_radius=self.border_radius)

# ===== Classe ScrollBar para rolagem =====
class ScrollBar:
    def __init__(self, x, y, width, height, total_items, visible_items):
        self.track_rect = pygame.Rect(x, y, width, height)
        self.total_items = total_items
        self.visible_items = visible_items
        self.offset = 0
        self.max_offset = max(0, total_items - visible_items)
        
    def update_dimensions(self, total_items, visible_items):
        self.total_items = total_items
        self.visible_items = visible_items
        self.max_offset = max(0, total_items - visible_items)
        self.offset = min(self.offset, self.max_offset)
    
    def get_thumb_rect(self):
        if self.max_offset == 0:
            return self.track_rect
        thumb_height = max(20, self.track_rect.height * (self.visible_items / self.total_items))
        thumb_y = self.track_rect.y + (self.offset / self.max_offset) * (self.track_rect.height - thumb_height)
        return pygame.Rect(self.track_rect.x, thumb_y, self.track_rect.width, thumb_height)
    
    def scroll(self, delta):
        self.offset = max(0, min(self.offset + delta, self.max_offset))
    
    def draw(self, surface):
        # Desenha track (fundo)
        pygame.draw.rect(surface, (30, 40, 60), self.track_rect, border_radius=8)
        # Desenha thumb (controle)
        thumb = self.get_thumb_rect()
        pygame.draw.rect(surface, COLORS['primary'], thumb, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255, 100), thumb, width=1, border_radius=8)

# ===== Botões da UI =====
menu_btn = Button(20, 20, 100, 40, "Menu", COLORS['primary'])
hammer_btn = Button(130, 20, 130, 40, "Martelo", COLORS['danger'])
collect_btn = Button(270, 20, 160, 40, "Cortar ($5)", COLORS['success'])
pickaxe_btn = Button(440, 20, 140, 40, "Picareta ($5)", (100, 70, 30))
upgrade_btn = Button(590, 20, 120, 40, "Upgrades", COLORS['gold'])

# Painel de recursos
resources_panel = Panel(SCREEN_WIDTH - 280, 20, 260, 360)

# ----- CÂMERA COM ZOOM SUAVE -----
camera_x = 250
camera_y = 250
target_camera_x = 250
target_camera_y = 250
zoom = 1.0
target_zoom = 1.0
dragging = False
last_mouse_pos = (0, 0)
bot_initial_pan_done = False  # Rastreia se já fez o pan inicial para mostrar o bot

# ===== Gerador de mapa orgânico =====
class MapGenerator:
    def __init__(self):
        self.water_map = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.sand_map = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.generate_organic_map()
    
    def noise(self, x, y):
        return math.sin(x * 0.3) * math.cos(y * 0.3) * random.uniform(-1, 1)

    def generate_organic_map(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CENTER_X
                dy = y - CENTER_Y
                distance = math.sqrt(dx*dx + dy*dy)
                
                noise_value = (
                    self.noise(x * 0.5, y * 0.5) * NOISE_STRENGTH +
                    math.sin(x * 0.2) * math.cos(y * 0.2) * 3
                )
                
                noisy_distance = distance + noise_value
                is_water = noisy_distance > MAP_RADIUS - 2
                is_sand = not is_water and noisy_distance > MAP_RADIUS - 5
                
                self.water_map[y][x] = is_water
                self.sand_map[y][x] = is_sand and not is_water
    
    def is_water(self, x, y):
        if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
            return True
        return self.water_map[y][x]
    
    def is_sand(self, x, y):
        if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
            return False
        return self.sand_map[y][x]

map_generator = MapGenerator()

# ===== Sistema de Viewport Culling =====
def get_visible_range():
    start_x = int(camera_x // BASE_CELL_SIZE)
    start_y = int(camera_y // BASE_CELL_SIZE)
    
    visible_cells_x = int(SCREEN_WIDTH / (BASE_CELL_SIZE * zoom)) + 2
    visible_cells_y = int(SCREEN_HEIGHT / (BASE_CELL_SIZE * zoom)) + 2
    
    end_x = start_x + visible_cells_x
    end_y = start_y + visible_cells_y
    
    start_x = max(0, min(start_x, GRID_SIZE))
    start_y = max(0, min(start_y, GRID_SIZE))
    end_x = max(0, min(end_x, GRID_SIZE))
    end_y = max(0, min(end_y, GRID_SIZE))
    
    return start_x, start_y, end_x, end_y

# ----- ECONOMIA -----
# JOGADOR
money = 1000
wood = 0
oil = 0
stone = 0

# BOT (IA COMPETIDORA)
bot_money = 1000
bot_wood = 100  # Recursos iniciais para começar a colher
bot_oil = 0
bot_stone = 100  # Recursos iniciais
bot_buildings_completed_by_name = {}  # Similar ao jogador
bot_building_id_counter = 0
bot_total_buildings_completed = 0
bot_collecting_trees = []  # Árvores que o bot está coletando
bot_collecting_rocks = []  # Rochas que o bot está coletando
bot_collect_start_times = {}  # Rastreador de tempo de coleta

# Sistemas de população SEPARADOS
class PopulationSystem:
    def __init__(self, owner="player"):
        self.population = 0
        self.owner = owner  # "player" ou "bot"
        
    def calculate_population(self, grid, owner="player"):
        total = 0
        counted_buildings = set()
        
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid[y][x] is not None:
                    # Verifica se o prédio pertence a este owner
                    if grid[y][x].get("owner", "player") != owner:
                        continue
                    
                    building_id = grid[y][x]["id"]
                    if building_id not in counted_buildings:
                        building_name = grid[y][x]["name"]
                        if building_name == "Casa":
                            total += 4
                        elif building_name == "Predio":
                            total += 20
                        counted_buildings.add(building_id)
        
        self.population = total
        return total
    
    def get_income_multiplier(self):
        return 1.0 + (self.population * 0.01)

population_system = PopulationSystem(owner="player")
bot_population_system = PopulationSystem(owner="bot")

# ===== SISTEMA DE UPGRADES =====
class UpgradeSystem:
    def __init__(self):
        # Upgrade de cortes simultâneos
        self.simultaneous_cuts_level = 1
        self.max_simultaneous_cuts_level = 5
        self.simultaneous_cuts_cost = [500, 5000, 50000, 500000, 5000000]
        
        # Upgrade de tempo de corte
        self.cut_time_level = 1
        self.max_cut_time_level = 5
        self.cut_time_cost = [30, 60, 120, 240, 480]
        self.base_cut_time = 10000
        self.min_cut_time = 3000
        
        # Upgrade de tempo de construção
        self.construction_time_level = 1
        self.max_construction_time_level = 7
        self.construction_time_cost = [0, 1000, 5000, 25000, 100000, 500000, 1000000]
        self.construction_time_reduction = [0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95]
        
    def get_current_cut_time(self):
        time_reduction = (self.cut_time_level - 1) * 1750
        return max(self.min_cut_time, self.base_cut_time - time_reduction)
    
    def get_construction_time_multiplier(self):
        return 1.0 - self.construction_time_reduction[self.construction_time_level - 1]
    
    def can_upgrade_simultaneous(self):
        return (self.simultaneous_cuts_level < self.max_simultaneous_cuts_level and 
                money >= self.simultaneous_cuts_cost[self.simultaneous_cuts_level])
    
    def can_upgrade_cut_time(self):
        return (self.cut_time_level < self.max_cut_time_level and 
                money >= self.cut_time_cost[self.cut_time_level])
    
    def can_upgrade_construction_time(self):
        return (self.construction_time_level < self.max_construction_time_level and 
                money >= self.construction_time_cost[self.construction_time_level])
    
    def upgrade_simultaneous(self):
        if self.can_upgrade_simultaneous():
            global money
            money -= self.simultaneous_cuts_cost[self.simultaneous_cuts_level]
            self.simultaneous_cuts_level += 1
            button_sound.play()  # Mudado de upgrade_sound para button_sound
            return True
        return False
    
    def upgrade_cut_time(self):
        if self.can_upgrade_cut_time():
            global money
            money -= self.cut_time_cost[self.cut_time_level]
            self.cut_time_level += 1
            button_sound.play()  # Mudado de upgrade_sound para button_sound
            return True
        return False
    
    def upgrade_construction_time(self):
        if self.can_upgrade_construction_time():
            global money
            money -= self.construction_time_cost[self.construction_time_level]
            self.construction_time_level += 1
            button_sound.play()  # Mudado de upgrade_sound para button_sound
            return True
        return False

    def max_all(self):
        """Cheat: leva todos os upgrades ao nível máximo."""
        for attr, value in self.__dict__.items():
            if attr.startswith("max_"):
                level_attr = attr[len("max_"):]
                if level_attr in self.__dict__:
                    self.__dict__[level_attr] = value

upgrades = UpgradeSystem()
bot_upgrades = UpgradeSystem()  # Bot tem seus próprios upgrades

class MissionSystem:
    def __init__(self):
        self.missions = [
            {"title": "Conclua 3 construcoes", "type": "build_total", "target": 3, "reward_money": 500},
            {"title": "Construa uma Lojinha", "type": "build_name", "key": "Lojinha", "target": 1, "reward_money": 800},
            {"title": "Junte 30 de madeira", "type": "wood", "target": 30, "reward_money": 600},
            {"title": "Junte 20 de pedra", "type": "stone", "target": 20, "reward_money": 700},
            {"title": "Construa 5 Casas", "type": "build_name", "key": "Casa", "target": 5, "reward_money": 1500},
            {"title": "Construa uma School", "type": "build_name", "key": "School", "target": 1, "reward_money": 2500},
            {"title": "Construa um Mall", "type": "build_name", "key": "Mall", "target": 1, "reward_money": 3000},
            {"title": "Junte 100 de pedra", "type": "stone", "target": 100, "reward_money": 4000},
            {"title": "Construa uma Factory", "type": "build_name", "key": "Factory", "target": 1, "reward_money": 5000},
            {"title": "Junte 200 de petroleo", "type": "oil", "target": 200, "reward_money": 10000},
            {"title": "Construa um Gerador de petroleo", "type": "build_name", "key": "Gerador de petróleo", "target": 1, "reward_money": 30000},
        ]
        self.started = False
        self.current_index = 0
        self.last_reward_message = ""
        self.last_reward_time = 0

    def reset(self):
        self.started = False
        self.current_index = 0
        self.last_reward_message = ""
        self.last_reward_time = 0

    def start(self):
        self.started = True

    def get_current_mission(self):
        if self.current_index >= len(self.missions):
            return None
        return self.missions[self.current_index]

    def get_progress(self, total_buildings_completed, completed_by_name, oil_amount, stone_amount, wood_amount=0):
        mission = self.get_current_mission()
        if mission is None:
            return 0, 0

        if mission["type"] == "build_total":
            value = total_buildings_completed
        elif mission["type"] == "build_name":
            value = completed_by_name.get(mission["key"], 0)
        elif mission["type"] == "oil":
            value = oil_amount
        elif mission["type"] == "stone":
            value = stone_amount
        elif mission["type"] == "wood":
            value = wood_amount
        else:
            value = 0

        return value, mission["target"]

    def update(self, total_buildings_completed, completed_by_name, oil_amount, stone_amount, wood_amount=0):
        global money

        if not self.started:
            return

        while True:
            mission = self.get_current_mission()
            if mission is None:
                break

            progress, target = self.get_progress(total_buildings_completed, completed_by_name, oil_amount, stone_amount, wood_amount)
            if progress < target:
                break

            money += mission["reward_money"]
            self.last_reward_message = f"Missao concluida: +${mission['reward_money']}"
            self.last_reward_time = pygame.time.get_ticks()
            self.current_index += 1

mission_system = MissionSystem()
total_buildings_completed = 0
buildings_completed_by_name = {}


# ===== BOT PLAYER =====
class BotPlayer:
    """Bot simulado com recursos que crescem passivamente ao longo do tempo."""
    def __init__(self, name="BOT-7"):
        self.name = name
        self.money  = random.randint(800, 1200)
        self.wood   = random.randint(0, 20)
        self.stone  = random.randint(0, 10)
        self.oil    = 0
        self.population = random.randint(0, 8)

        # taxas de ganho por segundo (crescem ligeiramente com o tempo)
        self._income      = random.uniform(0.8, 2.0)
        self._wood_rate   = random.uniform(0.3, 0.8)
        self._stone_rate  = random.uniform(0.1, 0.4)
        self._oil_rate    = 0.0
        self._pop_rate    = random.uniform(0.02, 0.06)

        self._last_tick   = pygame.time.get_ticks()
        self._phase_timer = 0   # ms acumulados para avançar de fase

    def tick(self, current_time):
        elapsed = (current_time - self._last_tick) / 1000.0
        self._last_tick = current_time
        self._phase_timer += current_time - (current_time - int(elapsed * 1000))

        # Aplica ganhos
        self.money     += self._income     * elapsed
        self.wood      += self._wood_rate  * elapsed
        self.stone     += self._stone_rate * elapsed
        self.oil       += self._oil_rate   * elapsed
        self.population = max(0, self.population + self._pop_rate * elapsed)

        # A cada 30 s o bot "cresce" um pouco
        self._phase_timer += int(elapsed * 1000)
        if self._phase_timer >= 30_000:
            self._phase_timer -= 30_000
            self._income    *= random.uniform(1.05, 1.15)
            self._wood_rate *= random.uniform(1.02, 1.08)
            self._stone_rate*= random.uniform(1.02, 1.08)
            if self.money > 50_000 and self._oil_rate == 0:
                self._oil_rate = random.uniform(0.05, 0.2)

    # inteiros para exibição
    def fmt_money(self):   return int(self.money)
    def fmt_wood(self):    return int(self.wood)
    def fmt_stone(self):   return int(self.stone)
    def fmt_oil(self):     return int(self.oil)
    def fmt_pop(self):     return int(self.population)


bot = BotPlayer()
show_bot_panel = False      # abre/fecha com botão
bot_panel_x = 10            # posição arrastável
bot_panel_y = 20
bot_panel_dragging = False
bot_panel_drag_offset = (0, 0)


class FlyingIcon:
    def __init__(self, start_x, start_y, end_x, end_y, image, duration=1000):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.image = image
        self.duration = duration  # duração em milissegundos
        self.start_time = pygame.time.get_ticks()
        
        # Calcula a distância total para usar na curva de movimento
        self.total_distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
    def update(self, current_time):
        # Calcula o progresso da animação (0 a 1)
        progress = (current_time - self.start_time) / self.duration
        progress = min(1.0, max(0.0, progress))
        
        # Usa uma curva de easing para movimento mais suave (quadrático)
        # progress = progress  # linear
        # progress = progress * progress  # acelerando
        progress = 1 - (1 - progress) * (1 - progress)  # desacelerando (mais natural)
        
        # Calcula posição atual com uma leve curva para efeito mais interessante
        current_x = self.start_x + (self.end_x - self.start_x) * progress
        current_y = self.start_y + (self.end_y - self.start_y) * progress
        
        # Adiciona um pequeno arco na trajetória (opcional)
        arc_height = 50 * math.sin(progress * math.pi)  # arco de 50 pixels
        current_y -= arc_height
        
        # Calcula a escala (começa grande e diminui)
        scale = 1.0 + 0.5 * (1 - progress)  # começa 1.5x, termina 1.0x
        
        return current_x, current_y, scale, progress
    
    def is_finished(self, current_time):
        return current_time - self.start_time >= self.duration

# Lista para armazenar ícones voadores
flying_icons = []

# ----- ÁRVORES (METADE DO JOGADOR: x 0-74) -----
trees = []
for _ in range(500):  # Reduzido porque agora está dividido com bot
    attempts = 0
    while attempts < 100:
        x = random.randint(0, 74)  # Apenas metade do jogador
        y = random.randint(0, GRID_SIZE-1)
        if not map_generator.is_water(x, y) and not map_generator.is_sand(x, y):
            trees.append({
                "pos": (x, y),
                "type": random.randint(0, 4)
            })
            break
        attempts += 1

# ----- ÁRVORES (METADE DO BOT: x 75-149) -----
for _ in range(500):  # Mesma quantidade para o bot
    attempts = 0
    while attempts < 100:
        x = random.randint(75, GRID_SIZE-1)  # Apenas metade do bot
        y = random.randint(0, GRID_SIZE-1)
        if not map_generator.is_water(x, y) and not map_generator.is_sand(x, y):
            trees.append({
                "pos": (x, y),
                "type": random.randint(0, 4)
            })
            break
        attempts += 1

# ----- SISTEMA DE COLETA -----
collecting_trees = []
collect_start_times = {}
cutting_sounds_playing = {}  # Dicionário para controlar sons de corte por árvore
COLLECT_COST = 10

# ----- ROCHAS (mineração de pedra) -----
MINE_TIME = 6000       # ms para minerar uma rocha
MINE_YIELD = 3         # pedras por rocha
rocks = []
occupied_by_trees = {tuple(t["pos"]) for t in trees}

# ROCHAS (METADE DO JOGADOR: x 0-74)
for _ in range(250):
    attempts = 0
    while attempts < 100:
        x = random.randint(0, 74)  # Apenas metade do jogador
        y = random.randint(0, GRID_SIZE - 1)
        if (not map_generator.is_water(x, y) and not map_generator.is_sand(x, y)
                and (x, y) not in occupied_by_trees):
            rocks.append({"pos": (x, y)})
            occupied_by_trees.add((x, y))
            break
        attempts += 1

# ROCHAS (METADE DO BOT: x 75-149)
for _ in range(250):
    attempts = 0
    while attempts < 100:
        x = random.randint(75, GRID_SIZE - 1)  # Apenas metade do bot
        y = random.randint(0, GRID_SIZE - 1)
        if (not map_generator.is_water(x, y) and not map_generator.is_sand(x, y)
                and (x, y) not in occupied_by_trees):
            rocks.append({"pos": (x, y)})
            occupied_by_trees.add((x, y))
            break
        attempts += 1
del occupied_by_trees

collecting_rocks = []
collect_rock_start_times = {}

# ===== SISTEMA DE RESPAWN DE RECURSOS =====
SPAWN_TIME = 30000  # A cada 30 segundos
SPAWN_RATE = 1      # Quantas árvores/rochas gerar por vez
last_spawn_check = 0  # Último timestamp onde verificamos spawn

# ===== SISTEMA DE ATAQUE DO BOT =====
ATTACKS_TO_DESTROY = 3  # Quantos ataques são necessários para destruir um prédio
bot_attacking = False   # Se o bot está no modo ataque
bot_attack_damage = {}  # Dicionário rastreando dano de cada prédio {(x, y): ataques}
bot_attack_cooldown = 0 # Cooldown entre ataques do bot (ms)
bot_last_attack = 0     # Último ataque realizado
BOT_ATTACK_INTERVAL = 2000  # Intervalo entre ataques do bot (2 segundos)
bot_attack_notified = False  # Se já notificou o jogador sobre o ataque do bot
bot_last_attacked_building = None  # Último prédio atacado para mostrar na tela
bot_attack_animation_time = 0  # Tempo da animação do ataque (para mostrar visual)
BOT_ATTACK_VISUAL_DURATION = 1000  # Duração visual do ataque (1 segundo)

# ===== SISTEMA DE MOVIMENTO DO BOT =====
bot_spawned = False  # Se o bot já apareceu no mapa
bot_position = None  # Posição atual do bot (x, y) em grid
bot_target = None  # Prédio alvo do bot (x, y) em grid
BOT_SPEED = 0.15  # Velocidade de movimento do bot (células por frame)
BOT_DETECTION_RANGE = 1.5  # Proximidade para começar a atacar (em células)
bot_buildings_destroyed = 0  # Contador de prédios destruídos

# ===== SISTEMA DE CONSTRUÇÃO =====
buildings_in_progress = []
building_start_times = {}

# ----- PRÉDIOS -----
buildings = {
    "Casa": {"cost_money": 20, "cost_wood": 10, "color": (0, 150, 0), "income": 1, "size": (1, 1), "population": 20, "build_time": 6000},
    "Predio": {"cost_money": 50, "cost_wood": 25, "color": (150, 0, 0), "income": 5, "size": (1, 1), "population": 200, "build_time": 10000},
    "Lojinha": {"cost_money": 270, "cost_wood": 50, "color": (0, 0, 120), "income": 27, "size": (1, 1), "population": 0, "build_time": 15000},
    "Shopping": {"cost_money": 3000, "cost_wood": 200, "cost_stone": 50, "color": (120, 0, 120), "income": 670, "size": (2, 3), "population": 0, "build_time": 20000},
    "Factory": {"cost_money": 9000, "cost_wood": 500, "cost_stone": 150, "color": (120, 40, 120), "income": 900, "size": (3, 3), "population": 0, "build_time": 50000},
    "School": {"cost_money": 1500, "cost_wood": 100, "cost_stone": 80, "color": (255, 165, 0), "income": 370, "size": (4, 3), "population": 0, "build_time": 15000},
    "Mall": {"cost_money": 900, "cost_wood": 90, "cost_stone": 30, "color": (128, 0, 128), "income": 34, "size": (3, 1), "population": 0, "build_time": 10000},
    "Gerador de petróleo": {"cost_money": 500000, "cost_wood": 50000, "cost_stone": 500, "color": (40, 60, 100), "income": 350000, "size": (5, 5), "population": 0, "build_time": 300, "oil_output": 3},
    "Mina": {"cost_money": 80000, "cost_wood": 2000, "color": (100, 100, 110), "income": 5000, "size": (2, 2), "population": 0, "build_time": 8000, "stone_output": 2},
}

grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
building_id_counter = 0

# ----- MODOS -----
current_mode = "none"
selected_building = None
preview_active = False

# ----- MENU PRINCIPAL (para botões) -----
building_names = list(buildings.keys())  # Lista ordenada de nomes
menu_buttons = {}
y_offset = 0
for name in building_names:
    btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 150 + y_offset, 300, 45)
    menu_buttons[name] = (name, btn_rect)
    y_offset += 50

# ===== ESTADO DO JOGO =====
game_state = "start_screen"  # start_screen | playing | paused | options
options_from = "start"        # "start" ou "game"
sfx_volume = 1.0
menu_scroll = ScrollBar(SCREEN_WIDTH//2 + 155, SCREEN_HEIGHT//2 - 95, 15, 100, len(buildings), 4)

# Botões tela inicial
_bw, _bh = 280, 65
start_play_btn    = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 - 30,  _bw, _bh, "Jogar",  COLORS['success'])
start_options_btn = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 55,  _bw, _bh, "Opções", COLORS['primary'])
start_quit_btn    = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 140, _bw, _bh, "Sair",   COLORS['danger'])

# Botões menu de pausa
pause_resume_btn  = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 - 120, _bw, _bh, "Continuar", COLORS['success'])
pause_newgame_btn = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 - 35,  _bw, _bh, "Novo Jogo", COLORS['primary'])
pause_save_btn    = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 50,  _bw, _bh, "Salvar",    COLORS['gold'])
pause_options_btn = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 135, _bw, _bh, "Opções",    COLORS['warning'])
pause_quit_btn    = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 220, _bw, _bh, "Sair",      COLORS['danger'])

# Botão para abrir/fechar painel do bot (canto inferior direito)
bot_btn = Button(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 55, 130, 40, "BOT-7", COLORS['danger'])

# ===== FUNÇÕES DE CÂMERA E ZOOM =====
def world_to_screen(world_x, world_y):
    screen_x = (world_x - camera_x) * zoom
    screen_y = (world_y - camera_y) * zoom
    return screen_x, screen_y

def screen_to_world(screen_x, screen_y):
    world_x = screen_x / zoom + camera_x
    world_y = screen_y / zoom + camera_y
    return world_x, world_y

def apply_zoom(new_zoom, mouse_x, mouse_y):
    global target_zoom, target_camera_x, target_camera_y, camera_x, camera_y, zoom
    
    world_x, world_y = screen_to_world(mouse_x, mouse_y)
    target_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))
    target_camera_x = world_x - mouse_x / target_zoom
    target_camera_y = world_y - mouse_y / target_zoom
    
    max_x = GRID_SIZE * BASE_CELL_SIZE - SCREEN_WIDTH / target_zoom
    max_y = GRID_SIZE * BASE_CELL_SIZE - SCREEN_HEIGHT / target_zoom
    target_camera_x = max(0, min(target_camera_x, max_x))
    target_camera_y = max(0, min(target_camera_y, max_y))

def update_camera_smooth():
    global camera_x, camera_y, zoom
    smooth_factor = 0.2
    camera_x += (target_camera_x - camera_x) * smooth_factor
    camera_y += (target_camera_y - camera_y) * smooth_factor
    zoom += (target_zoom - zoom) * smooth_factor

def get_cell_at_mouse(mouse_x, mouse_y):
    world_x, world_y = screen_to_world(mouse_x, mouse_y)
    gx = int(world_x // BASE_CELL_SIZE)
    gy = int(world_y // BASE_CELL_SIZE)
    return gx, gy

def get_building_counts(owner="player"):
    """Retorna contagem de prédios para um owner específico."""
    counted = set()
    counts = {}

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = grid[y][x]
            if cell is None:
                continue
            
            if cell.get("owner", "player") != owner:
                continue

            b_id = cell["id"]
            if b_id in counted:
                continue

            counted.add(b_id)
            b_name = cell["name"]
            counts[b_name] = counts.get(b_name, 0) + 1

    return counts

# ===== FUNÇÕES DO JOGO =====
def can_place_building(name, gx, gy, owner="player"):
    """Verifica se é possível construir, respeitando ilhas separadas."""
    width, height = buildings[name]["size"]
    
    # VALIDAÇÃO DE ILHAS
    if owner == "player":
        # Jogador constrói de x: 0-74
        if gx < 0 or gx + width > 75 or gy < 0 or gy + height > GRID_SIZE:
            return False
    elif owner == "bot":
        # Bot constrói de x: 75-149
        if gx < 75 or gx + width > GRID_SIZE or gy < 0 or gy + height > GRID_SIZE:
            return False

    # Verifica se o terreno é válido
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            if name == "Gerador de petróleo":
                # Gerador de petróleo SÓ pode ser construído na água
                if not map_generator.is_water(x, y):
                    return False
            else:
                # Outros prédios não podem ser construídos em água ou areia
                if map_generator.is_water(x, y) or map_generator.is_sand(x, y):
                    return False

    # Verifica se alguma célula já está ocupada por uma construção completa
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            if grid[y][x] is not None:
                return False
    
    # Verifica se alguma célula já está ocupada por uma construção em andamento
    for construction in buildings_in_progress:
        if construction.get("owner", "player") != owner:  # Só verifica construções do mesmo owner
            continue
        for cell_x, cell_y in construction["cells"]:
            # Verifica se a célula está dentro da área da nova construção
            if (gx <= cell_x < gx + width) and (gy <= cell_y < gy + height):
                return False
    
    # Verifica se há árvores no local
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            for tree in trees:
                if tree["pos"] == (x, y):
                    return False

    # Verifica se há rochas no local
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            for rock in rocks:
                if rock["pos"] == (x, y):
                    return False

    return True

def start_construction(name, gx, gy, owner="player"):
    """Inicia construção para player ou bot."""
    global money, wood, stone, bot_money, bot_wood, bot_stone, buildings_in_progress, bot_upgrades
    width, height = buildings[name]["size"]
    
    if owner == "player":
        money -= buildings[name]["cost_money"]
        wood -= buildings[name]["cost_wood"]
        stone -= buildings[name].get("cost_stone", 0)
    else:  # bot
        bot_money -= buildings[name]["cost_money"]
        bot_wood -= buildings[name]["cost_wood"]
        bot_stone -= buildings[name].get("cost_stone", 0)
    
    base_time = buildings[name]["build_time"]
    if owner == "player":
        multiplier = upgrades.get_construction_time_multiplier()
    else:  # bot
        multiplier = bot_upgrades.get_construction_time_multiplier()
    build_time = int(base_time * multiplier)
    
    construction = {
        "name": name,
        "pos": (gx, gy),
        "width": width,
        "height": height,
        "build_time": build_time,
        "cells": [],
        "owner": owner
    }
    
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            construction["cells"].append((x, y))
    
    buildings_in_progress.append(construction)
    building_start_times[(gx, gy)] = pygame.time.get_ticks()
    
    # Remove árvores e rochas da área de construção
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            trees[:] = [t for t in trees if t["pos"] != (x, y)]
            rocks[:] = [r for r in rocks if r["pos"] != (x, y)]

    if owner == "player" and not mission_system.started:
        mission_system.start()

    build_sound.play()

def complete_construction(construction):
    global building_id_counter, total_buildings_completed, bot_building_id_counter, bot_total_buildings_completed
    
    owner = construction.get("owner", "player")
    
    if owner == "player":
        building_id_counter += 1
        building_id = building_id_counter
    else:  # bot
        bot_building_id_counter += 1
        building_id = bot_building_id_counter
    
    name = construction["name"]
    gx, gy = construction["pos"]
    width, height = construction["width"], construction["height"]
    
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            grid[y][x] = {"name": name, "id": building_id, "owner": owner}
    
    # Remove árvores e rochas remanescentes (garantia)
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            trees[:] = [t for t in trees if t["pos"] != (x, y)]
            rocks[:] = [r for r in rocks if r["pos"] != (x, y)]
    
    if owner == "player":
        population_system.calculate_population(grid, owner="player")
        total_buildings_completed += 1
        buildings_completed_by_name[name] = buildings_completed_by_name.get(name, 0) + 1
        mission_system.update(total_buildings_completed, buildings_completed_by_name, oil, stone, wood)
    else:
        bot_population_system.calculate_population(grid, owner="bot")
        bot_total_buildings_completed += 1
        bot_buildings_completed_by_name[name] = bot_buildings_completed_by_name.get(name, 0) + 1

    buildings_in_progress.remove(construction)
    del building_start_times[(gx, gy)]
    
    build_finish_sound.play()

def demolish_building(gx, gy):
    if grid[gy][gx] is None:
        return
    building_id = grid[gy][gx]["id"]
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] and grid[y][x]["id"] == building_id:
                grid[y][x] = None
    
    population_system.calculate_population(grid, owner="player")
    bot_population_system.calculate_population(grid, owner="bot")
    break_sound.play()

# ===== SISTEMA DE IA DO BOT (COMPETIÇÃO) =====
bot_last_action_time = 0
BOT_ACTION_INTERVAL = 2000  # Bot toma ações a cada 2 segundos

def bot_can_afford_building(building_name):
    """Verifica se o bot pode construir algo com seus recursos."""
    cost = buildings[building_name]["cost_money"]
    cost_wood = buildings[building_name]["cost_wood"]
    cost_stone = buildings[building_name].get("cost_stone", 0)
    
    return bot_money >= cost and bot_wood >= cost_wood and bot_stone >= cost_stone

def bot_find_build_location(building_name):
    """Encontra uma posição válida para o bot construir (na sua metade)."""
    global trees, rocks
    width, height = buildings[building_name]["size"]
    
    # Tenta posições aleatórias na metade do bot (x: 75-149)
    attempts = 0
    while attempts < 50:  # Aumentado de 20 para 50 tentativas
        gx = random.randint(75, min(145, GRID_SIZE - width))
        gy = random.randint(0, GRID_SIZE - height)
        
        # Verifica se PODE colocar (ignora árvores/rochas temporariamente)
        if can_place_building(building_name, gx, gy, owner="bot"):
            return gx, gy
        
        # Se não conseguiu, tenta limpar árvores/rochas da área e tenta novamente
        for y in range(gy, min(gy+height, GRID_SIZE)):
            for x in range(gx, min(gx+width, GRID_SIZE)):
                # Remove árvores na área
                trees[:] = [t for t in trees if t["pos"] != (x, y)]
                rocks[:] = [r for r in rocks if r["pos"] != (x, y)]
        
        # Depois de limpar, verifica novamente
        if can_place_building(building_name, gx, gy, owner="bot"):
            return gx, gy
        
        attempts += 1
    
    return None

def bot_decide_what_to_build():
    """IA: Decide o que o bot deve construir."""
    # Prioridade: Casa (população) → Predio (população) → Lojinha (renda) → Outros
    priority_buildings = ["Casa", "Predio", "Lojinha", "Shopping", "Mall", "School", "Factory", "Mina"]
    
    for building_name in priority_buildings:
        if bot_can_afford_building(building_name):
            location = bot_find_build_location(building_name)
            if location:
                return building_name, location
    
    return None, None

def bot_collect_resources(current_time):
    """Bot coleta árvores e rochas automaticamente com limites de upgrade."""
    global bot_wood, bot_stone, bot_collecting_trees, bot_collecting_rocks, bot_collect_start_times
    
    trees_collected = 0
    rocks_collected = 0
    
    # Completa coletas de árvores (usando posições, não índices)
    completed_trees = []
    for tree_pos in bot_collecting_trees[:]:
        # Procura a árvore por posição
        tree_found = None
        for tree in trees:
            if tuple(tree["pos"]) == tree_pos:
                tree_found = tree
                break
        
        if tree_found and tree_pos in bot_collect_start_times:
            elapsed = current_time - bot_collect_start_times[tree_pos]
            cut_time = bot_upgrades.get_current_cut_time()
            if elapsed >= cut_time:
                trees.remove(tree_found)
                bot_wood += 5
                trees_collected += 1
                completed_trees.append(tree_pos)
                del bot_collect_start_times[tree_pos]
        elif not tree_found:
            # Árvore foi destruída/removida
            if tree_pos in bot_collecting_trees:
                bot_collecting_trees.remove(tree_pos)
            if tree_pos in bot_collect_start_times:
                del bot_collect_start_times[tree_pos]
    
    # Remove árvores completadas
    for tree_pos in completed_trees:
        if tree_pos in bot_collecting_trees:
            bot_collecting_trees.remove(tree_pos)
    
    # Completa coletas de rochas (usando posições, não índices)
    completed_rocks = []
    for rock_pos in bot_collecting_rocks[:]:
        # Procura a rocha por posição
        rock_found = None
        for rock in rocks:
            if tuple(rock["pos"]) == rock_pos:
                rock_found = rock
                break
        
        if rock_found and rock_pos in bot_collect_start_times:
            elapsed = current_time - bot_collect_start_times[rock_pos]
            cut_time = bot_upgrades.get_current_cut_time()
            if elapsed >= cut_time:
                rocks.remove(rock_found)
                bot_stone += 3
                rocks_collected += 1
                completed_rocks.append(rock_pos)
                del bot_collect_start_times[rock_pos]
        elif not rock_found:
            # Rocha foi destruída/removida
            if rock_pos in bot_collecting_rocks:
                bot_collecting_rocks.remove(rock_pos)
            if rock_pos in bot_collect_start_times:
                del bot_collect_start_times[rock_pos]
    
    # Remove rochas completadas
    for rock_pos in completed_rocks:
        if rock_pos in bot_collecting_rocks:
            bot_collecting_rocks.remove(rock_pos)
    
    if trees_collected > 0 or rocks_collected > 0:
        print(f"[BOT] Coletou: {trees_collected} árvores (+{trees_collected*5} wood), {rocks_collected} rochas (+{rocks_collected*3} stone)")
    
    # Inicia novas coletas de árvores (respeitando limite simultâneo)
    if len(bot_collecting_trees) < bot_upgrades.simultaneous_cuts_level:
        for tree in trees:
            tree_pos_tuple = tuple(tree["pos"])
            if (75 <= tree["pos"][0] < GRID_SIZE and 
                len(bot_collecting_trees) < bot_upgrades.simultaneous_cuts_level and
                tree_pos_tuple not in bot_collecting_trees):
                bot_collecting_trees.append(tree_pos_tuple)
                bot_collect_start_times[tree_pos_tuple] = current_time
                if len(bot_collecting_trees) >= bot_upgrades.simultaneous_cuts_level:
                    break
    
    # Inicia novas coletas de rochas (respeitando limite simultâneo)
    if len(bot_collecting_rocks) < bot_upgrades.simultaneous_cuts_level:
        for rock in rocks:
            rock_pos_tuple = tuple(rock["pos"])
            if (75 <= rock["pos"][0] < GRID_SIZE and 
                len(bot_collecting_rocks) < bot_upgrades.simultaneous_cuts_level and
                rock_pos_tuple not in bot_collecting_rocks):
                bot_collecting_rocks.append(rock_pos_tuple)
                bot_collect_start_times[rock_pos_tuple] = current_time
                if len(bot_collecting_rocks) >= bot_upgrades.simultaneous_cuts_level:
                    break
    
    if len(bot_collecting_trees) > 0 or len(bot_collecting_rocks) > 0:
        print(f"[BOT] Coletando: {len(bot_collecting_trees)} árvores, {len(bot_collecting_rocks)} rochas")

def bot_tick(current_time):
    """Função principal do bot - executada a cada intervalo."""
    global bot_last_action_time, bot_money, bot_oil, bot_wood, bot_stone
    
    if current_time - bot_last_action_time < BOT_ACTION_INTERVAL:
        return
    
    bot_last_action_time = current_time
    
    # Bot coleta renda passiva de seus prédios
    building_counts = {}
    for y in range(75, GRID_SIZE):  # Apenas ilha do bot
        for x in range(75, GRID_SIZE):
            if grid[y][x] is not None and grid[y][x].get("owner") == "bot":
                name = grid[y][x]["name"]
                if name not in building_counts:
                    building_counts[name] = 0
                building_counts[name] += 1
    
    # Aplica renda
    for name, count in building_counts.items():
        bot_money += buildings[name]["income"] * count * (current_time - bot_last_action_time) / 1000
    
    # Coleta óleo
    bot_oil += building_counts.get("Gerador de petróleo", 0) * 3 * (current_time - bot_last_action_time) / 1000
    
    # Bot tenta construir algo
    building_to_build, location = bot_decide_what_to_build()
    if building_to_build and location:
        gx, gy = location
        # DEBUG: Mostrar intenção de construção
        print(f"[BOT] Construindo {building_to_build} em ({gx}, {gy})")
        print(f"[BOT] Recursos ANTES: money={bot_money:.0f}, wood={bot_wood:.0f}, stone={bot_stone:.0f}")
        start_construction(building_to_build, gx, gy, owner="bot")
        print(f"[BOT] Recursos DEPOIS: money={bot_money:.0f}, wood={bot_wood:.0f}, stone={bot_stone:.0f}")
    else:
        print(f"[BOT] Não pode construir. Recursos: money={bot_money:.0f}, wood={bot_wood:.0f}, stone={bot_stone:.0f}")

def bot_attack_building(current_time):
    """Bot ataca um prédio do jogador aleatoriamente."""
    global bot_attacking, bot_attack_damage, bot_last_attack, bot_attack_notified, bot_last_attacked_building, bot_attack_animation_time
    
    # Coleta todos os prédios do jogador
    player_buildings = []
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] is not None:
                player_buildings.append((x, y))
    
    # Se não há prédios, o bot não pode atacar
    if not player_buildings:
        return
    
    # Escolhe um prédio aleatório para atacar
    target = random.choice(player_buildings)
    bot_last_attacked_building = target  # Rastreia qual prédio foi atacado
    bot_attack_animation_time = current_time  # Marca o tempo para animação visual
    
    # Se não estava atacando este prédio, reseta o dano
    if target not in bot_attack_damage:
        bot_attack_damage[target] = 0
    
    # Incrementa o dano
    bot_attack_damage[target] += 1
    
    building_name = grid[target[1]][target[0]]["name"] if grid[target[1]][target[0]] else "?"
    print(f"🤖 BOT-7 atacando {building_name} em ({target[0]}, {target[1]}) - {bot_attack_damage[target]}/{ATTACKS_TO_DESTROY}")
    
    # Se atingiu o limite de ataques, destrói o prédio
    if bot_attack_damage[target] >= ATTACKS_TO_DESTROY:
        demolish_building(target[0], target[1])
        del bot_attack_damage[target]
        print(f"💥 {building_name} foi DESTRUÍDO pelo BOT-7!")
        break_sound.play()
    else:
        # Som de dano (usando break_sound como feedback)
        break_sound.play()
    
    bot_last_attack = pygame.time.get_ticks()

def bot_spawn():
    """Faz o bot aparecer em um canto aleatório do mapa."""
    global bot_spawned, bot_position
    
    corners = [
        (0, 0),                           # Canto superior esquerdo
        (GRID_SIZE - 1, 0),              # Canto superior direito
        (0, GRID_SIZE - 1),              # Canto inferior esquerdo
        (GRID_SIZE - 1, GRID_SIZE - 1)   # Canto inferior direito
    ]
    
    bot_position = random.choice(corners)
    bot_spawned = True
    print(f"🤖 BOT-7 apareceu no canto ({bot_position[0]}, {bot_position[1]})!")

def bot_move_to_target():
    """Move o bot em direção ao alvo mais próximo."""
    global bot_position, bot_target
    
    if bot_position is None or bot_target is None:
        return
    
    # Calcula distância até o alvo
    dx = bot_target[0] - bot_position[0]
    dy = bot_target[1] - bot_position[1]
    distance = math.sqrt(dx*dx + dy*dy)
    
    # Se chegou perto do alvo, não move mais
    if distance < BOT_DETECTION_RANGE:
        return
    
    # Normaliza direção e move
    if distance > 0:
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        new_x = bot_position[0] + dx_norm * BOT_SPEED
        new_y = bot_position[1] + dy_norm * BOT_SPEED
        
        # Clamp para dentro do mapa
        new_x = max(0, min(GRID_SIZE - 1, new_x))
        new_y = max(0, min(GRID_SIZE - 1, new_y))
        
        bot_position = (new_x, new_y)

# ===== FUNÇÕES DE DESENHO =====
def draw_grid():
    cell_size_scaled = BASE_CELL_SIZE * zoom
    start_x, start_y, end_x, end_y = get_visible_range()
    
    # 1. PRIMEIRO: Desenha o fundo (água com degradê, areia, grama)
    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            screen_x, screen_y = world_to_screen(x * BASE_CELL_SIZE, y * BASE_CELL_SIZE)
            
            # Arredonda as coordenadas para evitar gaps
            screen_x = round(screen_x)
            screen_y = round(screen_y)
            cell_width = round(cell_size_scaled) + 1  # +1 para eliminar gaps
            cell_height = round(cell_size_scaled) + 1  # +1 para eliminar gaps
            
            rect = pygame.Rect(screen_x, screen_y, cell_width, cell_height)
            
            if map_generator.is_water(x, y):
                # Calcula distância do centro para efeito degradê
                dx = x - CENTER_X
                dy = y - CENTER_Y
                distance = math.sqrt(dx*dx + dy*dy)
                water_color = get_water_color(distance, MAP_RADIUS)
                pygame.draw.rect(screen, water_color, rect)
            elif map_generator.is_sand(x, y):
                pygame.draw.rect(screen, SAND_COLOR, rect)
            else:
                is_construction = False
                for construction in buildings_in_progress:
                    if (x, y) in construction["cells"]:
                        is_construction = True
                        break

                if not is_construction:
                    pygame.draw.rect(screen, GRASS_COLOR, rect)
    
    # 2. SEGUNDO: Desenha construções em andamento (apenas fundo amarelo)
    for construction in buildings_in_progress:
        gx, gy = construction["pos"]
        if gx < start_x or gx >= end_x or gy < start_y or gy >= end_y:
            continue
        
        for cell_x, cell_y in construction["cells"]:
            if cell_x < start_x or cell_x >= end_x or cell_y < start_y or cell_y >= end_y:
                continue
            cell_screen_x, cell_screen_y = world_to_screen(cell_x * BASE_CELL_SIZE, cell_y * BASE_CELL_SIZE)
            cell_screen_x = round(cell_screen_x)
            cell_screen_y = round(cell_screen_y)
            cell_width = round(cell_size_scaled) + 1
            cell_height = round(cell_size_scaled) + 1
            
            cell_rect = pygame.Rect(cell_screen_x, cell_screen_y, cell_width, cell_height)
            s = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            s.fill((241, 196, 15, 100))
            screen.blit(s, cell_rect)
    
    # 3. TERCEIRO: Desenha as árvores e rochas
    draw_trees()
    draw_rocks()
    
    # 3.5: Desenha o bot
    if bot_spawned:
        draw_bot()
    
    # 4. QUARTO: Desenha as LINHAS DO GRID - AGORA ANTES DOS PRÉDIOS
    line_width = max(1, int(zoom * 0.8))  # linhas um pouco mais finas também ajudam
    line_color = (70, 70, 70)  # Cinza escuro suave
    
    # Desenha linhas verticais
    for x in range(start_x, end_x + 1):
        screen_x, _ = world_to_screen(x * BASE_CELL_SIZE, 0)
        screen_x = int(round(screen_x))
        
        if 0 <= screen_x < SCREEN_WIDTH:
            pygame.draw.line(screen, line_color, 
                           (screen_x, 0), 
                           (screen_x, SCREEN_HEIGHT), 
                           line_width)
    
    # Desenha linhas horizontais
    for y in range(start_y, end_y + 1):
        _, screen_y = world_to_screen(0, y * BASE_CELL_SIZE)
        screen_y = int(round(screen_y))
        
        if 0 <= screen_y < SCREEN_HEIGHT:
            pygame.draw.line(screen, line_color, 
                           (0, screen_y), 
                           (SCREEN_WIDTH, screen_y), 
                           line_width)
    
    # 5. QUINTO: Desenha construções completas (AGORA POR CIMA DO GRID)
    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            if grid[y][x] is not None:
                building_data = grid[y][x]
                building_name = building_data["name"]

                is_origin = True
                if x > 0 and grid[y][x-1] and grid[y][x-1]["id"] == building_data["id"]:
                    is_origin = False
                if y > 0 and grid[y-1][x] and grid[y-1][x]["id"] == building_data["id"]:
                    is_origin = False

                if is_origin:
                    width, height = buildings[building_name]["size"]
                    img_screen_x, img_screen_y = world_to_screen(x * BASE_CELL_SIZE, y * BASE_CELL_SIZE)
                    img_screen_x = round(img_screen_x)
                    img_screen_y = round(img_screen_y)
                    img_width = round(width * BASE_CELL_SIZE * zoom) + 1
                    img_height = round(height * BASE_CELL_SIZE * zoom) + 1
                    
                    img = pygame.transform.scale(
                        building_images_original[building_name],
                        (img_width, img_height)
                    )
                    screen.blit(img, (img_screen_x, img_screen_y))
    
    # 6. SEXTO: Desenha as barras de progresso (por cima dos prédios)
    current_time = pygame.time.get_ticks()
    for construction in buildings_in_progress:
        gx, gy = construction["pos"]
        if gx < start_x or gx >= end_x or gy < start_y or gy >= end_y:
            continue
            
        start_time = building_start_times[(gx, gy)]
        progress = (current_time - start_time) / construction["build_time"]
        progress = min(1.0, max(0.0, progress))
        
        screen_x, screen_y = world_to_screen(gx * BASE_CELL_SIZE, gy * BASE_CELL_SIZE)
        screen_x = round(screen_x)
        screen_y = round(screen_y)
        
        bar_width_total = cell_size_scaled * construction["width"]
        bar_height = 8
        bar_y = screen_y - 15
        
        bar_bg_rect = pygame.Rect(screen_x, bar_y, bar_width_total, bar_height)
        pygame.draw.rect(screen, (60, 60, 60), bar_bg_rect, border_radius=4)
        
        bar_fg_width = bar_width_total * progress
        if bar_fg_width > 0:
            bar_surf = pygame.Surface((bar_fg_width, bar_height), pygame.SRCALPHA)
            for i in range(int(bar_fg_width)):
                t = i / bar_fg_width
                r = int(255 - t * 50)
                g = int(215 - t * 30)
                b = int(0 + t * 20)
                alpha = 255
                pygame.draw.line(bar_surf, (r, g, b, alpha), (i, 0), (i, bar_height))
            screen.blit(bar_surf, (screen_x, bar_y))
        
        border_rect = pygame.Rect(screen_x, bar_y, bar_width_total, bar_height)
        pygame.draw.rect(screen, (255, 255, 200, 100), border_rect, width=1, border_radius=4)
        
        if progress > 0.1:
            glow_width = max(2, int(bar_fg_width * 0.3))
            glow_x = screen_x + bar_fg_width - glow_width
            glow_rect = pygame.Rect(glow_x, bar_y, glow_width, bar_height)
            glow_surf = pygame.Surface((glow_width, bar_height), pygame.SRCALPHA)
            for i in range(glow_width):
                alpha = int(100 * (1 - i / glow_width))
                pygame.draw.line(glow_surf, (255, 255, 255, alpha), (i, 0), (i, bar_height))
            screen.blit(glow_surf, (glow_x, bar_y))
        
        if bar_fg_width > 30:
            percent_text = font_small.render(f"{int(progress * 100)}%", True, (255, 255, 255))
            text_rect = percent_text.get_rect(center=(screen_x + bar_fg_width/2, bar_y - 10))
            text_bg_rect = text_rect.inflate(10, 4)
            pygame.draw.rect(screen, (0, 0, 0, 150), text_bg_rect, border_radius=3)
            screen.blit(percent_text, text_rect)
            
# Adicione esta função nova na seção de funções de desenho
def draw_popup(screen, message, duration=2000, popup_type="warning"):
    """Desenha um popup no centro da tela por um determinado tempo
    popup_type: 'warning' (amarelo), 'success' (verde), 'error' (vermelho)
    """
    popup_start_time = pygame.time.get_ticks()
    showing_popup = True
    
    # Define cores baseado no tipo
    color_map = {
        'warning': COLORS['gold'],
        'success': COLORS['success'],
        'error': COLORS['danger']
    }
    border_color = color_map.get(popup_type, COLORS['gold'])
    icon_map = {
        'warning': "⚠️",
        'success': "✅",
        'error': "❌"
    }
    icon = icon_map.get(popup_type, "⚠️")
    
    # Cria uma superfície para o popup
    popup_width = 400
    popup_height = 100
    popup_surf = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    
    # Desenha o fundo do popup
    pygame.draw.rect(popup_surf, (44, 62, 80, 230), 
                    (0, 0, popup_width, popup_height), border_radius=15)
    pygame.draw.rect(popup_surf, border_color, 
                    (0, 0, popup_width, popup_height), width=3, border_radius=15)
    
    # Desenha o texto
    text = font_medium.render(message, True, (255, 255, 255))
    text_rect = text.get_rect(center=(popup_width//2, popup_height//2))
    popup_surf.blit(text, text_rect)
    
    # Desenha um ícone
    warning_icon = font_large.render(icon, True, border_color)
    icon_rect = warning_icon.get_rect(center=(popup_width//2, popup_height//2 - 20))
    popup_surf.blit(warning_icon, icon_rect)
    
    # Posiciona o popup no centro da tela
    popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    
    # Desenha o popup na tela
    screen.blit(popup_surf, popup_rect)
    
    return popup_start_time + duration > pygame.time.get_ticks()

def draw_trees():
    cell_size_scaled = BASE_CELL_SIZE * zoom
    current_time = pygame.time.get_ticks()
    start_x, start_y, end_x, end_y = get_visible_range()
    
    for tree in trees:
        tx, ty = tree["pos"]
        if tx < start_x or tx >= end_x or ty < start_y or ty >= end_y:
            continue
        if map_generator.is_sand(tx, ty):
            continue
            
        tree_type = tree["type"]
        screen_x, screen_y = world_to_screen(tx * BASE_CELL_SIZE, ty * BASE_CELL_SIZE)
        
        # Arredonda as coordenadas para evitar blur
        screen_x = round(screen_x)
        screen_y = round(screen_y)
        cell_width = round(cell_size_scaled)
        cell_height = round(cell_size_scaled)
        
        rect = pygame.Rect(screen_x, screen_y, cell_width, cell_height)
        
        tree_img = pygame.transform.scale(
            tree_images_original[tree_type],
            (cell_width, cell_height)
        )
        
        is_collecting = False
        progress = 0
        for collecting_tree in collecting_trees:
            if collecting_tree["pos"] == (tx, ty):
                is_collecting = True
                start_time = collect_start_times[(tx, ty)]
                progress = (current_time - start_time) / upgrades.get_current_cut_time()
                progress = min(1.0, max(0.0, progress))
                break
        
        if is_collecting:
            # Primeiro desenha a árvore com um overlay escuro
            dark_overlay = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 100))
            screen.blit(tree_img, rect.topleft)
            screen.blit(dark_overlay, rect.topleft)
            
            # Desenha a barra de progresso NO TOPO da árvore (mais visível)
            bar_width = cell_width
            bar_height = max(4, round(cell_height * 0.1))  # 10% da altura da célula
            bar_y = screen_y + 5  # Pequeno espaçamento do topo
            
            # Fundo da barra
            bar_bg_rect = pygame.Rect(screen_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, (40, 40, 40), bar_bg_rect, border_radius=bar_height//2)
            
            # Barra de progresso com gradiente
            bar_fg_width = round(bar_width * progress)
            if bar_fg_width > 0:
                # Cria gradiente do amarelo ao verde
                bar_surf = pygame.Surface((bar_fg_width, bar_height))
                for i in range(bar_fg_width):
                    t = i / bar_fg_width
                    # Transição de amarelo para verde
                    r = int(255 - t * 155)  # 255 → 100
                    g = int(215 + t * 40)   # 215 → 255
                    b = int(0)
                    pygame.draw.line(bar_surf, (r, g, b), (i, 0), (i, bar_height))
                
                bar_fg_rect = pygame.Rect(screen_x, bar_y, bar_fg_width, bar_height)
                screen.blit(bar_surf, bar_fg_rect)
            
            # Borda branca sutil
            pygame.draw.rect(screen, (255, 255, 255, 100), 
                           (screen_x, bar_y, bar_width, bar_height), 
                           width=1, border_radius=bar_height//2)
            
            # Texto de porcentagem (opcional, só aparece se a barra for grande o suficiente)
            if bar_width > 40 and progress > 0.05:
                percent_text = font_small.render(f"{int(progress * 100)}%", True, (255, 255, 255))
                text_rect = percent_text.get_rect(center=(screen_x + bar_width//2, bar_y + bar_height//2))
                # Sombra do texto
                shadow_rect = text_rect.copy()
                shadow_rect.x += 1
                shadow_rect.y += 1
                shadow_text = font_small.render(f"{int(progress * 100)}%", True, (0, 0, 0, 128))
                screen.blit(shadow_text, shadow_rect)
                screen.blit(percent_text, text_rect)
        else:
            screen.blit(tree_img, rect.topleft)

def draw_preview():
    if not preview_active or not selected_building:
        return
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    gx, gy = get_cell_at_mouse(mouse_x, mouse_y)
    
    width, height = buildings[selected_building]["size"]
    valid = can_place_building(selected_building, gx, gy)
    
    cost_money = buildings[selected_building]["cost_money"]
    cost_wood = buildings[selected_building]["cost_wood"]
    cost_stone = buildings[selected_building].get("cost_stone", 0)
    
    if valid and money >= cost_money and wood >= cost_wood and stone >= cost_stone:
        color = (0,255,0,120)
    else:
        color = (255,0,0,120)

    screen_x, screen_y = world_to_screen(gx * BASE_CELL_SIZE, gy * BASE_CELL_SIZE)
    preview_width = width * BASE_CELL_SIZE * zoom
    preview_height = height * BASE_CELL_SIZE * zoom
    
    s = pygame.Surface((preview_width, preview_height), pygame.SRCALPHA)
    s.fill(color)
    screen.blit(s, (screen_x, screen_y))

def draw_rocks():
    cell_size_scaled = BASE_CELL_SIZE * zoom
    current_time = pygame.time.get_ticks()
    start_x, start_y, end_x, end_y = get_visible_range()

    for rock in rocks:
        rx, ry = rock["pos"]
        if rx < start_x or rx >= end_x or ry < start_y or ry >= end_y:
            continue

        screen_rx, screen_ry = world_to_screen(rx * BASE_CELL_SIZE, ry * BASE_CELL_SIZE)
        screen_rx = round(screen_rx)
        screen_ry = round(screen_ry)
        cw = round(cell_size_scaled)
        ch = round(cell_size_scaled)

        # Desenha rocha
        if rock_img is not None:
            scaled_rock = pygame.transform.scale(rock_img, (cw, ch))
            screen.blit(scaled_rock, (screen_rx, screen_ry))
        else:
            cx = screen_rx + cw // 2
            cy = screen_ry + ch // 2
            r = max(4, round(cw * 0.28))
            pygame.draw.circle(screen, (120, 120, 130), (cx, cy), r)
            pygame.draw.circle(screen, (80, 80, 90), (cx, cy), r, max(1, r // 5))
            r2 = max(2, round(r * 0.55))
            pygame.draw.circle(screen, (140, 140, 150), (cx + round(r * 0.7), cy + round(r * 0.4)), r2)
            pygame.draw.circle(screen, (80, 80, 90), (cx + round(r * 0.7), cy + round(r * 0.4)), r2, max(1, r2 // 4))

        # Barra de progresso se estiver sendo minerada
        for cr in collecting_rocks:
            if cr["pos"] == (rx, ry):
                start_time = collect_rock_start_times[(rx, ry)]
                progress = min(1.0, (current_time - start_time) / MINE_TIME)

                dark_overlay = pygame.Surface((cw, ch), pygame.SRCALPHA)
                dark_overlay.fill((0, 0, 0, 80))
                screen.blit(dark_overlay, (screen_rx, screen_ry))

                bar_width = cw
                bar_height = max(4, round(ch * 0.1))
                bar_y = screen_ry + 5

                pygame.draw.rect(screen, (40, 40, 40),
                                 pygame.Rect(screen_rx, bar_y, bar_width, bar_height),
                                 border_radius=bar_height // 2)
                bar_fg_width = round(bar_width * progress)
                if bar_fg_width > 0:
                    bar_surf = pygame.Surface((bar_fg_width, bar_height))
                    for i in range(bar_fg_width):
                        t = i / bar_fg_width
                        rr = int(180 + t * 20)
                        gg = int(180 + t * 20)
                        bb = int(190 + t * 20)
                        pygame.draw.line(bar_surf, (rr, gg, bb), (i, 0), (i, bar_height))
                    screen.blit(bar_surf, (screen_rx, bar_y))
                break


def draw_bot():
    """Desenha o bot no mapa circulando pela ilha dele e adiciona sinalizador."""
    global bot_spawned
    if not bot_spawned:
        return
    
    # Se bot_position for None, cria uma posição padrão (centro da ilha do bot)
    bot_display_pos = bot_position if bot_position is not None else (112, 75)  # Centro da ilha do bot
    
    # Converte posição do bot para coordenadas de tela
    screen_x, screen_y = world_to_screen(bot_display_pos[0] * BASE_CELL_SIZE + BASE_CELL_SIZE/2,
                                         bot_display_pos[1] * BASE_CELL_SIZE + BASE_CELL_SIZE/2)
    
    # Verifica se está dentro da tela
    if screen_x < -200 or screen_x > SCREEN_WIDTH + 200 or screen_y < -200 or screen_y > SCREEN_HEIGHT + 200:
        return  # Fora da tela, não renderiza
    
    # Desenha círculos de sinalizador
    pygame.draw.circle(screen, (255, 100, 100), (int(screen_x), int(screen_y)), max(5, int(50 * zoom)), 3)
    pulse = int(10 * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
    pygame.draw.circle(screen, (255, 150, 150), (int(screen_x), int(screen_y)), max(5, int(55 * zoom + pulse)), 1)
    
    # Desenha a imagem do bot
    bot_size = max(10, int(80 * zoom))
    try:
        scaled_bot = pygame.transform.scale(bot_image, (bot_size, bot_size))
        screen.blit(scaled_bot, (int(screen_x - bot_size/2), int(screen_y - bot_size/2)))
    except:
        # Fallback: desenha círculo vermelho
        pygame.draw.circle(screen, (255, 50, 50), (int(screen_x), int(screen_y)), int(bot_size/2))
    
    # Desenha linha do bot até o alvo se houver um
    if bot_target is not None:
        target_screen_x, target_screen_y = world_to_screen(bot_target[0] * BASE_CELL_SIZE + BASE_CELL_SIZE/2,
                                                           bot_target[1] * BASE_CELL_SIZE + BASE_CELL_SIZE/2)
        pygame.draw.line(screen, (255, 50, 50), (int(screen_x), int(screen_y)), 
                        (int(target_screen_x), int(target_screen_y)), 2)


def draw_ui():
    menu_btn.draw(screen)
    hammer_btn.draw(screen)
    collect_btn.draw(screen)
    pickaxe_btn.draw(screen)
    upgrade_btn.draw(screen)
    
    resources_panel.draw(screen)
    
    icon_y = resources_panel.rect.y + 15
    
    screen.blit(money_icon, (resources_panel.rect.x + 15, icon_y))
    money_text = font_large.render(f"${money}", True, (255,255,255))
    screen.blit(money_text, (resources_panel.rect.x + 60, icon_y + 5))
    
    screen.blit(wood_icon, (resources_panel.rect.x + 15, icon_y + 45))
    wood_text = font_large.render(f"{wood}", True, (255,255,255))
    screen.blit(wood_text, (resources_panel.rect.x + 60, icon_y + 50))
    
    screen.blit(population_icon, (resources_panel.rect.x + 15, icon_y + 90))
    pop_text = font_large.render(f"{population_system.population}", True, COLORS['gold'])
    screen.blit(pop_text, (resources_panel.rect.x + 60, icon_y + 95))

    screen.blit(oil_icon, (resources_panel.rect.x + 15, icon_y + 130))
    oil_text = font_large.render(f"{oil}", True, (255, 180, 80))
    screen.blit(oil_text, (resources_panel.rect.x + 60, icon_y + 135))

    screen.blit(stone_icon, (resources_panel.rect.x + 15, icon_y + 170))
    stone_text = font_large.render(f"{stone}", True, (200, 200, 215))
    screen.blit(stone_text, (resources_panel.rect.x + 60, icon_y + 175))
    
    multiplier = population_system.get_income_multiplier()
    mult_text = font_small.render(f"Multiplicador: {multiplier:.2f}x", True, COLORS['gold'])
    screen.blit(mult_text, (resources_panel.rect.x + 15, icon_y + 215))
    
    cut_y = icon_y + 240
    cuts_text = font_small.render(f"Cortes: {len(collecting_trees)}/{upgrades.simultaneous_cuts_level}", True, (200,200,200))
    screen.blit(cuts_text, (resources_panel.rect.x + 15, cut_y))
    
    time_text = font_small.render(f"Tempo: {upgrades.get_current_cut_time()/1000:.1f}s", True, (200,200,200))
    screen.blit(time_text, (resources_panel.rect.x + 15, cut_y + 20))
    
    const_text = font_small.render(f"Construção: {int(upgrades.get_construction_time_multiplier()*100)}%", True, (200,200,200))
    screen.blit(const_text, (resources_panel.rect.x + 15, cut_y + 40))
    
    zoom_text = font_small.render(f"Zoom: {zoom:.1f}x", True, (200,200,200))
    screen.blit(zoom_text, (resources_panel.rect.x + 15, cut_y + 60))

def draw_competition_panel():
    """(DEPRECATED: Agora integrado ao painel BOT-7) Apenas para retrocompatibilidade."""
    pass  # Removido - conteúdo movido para draw_bot_panel()

def draw_mission_panel():
    mission_panel = Panel(20, SCREEN_HEIGHT - 145, 470, 120, (44, 62, 80, 220))
    mission_panel.draw(screen)

    title = font_medium.render("Metas", True, COLORS['gold'])
    screen.blit(title, (35, SCREEN_HEIGHT - 135))

    if not mission_system.started:
        text = font_small.render("As metas começam à partir da primeira construção.", True, (220, 220, 220))
        screen.blit(text, (35, SCREEN_HEIGHT - 105))
        return

    current = mission_system.get_current_mission()
    if current is None:
        text = font_small.render("Todas as metas concluídas.", True, (120, 255, 170))
        screen.blit(text, (35, SCREEN_HEIGHT - 105))
        return

    progress, target = mission_system.get_progress(total_buildings_completed, buildings_completed_by_name, oil, stone)
    progress = min(progress, target)

    desc = font_small.render(current["title"], True, (255, 255, 255))
    screen.blit(desc, (35, SCREEN_HEIGHT - 105))

    progress_text = font_small.render(f"Progresso: {progress}/{target} | Recompensa: ${current['reward_money']}", True, (220, 220, 220))
    screen.blit(progress_text, (35, SCREEN_HEIGHT - 82))

    bar_bg = pygame.Rect(35, SCREEN_HEIGHT - 55, 430, 16)
    pygame.draw.rect(screen, (60, 60, 60), bar_bg, border_radius=8)
    fill_ratio = 0 if target == 0 else (progress / target)
    fill_w = int(bar_bg.width * fill_ratio)
    if fill_w > 0:
        pygame.draw.rect(screen, COLORS['success'], (bar_bg.x, bar_bg.y, fill_w, bar_bg.height), border_radius=8)
    pygame.draw.rect(screen, (220, 220, 220), bar_bg, width=1, border_radius=8)

    if mission_system.last_reward_message and pygame.time.get_ticks() - mission_system.last_reward_time < 2500:
        reward_text = font_small.render(mission_system.last_reward_message, True, (120, 255, 170))
        screen.blit(reward_text, (250, SCREEN_HEIGHT - 135))


def draw_menu():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    # Painel principal
    panel_x, panel_y = SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 200
    panel_w, panel_h = 400, 400
    menu_panel = Panel(panel_x, panel_y, panel_w, panel_h, (44, 62, 80, 240))
    menu_panel.draw(screen)
    
    # Título
    title = font_large.render("CONSTRUÇÕES", True, COLORS['gold'])
    screen.blit(title, (SCREEN_WIDTH//2 - 120, panel_y + 30))
    
    # Área de scroll (onde os botões aparecem)
    scroll_area_x = panel_x + 15
    scroll_area_y = panel_y + 70
    scroll_area_w = 370
    scroll_area_h = 280
    
    # Cria clipping region para os botões
    clip_rect = pygame.Rect(scroll_area_x, scroll_area_y, scroll_area_w, scroll_area_h)
    old_clip = screen.get_clip()
    screen.set_clip(clip_rect)
    
    # Desenha botões com offset de scroll
    y_offset = scroll_area_y - int(menu_scroll.offset * 50)  # 50 é a altura de cada botão
    
    for name in building_names:
        # Cria novo rect com posição atualizada pelo scroll
        btn_rect = pygame.Rect(scroll_area_x + 25, y_offset, 300, 45)
        
        # Só desenha se está visível (dentro da área de scroll)
        if btn_rect.top < scroll_area_y + scroll_area_h and btn_rect.bottom > scroll_area_y:
            color = COLORS['primary'] if buildings[name]['population'] == 0 else COLORS['success']
            
            pygame.draw.rect(screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(screen, (255,255,255,50), btn_rect, width=2, border_radius=8)
            
            name_text = font_medium.render(name, True, (255,255,255))
            screen.blit(name_text, (btn_rect.x + 10, btn_rect.y + 5))
            
            screen.blit(pygame.transform.scale(money_icon, (15, 15)), (btn_rect.x + 10, btn_rect.y + 30))
            cost_text = font_small.render(f"{buildings[name]['cost_money']}", True, (255,255,255))
            screen.blit(cost_text, (btn_rect.x + 30, btn_rect.y + 30))
            
            screen.blit(pygame.transform.scale(wood_icon, (15, 15)), (btn_rect.x + 80, btn_rect.y + 30))
            wood_text = font_small.render(f"{buildings[name]['cost_wood']}", True, (255,255,255))
            screen.blit(wood_text, (btn_rect.x + 100, btn_rect.y + 30))

            _cs = buildings[name].get("cost_stone", 0)
            if _cs > 0:
                screen.blit(pygame.transform.scale(stone_icon, (15, 15)), (btn_rect.x + 155, btn_rect.y + 30))
                stone_lbl = font_small.render(f"{_cs}", True, (200, 200, 215))
                screen.blit(stone_lbl, (btn_rect.x + 175, btn_rect.y + 30))
            elif buildings[name]['population'] > 0:
                pop_text = font_small.render(f"+{buildings[name]['population']} pop", True, COLORS['gold'])
                screen.blit(pop_text, (btn_rect.x + 155, btn_rect.y + 30))
            
            # Armazena a posição atualizada para clique
            menu_buttons[name] = (name, btn_rect)
        
        y_offset += 55
    
    # Remove clipping
    screen.set_clip(old_clip)
    
    # Desenha borda da área de scroll
    pygame.draw.rect(screen, (255, 255, 255, 50), clip_rect, width=2, border_radius=8)
    
    # Desenha scrollbar (posicionado corretamente)
    scrollbar_x = scroll_area_x + scroll_area_w + -25
    menu_scroll.track_rect.x = scrollbar_x
    menu_scroll.track_rect.y = scroll_area_y
    menu_scroll.track_rect.height = scroll_area_h
    menu_scroll.draw(screen)

def draw_upgrade_menu():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    upgrade_panel = Panel(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 250, 500, 450, (44, 62, 80, 240))
    upgrade_panel.draw(screen)
    
    title = font_large.render("UPGRADES", True, COLORS['gold'])
    screen.blit(title, (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 - 220))
    
    y = SCREEN_HEIGHT//2 - 180
    
    if upgrades.simultaneous_cuts_level < upgrades.max_simultaneous_cuts_level:
        color = COLORS['success'] if money >= upgrades.simultaneous_cuts_cost[upgrades.simultaneous_cuts_level] else (100,100,100)
    else:
        color = (80,80,80)
    
    sim_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
    pygame.draw.rect(screen, color, sim_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS['gold'], sim_rect, width=2, border_radius=10)
    
    if upgrades.simultaneous_cuts_level < upgrades.max_simultaneous_cuts_level:
        text1 = font_small.render(f"Cortes Simultâneos: {upgrades.simultaneous_cuts_level} → {upgrades.simultaneous_cuts_level + 1}", True, (255,255,255))
        screen.blit(text1, (SCREEN_WIDTH//2 - 190, y + 5))
        
        screen.blit(pygame.transform.scale(money_icon, (15, 15)), (SCREEN_WIDTH//2 - 190, y + 25))
        cost_text = font_small.render(f": {upgrades.simultaneous_cuts_cost[upgrades.simultaneous_cuts_level]}", True, (255,255,255))
        screen.blit(cost_text, (SCREEN_WIDTH//2 - 165, y + 25))
    else:
        text1 = font_small.render(f"Cortes Simultâneos: {upgrades.simultaneous_cuts_level} (MÁXIMO)", True, COLORS['gold'])
        screen.blit(text1, (SCREEN_WIDTH//2 - 150, y + 15))
    
    y += 60
    
    if upgrades.cut_time_level < upgrades.max_cut_time_level:
        color = COLORS['success'] if money >= upgrades.cut_time_cost[upgrades.cut_time_level] else (100,100,100)
    else:
        color = (80,80,80)
    
    time_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
    pygame.draw.rect(screen, color, time_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS['gold'], time_rect, width=2, border_radius=10)
    
    current_time = upgrades.get_current_cut_time() / 1000
    if upgrades.cut_time_level < upgrades.max_cut_time_level:
        next_time = max(upgrades.min_cut_time, upgrades.base_cut_time - (upgrades.cut_time_level * 1750)) / 1000
        text2 = font_small.render(f"Tempo de Corte: {current_time:.1f}s → {next_time:.1f}s", True, (255,255,255))
        screen.blit(text2, (SCREEN_WIDTH//2 - 190, y + 5))
        
        screen.blit(pygame.transform.scale(money_icon, (15, 15)), (SCREEN_WIDTH//2 - 190, y + 25))
        cost_text = font_small.render(f": {upgrades.cut_time_cost[upgrades.cut_time_level]}", True, (255,255,255))
        screen.blit(cost_text, (SCREEN_WIDTH//2 - 165, y + 25))
    else:
        text2 = font_small.render(f"Tempo de Corte: {current_time:.1f}s (MÁXIMO)", True, COLORS['gold'])
        screen.blit(text2, (SCREEN_WIDTH//2 - 150, y + 15))
    
    y += 60
    
    if upgrades.construction_time_level < upgrades.max_construction_time_level:
        color = COLORS['success'] if money >= upgrades.construction_time_cost[upgrades.construction_time_level] else (100,100,100)
    else:
        color = (80,80,80)
    
    const_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
    pygame.draw.rect(screen, color, const_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS['gold'], const_rect, width=2, border_radius=10)
    
    current_reduction = upgrades.construction_time_reduction[upgrades.construction_time_level - 1] * 100
    if upgrades.construction_time_level < upgrades.max_construction_time_level:
        next_reduction = upgrades.construction_time_reduction[upgrades.construction_time_level] * 100
        text3 = font_small.render(f"Tempo de Construção: {current_reduction:.0f}% → {next_reduction:.0f}%", True, (255,255,255))
        screen.blit(text3, (SCREEN_WIDTH//2 - 190, y + 5))
        
        screen.blit(pygame.transform.scale(money_icon, (15, 15)), (SCREEN_WIDTH//2 - 190, y + 25))
        cost_text = font_small.render(f": {upgrades.construction_time_cost[upgrades.construction_time_level]}", True, (255,255,255))
        screen.blit(cost_text, (SCREEN_WIDTH//2 - 165, y + 25))
    else:
        text3 = font_small.render(f"Tempo de Construção: {current_reduction:.0f}% (MÁXIMO)", True, COLORS['gold'])
        screen.blit(text3, (SCREEN_WIDTH//2 - 150, y + 15))
    
    y += 60
    
    inst_text = font_small.render("Clique nos upgrades para comprar | ESC para fechar", True, (200,200,200))
    screen.blit(inst_text, (SCREEN_WIDTH//2 - 200, y + 20))

# ===== NOVO: Função para desenhar cursor personalizado =====
def draw_custom_cursor(screen, mouse_x, mouse_y):
    if current_mode == "collect":
        # Desenha cursor de machado
        cursor_rect = axe_cursor.get_rect(center=(mouse_x, mouse_y))
        screen.blit(axe_cursor, cursor_rect)
    elif current_mode == "mine":
        cursor_rect = pickaxe_cursor.get_rect(center=(mouse_x, mouse_y))
        screen.blit(pickaxe_cursor, cursor_rect)
    elif current_mode == "demolish":
        # Desenha cursor de martelo
        cursor_rect = hammer_cursor.get_rect(center=(mouse_x, mouse_y))
        screen.blit(hammer_cursor, cursor_rect)
    else:
        # Desenha cursor padrão (uma pequena cruz)
        pygame.draw.line(screen, (255,255,255), (mouse_x - 10, mouse_y), (mouse_x + 10, mouse_y), 2)
        pygame.draw.line(screen, (255,255,255), (mouse_x, mouse_y - 10), (mouse_x, mouse_y + 10), 2)
        pygame.draw.circle(screen, (255,255,255), (mouse_x, mouse_y), 5, 2)
# =========================================================



# ===== NOVO: Função para calcular e desenhar FPS =====
def draw_fps(screen, clock):
    global fps_update_time, fps_counter, fps_display
    
    fps_counter += 1
    current_time = pygame.time.get_ticks()
    
    # Atualiza o contador a cada 500ms
    if current_time - fps_update_time > 500:
        fps_display = str(int(fps_counter * (1000 / (current_time - fps_update_time))))
        fps_counter = 0
        fps_update_time = current_time
    
    # Desenha o FPS no canto superior direito
    fps_text = font_small.render(f"FPS: {fps_display}", True, (0, 0, 0))
    screen.blit(fps_text, (SCREEN_WIDTH - 100, 5))

def draw_flying_icons():
    current_time = pygame.time.get_ticks()
    finished_icons = []
    
    for icon in flying_icons:
        x, y, scale, progress = icon.update(current_time)
        
        # Redimensiona a imagem conforme a escala
        icon_width = int(ICON_SIZE[0] * scale)
        icon_height = int(ICON_SIZE[1] * scale)
        scaled_icon = pygame.transform.scale(icon.image, (icon_width, icon_height))
        
        # Calcula a posição para centralizar a imagem redimensionada
        draw_x = x - icon_width // 2
        draw_y = y - icon_height // 2
        
        # Adiciona efeito de fade out no final
        if progress > 0.8:
            alpha = int(255 * (1 - (progress - 0.8) / 0.2))
            scaled_icon.set_alpha(alpha)
        
        screen.blit(scaled_icon, (draw_x, draw_y))
        
        if icon.is_finished(current_time):
            finished_icons.append(icon)
    
    # Remove ícones que terminaram
    for icon in finished_icons:
        flying_icons.remove(icon)


# ===== RESET DO JOGO =====
def reset_game():
    global money, wood, oil, stone, grid, trees, collecting_trees, collect_start_times
    global cutting_sounds_playing, buildings_in_progress, building_start_times
    global building_id_counter, current_mode, selected_building, preview_active
    global total_buildings_completed, buildings_completed_by_name
    global rocks, collecting_rocks, collect_rock_start_times
    global bot_attacking, bot_attack_damage, bot_attack_notified, bot_last_attacked_building, bot_attack_animation_time
    global bot_spawned, bot_position, bot_target
    global bot_money, bot_wood, bot_oil, bot_stone, bot_total_buildings_completed, bot_buildings_completed_by_name, bot_building_id_counter
    global bot_collecting_trees, bot_collecting_rocks, bot_collect_start_times, bot_upgrades, bot_initial_pan_done
    
    for ch in cutting_sounds_playing.values():
        ch.stop()
    cutting_sounds_playing.clear()
    
    # RESET PLAYER
    money = 1000
    wood = 0
    oil = 0
    stone = 0
    building_id_counter = 0
    total_buildings_completed = 0
    buildings_completed_by_name.clear()
    
    # RESET BOT
    bot_money = 1000
    bot_wood = 100  # Recursos iniciais para novo jogo
    bot_oil = 0
    bot_stone = 100  # Recursos iniciais
    bot_building_id_counter = 0
    bot_total_buildings_completed = 0
    bot_buildings_completed_by_name.clear()
    bot_upgrades = UpgradeSystem()  # Reseta upgrades do bot
    bot_collecting_trees.clear()
    bot_collecting_rocks.clear()
    bot_collect_start_times.clear()
    bot_spawned = True  # Bot aparece quando o jogo inicia
    bot_initial_pan_done = False  # Reseta pan automático para novo jogo
    
    grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    collecting_trees.clear()
    collect_start_times.clear()
    collecting_rocks.clear()
    collect_rock_start_times.clear()
    buildings_in_progress.clear()
    building_start_times.clear()
    mission_system.reset()
    bot_attacking = False
    bot_attack_damage.clear()
    bot_attack_notified = False
    bot_last_attacked_building = None
    bot_attack_animation_time = 0
    bot_spawned = False
    bot_position = None
    bot_target = None
    flying_icons.clear()
    trees.clear()
    for _ in range(1000):
        attempts = 0
        while attempts < 100:
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            if not map_generator.is_water(x, y) and not map_generator.is_sand(x, y):
                trees.append({"pos": (x, y), "type": random.randint(0, 4)})
                break
            attempts += 1
    rocks.clear()
    _occupied = {tuple(t["pos"]) for t in trees}
    for _ in range(500):
        attempts = 0
        while attempts < 100:
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            if (not map_generator.is_water(x, y) and not map_generator.is_sand(x, y)
                    and (x, y) not in _occupied):
                rocks.append({"pos": (x, y)})
                _occupied.add((x, y))
                break
            attempts += 1
    population_system.calculate_population(grid, owner="player")
    bot_population_system.calculate_population(grid, owner="bot")
    current_mode = "none"
    selected_building = None
    preview_active = False


def _apply_sfx_volume(vol):
    build_sound.set_volume(0.5 * vol)
    break_sound.set_volume(0.5 * vol)
    button_sound.set_volume(vol)
    build_finish_sound.set_volume(vol)
    cutting_sound.set_volume(3.0 * vol)
    falling_tree_sound.set_volume(0.4 * vol)


def draw_start_screen():
    screen.fill((15, 25, 45))
    for gx in range(0, SCREEN_WIDTH, 60):
        pygame.draw.line(screen, (25, 40, 65), (gx, 0), (gx, SCREEN_HEIGHT))
    for gy in range(0, SCREEN_HEIGHT, 60):
        pygame.draw.line(screen, (25, 40, 65), (0, gy), (SCREEN_WIDTH, gy))

    title_font = pygame.font.Font(None, 110)
    title_surf = title_font.render("City Builder", True, COLORS['gold'])
    screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 160)))

    sub = font_medium.render("Construa a cidade dos seus sonhos!", True, (180, 210, 240))
    screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 90)))

    mx, my = pygame.mouse.get_pos()
    for btn in (start_play_btn, start_options_btn, start_quit_btn):
        btn.hovered = btn.rect.collidepoint(mx, my)
        btn.draw(screen)

    draw_custom_cursor(screen, mx, my)


def draw_pause_menu():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # Painel expandido para cobrir todos os botões
    panel = Panel(SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 2 - 185, 420, 490, (44, 62, 80, 245))
    panel.draw(screen)

    t = font_large.render("PAUSADO", True, COLORS['gold'])
    screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 155)))

    mx, my = pygame.mouse.get_pos()
    for btn in (pause_resume_btn, pause_newgame_btn, pause_save_btn, pause_options_btn, pause_quit_btn):
        btn.hovered = btn.rect.collidepoint(mx, my)
        btn.draw(screen)

    draw_custom_cursor(screen, mx, my)


# ===== PAINEL DO BOT =====
def draw_bot_panel():
    """Painel unificado BOT-7 com recursos + competição."""
    global bot_panel_x, bot_panel_y
    PW, PH = 340, 360  # Expandido para incluir competição
    PX = bot_panel_x
    PY = bot_panel_y

    # Garante que o painel fique dentro da tela
    PX = max(0, min(PX, SCREEN_WIDTH  - PW))
    PY = max(0, min(PY, SCREEN_HEIGHT - PH))
    bot_panel_x, bot_panel_y = PX, PY

    # fundo
    surf = pygame.Surface((PW, PH), pygame.SRCALPHA)
    pygame.draw.rect(surf, (25, 35, 55, 215), surf.get_rect(), border_radius=14)
    screen.blit(surf, (PX, PY))
    pygame.draw.rect(screen, (231, 76, 60), pygame.Rect(PX, PY, PW, PH), width=2, border_radius=14)

    # cabeçalho (área de drag)
    header_rect = pygame.Rect(PX, PY, PW, 32)
    header_surf = pygame.Surface((PW, 32), pygame.SRCALPHA)
    pygame.draw.rect(header_surf, (231, 76, 60, 200), header_surf.get_rect(), border_radius=14)
    screen.blit(header_surf, (PX, PY))

    # ícone de arrastar (6 pontinhos) no lado esquerdo do header
    for di in range(2):
        for dj in range(3):
            pygame.draw.circle(screen, (255, 255, 255, 180),
                               (PX + 8 + di * 6, PY + 8 + dj * 6), 2)

    # ícone de robô (primitivas)
    rx, ry = PX + 22, PY + 8
    pygame.draw.rect(screen, (200, 200, 210), (rx, ry + 2, 14, 12), border_radius=3)
    pygame.draw.rect(screen, (100, 100, 120), (rx + 2, ry + 4, 3, 3))
    pygame.draw.rect(screen, (100, 100, 120), (rx + 9, ry + 4, 3, 3))
    pygame.draw.line(screen, (200, 200, 210), (rx + 7, ry), (rx + 7, ry + 2), 2)
    pygame.draw.rect(screen, (150, 150, 160), (rx + 3, ry + 9, 8, 2))

    title = font_medium.render("🤖 BOT-7", True, (255, 255, 255))
    screen.blit(title, (PX + 42, PY + 7))

    # ===== SEÇÃO DE RECURSOS DO BOT =====
    y_pos = PY + 40
    res_label = font_small.render("Recursos:", True, (200, 200, 255))
    screen.blit(res_label, (PX + 10, y_pos))
    y_pos += 22
    
    # recursos
    row_h = 28
    items = [
        (money_icon,     f"${bot.fmt_money():,}",  (255, 230, 100)),
        (wood_icon,      str(bot.fmt_wood()),        (180, 255, 150)),
        (stone_icon,     str(bot.fmt_stone()),       (200, 200, 220)),
        (oil_icon,       str(bot.fmt_oil()),         (255, 180,  80)),
        (population_icon,str(bot.fmt_pop()),         (120, 210, 255)),
    ]

    for i, (icon, text, color) in enumerate(items):
        iy = y_pos + i * row_h
        small_icon = pygame.transform.scale(icon, (20, 20))
        screen.blit(small_icon, (PX + 12, iy))
        val_surf = font_small.render(text, True, color)
        screen.blit(val_surf, (PX + 36, iy + 2))

    # ===== SEÇÃO DE COMPETIÇÃO =====
    y_pos += len(items) * row_h + 15
    
    # Divider
    pygame.draw.line(screen, (150, 150, 150), (PX + 10, y_pos), (PX + PW - 10, y_pos), 1)
    y_pos += 10
    
    comp_label = font_small.render("⚔️ Competição:", True, (255, 200, 0))
    screen.blit(comp_label, (PX + 10, y_pos))
    y_pos += 22
    
    # Comparações
    player_pop = population_system.population
    bot_pop = bot_population_system.population
    player_building_count = sum(1 for y in range(GRID_SIZE) for x in range(75) if grid[y][x] and grid[y][x].get("owner", "player") == "player")
    bot_building_count = sum(1 for y in range(GRID_SIZE) for x in range(75, GRID_SIZE) if grid[y][x] and grid[y][x].get("owner") == "bot")
    
    comp_items = [
        (f"Você: ${int(money)}" if money > bot_money else f"Bot: ${int(bot_money)}", (100, 255, 100) if money > bot_money else (255, 100, 100)),
        (f"Pop Você: {player_pop}" if player_pop > bot_pop else f"Pop Bot: {bot_pop}", (100, 255, 100) if player_pop > bot_pop else (255, 100, 100)),
        (f"Prédios Você: {player_building_count}" if player_building_count > bot_building_count else f"Prédios Bot: {bot_building_count}", (100, 255, 100) if player_building_count > bot_building_count else (255, 100, 100)),
    ]
    
    comp_row_h = 22
    for i, (text, color) in enumerate(comp_items):
        iy = y_pos + i * comp_row_h
        comp_surf = font_small.render(text, True, color)
        screen.blit(comp_surf, (PX + 15, iy))

    # botão fechar (X) no canto do painel
    close_x = PX + PW - 22
    close_y = PY + 6
    pygame.draw.circle(screen, (180, 50, 40), (close_x, close_y + 8), 9)
    cx_text = font_small.render("X", True, (255, 255, 255))
    screen.blit(cx_text, cx_text.get_rect(center=(close_x, close_y + 8)))

    return header_rect, pygame.Rect(close_x - 9, close_y, 18, 18)


def draw_options_screen():
    is_from_game = (options_from == "game")
    if not is_from_game:
        screen.fill((15, 25, 45))
        for gx in range(0, SCREEN_WIDTH, 60):
            pygame.draw.line(screen, (25, 40, 65), (gx, 0), (gx, SCREEN_HEIGHT))
        for gy in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.line(screen, (25, 40, 65), (0, gy), (SCREEN_WIDTH, gy))
    else:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

    panel = Panel(SCREEN_WIDTH // 2 - 260, SCREEN_HEIGHT // 2 - 200, 520, 400, (44, 62, 80, 245))
    panel.draw(screen)

    t = font_large.render("OPÇÕES", True, COLORS['gold'])
    screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 168)))

    lbl = font_medium.render(f"Volume dos Sons: {int(sfx_volume * 100)}%", True, (255, 255, 255))
    screen.blit(lbl, (SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 120))

    bar_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 85, 440, 24)
    pygame.draw.rect(screen, (50, 50, 60), bar_rect, border_radius=12)
    fill = int(440 * sfx_volume)
    if fill:
        pygame.draw.rect(screen, COLORS['primary'],
                         pygame.Rect(bar_rect.x, bar_rect.y, fill, 24), border_radius=12)
    pygame.draw.rect(screen, (180, 180, 200), bar_rect, width=2, border_radius=12)

    hint = font_small.render("Clique ou arraste na barra para ajustar", True, (160, 160, 180))
    screen.blit(hint, (SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 55))

    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 140, 280, 55)
    mx, my = pygame.mouse.get_pos()
    bc = COLORS['danger'] if back_rect.collidepoint(mx, my) else (170, 40, 30)
    pygame.draw.rect(screen, bc, back_rect, border_radius=10)
    bt = font_medium.render("Voltar", True, (255, 255, 255))
    screen.blit(bt, bt.get_rect(center=back_rect.center))

    draw_custom_cursor(screen, mx, my)


def draw_save_confirmation_dialog():
    """Mostra diálogo de confirmação para salvar ao sair."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    
    dialog_w, dialog_h = 400, 200
    dialog_x = SCREEN_WIDTH // 2 - dialog_w // 2
    dialog_y = SCREEN_HEIGHT // 2 - dialog_h // 2
    
    panel = Panel(dialog_x, dialog_y, dialog_w, dialog_h, (44, 62, 80, 245))
    panel.draw(screen)
    
    # Título
    title = font_large.render("Salvar Jogo?", True, COLORS['gold'])
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, dialog_y + 30)))
    
    # Mensagem
    msg = font_medium.render("Deseja salvar o progresso antes de sair?", True, (255, 255, 255))
    screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, dialog_y + 70)))
    
    # Botão Salvar
    btn_save_rect = pygame.Rect(dialog_x + 30, dialog_y + 120, 150, 50)
    mx, my = pygame.mouse.get_pos()
    save_hover = btn_save_rect.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['success'] if save_hover else (30, 120, 60), btn_save_rect, border_radius=8)
    save_text = font_medium.render("Salvar", True, (255, 255, 255))
    screen.blit(save_text, save_text.get_rect(center=btn_save_rect.center))
    
    # Botão Descartar
    btn_discard_rect = pygame.Rect(dialog_x + 220, dialog_y + 120, 150, 50)
    discard_hover = btn_discard_rect.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['danger'] if discard_hover else (120, 30, 30), btn_discard_rect, border_radius=8)
    discard_text = font_medium.render("Descartar", True, (255, 255, 255))
    screen.blit(discard_text, discard_text.get_rect(center=btn_discard_rect.center))


def draw_load_confirmation_dialog():
    """Mostra diálogo de confirmação para carregar save."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    
    dialog_w, dialog_h = 420, 220
    dialog_x = SCREEN_WIDTH // 2 - dialog_w // 2
    dialog_y = SCREEN_HEIGHT // 2 - dialog_h // 2
    
    panel = Panel(dialog_x, dialog_y, dialog_w, dialog_h, (44, 62, 80, 245))
    panel.draw(screen)
    
    # Título
    title = font_large.render("Carregar Jogo?", True, COLORS['gold'])
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, dialog_y + 30)))
    
    # Mensagem
    msg = font_medium.render("Um save foi encontrado!", True, (255, 255, 255))
    screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, dialog_y + 70)))
    msg2 = font_small.render("Deseja continuar desse save ou começar novo jogo?", True, (200, 200, 200))
    screen.blit(msg2, msg2.get_rect(center=(SCREEN_WIDTH // 2, dialog_y + 100)))
    
    # Botão Carregar
    btn_load_rect = pygame.Rect(dialog_x + 30, dialog_y + 140, 160, 50)
    mx, my = pygame.mouse.get_pos()
    load_hover = btn_load_rect.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['success'] if load_hover else (30, 120, 60), btn_load_rect, border_radius=8)
    load_text = font_medium.render("Carregar", True, (255, 255, 255))
    screen.blit(load_text, load_text.get_rect(center=btn_load_rect.center))
    
    # Botão Novo Jogo
    btn_new_rect = pygame.Rect(dialog_x + 230, dialog_y + 140, 160, 50)
    new_hover = btn_new_rect.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['primary'] if new_hover else (40, 100, 150), btn_new_rect, border_radius=8)
    new_text = font_medium.render("Novo Jogo", True, (255, 255, 255))
    screen.blit(new_text, new_text.get_rect(center=btn_new_rect.center))


def draw_select_save_screen():
    """Mostra tela de seleção de saves."""
    global selected_save_index
    
    screen.fill((15, 25, 45))
    
    # Título
    title = font_large.render("Selecione um Save", True, COLORS['gold'])
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 50)))
    
    saves = get_save_files()
    
    if not saves:
        msg = font_medium.render("Nenhum save encontrado", True, (200, 100, 100))
        screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        
        # Botão voltar
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        mx, my = pygame.mouse.get_pos()
        back_hover = btn_back.collidepoint(mx, my)
        pygame.draw.rect(screen, COLORS['primary'] if back_hover else (40, 100, 150), btn_back, border_radius=8)
        back_text = font_medium.render("Voltar", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=btn_back.center))
        return
    
    # Área de scroll
    scroll_area_y = 120
    scroll_area_h = SCREEN_HEIGHT - 250
    item_height = 80
    total_height = len(saves) * item_height
    
    # Lista de saves
    mx, my = pygame.mouse.get_pos()
    for i, save_file in enumerate(saves):
        save_info = get_save_info(save_file)
        if not save_info:
            continue
        
        y = scroll_area_y + i * item_height - save_scroll_offset
        
        if y < scroll_area_y or y + item_height > scroll_area_y + scroll_area_h:
            continue
        
        # Retângulo do item
        item_rect = pygame.Rect(50, y, SCREEN_WIDTH - 100, item_height - 10)
        
        # Cor: selecionado ou hover
        is_hover = item_rect.collidepoint(mx, my)
        is_selected = (i == selected_save_index)
        
        if is_selected:
            color = COLORS['primary']
        elif is_hover:
            color = (80, 120, 160)
        else:
            color = (50, 80, 120)
        
        pygame.draw.rect(screen, color, item_rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['gold'] if is_selected else (100, 150, 200), item_rect, width=2, border_radius=8)
        
        # Texto do save
        date_text = font_small.render(f"📅 {save_info['date']}", True, (200, 200, 200))
        screen.blit(date_text, (item_rect.x + 20, item_rect.y + 15))
        
        res_text = f"💰 ${save_info['money']} | 🏢 {save_info['buildings']} prédios"
        res_render = font_small.render(res_text, True, (150, 200, 150))
        screen.blit(res_render, (item_rect.x + 20, item_rect.y + 45))
    
    # Botões de ação
    btn_load = pygame.Rect(SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT - 90, 150, 50)
    btn_delete = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 90, 150, 50)
    btn_new = pygame.Rect(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT - 90, 150, 50)
    
    # Carregar
    load_hover = btn_load.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['success'] if load_hover else (30, 120, 60), btn_load, border_radius=8)
    screen.blit(font_medium.render("Carregar", True, (255, 255, 255)), btn_load.move(10, 12))
    
    # Deletar
    del_hover = btn_delete.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['danger'] if del_hover else (120, 40, 40), btn_delete, border_radius=8)
    screen.blit(font_medium.render("Deletar", True, (255, 255, 255)), btn_delete.move(10, 12))
    
    # Novo Jogo
    new_hover = btn_new.collidepoint(mx, my)
    pygame.draw.rect(screen, COLORS['primary'] if new_hover else (40, 100, 150), btn_new, border_radius=8)
    screen.blit(font_medium.render("Novo Jogo", True, (255, 255, 255)), btn_new.move(10, 12))


# ===== SISTEMA DE SAVE/LOAD MÚLTIPLO =====
SAVES_DIR = "saves"

# Cria diretório de saves se não existir
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

def get_save_files():
    """Retorna lista de arquivos de save ordenados por data (mais recente primeiro)."""
    try:
        saves = [f for f in os.listdir(SAVES_DIR) if f.startswith("save_") and f.endswith(".json")]
        # Ordena por data modificada (mais recente primeiro)
        saves.sort(key=lambda x: os.path.getmtime(os.path.join(SAVES_DIR, x)), reverse=True)
        return saves
    except:
        return []

def get_save_info(filename):
    """Extrai informações do save (data, recursos, prédios)."""
    filepath = os.path.join(SAVES_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mtime = os.path.getmtime(filepath)
        date_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        
        money = data.get("money", 0)
        buildings = data.get("total_buildings_completed", 0)
        
        return {
            "date": date_str,
            "money": money,
            "buildings": buildings,
            "filename": filename
        }
    except:
        return None

def save_game(custom_name=""):
    """Salva o estado do jogo em arquivo JSON com timestamp."""
    # Gera nome do arquivo com timestamp
    if custom_name:
        timestamp = custom_name.replace(" ", "_")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    save_file = os.path.join(SAVES_DIR, f"save_{timestamp}.json")
    
    game_data = {
        "money": money,
        "wood": wood,
        "oil": oil,
        "stone": stone,
        "grid": [[cell.copy() if cell else None for cell in row] for row in grid],
        "trees": trees.copy(),
        "rocks": rocks.copy(),
        "buildings_in_progress": list(buildings_in_progress),
        "building_start_times": {str(k): v for k, v in building_start_times.items()},
        "building_id_counter": building_id_counter,
        "total_buildings_completed": total_buildings_completed,
        "buildings_completed_by_name": buildings_completed_by_name.copy(),
        "mission_data": mission_system.get_state() if hasattr(mission_system, 'get_state') else {},
        "upgrades": {
            "simultaneous_cuts_level": upgrades.simultaneous_cuts_level,
            "cut_time_level": upgrades.cut_time_level,
            "construction_time_level": upgrades.construction_time_level
        }
    }
    
    try:
        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Jogo salvo em {save_file}")
        return f"save_{timestamp}.json"  # Retorna o nome do arquivo
    except Exception as e:
        print(f"[ERRO] Erro ao salvar jogo: {e}")
        return None

def save_game_to_file(filename):
    """Sobrescreve um arquivo de save específico."""
    filepath = os.path.join(SAVES_DIR, filename)
    
    game_data = {
        "money": money,
        "wood": wood,
        "oil": oil,
        "stone": stone,
        "grid": [[cell.copy() if cell else None for cell in row] for row in grid],
        "trees": trees.copy(),
        "rocks": rocks.copy(),
        "buildings_in_progress": list(buildings_in_progress),
        "building_start_times": {str(k): v for k, v in building_start_times.items()},
        "building_id_counter": building_id_counter,
        "total_buildings_completed": total_buildings_completed,
        "buildings_completed_by_name": buildings_completed_by_name.copy(),
        "mission_data": mission_system.get_state() if hasattr(mission_system, 'get_state') else {},
        "upgrades": {
            "simultaneous_cuts_level": upgrades.simultaneous_cuts_level,
            "cut_time_level": upgrades.cut_time_level,
            "construction_time_level": upgrades.construction_time_level
        }
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Jogo sobrescrito em {filepath}")
        return True
    except Exception as e:
        print(f"[ERRO] Erro ao salvar jogo: {e}")
        return False

def load_game(save_file):
    """Carrega o estado do jogo de arquivo JSON específico."""
    global money, wood, oil, stone, grid, trees, rocks, buildings_in_progress
    global building_start_times, building_id_counter, total_buildings_completed, buildings_completed_by_name
    global population_system, bot_upgrades
    
    filepath = os.path.join(SAVES_DIR, save_file)
    if not os.path.exists(filepath):
        print(f"[INFO] Save nao encontrado ({filepath})")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Atribui valores carregados às variáveis globais
        money = game_data.get("money", 1000)
        wood = game_data.get("wood", 0)
        oil = game_data.get("oil", 0)
        stone = game_data.get("stone", 0)
        grid[:] = game_data.get("grid", [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)])
        trees[:] = game_data.get("trees", [])
        rocks[:] = game_data.get("rocks", [])
        building_id_counter = game_data.get("building_id_counter", 0)
        total_buildings_completed = game_data.get("total_buildings_completed", 0)
        buildings_completed_by_name.clear()
        buildings_completed_by_name.update(game_data.get("buildings_completed_by_name", {}))
        
        # Restaura building_start_times (converte strings de volta para tuplas)
        building_start_times.clear()
        for str_key, v in game_data.get("building_start_times", {}).items():
            try:
                key = tuple(map(int, str_key.strip('()').split(', ')))
                building_start_times[key] = v
            except:
                pass
        
        buildings_in_progress.clear()
        buildings_in_progress.extend(game_data.get("buildings_in_progress", []))
        
        # Restaura upgrades
        upgrades_data = game_data.get("upgrades", {})
        if upgrades_data:
            upgrades.simultaneous_cuts_level = upgrades_data.get("simultaneous_cuts_level", 1)
            upgrades.cut_time_level = upgrades_data.get("cut_time_level", 1)
            upgrades.construction_time_level = upgrades_data.get("construction_time_level", 1)
        
        # Restaura bot_upgrades (por enquanto com valores padrão)
        bot_upgrades = UpgradeSystem()
        
        # Recalcula população
        population_system.calculate_population(grid, owner="player")
        bot_population_system.calculate_population(grid, owner="bot")
        
        print(f"[OK] Jogo carregado de {filepath}")
        return True
    except Exception as e:
        print(f"[ERRO] Erro ao carregar jogo: {e}")
        return False

def show_save_confirmation_dialog():
    """Mostra um diálogo de confirmação para salvar ao sair."""
    dialog_width = 400
    dialog_height = 180
    dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
    dialog_y = SCREEN_HEIGHT // 2 - dialog_height // 2
    
    # Retorna: "save", "discard", ou None (ao clicar no X ou Esc)
    return {"x": dialog_x, "y": dialog_y, "w": dialog_width, "h": dialog_height}


# ----- LOOP PRINCIPAL -----
running = True
last_income_time = pygame.time.get_ticks()
save_dialog_active = False
selected_save_index = 0
save_scroll_offset = 0
popup_active = False
popup_message = ""
popup_type = "warning"  # 'warning', 'success', 'error'
popup_start_time = 0
game_saved = False  # Flag para rastrear se o jogo foi salvo recentemente
last_save_file = None  # Rastreia o último arquivo salvo para sobrescrever

population_system.calculate_population(grid, owner="player")
bot_population_system.calculate_population(grid, owner="bot")

while running:
    current_time = pygame.time.get_ticks()
    dt = clock.tick(60)

    if current_time - last_income_time >= 1000:
        # RENDA DO JOGADOR
        base_income = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid[y][x] is not None and grid[y][x].get("owner", "player") == "player":
                    base_income += buildings[grid[y][x]["name"]]["income"]

        building_counts = get_building_counts()
        oil += building_counts.get("Gerador de petróleo", 0) * buildings["Gerador de petróleo"].get("oil_output", 0)
        stone += building_counts.get("Mina", 0) * buildings["Mina"].get("stone_output", 0)
        
        multiplier = population_system.get_income_multiplier()
        money += int(base_income * multiplier)
        mission_system.update(total_buildings_completed, buildings_completed_by_name, oil, stone, wood)
        
        # RENDA DO BOT
        bot_base_income = 0
        for y in range(75, GRID_SIZE):
            for x in range(75, GRID_SIZE):
                if grid[y][x] is not None and grid[y][x].get("owner") == "bot":
                    bot_base_income += buildings[grid[y][x]["name"]]["income"]
        
        bot_multiplier = bot_population_system.get_income_multiplier()
        bot_money += int(bot_base_income * bot_multiplier)
        
        last_income_time = current_time

    # ===== IA DO BOT - ATIVADA =====
    bot_tick(current_time)
    if game_state == "playing":
        bot_collect_resources(current_time)

    # ===== AÇÕES DO BOT - DESABILITADAS =====
    # Conta construções do JOGADOR (não do bot)
    player_building_count = get_building_counts()
    total_player_buildings = sum(player_building_count.values())
    # if total_player_buildings >= 5 and not bot_spawned:
    #     bot_spawn()
    # 
    # # Se bot spawned, move em direção ao alvo
    # if bot_spawned and bot_position is not None:
    #     # Escolhe um alvo aleatório se não tem um
    #     if bot_target is None:
    #         player_buildings = []
    #         for y in range(GRID_SIZE):
    #             for x in range(GRID_SIZE):
    #                 if grid[y][x] is not None:
    #                     player_buildings.append((x, y))
    #         if player_buildings:
    #             bot_target = random.choice(player_buildings)
    #     
    #     # Move o bot
    #     bot_move_to_target()
    #     
    #     # Se chegou próximo, começa a atacar
    #     if bot_target is not None:
    #         dx = bot_target[0] - bot_position[0]
    #         dy = bot_target[1] - bot_position[1]
    #         distance = math.sqrt(dx*dx + dy*dy)
    #         
    #         if distance < BOT_DETECTION_RANGE and current_time - bot_last_attack >= BOT_ATTACK_INTERVAL:
    #             bot_attacking = True
    #             bot_attack_building(current_time)
    #             # Escolhe novo alvo
    #             player_buildings = []
    #             for y in range(GRID_SIZE):
    #                 for x in range(GRID_SIZE):
    #                     if grid[y][x] is not None:
    #                         player_buildings.append((x, y))
    #             if player_buildings:
    #                 bot_target = random.choice(player_buildings)
    #             
    #             if not bot_attack_notified:
    #                 bot_attack_notified = True
    #                 print("🤖 BOT-7 começou a atacar suas construções!")

    # ===== SISTEMA DE GERAÇÃO DE RECURSOS =====
    # Desabilitado por enquanto para evitar conflitos com construções
    # A cada 30 segundos, o jogo geraria NOVAS árvores e rochas em espaços vazios
    
    # if current_time - last_spawn_check >= SPAWN_TIME:
    #     last_spawn_check = current_time
    #     ... código removido ...

    completed_trees = []

    for collecting_tree in collecting_trees:
        tree_pos = collecting_tree["pos"]
        start_time = collect_start_times[tree_pos]
        
        # Toca o som de corte se ainda não estiver tocando para esta árvore
        if tree_pos not in cutting_sounds_playing:
            # Para em canais diferentes para não haver conflito
            channel = cutting_sound.play(-1)  # -1 faz loop infinito
            if channel:
                channel.set_volume(0.8)  # Volume alto
                cutting_sounds_playing[tree_pos] = channel
            else:
                # Se não conseguiu tocar (sem canais disponíveis), tenta novamente
                print("Sem canais disponíveis, tentando novamente...")
                pygame.mixer.set_num_channels(pygame.mixer.get_num_channels() + 5)
                channel = cutting_sound.play(-1)
                if channel:
                    channel.set_volume(0.8)
                    cutting_sounds_playing[tree_pos] = channel
 
        if current_time - start_time >= upgrades.get_current_cut_time():
            # Para o som de corte
            if tree_pos in cutting_sounds_playing:
                cutting_sounds_playing[tree_pos].stop()
                del cutting_sounds_playing[tree_pos]
            
            # Toca o som de árvore caindo
            falling_tree_sound.play()
            
            # Calcula a posição de início (onde a árvore foi cortada)
            tree_x, tree_y = tree_pos
            start_screen_x, start_screen_y = world_to_screen(tree_x * BASE_CELL_SIZE + BASE_CELL_SIZE/2, 
                                                            tree_y * BASE_CELL_SIZE + BASE_CELL_SIZE/2)
            
            # Posição de destino - AGORA APONTANDO PARA O ÍCONE DE MADEIRA
            # O ícone de madeira está em: resources_panel.rect.x + 15, icon_y + 45
            icon_y = resources_panel.rect.y + 15
            end_x = resources_panel.rect.x + 15 + ICON_SIZE[0]//2  # centro do ícone de madeira
            end_y = icon_y + 45 + ICON_SIZE[1]//2  # centro do ícone de madeira (45 pixels abaixo do money)
            
            # Cria 3 ícones voadores para dar mais impacto
            for i in range(3):
                # Pequena variação na posição inicial para não ficarem todos iguais
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                
                flying_icon = FlyingIcon(
                    start_screen_x + offset_x, 
                    start_screen_y + offset_y,
                    end_x + random.randint(-5, 5),  # pequena variação no destino
                    end_y + random.randint(-5, 5),
                    wood_icon,
                    duration=800 + random.randint(-100, 100)  # duração variada
                )
                flying_icons.append(flying_icon)
            
            # Remove a árvore
            for i, tree in enumerate(trees):
                if tree["pos"] == tree_pos:
                    trees.pop(i)
                    wood += 5
                    break
            completed_trees.append(collecting_tree)
    
    for tree in completed_trees:
        tree_pos = tree["pos"]
        # Garante que o som pare
        if tree_pos in cutting_sounds_playing:
            cutting_sounds_playing[tree_pos].stop()
            del cutting_sounds_playing[tree_pos]
        collecting_trees.remove(tree)
        del collect_start_times[tree_pos]

    # ----- Conclusão da mineração de rochas -----
    completed_rocks = []
    for cr in collecting_rocks:
        rock_pos = cr["pos"]
        start_time = collect_rock_start_times[rock_pos]
        if current_time - start_time >= MINE_TIME:
            rx, ry = rock_pos
            start_screen_x, start_screen_y = world_to_screen(
                rx * BASE_CELL_SIZE + BASE_CELL_SIZE / 2,
                ry * BASE_CELL_SIZE + BASE_CELL_SIZE / 2
            )
            icon_y_pos = resources_panel.rect.y + 15
            end_fx = resources_panel.rect.x + 15 + ICON_SIZE[0] // 2
            end_fy = icon_y_pos + 170 + ICON_SIZE[1] // 2
            for i in range(3):
                flying_icons.append(FlyingIcon(
                    start_screen_x + random.randint(-20, 20),
                    start_screen_y + random.randint(-20, 20),
                    end_fx + random.randint(-5, 5),
                    end_fy + random.randint(-5, 5),
                    stone_icon,
                    duration=800 + random.randint(-100, 100)
                ))
            # Remove a rocha
            for i, rock in enumerate(rocks):
                if rock["pos"] == rock_pos:
                    rocks.pop(i)
                    stone += MINE_YIELD
                    break
            completed_rocks.append(cr)
    for cr in completed_rocks:
        collecting_rocks.remove(cr)
        del collect_rock_start_times[cr["pos"]]

    completed_constructions = []
    for construction in buildings_in_progress:
        start_time = building_start_times[construction["pos"]]
        if current_time - start_time >= construction["build_time"]:
            completed_constructions.append(construction)
    
    for construction in completed_constructions:
        complete_construction(construction)

    if game_state == "playing":
        update_camera_smooth()
        
        # Pan automático para mostrar o bot na primeira vez que o jogo entra em "playing"
        if not bot_initial_pan_done:
            # Posiciona câmera para mostrar a ilha do bot (x: 75-149)
            # Centro da ilha do bot: x=112, y=75
            target_camera_x = 112 * BASE_CELL_SIZE - SCREEN_WIDTH / (2 * target_zoom)
            target_camera_y = 75 * BASE_CELL_SIZE - SCREEN_HEIGHT / (2 * target_zoom)
            
            # Garante que fica dentro dos limites
            max_x = GRID_SIZE * BASE_CELL_SIZE - SCREEN_WIDTH / target_zoom
            max_y = GRID_SIZE * BASE_CELL_SIZE - SCREEN_HEIGHT / target_zoom
            target_camera_x = max(0, min(target_camera_x, max_x))
            target_camera_y = max(0, min(target_camera_y, max_y))
            
            bot_initial_pan_done = True

    if game_state in ("playing", "paused"):
        screen.fill((200, 240, 200))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    menu_btn.hovered = menu_btn.rect.collidepoint(mouse_x, mouse_y)
    hammer_btn.hovered = hammer_btn.rect.collidepoint(mouse_x, mouse_y)
    collect_btn.hovered = collect_btn.rect.collidepoint(mouse_x, mouse_y)
    pickaxe_btn.hovered = pickaxe_btn.rect.collidepoint(mouse_x, mouse_y)
    upgrade_btn.hovered = upgrade_btn.rect.collidepoint(mouse_x, mouse_y)
    bot_btn.hovered = bot_btn.rect.collidepoint(mouse_x, mouse_y)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.key == pygame.K_q and game_state == "playing":
                money += 999999
                print(f"DEBUG: Money+999999, total={money}")
                wood += 9999
                stone += 9999
                oil += 9999
            elif event.key == pygame.K_w and game_state == "playing":
                upgrades.max_all()
            # F6 removido - usar botão Salvar no menu de pausa
            elif event.key == pygame.K_ESCAPE:
                if game_state == "playing":
                    game_state = "paused"
                    current_mode = "none"
                    selected_building = None
                    preview_active = False
                elif game_state == "paused":
                    game_state = "playing"
                elif game_state == "save_confirmation":
                    game_state = "paused"
                elif game_state == "load_confirmation":
                    game_state = "start_screen"
                elif game_state == "select_save":
                    game_state = "start_screen"
                elif game_state == "options":
                    game_state = "start_screen" if options_from == "start" else "paused"
                else:
                    current_mode = "none"
                    selected_building = None
                    preview_active = False

        if event.type == pygame.MOUSEWHEEL:
            if game_state == "select_save":
                # Scroll na lista de saves
                saves = get_save_files()
                if saves:
                    item_height = 80
                    total_height = len(saves) * item_height
                    scroll_area_h = SCREEN_HEIGHT - 250
                    max_offset = max(0, total_height - scroll_area_h)
                    save_scroll_offset = max(0, min(max_offset, save_scroll_offset - event.y * 50))
            elif game_state == "playing":
                # Verifica se está no menu com scroll aberto
                if current_mode == "menu":
                    menu_area = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 200, 400, 400)
                    if menu_area.collidepoint(mouse_x, mouse_y):
                        menu_scroll.scroll(-event.y)  # Inverte para scroll natural
                    else:
                        new_zoom = target_zoom + (event.y * ZOOM_SPEED)
                        apply_zoom(new_zoom, mouse_x, mouse_y)
                else:
                    new_zoom = target_zoom + (event.y * ZOOM_SPEED)
                    apply_zoom(new_zoom, mouse_x, mouse_y)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # --- Tela inicial ---
                if game_state == "start_screen":
                    if start_play_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        saves = get_save_files()
                        if saves:
                            game_state = "select_save"
                            selected_save_index = 0
                            save_scroll_offset = 0
                        else:
                            game_state = "playing"
                    elif start_options_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        options_from = "start"
                        game_state = "options"
                    elif start_quit_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        running = False

                # --- Menu de pausa ---
                elif game_state == "paused":
                    if pause_resume_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        game_saved = False
                        game_state = "playing"
                    elif pause_newgame_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        reset_game()
                        game_saved = False
                        game_state = "playing"
                    elif pause_save_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        saved_file = save_game()
                        if saved_file:
                            last_save_file = saved_file
                        game_saved = True
                        popup_active = True
                        popup_message = "Jogo salvo com sucesso!"
                        popup_type = "success"
                        popup_start_time = current_time
                    elif pause_options_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        options_from = "game"
                        game_state = "options"
                    elif pause_quit_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        if not game_saved:
                            game_state = "save_confirmation"
                        else:
                            running = False

                # --- Tela de opções ---
                elif game_state == "options":
                    _bar = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 85, 440, 24)
                    _back = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 140, 280, 55)
                    if _back.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        game_state = "start_screen" if options_from == "start" else "paused"
                    elif _bar.collidepoint(mouse_x, mouse_y):
                        sfx_volume = max(0.0, min(1.0, (mouse_x - _bar.x) / _bar.width))
                        _apply_sfx_volume(sfx_volume)

                # --- Diálogo de confirmação de save ---
                elif game_state == "save_confirmation":
                    dialog_w, dialog_h = 400, 200
                    dialog_x = SCREEN_WIDTH // 2 - dialog_w // 2
                    dialog_y = SCREEN_HEIGHT // 2 - dialog_h // 2
                    
                    btn_save_rect = pygame.Rect(dialog_x + 30, dialog_y + 120, 150, 50)
                    btn_discard_rect = pygame.Rect(dialog_x + 220, dialog_y + 120, 150, 50)
                    
                    if btn_save_rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        # Ao sair, sobrescreve o último save ao invés de criar novo
                        if last_save_file:
                            save_game_to_file(last_save_file)
                        else:
                            saved_file = save_game()
                            if saved_file:
                                last_save_file = saved_file
                        game_saved = True
                        running = False
                    elif btn_discard_rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        running = False

                # --- Diálogo de confirmação de load ---
                elif game_state == "load_confirmation":
                    dialog_w, dialog_h = 420, 220
                    dialog_x = SCREEN_WIDTH // 2 - dialog_w // 2
                    dialog_y = SCREEN_HEIGHT // 2 - dialog_h // 2
                    
                    btn_load_rect = pygame.Rect(dialog_x + 30, dialog_y + 140, 160, 50)
                    btn_new_rect = pygame.Rect(dialog_x + 230, dialog_y + 140, 160, 50)
                    
                    if btn_load_rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        # Carrega o arquivo mais recente
                        saves = get_save_files()
                        if saves:
                            load_game(saves[0])  # O primeiro da lista é o mais recente (ordenado por data)
                            last_save_file = saves[0]
                        game_saved = False
                        game_state = "playing"
                    elif btn_new_rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        game_saved = False
                        game_state = "playing"

                # --- Seleção de save ---
                elif game_state == "select_save":
                    saves = get_save_files()
                    if not saves:
                        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
                        if btn_back.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            game_state = "start_screen"
                    else:
                        # Botões de ação
                        btn_load = pygame.Rect(SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT - 90, 150, 50)
                        btn_delete = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 90, 150, 50)
                        btn_new = pygame.Rect(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT - 90, 150, 50)
                        
                        if btn_load.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            if selected_save_index < len(saves):
                                load_game(saves[selected_save_index])
                                last_save_file = saves[selected_save_index]
                                game_state = "playing"
                        elif btn_delete.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            if selected_save_index < len(saves):
                                save_to_delete = os.path.join(SAVES_DIR, saves[selected_save_index])
                                try:
                                    os.remove(save_to_delete)
                                    print(f"[OK] Save deletado: {saves[selected_save_index]}")
                                    selected_save_index = max(0, selected_save_index - 1)
                                except:
                                    print("[ERRO] Erro ao deletar save")
                        elif btn_new.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            game_state = "playing"
                        
                        # Scroll com mouse
                        scroll_area_y = 120
                        scroll_area_h = SCREEN_HEIGHT - 250
                        item_height = 80
                        
                        # Navegação com clique nos saves
                        for i, save_file in enumerate(saves):
                            y = scroll_area_y + i * item_height - save_scroll_offset
                            if scroll_area_y <= y < scroll_area_y + scroll_area_h:
                                item_rect = pygame.Rect(50, y, SCREEN_WIDTH - 100, item_height - 10)
                                if item_rect.collidepoint(mouse_x, mouse_y):
                                    selected_save_index = i

                # --- Jogo ---
                elif game_state == "playing":
                    clicked = False

                    if bot_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        show_bot_panel = not show_bot_panel
                        clicked = True

                    elif menu_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        if current_mode == "menu":
                            current_mode = "none"
                        else:
                            current_mode = "menu"
                        preview_active = False
                        selected_building = None
                        clicked = True

                    elif hammer_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        current_mode = "demolish" if current_mode != "demolish" else "none"
                        preview_active = False
                        selected_building = None
                        clicked = True

                    elif collect_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        current_mode = "collect" if current_mode != "collect" else "none"
                        preview_active = False
                        selected_building = None
                        clicked = True

                    elif pickaxe_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        current_mode = "mine" if current_mode != "mine" else "none"
                        preview_active = False
                        selected_building = None
                        clicked = True

                    elif upgrade_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        if current_mode == "upgrade":
                            current_mode = "none"
                        else:
                            current_mode = "upgrade"
                        preview_active = False
                        selected_building = None
                        clicked = True

                    elif current_mode == "upgrade" and not clicked:
                        upgrade_panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 250, 500, 450)
                        y = SCREEN_HEIGHT//2 - 180

                        sim_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
                        if sim_rect.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            upgrades.upgrade_simultaneous()
                            clicked = True

                        y += 60
                        time_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
                        if time_rect.collidepoint(mouse_x, mouse_y) and not clicked:
                            button_sound.play()
                            upgrades.upgrade_cut_time()
                            clicked = True

                        y += 60
                        const_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
                        if const_rect.collidepoint(mouse_x, mouse_y) and not clicked:
                            button_sound.play()
                            upgrades.upgrade_construction_time()
                            clicked = True

                        if not clicked and not upgrade_panel_rect.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            current_mode = "none"
                            clicked = True

                    elif current_mode == "menu" and not clicked:
                        menu_panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 200, 400, 400)
                        clicked_on_menu_button = False
                        for name, (_, btn_rect) in menu_buttons.items():
                            if btn_rect.collidepoint(mouse_x, mouse_y):
                                button_sound.play()
                                selected_building = name
                                current_mode = "none"
                                clicked = True
                                clicked_on_menu_button = True
                                break

                        if not clicked_on_menu_button and not menu_panel_rect.collidepoint(mouse_x, mouse_y):
                            button_sound.play()
                            current_mode = "none"
                            selected_building = None
                            clicked = True

                    if not clicked:
                        gx, gy = get_cell_at_mouse(mouse_x, mouse_y)
                        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                            if current_mode == "collect":
                                if len(collecting_trees) < upgrades.simultaneous_cuts_level:
                                    for tree in trees:
                                        if tree["pos"] == (gx, gy) and money >= COLLECT_COST:
                                            already_collecting = False
                                            for ct in collecting_trees:
                                                if ct["pos"] == (gx, gy):
                                                    already_collecting = True
                                                    break
                                            if not already_collecting:
                                                money -= COLLECT_COST
                                                collecting_trees.append(tree)
                                                collect_start_times[(gx, gy)] = pygame.time.get_ticks()
                                            break
                                else:
                                    popup_active = True
                                    popup_message = f"Limite de cortes atingido! ({upgrades.simultaneous_cuts_level}/{upgrades.simultaneous_cuts_level})"
                                    popup_type = "warning"
                                    popup_start_time = pygame.time.get_ticks()
                                    button_sound.play()
                            elif current_mode == "mine":
                                for rock in rocks:
                                    if rock["pos"] == (gx, gy):
                                        already_mining = any(cr["pos"] == (gx, gy) for cr in collecting_rocks)
                                        if not already_mining:
                                            collecting_rocks.append(rock)
                                            collect_rock_start_times[(gx, gy)] = pygame.time.get_ticks()
                                        break
                            elif current_mode == "demolish":
                                demolish_building(gx, gy)
                            elif selected_building and current_mode == "none":
                                preview_active = True

            elif event.button == 3:
                if game_state == "playing":
                    dragging = True
                    last_mouse_pos = (mouse_x, mouse_y)
                    last_camera_x = target_camera_x
                    last_camera_y = target_camera_y

            # Inicia drag do painel do bot (botão esquerdo no header)
            if event.button == 1 and show_bot_panel and game_state == "playing":
                _hdr = pygame.Rect(bot_panel_x, bot_panel_y, 230, 32)
                _cls = pygame.Rect(bot_panel_x + 230 - 31, bot_panel_y + 6, 18, 18)
                if _hdr.collidepoint(mouse_x, mouse_y) and not _cls.collidepoint(mouse_x, mouse_y):
                    bot_panel_dragging = True
                    bot_panel_drag_offset = (mouse_x - bot_panel_x, mouse_y - bot_panel_y)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                bot_panel_dragging = False
            if game_state == "playing":
                if event.button == 3:
                    dragging = False

                if event.button == 1 and preview_active:
                    gx, gy = get_cell_at_mouse(mouse_x, mouse_y)
                    cost_money = buildings[selected_building]["cost_money"]
                    cost_wood = buildings[selected_building]["cost_wood"]
                    cost_stone_req = buildings[selected_building].get("cost_stone", 0)
                    if (can_place_building(selected_building, gx, gy) and
                            money >= cost_money and wood >= cost_wood and stone >= cost_stone_req):
                        start_construction(selected_building, gx, gy)
                    preview_active = False

        if event.type == pygame.MOUSEMOTION:
            if bot_panel_dragging:
                bot_panel_x = mouse_x - bot_panel_drag_offset[0]
                bot_panel_y = mouse_y - bot_panel_drag_offset[1]
            elif game_state == "options" and pygame.mouse.get_pressed()[0]:
                _bar = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 85, 440, 24)
                if _bar.collidepoint(mouse_x, mouse_y):
                    sfx_volume = max(0.0, min(1.0, (mouse_x - _bar.x) / _bar.width))
                    _apply_sfx_volume(sfx_volume)
            elif dragging and game_state == "playing":
                dx = mouse_x - last_mouse_pos[0]
                dy = mouse_y - last_mouse_pos[1]
                target_camera_x = last_camera_x - dx / zoom
                target_camera_y = last_camera_y - dy / zoom
                max_x = GRID_SIZE * BASE_CELL_SIZE - SCREEN_WIDTH / zoom
                max_y = GRID_SIZE * BASE_CELL_SIZE - SCREEN_HEIGHT / zoom
                target_camera_x = max(0, min(target_camera_x, max_x))
                target_camera_y = max(0, min(target_camera_y, max_y))
                last_camera_x = target_camera_x
                last_camera_y = target_camera_y
                last_mouse_pos = (mouse_x, mouse_y)

    if game_state == "start_screen":
        draw_start_screen()
    elif game_state == "options":
        draw_options_screen()
    elif game_state == "select_save":
        draw_select_save_screen()
    else:  # playing or paused
        menu_btn.active = (current_mode == "menu")
        hammer_btn.active = (current_mode == "demolish")
        collect_btn.active = (current_mode == "collect")
        pickaxe_btn.active = (current_mode == "mine")
        upgrade_btn.active = (current_mode == "upgrade")

        draw_grid()
        if preview_active:
            draw_preview()
        draw_ui()
        draw_mission_panel()
        draw_flying_icons()

        # Botão do bot (sempre visível durante o jogo)
        bot_btn.active = show_bot_panel
        bot_btn.draw(screen)

        # Painel do bot
        if show_bot_panel:
            _header_rect, _close_rect = draw_bot_panel()
            # clique no X dentro do painel fecha
            if pygame.mouse.get_pressed()[0] and _close_rect.collidepoint(mouse_x, mouse_y):
                show_bot_panel = False

        if current_mode == "menu":
            draw_menu()
        elif current_mode == "upgrade":
            draw_upgrade_menu()

        # ===== VISUAL DE ATAQUE DO BOT =====
        # if bot_attacking and bot_last_attacked_building is not None:
        #     elapsed = current_time - bot_attack_animation_time
        #     if elapsed < BOT_ATTACK_VISUAL_DURATION:
        #         bx, by = bot_last_attacked_building
        #         screen_x, screen_y = world_to_screen(bx * BASE_CELL_SIZE + BASE_CELL_SIZE/2, 
        #                                               by * BASE_CELL_SIZE + BASE_CELL_SIZE/2)
        #         
        #         # Desenha o bot atacando com animação pulsante
        #         alpha = int(255 * (1 - elapsed / BOT_ATTACK_VISUAL_DURATION))
        #         bot_image.set_alpha(alpha)
        #         screen.blit(bot_image, (int(screen_x - 40), int(screen_y - 40)))
        #         
        #         # Notificação de ataque
        #         attack_text = font_medium.render("🤖 BOT ATACANDO!", True, (255, 50, 50))
        #         screen.blit(attack_text, (SCREEN_WIDTH // 2 - 100, 50))

        if show_fps:
            draw_fps(screen, clock)

        if 'popup_active' in locals() and popup_active:
            if current_time - popup_start_time < 2000:
                draw_popup(screen, popup_message, popup_type=popup_type)
            else:
                popup_active = False

        if game_state == "paused":
            draw_pause_menu()
        elif game_state == "save_confirmation":
            draw_save_confirmation_dialog()
        elif game_state == "load_confirmation":
            draw_load_confirmation_dialog()
        else:
            draw_custom_cursor(screen, mouse_x, mouse_y)

    pygame.display.flip()

# Para todos os sons de corte antes de sair
for sound in cutting_sounds_playing.values():
    sound.stop()
    
pygame.quit()
sys.exit()