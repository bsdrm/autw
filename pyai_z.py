import pygame
import random
from random import randint
import numpy as np
from heapq import *
from pyke import knowledge_engine
import os
import copy
import csv
from math import log2, fsum, inf

EMPTY = 0
TRUCK = 1
TRASH = 2
LANDFILL = 3
HOUSE = 4
FACTORY = 5

BOARD = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 3, 8, 8, 3, 8, 8, 3, 8, 8, 3, 0, 6, 0, 3, 0, 0, 0],  # (2, 3/6/9/12/15) - landfills
    [0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 8, 9, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 7, 0, 0, 0, 6, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 6, 0, 7, 0, 0, 6, 0, 0, 0, 9, 0, 0, 0, 0, 0],  # (5, 16) - house
    [0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 6, 8, 0, 0, 4, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 7, 6, 0, 7, 0, 6, 6, 0, 0, 4, 4, 0, 0, 0],
    [0, 0, 0, 4, 4, 0, 9, 0, 0, 0, 7, 6, 0, 0, 0, 0, 0, 0, 0, 0],  # (8, 3) - house
    [0, 0, 0, 4, 4, 2, 0, 0, 7, 8, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 8, 0, 0, 9, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 6, 7, 0, 7, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0],  # (11, 13) - house
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 2, 4, 4, 0, 0, 0, 0, 0],
    [0, 0, 0, 5, 5, 5, 6, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # (13, 8) -truck
    [0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0, 9, 0, 6, 0, 9, 0, 0, 0, 0],
    [0, 0, 0, 5, 5, 5, 5, 9, 0, 0, 0, 0, 0, 6, 0, 0, 9, 0, 0, 0],
    [0, 0, 0, 5, 5, 5, 5, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # (16, 5) - house
    [0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # (17, 7)
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
factory_img = pygame.image.load('factory(3).png').convert()
waste_img = pygame.image.load('toxic(1).png').convert_alpha()

all_sprites = pygame.sprite.Group()
truck_sprite = pygame.sprite.Group()

class Utilities:
	'Utility functions'

	#Entropy (true with probability q)
	B = lambda q : q if q == 0.0 else -1 * (q * log2(q) + (((1 - q) * log2(1 - q)) if q < 1 else 0))

	#Remainder(A) will be the sum of this computation for each subset.
	#counts - counts tuple (p, n, pk, nk)
	ExpectedEntropy = lambda counts : ((counts[2] + counts[3])/(counts[0] + counts[1])) * Utilities.B((counts[2]/(counts[2] + counts[3])) if (counts[2] + counts[3] > 0) else 0)

	#floating point sum of the elements in list
	Sum = lambda list : fsum(list)

	#Remainder(A) calculation
	#subsets has the list of count arrays of each subset of example on splitting with Attribute A
	Remainder = lambda subsets : Utilities.Sum(map(Utilities.ExpectedEntropy, subsets))

	#Gain calculation
	Gain = lambda p, n, subsets : Utilities.B(p/(p + n)) - Utilities.Remainder(subsets)

class DTNode:
	'Node of the Decision Tree'

	def __init__(self, parent, pk, nk, nodeType, attributeName=None, attributeIndex=-1, classification=None):
		self.parent = parent
		self.p = pk
		self.n = nk
		self.type = nodeType
		if(self.type == 'testNode'):
			self.attributeName = attributeName
			self.attributeIndex = attributeIndex
		else:
			self.classification = classification
		self.branches = {} #key of branches will be the different values for the attribute

class DecisionTree:
	def __init__(self, dataset):
		i = 0
		self.examples = []
		for row in dataset:
			if(i == 0):
				i = 1
				self.attributes = copy.deepcopy(row)
			else:
				self.examples.append(copy.deepcopy(row))
		
		self.attributeValues = self.getAttributeValues(self.attributes, self.examples)
		targetVals = self.attributeValues[self.attributes[len(self.attributes) - 1]]
		self.pValue, self.nValue = targetVals[0], targetVals[1]
		self.p, self.n = self.getClassCount(self.examples)
		self.takenAttributes = []


	def DTL(self, examples, attributes, parent, parentExamples):
		if(len(examples) == 0):
			#return a leaf node with the majority class value in parent examples
			return self.pluralityValue(parent, parentExamples)
		elif(self.hasSameClass(examples)):
			#return a leaf node with the class value
			p, n = self.getClassCount(examples)
			return DTNode(parent, p, n, 'leafNode', classification = self.pValue if p > 0 else self.nValue)
		elif((len(attributes) - len(self.takenAttributes)) == 0):
			#return a leaf node with the majority class value in examples
			return self.pluralityValue(parent, examples)
		else:
			#find the attribute that has max information gain
			attrIndex = self.importantAttrIndex(attributes, examples)
			attribute = attributes[attrIndex]
			p, n = self.getClassCount(examples)

			#create a root node
			root = DTNode(parent, p, n, 'testNode', attributeName = attribute, attributeIndex = attrIndex)
			#to track the attributes in inner nodes
			self.takenAttributes.append(attribute)

			#divide the examples and recursively call DTL to create child nodes
			for value in self.attributeValues[attribute]:
				newExample = []
				for row in examples:
					if(row[attrIndex] == value):
						newExample.append(copy.deepcopy(row))
				childNode = self.DTL(newExample, attributes, root, examples)

				#add the sub tree to the main tree
				root.branches[value] = childNode

		return root



	def importantAttrIndex(self, attributes, examples):
		'''
		Calculate the information gain for all attributes
		Return the attribute with max gain
		'''
		maxVal = -inf
		maxValInd = -1
		
		for index, a in enumerate(attributes[:len(attributes) - 1]):
			if(a not in self.takenAttributes):
				gain = self.importance(a, index, examples)
				if(gain > maxVal):
					maxVal = gain
					maxValInd = index

		return maxValInd


	def importance(self, attribute, index, examples):
		'''
		Calculate the gain for a given attribute
		'''
		subsets = []

		for value in self.attributeValues[attribute]:
			pk = nk = 0
			for row in examples:
				if(row[index] == value):
					if(row[len(row) - 1] == self.pValue):
						pk += 1
					else:
						nk += 1

			subsets.append((self.p, self.n, pk, nk))

		return Utilities.Gain(self.p, self.n, subsets)


	def getAttributeValues(self, attributes, examples):
		'''
		To find the domain values for each attribute
		'''
		values = {}

		for index, a in enumerate(attributes):
			temp = []
			for row in examples:
				if(row[index] not in temp):
					temp.append(row[index])
			values[a] = temp

		return values


	def hasSameClass(self, examples):
		'''
		Checks if the examples have the same target variable value
		'''
		prevValue = examples[0][len(examples[0]) - 1]
		
		for row in examples[1:]:
			if(row[len(row) - 1] != prevValue):
				return False

		return True

	def pluralityValue(self, parent, examples):
		'''
		Returns a leaf node with majority class value
		'''
		p, n = self.getClassCount(examples)
		return DTNode(parent, p, n, 'leafNode', classification = self.pValue if p > n else self.nValue)

	def getClassCount(self, examples):
		'''
		Returns the number of examples in positive and negative classes
		'''
		p = n = 0

		for row in examples:
			if(row[len(row) - 1] == self.pValue):
				p += 1
			elif(row[len(row) - 1] == self.nValue):
				n += 1

		return p, n

	def printDTree(self, node, value=None):
    
		print('If parent - ', node.parent.attributeName if node.parent else 'This is Root Node', ' = ', value if value else 'This is Root Node',
																											 ' | test node - ', node.attributeName)

		for branch in node.branches:
			if(node.branches[branch].type == 'leafNode'):
				print('If parent - ', node.branches[branch].parent.attributeName, ' = ', branch if branch else 'This is Root Node', ' | leaf node - ', 
																													node.branches[branch].classification)

		for branch in node.branches:
			if(node.branches[branch].type == 'testNode'):
				self.printDTree(node.branches[branch], branch)

	def traverseTree(self, test, node):
		'''
		Traverses the tree to classify the test data
		'''
		attributeValue = test[node.attributeName]
		if(node.branches[attributeValue].type == 'leafNode'):
			return node.branches[attributeValue].classification
		else:
			return self.traverseTree(test, node.branches[attributeValue])


	def predict(self, testSet):
		'''
		Returns the prediction for all the test data
		'''
		predictions = []
		for index, row in enumerate(testSet):
			if (index == 0):
				continue
			test = {}

			for index, data in enumerate(row):
				test[self.attributes[index]] = data

			predictions.append(self.traverseTree(test, self.root))

		return predictions

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

class Factory(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = factory_img
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

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
    
class Waste(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = waste_img
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)      

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

def decision():
    decisionTree = None
    with open('pl_train.csv') as csvFile:
        dataset = csv.reader(csvFile, delimiter=',')
        decisionTree = DecisionTree(dataset)


        decisionTree.root = decisionTree.DTL(decisionTree.examples, decisionTree.attributes, None, decisionTree.examples)

        decisionTree.printDTree(decisionTree.root)


        with open('pl_test.csv') as csvTest:
            testSet = csv.reader(csvTest, delimiter=',')
            predictions = decisionTree.predict(testSet)
            return predictions


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
nontoxic = Landfill(16 * CELL_WIDTH, 2 * CELL_WIDTH)

waste = Waste(15 * CELL_WIDTH, 15 * CELL_WIDTH)

all_sprites.add(plastic)
all_sprites.add(paper)
all_sprites.add(bio)
all_sprites.add(glass)
all_sprites.add(nontoxic)
all_sprites.add(waste)

factory = Factory(3 * CELL_WIDTH, 13 * CELL_WIDTH)
all_sprites.add(factory)

trashes = []
trash1 = Trash(5 * CELL_WIDTH, 9 * CELL_WIDTH)
trash1.rand()
trash2 = Trash(12 * CELL_WIDTH, 12 * CELL_WIDTH)
trash2.rand()
trash3 = Trash(17 * CELL_WIDTH, 7 * CELL_WIDTH)
trash3.rand()
trash4 = Trash(7 * CELL_WIDTH, 15 * CELL_WIDTH)
trashes.append(trash1)
trashes.append(trash2)
trashes.append(trash3)
trashes.append(trash4)
all_sprites.add(trash1)
all_sprites.add(trash2)
all_sprites.add(trash3)
all_sprites.add(trash4)

pred = decision()

def dec_check(meh):
    global pred
    global p
    if pred[meh] == 'yes':
        p = 'toxic'
    if pred[meh] == 'no':
        p = 'nontoxic'


i = 0
zed = ''


running = True
while running:



    
    clock.tick(FPS)
    
    # Rrocess input / events
    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False

    start = (int(truck.rect.y/20), int(truck.rect.x/20))
    #full_route = (astar(BOARD, start, (int(trash2.rect.y/20), int(trash2.rect.x/20))))

    

    if truck.full == 0:
        rand = 3 #randint(0, 3)
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
        elif rand == 3:
            full_route = (astar(BOARD, start, (int(trash4.rect.y/20), int(trash4.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 1
        


    if truck.full == 1 :
        rand = randint(0, 82)

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

        if truck.check_eaten(int(trash4.rect.y/20), int(trash4.rect.x/20)):
            print(pred[rand])
            dec_check(rand)
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

        if p == 'nontoxic':
            full_route = (astar(BOARD, start, (int(nontoxic.rect.y/20), int(nontoxic.rect.x/20))))
            truck.path = full_route[::-1]
            truck.full = 3

        if p == 'toxic':
            full_route = (astar(BOARD, start, (int(waste.rect.y/20), int(waste.rect.x/20))))
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

        if p == 'nontoxic':
            if nontoxic.rect.y - truck.rect.y <= 20 and nontoxic.rect.y - truck.rect.y >= -20 and nontoxic.rect.x - truck.rect.x <= 20 and nontoxic.rect.x - truck.rect.x >= -20:
                truck.full = 0
                score += 1

        if p == 'toxic':
            if waste.rect.y - truck.rect.y <= 20 and waste.rect.y - truck.rect.y >= -20 and waste.rect.x - truck.rect.x <= 20 and waste.rect.x - truck.rect.x >= -20:
                truck.full = 0
                score += 1



    
    '''
    if truck.full == 3:
        if p == 'glass':
            if truck.check_eaten(int(glass.rect.y/20), int(glass.rect.x/20)):
                truck.full = 0
                score += 1

        if p == 'plastic':
            if truck.check_eaten(int(plastic.rect.y/20), int(plastic.rect.x/20)):
                truck.full = 0
                score += 1

        if p == 'bio':
            if truck.check_eaten(int(bio.rect.y/20), int(bio.rect.x/20)):
                truck.full = 0
                score += 1

        if p == 'paper':
            if truck.check_eaten(int(paper.rect.y/20), int(paper.rect.x/20)):
                truck.full = 0
                score += 1
    '''


   
        

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
    draw_text(screen, "NONTOXIC", 12, nontoxic.rect.x, nontoxic.rect.y)
    draw_text(screen, "TOXIC", 12, waste.rect.x, waste.rect.y)

    
    pygame.display.flip()

pygame.quit()
