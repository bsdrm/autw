import pygame
import random
from random import randint
import numpy as np
from heapq import *
from pyke import knowledge_engine

EMPTY = 0
TRUCK = 1
TRASH = 2
LANDFILL = 3
HOUSE = 4

BOARD = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 3, 8, 8, 3, 8, 8, 3, 8, 8, 3, 0, 6, 0, 0, 0, 0, 0],  # (2, 3/6/9/12) - landfills
    [0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 8, 9, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 7, 0, 0, 0, 6, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 5, 0, 7, 0, 0, 6, 0, 0, 0, 9, 0, 0, 0, 0, 0],  # (5, 16) - house
    [0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 6, 8, 0, 0, 4, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 7, 5, 0, 7, 0, 6, 6, 0, 0, 4, 4, 0, 0, 0],
    [0, 0, 0, 4, 4, 0, 9, 0, 0, 0, 7, 6, 0, 0, 0, 0, 0, 0, 0, 0],  # (8, 3) - house
    [0, 0, 0, 4, 4, 2, 0, 0, 7, 8, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 8, 0, 0, 9, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 5, 7, 0, 7, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0],  # (11, 13) - house
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 2, 4, 4, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 9, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # (13, 8) -truck
    [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 9, 0, 6, 0, 9, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 6, 0, 0, 9, 0, 0, 0],
    [0, 0, 0, 0, 0, 4, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # (16, 5) - house
    [0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
])

WIDTH = 20  # width of our game window
FPS = 10 # frames per second

CELL_WIDTH = 20
width = WIDTH * CELL_WIDTH

pygame.init()
pygame.mixer.init()  # for sound
screen = pygame.display.set_mode((width, width))
pygame.display.set_caption("Autonomous Garbage Truck")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

scale = 10
score = 0

p = ''

data = []

truck_img = pygame.image.load('garbage-truck.png').convert()
house_img = pygame.image.load('house(2).png').convert()
trash_img = pygame.image.load('trash.png').convert()
landfill_img = pygame.image.load('trash(1).png').convert()

all_sprites = pygame.sprite.Group()
truck_sprite = pygame.sprite.Group()

class Truck(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = truck_img
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 0
        self.full = 0
        self.path = []
        self.path_len = len(self.path) - 1
        self.pierw = (13, 8)
        self.drug = (12, 12)

    def update(self, d):
        if d == 'right':
            self.rect.x += 20
        elif d == 'left':
            self.rect.x += -20
        elif d == "up":
            self.rect.y += -20
        elif d == "down":
            self.rect.y += 20

    def check_eaten(self, x, y):
        if self.rect.y/20 - x == 0 and self.rect.x/20 - y == 0:
            return True

    def which_package(self, packages, t):
        engine = knowledge_engine.engine(__file__)
        engine.activate('trash_info')
        global p

        for package in packages:
            engine.assert_('packages', 'package', (package,))

        try:
            vals, plans = engine.prove_1_goal('trash_info.packages($type, $smell, $where, $weight)', smell=t.smell, where=t.where, weight=t.weight)
            p = vals['type']
        except knowledge_engine.CanNotProve:
            print("No package applies")
        engine.reset()
                
            

class House(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = house_img
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x + 3, y + 8)

class Trash(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = trash_img
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)

    def rand(self):
        y = []
        with open('trash.txt') as f:
            for line in f:
                y.append(line.split())
        l = len(y)

        rand = randint(0, l - 1)
        for i in y[rand]:
            self.where = y[rand][1]
            self.weight = y[rand][2]
            self.smell = int(y[rand][3])

class Landfill(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = landfill_img
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.topleft = (x, y) #+3+8
    
        

def drawGrid():
    a = 0
    b = 0

    for l in range(WIDTH):
        a = a + CELL_WIDTH
        b = b + CELL_WIDTH
        pygame.draw.line(screen, (211, 211, 211), (a, 0), (a, width))
        pygame.draw.line(screen, (211, 211, 211), (0, b), (width, b))

def heuristic(a, b):
    return abs(b[0] - a[0]) + abs(b[1] - a[1])

def current_neighbors(current):
    neighbors = []
    kw = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for i, j in kw:
        element = (current[0] + i, current[1] + j)
        if BOARD[element] != 4:
            neighbors.append(element)
    return neighbors

def astar(array, start, goal):

    #neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    close_set = set()
    came_from = {}
    gscore = {start:0}
    fscore = {start:heuristic(start, goal)}
    oheap = []

    heappush(oheap, (fscore[start], start))
    
    while oheap:

        current = heappop(oheap)[1]

        if current == goal:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            return data
        
        neighbors = current_neighbors(current)

        close_set.add(current)
        for i in neighbors:
            neighbor = i           
            tentative_g_score = gscore[current] + heuristic(current, neighbor)
            if 0 <= neighbor[0] < array.shape[0]:
                if 0 <= neighbor[1] < array.shape[1]:                
                    if array[neighbor[0]][neighbor[1]] == 1:
                        continue
                else:
                    # array bound y walls
                    continue
            else:
                # array bound x walls
                continue
                
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue
                
            if  tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1]for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score + BOARD[neighbor]
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heappush(oheap, (fscore[neighbor], neighbor))


def score_update(w):
    myfont = pygame.font.SysFont('arial', 15)
    textsurface = myfont.render("Score: " + str(w), True, (0, 0, 0))
    screen.blit(textsurface, (0, 0))

def landf_update(z):
    myfont = pygame.font.SysFont('arial', 15)
    textsurface = myfont.render("Type of trash: " + z, True, (250, 0, 0))
    screen.blit(textsurface, (10, 375))

font_name = pygame.font.match_font('arial')
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x+9, y-13)
    surf.blit(text_surface, text_rect)



truck = Truck(8 * CELL_WIDTH, 13 * CELL_WIDTH)
truck_sprite.add(truck)

h1 = House(3 * CELL_WIDTH, 8 * CELL_WIDTH)
h2 = House(13 * CELL_WIDTH, 11 * CELL_WIDTH)
h3 = House(15 * CELL_WIDTH, 6 * CELL_WIDTH)
all_sprites.add(h1)
all_sprites.add(h2)
all_sprites.add(h3)

plastic = Landfill(3 * CELL_WIDTH, 2 * CELL_WIDTH)
paper = Landfill(6 * CELL_WIDTH, 2 * CELL_WIDTH)
bio = Landfill(9 * CELL_WIDTH, 2 * CELL_WIDTH)
glass = Landfill(12 * CELL_WIDTH, 2 * CELL_WIDTH)



all_sprites.add(plastic)
all_sprites.add(paper)
all_sprites.add(bio)
all_sprites.add(glass)

trashes = []
trash1 = Trash(5 * CELL_WIDTH, 9 * CELL_WIDTH)
trash1.rand()
trash2 = Trash(12 * CELL_WIDTH, 12 * CELL_WIDTH)
trash2.rand()
trash3 = Trash(17 * CELL_WIDTH, 7 * CELL_WIDTH)
trash3.rand()
trashes.append(trash1)
trashes.append(trash2)
trashes.append(trash3)
all_sprites.add(trash1)
all_sprites.add(trash2)
all_sprites.add(trash3)

i = 0



running = True
while running:



    
    clock.tick(FPS)
    
    # Rrocess input / events
    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False

    start = (int(truck.rect.y/20), int(truck.rect.x/20))
    
    if truck.full == 0:
        rand = randint(0, 2)
        if rand == 0:
            full_route = (astar(BOARD, start, (int(trash1.rect.y/20), int(trash1.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 1
        elif rand == 1:
            full_route = (astar(BOARD, start, (int(trash2.rect.y/20), int(trash2.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 1
        elif rand == 2:
            full_route = (astar(BOARD, start, (int(trash3.rect.y/20), int(trash3.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 1
        

    if truck.full == 1 :
        if truck.check_eaten(int(trash1.rect.y/20), int(trash1.rect.x/20)):
            truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash1)
            trash1.rand()
            truck.full = 2

        if truck.check_eaten(int(trash2.rect.y/20), int(trash2.rect.x/20)):
            truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash2)
            trash2.rand()
            truck.full = 2

        if truck.check_eaten(int(trash3.rect.y/20), int(trash3.rect.x/20)):
            truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash3)
            trash3.rand()
            truck.full = 2

    if truck.full == 2:
        if p == 'glass':
            full_route = (astar(BOARD, start, (int(glass.rect.y/20), int(glass.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 3

        if p == 'plastic':
            full_route = (astar(BOARD, start, (int(plastic.rect.y/20), int(plastic.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 3

        if p == 'bio':
            full_route = (astar(BOARD, start, (int(bio.rect.y/20), int(bio.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 3

        if p == 'paper':
            full_route = (astar(BOARD, start, (int(paper.rect.y/20), int(paper.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 3


    if truck.full == 3:
        if p == 'glass':
            if glass.rect.y - truck.rect.y <= 20 and glass.rect.y - truck.rect.y >= -20 and glass.rect.x - truck.rect.x <= 20 and glass.rect.x - truck.rect.x >= -20 :
                truck.full = 0
                score += 1
                    
        if p == 'plastic':
            if plastic.rect.y - truck.rect.y <= 20 and plastic.rect.y - truck.rect.y >= -20 and plastic.rect.x - truck.rect.x <= 20 and plastic.rect.x - truck.rect.x >= -20:
                truck.full = 0
                score += 1

        if p == 'bio':
            if bio.rect.y - truck.rect.y <= 20 and bio.rect.y - truck.rect.y >= -20 and bio.rect.x - truck.rect.x <= 20 and bio.rect.x - truck.rect.x >= -20:
                truck.full = 0
                score += 1

        if p == 'paper':
            if paper.rect.y - truck.rect.y <= 20 and paper.rect.y - truck.rect.y >= -20 and paper.rect.x - truck.rect.x <= 20 and paper.rect.x - truck.rect.x >= -20:
                truck.full = 0
                score += 1


    d = ''

    if truck.path_len:
        move = truck.path[0]
        x = move[0] * CELL_WIDTH
        y = move[1] * CELL_WIDTH
        
        if (y - truck.rect.x)/20 == -1:
            d = "left"
            del truck.path[0]
        elif (y - truck.rect.x)/20 == 1:
            d = "right"
            del truck.path[0]
        elif (x - truck.rect.y)/20 == -1:
            d = "up"
            del truck.path[0]
        elif (x - truck.rect.y)/20 == 1:
            d = "down"
            del truck.path[0]
        truck_sprite.update(d)
    

   
    # Update
    all_sprites.update()
    


    # Draw / render
    screen.fill(WHITE)
    drawGrid()
    all_sprites.draw(screen)
    truck_sprite.draw(screen)
    landf_update(p)
    score_update(score)
    draw_text(screen, "PLASTIC", 12, plastic.rect.x, plastic.rect.y)
    draw_text(screen, "PAPER", 12, paper.rect.x, paper.rect.y)
    draw_text(screen, "BIO", 12, bio.rect.x, bio.rect.y)
    draw_text(screen, "GLASS", 12, glass.rect.x, glass.rect.y)
    
    
    pygame.display.flip()

pygame.quit()
