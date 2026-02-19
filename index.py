import pygame
import sys

pygame.init()

# ----- CONFIG -----
GRID_SIZE = 50
CELL_SIZE = 60

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("City Builder")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ----- MAPA -----
MAP_WIDTH = GRID_SIZE * CELL_SIZE
MAP_HEIGHT = GRID_SIZE * CELL_SIZE

# ----- CÂMERA -----
camera_x = 0
camera_y = 0
dragging = False
last_mouse_pos = (0, 0)

# ----- ECONOMIA -----
money = 100
last_income_time = pygame.time.get_ticks()

buildings = {
    "Casa": {"cost": 20, "color": (0, 150, 0), "income": 1},
    "Fabrica": {"cost": 50, "color": (150, 0, 0), "income": 5},
    "lojinha": {"cost": 40, "color": (0, 0, 120), "income": 25}
    
}

selected_building = None
demolish_mode = False  # MODO MARTELLO

# ----- GRADE -----
grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# ----- MENU -----
menu_open = False
menu_width = 300
menu_height = 350  # altura do menu

menu_rect = pygame.Rect(
    SCREEN_WIDTH // 2 - menu_width // 2,
    SCREEN_HEIGHT // 2 - menu_height // 2,
    menu_width,
    menu_height
)

menu_button = pygame.Rect(20, 20, 120, 40)
hammer_button = pygame.Rect(20, 80, 120, 40)  # botão de martelo fora do menu, abaixo do menu

# Criar botões do menu (posição relativa ao menu)
buttons = []
y_offset = 80
for name in buildings:
    rect = pygame.Rect(
        menu_rect.x + 50,
        menu_rect.y + y_offset,
        200,
        40
    )
    buttons.append((name, rect))
    y_offset += 50

# ----- FUNÇÕES -----

def draw_grid():
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(
                x * CELL_SIZE - camera_x,
                y * CELL_SIZE - camera_y,
                CELL_SIZE,
                CELL_SIZE
            )

            if rect.right < 0 or rect.left > SCREEN_WIDTH:
                continue
            if rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                continue

            if grid[y][x] is None:
                pygame.draw.rect(screen, (200, 200, 200), rect)
            else:
                pygame.draw.rect(screen, buildings[grid[y][x]]["color"], rect)

            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

def draw_menu_button():
    pygame.draw.rect(screen, (0, 120, 200), menu_button)
    text = font.render("Menu", True, (255, 255, 255))
    screen.blit(text, (menu_button.x + 35, menu_button.y + 10))

def draw_hammer_button():
    color = (200, 0, 0) if demolish_mode else (100, 100, 100)
    pygame.draw.rect(screen, color, hammer_button)
    text = font.render("Martelo", True, (255, 255, 255))
    screen.blit(text, (hammer_button.x + 15, hammer_button.y + 10))

def draw_money():
    money_text = font.render(f"Dinheiro: {money}", True, (255, 255, 255))
    pygame.draw.rect(screen, (0, 0, 0), (SCREEN_WIDTH - 160, 20, 140, 30))
    screen.blit(money_text, (SCREEN_WIDTH - 150, 25))

def draw_menu():
    pygame.draw.rect(screen, (50, 50, 50), menu_rect)
    pygame.draw.rect(screen, (255, 255, 255), menu_rect, 3)

    money_text = font.render(f"Dinheiro: {money}", True, (255, 255, 255))
    screen.blit(money_text, (menu_rect.x + 80, menu_rect.y + 30))

    for name, rect in buttons:
        pygame.draw.rect(screen, (100, 100, 100), rect)
        text = font.render(f"{name} (${buildings[name]['cost']})", True, (255, 255, 255))
        screen.blit(text, (rect.x + 10, rect.y + 10))

# ----- LOOP PRINCIPAL -----
running = True
while running:

    current_time = pygame.time.get_ticks()

    # Sistema de renda
    if current_time - last_income_time >= 1000:
        total_income = 0
        for row in grid:
            for cell in row:
                if cell is not None:
                    total_income += buildings[cell]["income"]

        money += total_income
        last_income_time = current_time

    screen.fill((180, 220, 255))

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # BOTÃO DIREITO PARA ARRASTAR
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if event.button == 3:
                dragging = True
                last_mouse_pos = (mouse_x, mouse_y)

            # BOTÃO ESQUERDO
            if event.button == 1:

                # Botão de menu
                if menu_button.collidepoint(mouse_x, mouse_y):
                    menu_open = not menu_open
                    continue

                # Botão de martelo
                if hammer_button.collidepoint(mouse_x, mouse_y):
                    demolish_mode = not demolish_mode
                    continue

                # Se o menu está aberto
                if menu_open:
                    clicked_menu = False
                    for name, rect in buttons:
                        if rect.collidepoint(mouse_x, mouse_y):
                            selected_building = name
                            demolish_mode = False  # desativa martelo
                            menu_open = False
                            clicked_menu = True
                            break
                    if clicked_menu:
                        continue  # não constrói no mesmo clique

                # Construção ou demolir no grid
                grid_x = (mouse_x + camera_x) // CELL_SIZE
                grid_y = (mouse_y + camera_y) // CELL_SIZE

                if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                    if demolish_mode and grid[grid_y][grid_x] is not None:
                        b = grid[grid_y][grid_x]
                        refund = buildings[b]["cost"] // 3
                        money += refund
                        grid[grid_y][grid_x] = None
                    elif selected_building and grid[grid_y][grid_x] is None:
                        cost = buildings[selected_building]["cost"]
                        if money >= cost:
                            grid[grid_y][grid_x] = selected_building
                            money -= cost

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                dragging = False

        if event.type == pygame.MOUSEMOTION:
            if dragging:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - last_mouse_pos[0]
                dy = mouse_y - last_mouse_pos[1]

                camera_x -= dx
                camera_y -= dy

                camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))
                camera_y = max(0, min(camera_y, MAP_HEIGHT - SCREEN_HEIGHT))

                last_mouse_pos = (mouse_x, mouse_y)

    # Desenhar elementos
    draw_grid()
    draw_menu_button()
    draw_hammer_button()
    draw_money()

    if menu_open:
        draw_menu()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
