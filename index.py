import pygame
import sys
import random
import math

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

# Imagem temporária do Gerador de Petróleo (retângulo colorido)
oil_gen_placeholder = pygame.Surface((BASE_CELL_SIZE, BASE_CELL_SIZE), pygame.SRCALPHA)
pygame.draw.rect(oil_gen_placeholder, (40, 60, 100), (0, 0, BASE_CELL_SIZE, BASE_CELL_SIZE))
pygame.draw.circle(oil_gen_placeholder, (255, 140, 0), (BASE_CELL_SIZE//2, BASE_CELL_SIZE//2), BASE_CELL_SIZE//4)
pygame.draw.rect(oil_gen_placeholder, (100, 150, 200), (0, 0, BASE_CELL_SIZE, BASE_CELL_SIZE), width=3)
building_images_original["Gerador de petróleo"] = oil_gen_placeholder

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

# Esconde o cursor padrão do sistema
pygame.mouse.set_visible(False)
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
hammer_btn = Button(130, 20, 100, 40, "Martelo", COLORS['danger'])
collect_btn = Button(240, 20, 160, 40, "Cortar ($5)", COLORS['success'])
upgrade_btn = Button(410, 20, 120, 40, "Upgrades", COLORS['gold'])

# Painel de recursos
resources_panel = Panel(SCREEN_WIDTH - 280, 20, 260, 280)

# ----- CÂMERA COM ZOOM SUAVE -----
camera_x = 250
camera_y = 250
target_camera_x = 250
target_camera_y = 250
zoom = 1.0
target_zoom = 1.0
dragging = False
last_mouse_pos = (0, 0)

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
money = 10000033
wood = 2003300

# ===== SISTEMA DE POPULAÇÃO =====
class PopulationSystem:
    def __init__(self):
        self.population = 0
        
    def calculate_population(self, grid):
        total = 0
        counted_buildings = set()
        
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid[y][x] is not None:
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

population_system = PopulationSystem()

# ===== SISTEMA DE UPGRADES =====
class UpgradeSystem:
    def __init__(self):
        # Upgrade de cortes simultâneos
        self.simultaneous_cuts_level = 1
        self.max_simultaneous_cuts = 5
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
        return (self.simultaneous_cuts_level < self.max_simultaneous_cuts and 
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

upgrades = UpgradeSystem()

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

# ----- ÁRVORES -----
trees = []
for _ in range(1000):
    attempts = 0
    while attempts < 100:
        x = random.randint(0, GRID_SIZE-1)
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

# ===== SISTEMA DE CONSTRUÇÃO =====
buildings_in_progress = []
building_start_times = {}

# ----- PRÉDIOS -----
buildings = {
    "Casa": {"cost_money": 20, "cost_wood": 10, "color": (0, 150, 0), "income": 1, "size": (1, 1), "population": 20, "build_time": 6000},
    "Predio": {"cost_money": 50, "cost_wood": 25, "color": (150, 0, 0), "income": 5, "size": (1, 1), "population": 200, "build_time": 10000},
    "Lojinha": {"cost_money": 270, "cost_wood": 50, "color": (0, 0, 120), "income": 27, "size": (1, 1), "population": 0, "build_time": 15000},
    "Shopping": {"cost_money": 3000, "cost_wood": 200, "color": (120, 0, 120), "income": 670, "size": (2, 3), "population": 0, "build_time": 20000},
    "Factory": {"cost_money": 9000, "cost_wood": 500, "color": (120, 40, 120), "income": 900, "size": (3, 3), "population": 0, "build_time": 50000},
    "School": {"cost_money": 1500, "cost_wood": 100, "color": (255, 165, 0), "income": 370, "size": (4, 3), "population": 0, "build_time": 15000},
    "Mall": {"cost_money": 900, "cost_wood": 90, "color": (128, 0, 128), "income": 34, "size": (3, 1), "population": 0, "build_time": 10000},
    "Gerador de petróleo": {"cost_money": 500000, "cost_wood": 50000, "color": (40, 60, 100), "income": 350000, "size": (5, 5), "population": 0, "build_time": 300},
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
pause_options_btn = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 50,  _bw, _bh, "Opções",    COLORS['warning'])
pause_quit_btn    = Button(SCREEN_WIDTH//2 - _bw//2, SCREEN_HEIGHT//2 + 135, _bw, _bh, "Sair",      COLORS['danger'])

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

# ===== FUNÇÕES DO JOGO =====
def can_place_building(name, gx, gy):
    width, height = buildings[name]["size"]

    if gx < 0 or gy < 0:
        return False
    if gx + width > GRID_SIZE or gy + height > GRID_SIZE:
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
    
    return True

def start_construction(name, gx, gy):
    global money, wood
    width, height = buildings[name]["size"]
    
    money -= buildings[name]["cost_money"]
    wood -= buildings[name]["cost_wood"]
    
    base_time = buildings[name]["build_time"]
    multiplier = upgrades.get_construction_time_multiplier()
    build_time = int(base_time * multiplier)
    
    construction = {
        "name": name,
        "pos": (gx, gy),
        "width": width,
        "height": height,
        "build_time": build_time,
        "cells": []
    }
    
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            construction["cells"].append((x, y))
    
    buildings_in_progress.append(construction)
    building_start_times[(gx, gy)] = pygame.time.get_ticks()
    build_sound.play()

def complete_construction(construction):
    global building_id_counter
    building_id_counter += 1
    name = construction["name"]
    gx, gy = construction["pos"]
    width, height = construction["width"], construction["height"]
    
    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            grid[y][x] = {"name": name, "id": building_id_counter}
    
    population_system.calculate_population(grid)
    buildings_in_progress.remove(construction)
    del building_start_times[(gx, gy)]
    
    build_finish_sound.play()  # NOVO: som de construção concluída

def demolish_building(gx, gy):
    if grid[gy][gx] is None:
        return
    building_id = grid[gy][gx]["id"]
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] and grid[y][x]["id"] == building_id:
                grid[y][x] = None
    
    population_system.calculate_population(grid)
    break_sound.play()

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
            elif grid[y][x] is None:
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
    
    # 3. TERCEIRO: Desenha as árvores
    draw_trees()
    
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
            if map_generator.is_water(x, y) or map_generator.is_sand(x, y):
                continue
                
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
def draw_popup(screen, message, duration=2000):
    """Desenha um popup no centro da tela por um determinado tempo"""
    popup_start_time = pygame.time.get_ticks()
    showing_popup = True
    
    # Cria uma superfície para o popup
    popup_width = 400
    popup_height = 100
    popup_surf = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    
    # Desenha o fundo do popup
    pygame.draw.rect(popup_surf, (44, 62, 80, 230), 
                    (0, 0, popup_width, popup_height), border_radius=15)
    pygame.draw.rect(popup_surf, COLORS['gold'], 
                    (0, 0, popup_width, popup_height), width=3, border_radius=15)
    
    # Desenha o texto
    text = font_medium.render(message, True, (255, 255, 255))
    text_rect = text.get_rect(center=(popup_width//2, popup_height//2))
    popup_surf.blit(text, text_rect)
    
    # Desenha um ícone de aviso
    warning_icon = font_large.render("⚠️", True, COLORS['gold'])
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
    
    if map_generator.is_water(gx, gy) or map_generator.is_sand(gx, gy):
        return
    
    width, height = buildings[selected_building]["size"]
    valid = can_place_building(selected_building, gx, gy)
    
    cost_money = buildings[selected_building]["cost_money"]
    cost_wood = buildings[selected_building]["cost_wood"]
    
    if valid and money >= cost_money and wood >= cost_wood:
        color = (0,255,0,120)
    else:
        color = (255,0,0,120)

    screen_x, screen_y = world_to_screen(gx * BASE_CELL_SIZE, gy * BASE_CELL_SIZE)
    preview_width = width * BASE_CELL_SIZE * zoom
    preview_height = height * BASE_CELL_SIZE * zoom
    
    s = pygame.Surface((preview_width, preview_height), pygame.SRCALPHA)
    s.fill(color)
    screen.blit(s, (screen_x, screen_y))

def draw_ui():
    menu_btn.draw(screen)
    hammer_btn.draw(screen)
    collect_btn.draw(screen)
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
    
    multiplier = population_system.get_income_multiplier()
    mult_text = font_small.render(f"Multiplicador: {multiplier:.2f}x", True, COLORS['gold'])
    screen.blit(mult_text, (resources_panel.rect.x + 15, icon_y + 135))
    
    cut_y = icon_y + 160
    cuts_text = font_small.render(f"Cortes: {len(collecting_trees)}/{upgrades.simultaneous_cuts_level}", True, (200,200,200))
    screen.blit(cuts_text, (resources_panel.rect.x + 15, cut_y))
    
    time_text = font_small.render(f"Tempo: {upgrades.get_current_cut_time()/1000:.1f}s", True, (200,200,200))
    screen.blit(time_text, (resources_panel.rect.x + 15, cut_y + 20))
    
    const_text = font_small.render(f"Construção: {int(upgrades.get_construction_time_multiplier()*100)}%", True, (200,200,200))
    screen.blit(const_text, (resources_panel.rect.x + 15, cut_y + 40))
    
    zoom_text = font_small.render(f"Zoom: {zoom:.1f}x", True, (200,200,200))
    screen.blit(zoom_text, (resources_panel.rect.x + 15, cut_y + 60))
    
    if selected_building:
        cost_panel = Panel(SCREEN_WIDTH - 280, 300, 260, 120, COLORS['panel'])
        cost_panel.draw(screen)
        
        title_text = font_small.render(f"{selected_building}", True, COLORS['gold'])
        screen.blit(title_text, (SCREEN_WIDTH - 265, 310))
        
        cost_money = buildings[selected_building]["cost_money"]
        cost_wood = buildings[selected_building]["cost_wood"]
        build_time = int(buildings[selected_building]["build_time"] * upgrades.get_construction_time_multiplier() / 1000)
        
        screen.blit(pygame.transform.scale(money_icon, (20, 20)), (SCREEN_WIDTH - 265, 335))
        money_cost_text = font_small.render(f": {cost_money}", True, (255,255,255))
        screen.blit(money_cost_text, (SCREEN_WIDTH - 235, 337))
        
        screen.blit(pygame.transform.scale(wood_icon, (20, 20)), (SCREEN_WIDTH - 165, 335))
        wood_cost_text = font_small.render(f": {cost_wood}", True, (255,255,255))
        screen.blit(wood_cost_text, (SCREEN_WIDTH - 135, 337))
        
        time_text = font_small.render(f"⏱️ {build_time}s", True, COLORS['gold'])
        screen.blit(time_text, (SCREEN_WIDTH - 265, 360))
        
        if buildings[selected_building]["population"] > 0:
            pop_text = font_small.render(f"+{buildings[selected_building]['population']} pop", True, COLORS['gold'])
            screen.blit(pop_text, (SCREEN_WIDTH - 265, 380))

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
            
            if buildings[name]['population'] > 0:
                pop_text = font_small.render(f"+{buildings[name]['population']} pop", True, COLORS['gold'])
                screen.blit(pop_text, (btn_rect.x + 150, btn_rect.y + 30))
            
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
    
    if upgrades.simultaneous_cuts_level < upgrades.max_simultaneous_cuts:
        color = COLORS['success'] if money >= upgrades.simultaneous_cuts_cost[upgrades.simultaneous_cuts_level] else (100,100,100)
    else:
        color = (80,80,80)
    
    sim_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, y, 400, 50)
    pygame.draw.rect(screen, color, sim_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS['gold'], sim_rect, width=2, border_radius=10)
    
    if upgrades.simultaneous_cuts_level < upgrades.max_simultaneous_cuts:
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
    global money, wood, grid, trees, collecting_trees, collect_start_times
    global cutting_sounds_playing, buildings_in_progress, building_start_times
    global building_id_counter, current_mode, selected_building, preview_active
    for ch in cutting_sounds_playing.values():
        ch.stop()
    cutting_sounds_playing.clear()
    money = 10000033
    wood = 2003300
    grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    collecting_trees.clear()
    collect_start_times.clear()
    buildings_in_progress.clear()
    building_start_times.clear()
    building_id_counter = 0
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
    population_system.calculate_population(grid)
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

    panel = Panel(SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 2 - 185, 420, 390, (44, 62, 80, 245))
    panel.draw(screen)

    t = font_large.render("PAUSADO", True, COLORS['gold'])
    screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 155)))

    mx, my = pygame.mouse.get_pos()
    for btn in (pause_resume_btn, pause_newgame_btn, pause_options_btn, pause_quit_btn):
        btn.hovered = btn.rect.collidepoint(mx, my)
        btn.draw(screen)

    draw_custom_cursor(screen, mx, my)


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


# ----- LOOP PRINCIPAL -----
running = True
last_income_time = pygame.time.get_ticks()

population_system.calculate_population(grid)

while running:
    current_time = pygame.time.get_ticks()
    dt = clock.tick(60)

    if current_time - last_income_time >= 1000:
        base_income = 0
        for row in grid:
            for cell in row:
                if cell:
                    base_income += buildings[cell["name"]]["income"]
        
        multiplier = population_system.get_income_multiplier()
        money += int(base_income * multiplier)
        last_income_time = current_time

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
    
    completed_constructions = []
    for construction in buildings_in_progress:
        start_time = building_start_times[construction["pos"]]
        if current_time - start_time >= construction["build_time"]:
            completed_constructions.append(construction)
    
    for construction in completed_constructions:
        complete_construction(construction)

    if game_state == "playing":
        update_camera_smooth()

    if game_state in ("playing", "paused"):
        screen.fill((200, 240, 200))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    menu_btn.hovered = menu_btn.rect.collidepoint(mouse_x, mouse_y)
    hammer_btn.hovered = hammer_btn.rect.collidepoint(mouse_x, mouse_y)
    collect_btn.hovered = collect_btn.rect.collidepoint(mouse_x, mouse_y)
    upgrade_btn.hovered = upgrade_btn.rect.collidepoint(mouse_x, mouse_y)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.key == pygame.K_ESCAPE:
                if game_state == "playing":
                    game_state = "paused"
                    current_mode = "none"
                    selected_building = None
                    preview_active = False
                elif game_state == "paused":
                    game_state = "playing"
                elif game_state == "options":
                    game_state = "start_screen" if options_from == "start" else "paused"
                else:
                    current_mode = "none"
                    selected_building = None
                    preview_active = False

        if event.type == pygame.MOUSEWHEEL and game_state == "playing":
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
                        game_state = "playing"
                    elif start_options_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        options_from = "start"
                        game_state = "options"
                    elif start_quit_btn.rect.collidepoint(mouse_x, mouse_y):
                        running = False

                # --- Menu de pausa ---
                elif game_state == "paused":
                    if pause_resume_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        game_state = "playing"
                    elif pause_newgame_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        reset_game()
                        game_state = "playing"
                    elif pause_options_btn.rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        options_from = "game"
                        game_state = "options"
                    elif pause_quit_btn.rect.collidepoint(mouse_x, mouse_y):
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

                # --- Jogo ---
                elif game_state == "playing":
                    clicked = False

                    if menu_btn.rect.collidepoint(mouse_x, mouse_y):
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
                            if map_generator.is_water(gx, gy) or map_generator.is_sand(gx, gy):
                                pass
                            elif current_mode == "collect":
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
                                    popup_start_time = pygame.time.get_ticks()
                                    button_sound.play()
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

        if event.type == pygame.MOUSEBUTTONUP:
            if game_state == "playing":
                if event.button == 3:
                    dragging = False

                if event.button == 1 and preview_active:
                    gx, gy = get_cell_at_mouse(mouse_x, mouse_y)
                    if not (map_generator.is_water(gx, gy) or map_generator.is_sand(gx, gy)):
                        cost_money = buildings[selected_building]["cost_money"]
                        cost_wood = buildings[selected_building]["cost_wood"]
                        if (can_place_building(selected_building, gx, gy) and
                                money >= cost_money and wood >= cost_wood):
                            start_construction(selected_building, gx, gy)
                    preview_active = False

        if event.type == pygame.MOUSEMOTION:
            if game_state == "options" and pygame.mouse.get_pressed()[0]:
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
    else:  # playing or paused
        menu_btn.active = (current_mode == "menu")
        hammer_btn.active = (current_mode == "demolish")
        collect_btn.active = (current_mode == "collect")
        upgrade_btn.active = (current_mode == "upgrade")

        draw_grid()
        if preview_active:
            draw_preview()
        draw_ui()
        draw_flying_icons()

        if current_mode == "menu":
            draw_menu()
        elif current_mode == "upgrade":
            draw_upgrade_menu()

        if show_fps:
            draw_fps(screen, clock)

        if 'popup_active' in locals() and popup_active:
            if current_time - popup_start_time < 2000:
                draw_popup(screen, popup_message)
            else:
                popup_active = False

        if game_state == "paused":
            draw_pause_menu()
        else:
            draw_custom_cursor(screen, mouse_x, mouse_y)

    pygame.display.flip()

# Para todos os sons de corte antes de sair
for sound in cutting_sounds_playing.values():
    sound.stop()
    
pygame.quit()
sys.exit()