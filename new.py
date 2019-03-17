import sys
from random import randint

import pygame

pygame.init()

width = 500
rows = 20
scale = 10
score = 0

food_x = 240
food_y = 200

x_land = 4*(width // rows)
y_land = 2*(width // rows)

display = pygame.display.set_mode((width, width))
#bg = pygame.image.load("background.png")
pygame.display.set_caption("Intelligent Garbage Truck")
clock = pygame.time.Clock()

background = (255, 255, 255)
snake_colour = (236, 240, 241)
food_colour = (148, 49, 38)
snake_head = (247, 220, 111)


# ---------- TRUCK CLASS ------------
class Truck(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.history = [[self.x, self.y]]
        self.x_dir = 1  # starts by going right
        self.y_dir = 0
        self.history = [[self.x, self.y]]
        self.length = 1  # usunąć?

    def update(self):
        self.history[0][0] += self.x_dir*scale
        self.history[0][1] += self.y_dir*scale

    def check_eaten(self):
        if abs(self.history[0][0] - food_x) < scale and abs(self.history[0][1] - food_y) < scale:
            return True

    def check_out(self):
        if abs(self.history[0][0] - x_land) < scale and abs(self.history[0][1] - y_land) < scale:
            return True

    def displayTruck(self):
        image = pygame.image.load('garbage-truck.png')
        display.blit(image, (self.history[0][0], self.history[0][1]))

    def landout(self):
        if self.history[0][0] == width/3:
            if self.history[0][1] == width/10:
                self.info = 0  # opróżnianie




# ---------- TRASH CLASS ------------
class Trash(object):

    def trash_coord(self):
        global food_x, food_y
        x_rand = randint(20, width - 40)
        food_x = x_rand
        y_rand = randint(20, width - 40)
        food_y = y_rand

    def display_trash(self):
        image = pygame.image.load('trash.png')
        display.blit(image, (food_x, food_y))



def drawGrid(w, rows, surface):
    sizeBtwn = w // rows # width divided by no of rows = space between grid lines

    x = 0
    y = 0

    for l in range(rows):
        x = x + sizeBtwn
        y = y + sizeBtwn

        pygame.draw.line(surface, (211, 211, 211), (x, 0), (x, w)) # draw lines (black, place); vetrical, y at 0
        pygame.draw.line(surface, (211, 211, 211), (0, y), (w, y)) # horizontal, x at 0



class Landfill(object):

    def __init__(self):
        global x_land, y_land
        self.x_land = x_land
        self.y_land = y_land

    def display_landfill(self):
        image = pygame.image.load('trash(1).png')
        display.blit(image, (self.x_land, self.y_land))



def run():
    clock = pygame.time.Clock()
    count = 0
    info = 0

    landfill = Landfill()
    truck = Truck(width/2, width/2)
    trash = Trash()
    trash.trash_coord()


    flag = True
    while flag:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if truck.y_dir == 0:
                    if event.key == pygame.K_UP:
                        truck.x_dir = 0
                        truck.y_dir = -1
                    if event.key == pygame.K_DOWN:
                        truck.x_dir = 0
                        truck.y_dir = 1
                if truck.x_dir == 0:
                    if event.key == pygame.K_LEFT:
                        truck.x_dir = -1
                        truck.y_dir = 0
                    if event.key == pygame.K_RIGHT:
                        truck.x_dir = 1
                        truck.y_dir = 0




        display.fill(background)
        drawGrid(width, rows, display)

        landfill.display_landfill()
        truck.displayTruck()
        truck.update()
        trash.display_trash()

        if truck.check_eaten():
            if info == 0:
                trash.trash_coord()
                count += 1
                info = 1

        if truck.check_out():
            info = 0



        if truck.history[0][0] > width:
            truck.history[0][0] = 0
        if truck.history[0][0] < 0:
            truck.history[0][0] = width

        if truck.history[0][1] > width:
            truck.history[0][1] = 0
        if truck.history[0][1] < 0:
            truck.history[0][1] = width

        pygame.display.update()
        clock.tick(10)







run()
