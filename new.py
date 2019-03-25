import sys
from random import randint
from pyke import knowledge_engine

import pygame

pygame.init()

width = 500
rows = 20
scale = 10
score = 0

x_land = 0
y_land = 0

p = ''

r=width // rows
count = 0

display = pygame.display.set_mode((width, width))
pygame.display.set_caption("Intelligent Garbage Truck")
clock = pygame.time.Clock()

background = (255, 255, 255)

class Truck(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.x_dir = 1  # starts by going right
        self.y_dir = 0
        self.history = [[self.x, self.y]]

    def update(self):
        self.history[0][0] += self.x_dir*scale
        self.history[0][1] += self.y_dir*scale

    def check_eaten(self, x, y):
        if abs(self.history[0][0] - x) < scale and abs(self.history[0][1] - y) < scale:
            return True

    def check_out(self, x, y):
        if abs(self.history[0][0] - x) < scale and abs(self.history[0][1] - y) < scale:
            return True

    def displayTruck(self):
        image = pygame.image.load('garbage-truck.png')
        display.blit(image, (self.history[0][0], self.history[0][1]))

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


class Trash(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def rand(self):
        y = []
        with open('trash.txt') as f:
            for line in f:
                y.append(line.split())
        l = len(y)

        rand = randint(0, l - 1)
        print(rand)
        print(y[rand][2])
        for i in y[rand]:
            self.where = y[rand][1]
            self.weight = y[rand][2]
            self.smell = int(y[rand][3])

    def display_trash(self, truck):
        if truck.check_eaten(self.x, self.y):
            clock.tick(15)
            image = pygame.image.load('trash(3).png')
        else:
            image = pygame.image.load('trash.png')
        display.blit(image, (self.x, self.y))


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

    def __init__(self, x_land, y_land):
        self.x_land = x_land
        self.y_land = y_land


class PlasticL(Landfill):
    def display_landfill(self):
        image = pygame.image.load('trash(1).png')
        display.blit(image, (self.x_land, self.y_land))
        myfont = pygame.font.SysFont('arial', 12)
        textsurface = myfont.render('PLASTIC', True, (0, 0, 0))
        display.blit(textsurface, (self.x_land-12, self.y_land-15))


class PaperL(Landfill):
    def display_landfill(self):
        image = pygame.image.load('trash(1).png')
        display.blit(image, (self.x_land, self.y_land))
        myfont = pygame.font.SysFont('arial', 12)
        textsurface = myfont.render('PAPER', True, (0, 0, 0))
        display.blit(textsurface, (self.x_land - 10, self.y_land - 15))


class BioL(Landfill):
    def display_landfill(self):
        image = pygame.image.load('trash(1).png')
        display.blit(image, (self.x_land, self.y_land))
        myfont = pygame.font.SysFont('arial', 12)
        textsurface = myfont.render('BIO', True, (0, 0, 0))
        display.blit(textsurface, (self.x_land, self.y_land - 15))


class GlassL(Landfill):
    def display_landfill(self):
        image = pygame.image.load('trash(1).png')
        display.blit(image, (self.x_land, self.y_land))
        myfont = pygame.font.SysFont('arial', 12)
        textsurface = myfont.render('GLASS', True, (0, 0, 0))
        display.blit(textsurface, (self.x_land - 7, self.y_land - 15))


def score_update(w):
    myfont = pygame.font.SysFont('arial', 15)
    textsurface = myfont.render("Score: " + str(w), True, (0, 0, 0))
    display.blit(textsurface, (0, 0))


def current(w):
    myfont = pygame.font.SysFont('arial', 20)
    textsurface = myfont.render("Type of trash: " + w, True, (250, 0, 0))
    display.blit(textsurface, (5, 470))


class House(object):
    def display_house(self, a, b):
        image = pygame.image.load('house(2).png')
        display.blit(image, (a, b))

def run():
    global count
    global p
    clock = pygame.time.Clock()
    info = 0


    plastic_landfill = PlasticL(4*r, 2*r)
    paper_landfill = PaperL(7*r, 2*r)
    bio_landfill = BioL(10*r, 2*r)
    glass_landfill = GlassL(13*r, 2*r)
    truck = Truck(width/2, width/2)
    trash1 = Trash(14.2*r, 6.4*r)
    trash1.rand()
    trash2 = Trash(4.4 * r, 11.4 * r)
    trash2.rand()
    trash3 = Trash(11.2 * r, 16.4 * r)
    trash3.rand()
    trash4 = Trash(16.2 * r, 10.4 * r)
    trash4.rand()
    house1 = House()
    house2 = House()
    house3 = House()
    house4 = House()


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

        house1.display_house((15*r), (5.8*r))
        house2.display_house((3 * r), (10.8 * r))
        house3.display_house((12 * r), (15.8 * r))
        house4.display_house((17 * r), (9.8 * r))

        plastic_landfill.display_landfill()
        paper_landfill.display_landfill()
        glass_landfill.display_landfill()
        bio_landfill.display_landfill()

        truck.displayTruck()
        truck.update()

        trash1.display_trash(truck)
        trash2.display_trash(truck)
        trash3.display_trash(truck)
        trash4.display_trash(truck)

        score_update(count)


        if truck.check_eaten(trash1.x, trash1.y):
            if info == 0:
                truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash1)
                info = 1
                trash1.rand()

        if truck.check_eaten(trash2.x, trash2.y):
            if info == 0:
                truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash2)
                info = 1
                trash2.rand()

        if truck.check_eaten(trash3.x, trash3.y):
            if info == 0:
                truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash3)
                info = 1
                trash3.rand()

        if truck.check_eaten(trash4.x, trash4.y):
            if info == 0:
                truck.which_package(['glass', 'bio', 'paper', 'heavy plastic parts', 'plastic bottles', 'paper food packaging'], trash4)
                info = 1
                trash4.rand()

        current(p)

        if truck.check_out(glass_landfill.x_land, glass_landfill.y_land):
            if p == 'glass':
                info = 0
                count += 1

        if truck.check_out(plastic_landfill.x_land, plastic_landfill.y_land):
            if p == 'plastic':
                info = 0
                count += 1

        if truck.check_out(bio_landfill.x_land, bio_landfill.y_land):
            if p == 'bio':
                info = 0
                count += 1

        if truck.check_out(paper_landfill.x_land, paper_landfill.y_land):
            if p == 'paper':
                info = 0
                count += 1

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
