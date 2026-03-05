import pygame
import sys
import random

# 🔊 CONFIGURAÇÃO DE ÁUDIO
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# ----- CONFIG -----
GRID_SIZE = 50
BASE_CELL_SIZE = 60
MIN_ZOOM = 0.3
MAX_ZOOM = 2.0
ZOOM_SPEED = 0.1

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("City Builder")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 18)

# ----- SONS -----
build_sound = pygame.mixer.Sound("sound/build.wav")
break_sound = pygame.mixer.Sound("sound/breaking.wav")
upgrade_sound = pygame.mixer.Sound("sound/build.wav")  # Usando o mesmo som por enquanto

build_sound.set_volume(0.5)
break_sound.set_volume(0.5)
upgrade_sound.set_volume(0.5)

# ----- IMAGENS DOS PRÉDIOS (tamanho original) -----
building_images_original = {}

building_images_original["Casa"] = pygame.image.load("assets/casa.png").convert_alpha()
building_images_original["Predio"] = pygame.image.load("assets/predio.png").convert_alpha()
building_images_original["Lojinha"] = pygame.image.load("assets/loja-game.png").convert_alpha()
building_images_original["Shopping"] = pygame.image.load("assets/shopping-game.png").convert_alpha()
building_images_original["Factory"] = pygame.image.load("assets/factory-game.png").convert_alpha()

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

# ----- CÂMERA COM ZOOM SUAVE -----
camera_x = 250
camera_y = 250
target_camera_x = 250
target_camera_y = 250
zoom = 1.0
target_zoom = 1.0
dragging = False
last_mouse_pos = (0, 0)

# ----- ECONOMIA -----
money = 100033
wood = 20033

# ===== NOVO: SISTEMA DE UPGRADES =====
class UpgradeSystem:
    def __init__(self):
        # Upgrade de cortes simultâneos
        self.simultaneous_cuts_level = 1
        self.max_simultaneous_cuts = 5
        self.simultaneous_cuts_cost = [500, 5000, 50000, 500000, 5000000]  # Custo em dinheiro para cada nível
        
        # Upgrade de tempo de corte
        self.cut_time_level = 1
        self.max_cut_time_level = 5
        self.cut_time_cost = [30, 60, 120, 240, 480]  # Custo em dinheiro para cada nível
        self.base_cut_time = 10000  # 10 segundos em milissegundos
        self.min_cut_time = 3000    # 3 segundos em milissegundos
        
    def get_current_cut_time(self):
        # Quanto maior o nível, menor o tempo
        # Nível 1: 10s, Nível 2: 8.25s, Nível 3: 6.5s, Nível 4: 4.75s, Nível 5: 3s
        time_reduction = (self.cut_time_level - 1) * 1750  # Reduz 1.75s por nível
        return max(self.min_cut_time, self.base_cut_time - time_reduction)
    
    def can_upgrade_simultaneous(self):
        return (self.simultaneous_cuts_level < self.max_simultaneous_cuts and 
                money >= self.simultaneous_cuts_cost[self.simultaneous_cuts_level])  # Mudado de wood para money
    
    def can_upgrade_cut_time(self):
        return (self.cut_time_level < self.max_cut_time_level and 
                money >= self.cut_time_cost[self.cut_time_level])  # Mudado de wood para money
    
    def upgrade_simultaneous(self):
        if self.can_upgrade_simultaneous():
            global money  # Mudado de wood para money
            money -= self.simultaneous_cuts_cost[self.simultaneous_cuts_level]  # Mudado de wood para money
            self.simultaneous_cuts_level += 1
            upgrade_sound.play()
            return True
        return False
    
    def upgrade_cut_time(self):
        if self.can_upgrade_cut_time():
            global money  # Mudado de wood para money
            money -= self.cut_time_cost[self.cut_time_level]  # Mudado de wood para money
            self.cut_time_level += 1
            upgrade_sound.play()
            return True
        return False

upgrades = UpgradeSystem()
# ======================================

# ----- ÁRVORES -----
trees = []
for _ in range(500):
    trees.append({
        "pos": (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)),
        "type": random.randint(0, 4)
    })

# ===== MODIFICADO: Sistema de coleta com múltiplos cortes =====
collect_button = pygame.Rect(20, 140, 160, 40)
collecting_trees = []  # Agora é uma lista de árvores sendo coletadas
collect_start_times = {}  # Dicionário com tempo de início para cada árvore
COLLECT_COST = 5
# ==============================================================

# ----- PRÉDIOS -----
buildings = {
    "Casa": {"cost_money": 20, "cost_wood": 10, "color": (0, 150, 0), "income": 1, "size": (1, 1)},
    "Predio": {"cost_money": 50, "cost_wood": 25, "color": (150, 0, 0), "income": 5, "size": (1, 1)},
    "Lojinha": {"cost_money": 270, "cost_wood": 50, "color": (0, 0, 120), "income": 27, "size": (1, 1)},
    "Shopping": {"cost_money": 3000, "cost_wood": 200, "color": (120, 0, 120), "income": 670, "size": (2, 3)},
    "Factory": {"cost_money": 9000, "cost_wood": 500, "color": (120, 40, 120), "income": 900, "size": (3, 3)}
}

grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
building_id_counter = 0

# ----- MODOS -----
current_mode = "none"
selected_building = None
preview_active = False
preview_pos = (0, 0)

# ----- MENU PRINCIPAL -----
menu_button = pygame.Rect(20, 20, 120, 40)
hammer_button = pygame.Rect(20, 80, 120, 40)

menu_width = 300
menu_height = 350
menu_rect = pygame.Rect(
    SCREEN_WIDTH//2 - menu_width//2,
    SCREEN_HEIGHT//2 - menu_height//2,
    menu_width,
    menu_height
)

buttons = []
y_offset = 80
for name in buildings:
    rect = pygame.Rect(menu_rect.x + 50, menu_rect.y + y_offset, 200, 40)
    buttons.append((name, rect))
    y_offset += 50

# ===== NOVO: MENU DE UPGRADES =====
upgrade_button = pygame.Rect(20, 200, 120, 40)

upgrade_menu_width = 400
upgrade_menu_height = 300
upgrade_menu_rect = pygame.Rect(
    SCREEN_WIDTH//2 - upgrade_menu_width//2,
    SCREEN_HEIGHT//2 - upgrade_menu_height//2,
    upgrade_menu_width,
    upgrade_menu_height
)

# Botões de upgrade
simultaneous_upgrade_rect = pygame.Rect(upgrade_menu_rect.x + 50, upgrade_menu_rect.y + 80, 300, 50)
cut_time_upgrade_rect = pygame.Rect(upgrade_menu_rect.x + 50, upgrade_menu_rect.y + 150, 300, 50)
# ==================================

# ----- FUNÇÕES DE CÂMERA E ZOOM -----
def world_to_screen(world_x, world_y):
    """Converte coordenadas do mundo para coordenadas da tela"""
    screen_x = (world_x - camera_x) * zoom
    screen_y = (world_y - camera_y) * zoom
    return screen_x, screen_y

def screen_to_world(screen_x, screen_y):
    """Converte coordenadas da tela para coordenadas do mundo"""
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
    """Atualiza a câmera suavemente (interpolação linear)"""
    global camera_x, camera_y, zoom
    smooth_factor = 0.2
    camera_x += (target_camera_x - camera_x) * smooth_factor
    camera_y += (target_camera_y - camera_y) * smooth_factor
    zoom += (target_zoom - zoom) * smooth_factor

def get_cell_at_mouse(mouse_x, mouse_y):
    """Retorna a célula do grid na posição do mouse"""
    world_x, world_y = screen_to_world(mouse_x, mouse_y)
    gx = int(world_x // BASE_CELL_SIZE)
    gy = int(world_y // BASE_CELL_SIZE)
    return gx, gy

# ----- FUNÇÕES DO JOGO -----
def can_place_building(name, gx, gy):
    width, height = buildings[name]["size"]

    if gx < 0 or gy < 0:
        return False
    if gx + width > GRID_SIZE or gy + height > GRID_SIZE:
        return False

    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            if grid[y][x] is not None:
                return False
            for tree in trees:
                if tree["pos"] == (x, y):
                    return False
    return True

def place_building(name, gx, gy):
    global building_id_counter
    building_id_counter += 1
    width, height = buildings[name]["size"]

    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            grid[y][x] = {"name": name, "id": building_id_counter}

def demolish_building(gx, gy):
    if grid[gy][gx] is None:
        return
    building_id = grid[gy][gx]["id"]
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] and grid[y][x]["id"] == building_id:
                grid[y][x] = None
    break_sound.play()

def draw_grid():
    cell_size_scaled = BASE_CELL_SIZE * zoom
    
    # Fundo das células vazias
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            screen_x, screen_y = world_to_screen(x * BASE_CELL_SIZE, y * BASE_CELL_SIZE)
            rect = pygame.Rect(screen_x, screen_y, cell_size_scaled, cell_size_scaled)

            if rect.right < 0 or rect.left > SCREEN_WIDTH:
                continue
            if rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                continue

            if grid[y][x] is None:
                has_tree = False
                for tree in trees:
                    if tree["pos"] == (x, y):
                        has_tree = True
                        break
                
                if not has_tree:
                    pygame.draw.rect(screen, (144, 238, 144), rect)

    # Construções
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            screen_x, screen_y = world_to_screen(x * BASE_CELL_SIZE, y * BASE_CELL_SIZE)
            rect = pygame.Rect(screen_x, screen_y, cell_size_scaled, cell_size_scaled)

            if rect.right < 0 or rect.left > SCREEN_WIDTH:
                continue
            if rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
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
                    img_width = width * BASE_CELL_SIZE * zoom
                    img_height = height * BASE_CELL_SIZE * zoom
                    
                    img = pygame.transform.scale(
                        building_images_original[building_name],
                        (int(img_width), int(img_height))
                    )
                    
                    screen.blit(img, (img_screen_x, img_screen_y))

    # Linhas do grid
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            screen_x, screen_y = world_to_screen(x * BASE_CELL_SIZE, y * BASE_CELL_SIZE)
            rect = pygame.Rect(screen_x, screen_y, cell_size_scaled, cell_size_scaled)

            if rect.right < 0 or rect.left > SCREEN_WIDTH:
                continue
            if rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                continue

            draw_this_cell_line = True
            
            if grid[y][x] is not None:
                building_data = grid[y][x]
                building_name = building_data["name"]
                width, height = buildings[building_name]["size"]
                
                if width > 1 or height > 1:
                    draw_this_cell_line = False
            
            if draw_this_cell_line:
                pygame.draw.rect(screen, (0,0,0), rect, 1)

# ===== MODIFICADO: draw_trees para múltiplos cortes =====
def draw_trees():
    cell_size_scaled = BASE_CELL_SIZE * zoom
    current_time = pygame.time.get_ticks()
    
    for tree in trees:
        tx, ty = tree["pos"]
        tree_type = tree["type"]
        
        screen_x, screen_y = world_to_screen(tx * BASE_CELL_SIZE, ty * BASE_CELL_SIZE)
        rect = pygame.Rect(screen_x, screen_y, cell_size_scaled, cell_size_scaled)
        
        tree_img = pygame.transform.scale(
            tree_images_original[tree_type],
            (int(cell_size_scaled), int(cell_size_scaled))
        )
        
        # Verifica se esta árvore está sendo coletada
        is_collecting = False
        for collecting_tree in collecting_trees:
            if collecting_tree["pos"] == (tx, ty):
                is_collecting = True
                start_time = collect_start_times[(tx, ty)]
                progress = (current_time - start_time) / upgrades.get_current_cut_time()
                break
        
        if is_collecting:
            # Desenha árvore com efeito de seleção
            s = pygame.Surface((cell_size_scaled, cell_size_scaled), pygame.SRCALPHA)
            s.fill((255,255,0,100))
            screen.blit(tree_img, rect.topleft)
            screen.blit(s, rect.topleft)
            
            # Barra de progresso
            bar_width = cell_size_scaled * min(progress, 1.0)
            bar_rect = pygame.Rect(rect.x, rect.y + cell_size_scaled - 5, bar_width, 3)
            pygame.draw.rect(screen, (0,255,0), bar_rect)
        else:
            screen.blit(tree_img, rect.topleft)
# ========================================================

def draw_preview():
    if not preview_active or not selected_building:
        return
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    gx, gy = get_cell_at_mouse(mouse_x, mouse_y)
    preview_pos = (gx, gy)
    
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

# ===== NOVO: draw_upgrade_menu =====
def draw_upgrade_menu():
    # Fundo do menu
    pygame.draw.rect(screen, (50,50,50), upgrade_menu_rect)
    pygame.draw.rect(screen, (255,215,0), upgrade_menu_rect, 3)  # Borda dourada
    
    # Título
    title = font.render("UPGRADES", True, (255,215,0))
    screen.blit(title, (upgrade_menu_rect.x + upgrade_menu_rect.width//2 - 50, upgrade_menu_rect.y + 20))
    
    # Upgrade de cortes simultâneos
    if upgrades.simultaneous_cuts_level < upgrades.max_simultaneous_cuts:
        cost = upgrades.simultaneous_cuts_cost[upgrades.simultaneous_cuts_level]
        can_afford = money >= cost  # Mudado de wood para money
        color = (100,200,100) if can_afford else (100,100,100)
    else:
        color = (80,80,80)  # Cinza escuro para máximo
        cost = "MAX"
    
    pygame.draw.rect(screen, color, simultaneous_upgrade_rect)
    pygame.draw.rect(screen, (255,255,255), simultaneous_upgrade_rect, 2)
    
    # Texto do upgrade simultâneo
    if upgrades.simultaneous_cuts_level < upgrades.max_simultaneous_cuts:
        text1 = small_font.render(f"Cortes Simultâneos: {upgrades.simultaneous_cuts_level} → {upgrades.simultaneous_cuts_level + 1}", True, (255,255,255))
        screen.blit(text1, (simultaneous_upgrade_rect.x + 10, simultaneous_upgrade_rect.y + 5))
        
        # Ícone de dinheiro custo
        screen.blit(pygame.transform.scale(money_icon, (20, 20)), (simultaneous_upgrade_rect.x + 10, simultaneous_upgrade_rect.y + 25))
        cost_text = small_font.render(f": {cost}", True, (255,255,255))
        screen.blit(cost_text, (simultaneous_upgrade_rect.x + 35, simultaneous_upgrade_rect.y + 27))
    else:
        text1 = small_font.render(f"Cortes Simultâneos: {upgrades.simultaneous_cuts_level} (MÁXIMO)", True, (255,215,0))
        screen.blit(text1, (simultaneous_upgrade_rect.x + 10, simultaneous_upgrade_rect.y + 15))
    
    # Upgrade de tempo de corte
    if upgrades.cut_time_level < upgrades.max_cut_time_level:
        cost = upgrades.cut_time_cost[upgrades.cut_time_level]
        can_afford = money >= cost  # Mudado de wood para money
        color = (100,200,100) if can_afford else (100,100,100)
    else:
        color = (80,80,80)
        cost = "MAX"
    
    pygame.draw.rect(screen, color, cut_time_upgrade_rect)
    pygame.draw.rect(screen, (255,255,255), cut_time_upgrade_rect, 2)
    
    # Texto do upgrade de tempo
    current_time = upgrades.get_current_cut_time() / 1000
    if upgrades.cut_time_level < upgrades.max_cut_time_level:
        next_time = max(upgrades.min_cut_time, upgrades.base_cut_time - (upgrades.cut_time_level * 1750)) / 1000
        text2 = small_font.render(f"Tempo de Corte: {current_time:.1f}s → {next_time:.1f}s", True, (255,255,255))
        screen.blit(text2, (cut_time_upgrade_rect.x + 10, cut_time_upgrade_rect.y + 5))
        
        screen.blit(pygame.transform.scale(money_icon, (20, 20)), (cut_time_upgrade_rect.x + 10, cut_time_upgrade_rect.y + 25))
        cost_text = small_font.render(f": {cost}", True, (255,255,255))
        screen.blit(cost_text, (cut_time_upgrade_rect.x + 35, cut_time_upgrade_rect.y + 27))
    else:
        text2 = small_font.render(f"Tempo de Corte: {current_time:.1f}s (MÁXIMO)", True, (255,215,0))
        screen.blit(text2, (cut_time_upgrade_rect.x + 10, cut_time_upgrade_rect.y + 15))
    
    # Instrução
    instruction = small_font.render("Clique nos upgrades para comprar", True, (200,200,200))
    screen.blit(instruction, (upgrade_menu_rect.x + 80, upgrade_menu_rect.y + 250))
# ================================

def draw_ui():
    # Menu button
    pygame.draw.rect(screen, (0,120,200), menu_button)
    screen.blit(font.render("Menu", True, (255,255,255)), (55,30))

    # Hammer
    hammer_color = (200,0,0) if current_mode=="demolish" else (100,100,100)
    pygame.draw.rect(screen, hammer_color, hammer_button)
    screen.blit(font.render("Martelo", True, (255,255,255)), (35,90))

    # Collect
    collect_color = (200,140,60) if current_mode=="collect" else (150,75,0)
    pygame.draw.rect(screen, collect_color, collect_button)
    screen.blit(font.render("Cortar Madeira ($5)", True, (255,255,255)), (25,150))

    # ===== NOVO: Botão de upgrades =====
    upgrade_color = (255,215,0) if current_mode=="upgrade" else (180,150,0)
    pygame.draw.rect(screen, upgrade_color, upgrade_button)
    screen.blit(font.render("Upgrades", True, (255,255,255)), (35,210))
    # ===================================

    # UI com ícones
    pygame.draw.rect(screen, (0,0,0), (SCREEN_WIDTH-250, 20, 230, 120))
    
    screen.blit(money_icon, (SCREEN_WIDTH-245, 25))
    money_text = font.render(f": ${money}", True, (255,255,255))
    screen.blit(money_text, (SCREEN_WIDTH-205, 30))
    
    screen.blit(wood_icon, (SCREEN_WIDTH-245, 55))
    wood_text = font.render(f": {wood}", True, (255,255,255))
    screen.blit(wood_text, (SCREEN_WIDTH-205, 60))
    
    # ===== NOVO: Informações de upgrade na UI =====
    # Cortes simultâneos
    cuts_text = small_font.render(f"Cortes: {len(collecting_trees)}/{upgrades.simultaneous_cuts_level}", True, (255,255,255))
    screen.blit(cuts_text, (SCREEN_WIDTH-245, 90))
    
    # Tempo de corte
    time_text = small_font.render(f"Tempo de corte: {upgrades.get_current_cut_time()/1000:.1f}s", True, (255,255,255))
    screen.blit(time_text, (SCREEN_WIDTH-245, 110))
    # ==============================================
    
    # Zoom
    zoom_text = small_font.render(f"Zoom: {zoom:.1f}x", True, (255,255,255))
    screen.blit(zoom_text, (SCREEN_WIDTH-245, 130))
    
    if selected_building:
        cost_money = buildings[selected_building]["cost_money"]
        cost_wood = buildings[selected_building]["cost_wood"]
        
        screen.blit(pygame.transform.scale(money_icon, (20, 20)), (SCREEN_WIDTH-245, 155))
        cost_money_text = small_font.render(f": ${cost_money}", True, (255,255,255))
        screen.blit(cost_money_text, (SCREEN_WIDTH-215, 157))
        
        screen.blit(pygame.transform.scale(wood_icon, (20, 20)), (SCREEN_WIDTH-140, 155))
        cost_wood_text = small_font.render(f": {cost_wood}", True, (255,255,255))
        screen.blit(cost_wood_text, (SCREEN_WIDTH-110, 157))

def draw_menu():
    pygame.draw.rect(screen, (50,50,50), menu_rect)
    pygame.draw.rect(screen, (255,255,255), menu_rect, 3)
    for name, rect in buttons:
        pygame.draw.rect(screen, (100,100,100), rect)
        
        name_text = small_font.render(f"{name}", True, (255,255,255))
        screen.blit(name_text, (rect.x+10, rect.y+5))
        
        screen.blit(pygame.transform.scale(money_icon, (15, 15)), (rect.x+10, rect.y+20))
        cost_money = buildings[name]['cost_money']
        money_text = small_font.render(f": {cost_money}", True, (255,255,255))
        screen.blit(money_text, (rect.x+30, rect.y+20))
        
        screen.blit(pygame.transform.scale(wood_icon, (15, 15)), (rect.x+80, rect.y+20))
        cost_wood = buildings[name]['cost_wood']
        wood_text = small_font.render(f": {cost_wood}", True, (255,255,255))
        screen.blit(wood_text, (rect.x+100, rect.y+20))

# ----- LOOP PRINCIPAL -----
running = True
last_income_time = pygame.time.get_ticks()

while running:

    current_time = pygame.time.get_ticks()
    dt = clock.tick(60)

    # Renda automática
    if current_time - last_income_time >= 1000:
        for row in grid:
            for cell in row:
                if cell:
                    money += buildings[cell["name"]]["income"]
        last_income_time = current_time

    # ===== MODIFICADO: Finalizar coletas múltiplas =====
    completed_trees = []
    for collecting_tree in collecting_trees:
        tree_pos = collecting_tree["pos"]
        start_time = collect_start_times[tree_pos]
        if current_time - start_time >= upgrades.get_current_cut_time():
            # Remove a árvore da lista de árvores
            for i, tree in enumerate(trees):
                if tree["pos"] == tree_pos:
                    trees.pop(i)
                    wood += 5
                    break
            completed_trees.append(collecting_tree)
    
    # Remove as árvores completadas das listas de coleta
    for tree in completed_trees:
        collecting_trees.remove(tree)
        del collect_start_times[tree["pos"]]
    # ===================================================

    # Atualiza câmera suavemente
    update_camera_smooth()

    screen.fill((200, 240, 200))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ZOOM SUAVE COM SCROLL DO MOUSE
        if event.type == pygame.MOUSEWHEEL:
            new_zoom = target_zoom + (event.y * ZOOM_SPEED)
            apply_zoom(new_zoom, mouse_x, mouse_y)

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # ===== NOVO: Botão de upgrades =====
                if upgrade_button.collidepoint(mouse_x, mouse_y):
                    current_mode = "upgrade" if current_mode != "upgrade" else "none"
                    preview_active = False
                    continue
                # ===================================

                if collect_button.collidepoint(mouse_x, mouse_y):
                    current_mode = "collect" if current_mode!="collect" else "none"
                    preview_active=False
                    continue

                if menu_button.collidepoint(mouse_x, mouse_y):
                    current_mode = "menu" if current_mode!="menu" else "none"
                    preview_active=False
                    continue

                if hammer_button.collidepoint(mouse_x, mouse_y):
                    current_mode = "demolish" if current_mode!="demolish" else "none"
                    preview_active=False
                    continue

                # ===== NOVO: Cliques no menu de upgrade =====
                if current_mode == "upgrade":
                    if simultaneous_upgrade_rect.collidepoint(mouse_x, mouse_y):
                        upgrades.upgrade_simultaneous()
                    elif cut_time_upgrade_rect.collidepoint(mouse_x, mouse_y):
                        upgrades.upgrade_cut_time()
                    continue
                # ===========================================

                if current_mode == "menu":
                    for name, rect in buttons:
                        if rect.collidepoint(mouse_x, mouse_y):
                            selected_building = name
                            current_mode="none"
                            break
                    continue

                gx, gy = get_cell_at_mouse(mouse_x, mouse_y)

                # ===== MODIFICADO: Coleta com múltiplos cortes =====
                if current_mode == "collect":
                    # Verifica se pode iniciar um novo corte
                    if len(collecting_trees) < upgrades.simultaneous_cuts_level:
                        for tree in trees:
                            if tree["pos"] == (gx, gy) and money >= COLLECT_COST:
                                # Verifica se esta árvore já não está sendo coletada
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
                    continue
                # ===================================================

                if current_mode == "demolish":
                    if 0<=gx<GRID_SIZE and 0<=gy<GRID_SIZE:
                        demolish_building(gx,gy)
                    continue

                if selected_building:
                    if 0<=gx<GRID_SIZE and 0<=gy<GRID_SIZE:
                        preview_active=True

            if event.button == 3:
                dragging=True
                last_mouse_pos = (mouse_x, mouse_y)
                last_camera_x = target_camera_x
                last_camera_y = target_camera_y

        if event.type == pygame.MOUSEBUTTONUP:

            if event.button == 3:
                dragging=False

            if event.button == 1 and preview_active:
                gx, gy = get_cell_at_mouse(mouse_x, mouse_y)
                cost_money = buildings[selected_building]["cost_money"]
                cost_wood = buildings[selected_building]["cost_wood"]

                if can_place_building(selected_building, gx, gy) and money >= cost_money and wood >= cost_wood:
                    place_building(selected_building, gx, gy)
                    money -= cost_money
                    wood -= cost_wood
                    build_sound.play()

                preview_active=False

        if event.type == pygame.MOUSEMOTION and dragging:
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

    # Desenha tudo
    draw_trees()
    draw_grid()
    if preview_active:
        draw_preview()
    draw_ui()

    if current_mode == "menu":
        draw_menu()
    elif current_mode == "upgrade":  # NOVO
        draw_upgrade_menu()

    pygame.display.flip()

pygame.quit()
sys.exit()