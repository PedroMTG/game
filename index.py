import pygame
import sys
import random

# 🔊 CONFIGURAÇÃO DE ÁUDIO
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# ----- CONFIG -----
GRID_SIZE = 50
CELL_SIZE = 60

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("City Builder")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ----- SONS -----
build_sound = pygame.mixer.Sound("sound/build.wav")
break_sound = pygame.mixer.Sound("sound/breaking.wav")

build_sound.set_volume(0.5)
break_sound.set_volume(0.5)

# ----- IMAGENS DOS PRÉDIOS -----
building_images = {}

building_images["Casa"] = pygame.transform.scale(
    pygame.image.load("assets/casa.png").convert_alpha(),
    (CELL_SIZE, CELL_SIZE)
)

building_images["Predio"] = pygame.transform.scale(
    pygame.image.load("assets/predio.png").convert_alpha(),
    (CELL_SIZE, CELL_SIZE)
)
building_images["Lojinha"] =  pygame.transform.scale(
    pygame.image.load("assets/loja-game.png").convert_alpha(),
    (CELL_SIZE, CELL_SIZE)
)

building_images["Shopping"] =  pygame.transform.scale(
    pygame.image.load("assets/shopping-game.png").convert_alpha(),
    (CELL_SIZE, CELL_SIZE)
)

building_images["Factory"] =  pygame.transform.scale(
    pygame.image.load("assets/factory-game.png").convert_alpha(),
    (CELL_SIZE, CELL_SIZE)
)

# ----- MAPA -----
MAP_WIDTH = GRID_SIZE * CELL_SIZE
MAP_HEIGHT = GRID_SIZE * CELL_SIZE

# ----- CÂMERA -----
camera_x = 250
camera_y = 250
dragging = False
last_mouse_pos = (0, 0)

# ----- ECONOMIA -----
money = 1000
wood = 200

# ----- ÁRVORES -----
trees = []
for _ in range(500):
    trees.append((random.randint(0, GRID_SIZE-1),
                  random.randint(0, GRID_SIZE-1)))

collect_button = pygame.Rect(20, 140, 160, 40)
collecting_tree = None
collect_start_time = 0
COLLECT_TIME = 5000
COLLECT_COST = 5

# ----- PRÉDIOS -----
buildings = {
    "Casa": {"cost": 20, "color": (0, 150, 0), "income": 1, "size": (1, 1)},
    "Predio": {"cost": 50, "color": (150, 0, 0), "income": 5, "size": (1, 1)},
    "Lojinha": {"cost": 270, "color": (0, 0, 120), "income": 27, "size": (1, 1)},
    "Shopping": {"cost": 3000, "color": (120, 0, 120), "income": 670, "size": (2, 3)},
    "Factory": {"cost": 9000, "color": (120, 40, 120), "income": 900, "size": (3, 3)}
}

grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
building_id_counter = 0

# ----- MODOS -----
current_mode = "none"  # none | menu | demolish | collect
selected_building = None
preview_active = False
preview_pos = (0, 0)

# ----- MENU -----
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

# ----- FUNÇÕES -----
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
            if (x, y) in trees:
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
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(
                x*CELL_SIZE - camera_x,
                y*CELL_SIZE - camera_y,
                CELL_SIZE,
                CELL_SIZE
            )

            if rect.right < 0 or rect.left > SCREEN_WIDTH:
                continue
            if rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                continue

            # Célula vazia
            if grid[y][x] is None:
                pygame.draw.rect(screen, (200,200,200), rect)

            else:
                building_data = grid[y][x]
                building_name = building_data["name"]

                # Verifica se é a célula principal do prédio
                is_main_cell = True

                if x > 0 and grid[y][x-1] and grid[y][x-1]["id"] == building_data["id"]:
                    is_main_cell = False
                if y > 0 and grid[y-1][x] and grid[y-1][x]["id"] == building_data["id"]:
                    is_main_cell = False

                if is_main_cell:
                    if building_name in building_images:
                        image = building_images[building_name]
                        screen.blit(image, rect.topleft)
                    else:
                        pygame.draw.rect(screen, buildings[building_name]["color"], rect)

            pygame.draw.rect(screen, (0,0,0), rect, 1)

def draw_trees():
    for tx, ty in trees:
        rect = pygame.Rect(
            tx*CELL_SIZE - camera_x,
            ty*CELL_SIZE - camera_y,
            CELL_SIZE,
            CELL_SIZE
        )
        color = (255,165,0) if collecting_tree == (tx,ty) else (34,139,34)
        pygame.draw.rect(screen, color, rect)

        # for i in range(5):
        #     img = pygame.image.load(f"assets/arvore{i+1}-game.png").convert_alpha()
        #     tree_imgs.append(img)
                
def draw_preview():
    if not preview_active or not selected_building:
        return
    gx, gy = preview_pos
    width, height = buildings[selected_building]["size"]
    valid = can_place_building(selected_building, gx, gy)
    color = (0,255,0,120) if valid else (255,0,0,120)

    for y in range(gy, gy+height):
        for x in range(gx, gx+width):
            rect = pygame.Rect(
                x*CELL_SIZE - camera_x,
                y*CELL_SIZE - camera_y,
                CELL_SIZE,
                CELL_SIZE
            )
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, rect.topleft)

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

    # Money
    pygame.draw.rect(screen, (0,0,0), (SCREEN_WIDTH-200, 20, 180, 60))
    screen.blit(font.render(f"Dinheiro: {money}", True,(255,255,255)), (SCREEN_WIDTH-190,25))
    screen.blit(font.render(f"Madeira: {wood}", True,(255,255,255)), (SCREEN_WIDTH-190,50))

def draw_menu():
    pygame.draw.rect(screen, (50,50,50), menu_rect)
    pygame.draw.rect(screen, (255,255,255), menu_rect, 3)
    for name, rect in buttons:
        pygame.draw.rect(screen, (100,100,100), rect)
        text = font.render(f"{name} (${buildings[name]['cost']})", True,(255,255,255))
        screen.blit(text, (rect.x+10, rect.y+10))

# ----- LOOP -----
running = True
last_income_time = pygame.time.get_ticks()

while running:

    current_time = pygame.time.get_ticks()

    # renda automática
    if current_time - last_income_time >= 1000:
        for row in grid:
            for cell in row:
                if cell:
                    money += buildings[cell["name"]]["income"]
        last_income_time = current_time

    # finalizar coleta
    if collecting_tree and pygame.time.get_ticks() - collect_start_time >= COLLECT_TIME:
        if collecting_tree in trees:
            trees.remove(collecting_tree)
            wood += 5
        collecting_tree = None

    screen.fill((180,220,255))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    if preview_active:
        gx = (mouse_x + camera_x)//CELL_SIZE
        gy = (mouse_y + camera_y)//CELL_SIZE
        preview_pos = (gx,gy)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # BOTÕES UI
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

                if current_mode == "menu":
                    for name, rect in buttons:
                        if rect.collidepoint(mouse_x, mouse_y):
                            selected_building = name
                            current_mode="none"
                            break
                    continue

                gx = (mouse_x + camera_x)//CELL_SIZE
                gy = (mouse_y + camera_y)//CELL_SIZE

                if current_mode == "collect":
                    if (gx,gy) in trees and not collecting_tree and money>=COLLECT_COST:
                        money -= COLLECT_COST
                        collecting_tree=(gx,gy)
                        collect_start_time=pygame.time.get_ticks()
                    continue

                if current_mode == "demolish":
                    if 0<=gx<GRID_SIZE and 0<=gy<GRID_SIZE:
                        demolish_building(gx,gy)
                    continue

                if selected_building:
                    if 0<=gx<GRID_SIZE and 0<=gy<GRID_SIZE:
                        preview_active=True
                        preview_pos=(gx,gy)

            if event.button == 3:
                dragging=True
                last_mouse_pos=(mouse_x,mouse_y)

        if event.type == pygame.MOUSEBUTTONUP:

            if event.button == 3:
                dragging=False

            if event.button == 1 and preview_active:
                gx,gy=preview_pos
                cost=buildings[selected_building]["cost"]

                if can_place_building(selected_building,gx,gy) and money>=cost:
                    place_building(selected_building,gx,gy)
                    money-=cost
                    build_sound.play()

                preview_active=False

        if event.type == pygame.MOUSEMOTION and dragging:
            dx=mouse_x-last_mouse_pos[0]
            dy=mouse_y-last_mouse_pos[1]
            camera_x-=dx
            camera_y-=dy
            camera_x=max(0,min(camera_x,MAP_WIDTH-SCREEN_WIDTH))
            camera_y=max(0,min(camera_y,MAP_HEIGHT-SCREEN_HEIGHT))
            last_mouse_pos=(mouse_x,mouse_y)

    draw_grid()
    draw_trees()
    draw_preview()
    draw_ui()

    if current_mode=="menu":
        draw_menu()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()