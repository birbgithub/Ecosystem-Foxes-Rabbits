import pygame
import random
import math
import noise
import pathfinding
from pygame.math import Vector2

# ---MAIN FILE OF THE PROJECT---
# Contains:
# - animal and plant behaviour functions
# - simulation loop


# finds random position within map borders
# - returns position as Vector2
def randomPos():
    x = random.randint(0, mapWidth - 1)  # random x
    y = random.randint(0, mapHeight - 1)  # random y
    return Vector2(x, y)  # return (x, y) as Vector2


# finds and returns random position in a square,
# takes inputs for centre of square and the distance from the centre to the edges
def randomPosInSquare(pos, hWidth):
    return Vector2(pos.x + random.randint(-hWidth, hWidth), pos.y + random.randint(-hWidth, hWidth))

# layer name input, index of coordinate list output - for ease of use
layerDic = {
    "snow": 0,
    "mountain peak": 1,
    "mountain upper": 2,
    "mountain middle": 3,
    "mountain lower": 4,
    "forest": 5,
    "grassland": 6,
    "sand": 7,
    "dry sand": 8,
    "wet sand": 9,
    "shallow water": 9,
    "deep water": 10,
    "deepest water": 11
}


# finds random position in layer of terrain
# takes input for layer
def randomPositionFromLayer(layer):
    positions = layerCoordinates[layerDic[layer]]  # get list of coordinates in layer
    return random.choice(positions)  # output random position from layer


# checks if position can be traversed
# takes input for position, returns boolean (true if traversable - false if untraversable)
def isTraversable(pos):
    pos = Vector2(int(pos.x), int(pos.y))
    return pos in traversableCoordinates


# finds and returns random traversable position
def randomTraversablePos():
    return random.choice(traversableCoordinates)


# calculates distance between two points
def pythagoras(x1, y1, x2, y2):
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


# converts input position to grid position
def posToGrid(pos):
    gridPos = pos / gridScale
    return Vector2(int(gridPos.x), int(gridPos.y))


# dictionary linking colours and ground type
groundColourDic = {
    "(255, 255, 255, 255)": "snow",
    "(79, 69, 61, 255)": "mountain",
    "(92, 69, 54, 255)": "mountain",
    "(79, 61, 49, 255)": "mountain",
    "(44, 38, 34, 255)": "mountain",
    "(70, 130, 50, 255)": "forest",
    "(168, 202, 88, 255)": "grassland",
    "(232, 193, 112, 255)": "dry sand",
    "(222, 158, 65, 255)": "wet sand",
    "(79, 143, 186, 255)": "shallow water",
    "(60, 94, 139, 255)": "deeper water",
    "(37, 58, 94, 255)": "deepest water"
}


# returns ground type at an input position
def getGround(pos):
    colour = ground.get_at((int(pos.x), int(pos.y)))
    return groundColourDic[str(colour)]


# validates input position, so that it is within bounds of map
# returns valid position
def boundPos(pos):
    x = max(0, min(pos.x, mapWidth - 1))  # bound x between 0 and map width
    y = max(0, min(pos.y, mapHeight - 1))  # bound y between 0 and map height
    return Vector2(x, y)  # return bounded position


# finds the closest object within a circle, out of an array of objects
# - takes inputs for circle centre, circle radius, and array of objects
# - returns closest object (if no object within circle, returns None)
def findClosestObjectInRadius(pos, radius, objectArr):
    closestDistance = math.inf
    closestObject = None
    # iterate through objects
    for gameObject in objectArr:
        distance = pos.distance_to(gameObject.pos)  # find distance to object
        if radius > distance > 0 and distance < closestDistance:
            closestDistance = distance
            closestObject = gameObject
    return closestObject  # return None if no objects found within radius


# finds closest object to position
# - takes input for position, array of objects
# - returns closest object (if no object found, returns None)
def findClosestObject(pos, objectArr):
    closestDistance = math.inf
    closestObject = None
    # iterate through objects
    for gameObject in objectArr:
        distance = pos.distance_to(gameObject.pos)  # find distance to object
        if distance < closestDistance:
            closestDistance = distance
            closestObject = gameObject
    return closestObject  # return None if no objects found within radius


# finds closest viable mate
# - takes inputs for position, array of species, and sex of animal
# - returns closest mate, returns None if no viable mates
def findClosestMate(pos, mateArr, sex):
    closestDistance = math.inf
    closestMate = None
    # iterate through objects
    for mate in mateArr:
        distance = pos.distance_to(mate.pos)  # find distance to object
        if mate.sex != sex and mate.state == "searching" and mate.objectToFind == "mate" and distance < closestDistance:
            closestDistance = distance
            closestMate = mate
    return closestMate  # return None if no objects found within radius


# converts position to node
# takes an input for position, returns node object
def posToNode(pos):
    pos = boundPos(pos)
    gridPos = pos / gridScale  # convert map position to grid position
    node = pathfindingGrid[int(gridPos.x)][int(gridPos.y)]  # get node at position
    if not node.traversable:  # if node not traversable
        node = findClosestTraversableNode(node)  # find closest traversable node
    return node  # return node


# finds closest traversable node to input node
# takes input for node object, returns closest node object
def findClosestTraversableNode(node):
    closestDistance = math.inf  # arbitrarily large number
    closestNode = None
    # iterate through nodes to find closest traversable node
    for row in pathfindingGrid:
        for currentNode in row:
            if currentNode.traversable:  # if current node is traversable
                distance = node.pos.distance_to(currentNode.pos)  # calculate distance to node
                if distance < closestDistance:  # if distance less than closest distance
                    closestDistance = distance  # set distance as new closest distance
                    closestNode = currentNode  # set closest node to current node
    return closestNode  # return closest node


mousePosOnMiddleClick = Vector2()
borderWidth = 0


# Camera group, containing all object sprites
# Methods to display all object, and, update all objects
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.screen = screen

        # camera offset
        self.offset = Vector2()
        self.changeInOffset = Vector2()

        # ground
        self.groundSurface = ground
        self.groundRect = self.groundSurface.get_rect(topleft=(0, 0))

        self.selectedSprite = None

        # gizmos
        self.gizmoSurface = gizmoSurface
        self.gizmos = True

    # draws all objects within group to screen,
    # taking into account panning of mouse
    def customDraw(self):
        mousePos = Vector2(pygame.mouse.get_pos())
        leftClicked = pygame.mouse.get_pressed()[0]

        # pan map with mouse drag
        if pygame.mouse.get_pressed()[1]:  # if middle button is held down
            # change in offset = change in mouse position whilst being held down
            self.changeInOffset = mousePos - mousePosOnMiddleClick
        else:  # on release
            self.offset += self.changeInOffset  # add change in offset to offset
            self.changeInOffset = Vector2()  # reset change in offset to zero

        widthDifference, heightDifference = width - mapWidth, height - mapHeight

        # checking for map border,
        # by bounding total offset between 0 and the negative of map width and height
        totalOffset = self.changeInOffset + self.offset
        if totalOffset.x > 0:  # if x offset outside zero
            self.changeInOffset.x = -self.offset.x  # bound total x offset to zero
        elif totalOffset.x < widthDifference:  # if x offset outside width difference
            self.changeInOffset.x = widthDifference - self.offset.x  # bound total x offset to width difference
        if totalOffset.y > 0:  # if y offset outside zero
            self.changeInOffset.y = -self.offset.y  # bound total y offset to zero
        elif totalOffset.y < heightDifference:  # if y offset outside height difference
            self.changeInOffset.y = heightDifference - self.offset.y  # bound total y offset to width difference

        displayedOffset = self.changeInOffset + self.offset

        # blit ground surface to display surface
        self.screen.blit(self.groundSurface, displayedOffset)

        if self.selectedSprite is not None:
            outline = changeColor(self.selectedSprite.image, (0, 0, 0))
            # pygame.Surface.fill(outline, (255, 255, 255))
            self.screen.blit(outline, self.selectedSprite.rect.topleft + displayedOffset)

        # elements
        for sprite in sorted(self.sprites(), key=lambda sprite: (sprite.rect.topleft[1])):
            sprite.draw()
            if leftClicked and sprite.__class__.__name__ == "Animal" and sprite.rect.collidepoint(
                    (mousePos / zoom - displayedOffset)):
                self.selectedSprite = sprite

        self.screen.blit(objectSurface, displayedOffset)

        # gizmos
        if True:
            self.screen.blit(gizmoSurface, displayedOffset)


# Change colour of image
# - takes input for image, colour
# - returns updated image filled with input colour
def changeColor(image, color):
    colouredImage = pygame.Surface(image.get_size()).convert_alpha()
    colouredImage.fill(color)

    finalImage = image.copy()
    finalImage.blit(colouredImage, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return finalImage


# finds largest possible simple division of y-axis
# - takes inputs for largest data value, number of divisions, and simple values
# - returns simple division
def findSimpleDivision(maxValue, divisions, simpleValues=[1, 2, 5]):
    division = maxValue / divisions  # y-axis will be marked at 8 points

    # find a suitable division of size 1, 2, or 5 of any order (e.g. 10, 200, or 500)
    n = 0
    while True:
        baseDivision = 10 ** n  # division = 1*10^n
        # iterate through simple values
        for simpleValue in simpleValues:
            simpleDivision = baseDivision * simpleValue  # division will be in form of "simple value * 10^n"
            if simpleDivision >= division:  # ">=" so that the largest value always fits on the graph
                return simpleDivision  # complete once found simple division large enough

        n += 1  # increase order of 10 by 1


# Sprite group for buttons
#
class ButtonCameraGroup(pygame.sprite.Group):
    def __init__(self, background):
        super().__init__()

        self.background = background
        self.backgroundRect = background.get_rect()
        self.backgroundRect.topleft = (28, 40)
        self.backgroundWidth = background.get_width()
        self.backgroundHeight = background.get_height()

        self.axesBackground = pygame.image.load("sprites/gridaxes.png")

        self.backgroundTopMiddle = self.backgroundRect.topleft + Vector2(self.backgroundWidth * 0.5, 0)

        self.displayedUI = None

        self.lineGraphText = font.render('Population Graph', True, (255, 255, 255))
        self.trophicPyramidText = font.render('Trophic Pyramid', True, (9, 10, 20))

        self.gridFont = pygame.font.Font('fonts/RobotoSlab-Bold.ttf', 8)

        # line graph

        self.offset = 40
        self.origin = self.backgroundRect.topleft + Vector2(self.offset, 0)
        self.yLength = self.backgroundHeight - self.offset
        self.xLength = self.backgroundWidth - self.offset

        self.maxPopulationData = 500
        self.dx = self.xLength / self.maxPopulationData

        self.divisions = 8

        self.graphSurface = pygame.Surface((self.backgroundWidth, self.backgroundHeight)).convert_alpha()

        # create axis and labels
        self.xAxisLabel = self.gridFont.render("Time (s)", True, (255, 255, 255))
        self.yAxisLabel = pygame.transform.rotate(self.gridFont.render("No. organisms", True, (255, 255, 255)), 90)
        self.axisSurface = pygame.Surface((self.backgroundWidth, self.backgroundHeight)).convert_alpha()
        self.axisSurface.fill((0, 0, 0, 0))
        self.axisSurface.blit(self.xAxisLabel, (self.offset + 0.5 * self.xLength - 0.5 * self.xAxisLabel.get_width(),
                                                self.backgroundHeight - 0.4 * self.offset - self.xAxisLabel.get_height()))
        self.axisSurface.blit(self.yAxisLabel, (0.3 * self.offset, 0.5 * self.yLength))

        # trophic pyramid

        self.triangleWidth = 260
        self.triangleHeight = 1.732 * self.triangleWidth * 0.5
        self.triangleArea = self.triangleWidth * self.triangleHeight * 0.5

        self.triangleTop = self.backgroundRect.midtop + Vector2(0, 45)
        self.titlePosition = self.backgroundRect.midtop + Vector2(-self.trophicPyramidText.get_width() * 0.5, 10)

    # draws graph line
    # - takes inputs for y data values, y scalar, change in x, colour of line, and surface to draw line on
    def drawLine(self, yData, yScalar, dx, colour, surface):
        yOffset = surface.get_height() - self.offset  # offset calculate before for loop to reduce operations
        points = []  # array of points that line will connect
        x = self.offset  # starting pixel value of x
        for y in yData:
            points.append((x, yOffset - y * yScalar))  # convert population to pixel coordinate
            x += dx  # increment x
        pygame.draw.lines(surface, colour, closed=False, points=points, width=2)  # draw line connecting points

    # draws graph axes
    # - takes inputs for axes division, y scalar, number of divisions, and surface to draw axes on
    def drawAxes(self, yDivision, yScalar, divisions, surface):
        # offsets (calculated before for loop to reduce number of operations)
        xOffset = self.offset - 3
        yOffset = surface.get_height() - self.offset
        # iterate through divisions of axis
        for i in range(divisions + 1):
            # render number at point on axis using font
            yNumber = self.gridFont.render(str(int(i * yDivision)), True, (255, 255, 255))
            # draw number to surface at position with offset
            surface.blit(yNumber, (xOffset - yNumber.get_width(),
                                   yOffset - i * yDivision * yScalar - 0.5 * yNumber.get_height()))

    # draws UI tabs,
    # decides which tab is selected
    def drawUI(self):
        # if a button is selected
        if self.displayedUI is not None:
            displayScreen.blit(self.background, self.backgroundRect)  # display UI background

            # POPULATION
            if self.displayedUI == "line graph":  # if line graph selected

                # find highest population of any species in time
                highestPopulation = 0
                for populationData in populationDic.values():
                    speciesHighestPopulation = max(populationData)  # find highest population of species through time
                    if speciesHighestPopulation > highestPopulation:  # if more than highest population of all species
                        highestPopulation = speciesHighestPopulation  # set as highest population

                # y-axis will be marked at 8 points
                simpleDivision = findSimpleDivision(highestPopulation, self.divisions)

                # scalar to convert population to y coordinate in pixels
                yScalar = self.yLength / ((self.divisions + 1) * simpleDivision)

                self.graphSurface.fill((0, 0, 0, 0))  # reset graph surface
                self.drawAxes(simpleDivision, yScalar, self.divisions, self.graphSurface)  # draw x and y axis

                for species in populationDic.keys():  # iterate through species
                    self.drawLine(populationDic[species], yScalar, self.dx,
                                  speciesColourDic[species], self.graphSurface)  # draw line for species

                displayScreen.blit(gridBackground, self.backgroundRect.topleft)  # display grid
                displayScreen.blit(self.axisSurface, self.backgroundRect.topleft)  # display axes
                displayScreen.blit(self.graphSurface, self.backgroundRect.topleft)  # display graph
                displayScreen.blit(self.axesBackground, self.backgroundRect.topleft)
                displayScreen.blit(self.lineGraphText, self.titlePosition)  # display title

            # BIOMASS
            elif self.displayedUI == "biomass":  # if biomass selected
                displayScreen.blit(self.trophicPyramidText, self.titlePosition)  # display biomass title

                reducedBiomassTotals = []
                # remove any biomass totals of zero, so they are not included in the pyramid
                for levelTotal in biomassTotals:
                    if levelTotal != 0:
                        reducedBiomassTotals.append(levelTotal)  # add to totals if not zero

                totalBiomass = sum(reducedBiomassTotals)  # get total biomass of all species
                reducedBiomassTotals.reverse()  # reverse totals array, so in descending order of level on food chain
                trianglePoints = []  # will hold bottom right point of triangle for each section within the pyramid

                # iterative formula for finding area of each triangle in the trophic pyramid,
                # where: percentage of total biomass = percentage of area of trophic pyramid
                area = 0
                for levelTotal in reducedBiomassTotals:
                    area = area + ((levelTotal / totalBiomass) * self.triangleArea)
                    x = (area * 0.57735) ** 0.5
                    y = x * 1.732
                    trianglePoints.append(Vector2(x, y))  # add calculated point to triangle points

                trianglePoints.reverse()  # reverse triangle points, so back in ascending order
                hue = 220
                for trianglePoint in trianglePoints:
                    p1 = self.triangleTop  # top of triangle
                    p2 = self.triangleTop + trianglePoint  # bottom-right point of triangle
                    p3 = self.triangleTop + Vector2(-trianglePoint.x, trianglePoint.y)  # bottom-left point of triangle
                    pygame.draw.polygon(displayScreen, (hue, hue, 255), [p1, p2, p3])  # draw solid triangle
                    pygame.draw.polygon(displayScreen, (9, 10, 20), [p1, p2, p3], width=3)  # draw triangle outline
                    hue -= 40  # decrease R and G values, so becomes more blue higher up the pyramid

        # iterate through buttons
        for sprite in self.sprites():
            if self.displayedUI == sprite.name:  # if selected
                displayScreen.blit(sprite.selectedImage, sprite.rect)  # display selected image
            else:  # if not selected
                displayScreen.blit(sprite.image, sprite.rect)  # display default image


# Button class, containing the position, default image, and selected image of each button
# contains method press, which selects button if it is clicked by the mouse
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, name, image, selectedImage, scale, group):
        super().__init__(group)
        self.group = group  # button group
        self.name = name  # button name, "line graph" or "biomass"
        self.image = image  # default image when unselected
        self.selectedImage = pygame.transform.scale_by(selectedImage, scale)  # scaled image of button when selected
        self.rect = self.image.get_rect()  # pygame rect of button image
        self.rect.topleft = (x, y)  # position of button

    # when called, checks if button is pressed and selects button
    def press(self):
        mousePos = pygame.mouse.get_pos()  # get position of mouse
        if self.rect.collidepoint(mousePos):  # if mouse collides with button
            if self.group.displayedUI == self.name:  # if already selected
                self.group.displayedUI = None  # deselect button
            else:  # if not already selected
                self.group.displayedUI = self.name  # select button


# Object class, containing general attributes required for every game object
# has draw method, to display object's sprite at its position
class Object(pygame.sprite.Sprite):
    def __init__(self, name, pos, group, image, colour=(255, 255, 255)):
        super().__init__(group)
        self.name = name
        self.image = image
        self.rect = self.image.get_rect(midbottom=pos)
        self.direction = Vector2(1, 0)
        self.pos = pos
        self.colour = colour

    # draws object to screen at its position
    def draw(self):
        objectSurface.blit(self.image, self.rect)


# Animal class, representing a species' characteristics by attributes
# Contains methods for each animal behaviour, and an 'update' method called every frame
class Animal(Object):
    def __init__(self, species,
                 name, pos, group, image, colour,
                 maxSpeed, maxHealth, senseRadius, attack, interactInterval=1, trophicLevel=1, mass=1,
                 foodNames=["berry"], threatNames=[],
                 matureAge=100, numberOfOffspring=1, hungerIncrease=0.35):
        super().__init__(name, pos, group, image, colour)
        self.rect.center = self.pos

        # - constants, specific to species -
        self.species = species
        self.maxSpeed = maxSpeed
        self.maxHealth = maxHealth
        self.attack = attack
        self.interactInterval = interactInterval * fps  # number of frames between interactions
        self.sex = random.choice(["male", "female"])
        self.trophicLevel = trophicLevel
        self.mass = mass
        self.senseRadius = senseRadius
        self.foodNames = foodNames  # e.g. ["hare", "berries"]
        self.threatNames = threatNames  # e.g. ["fox", "bear"]
        self.matureAge = matureAge
        self.numberOfOffspring = numberOfOffspring

        # - variables -
        self.age = 0
        self.mature = True
        self.health = maxHealth

        # desires (0-100)
        self.hunger = random.randint(0, 50)
        self.matingDesire = random.randint(0, 21)
        self.hungerIncrease = hungerIncrease

        # states: "eating", "drinking", "moving to", "attacking", "running from danger", "searching", "mating"
        self.state = "wandering"
        self.uninterruptibleStates = ["eating", "drinking", "mating", "moving to"]

        self.objectToFind = None
        self.targetObject = None
        self.targetPos = pos
        self.attackTimer = 0
        self.groundOn = None  # current ground type animal is standing on e.g. "grassland"
        self.threats = []

        # booleans
        self.canInteract = True
        self.alive = True
        self.wanderMove = True

        biomassTotals[trophicLevel] += mass
        speciesDic[self.species].append(self)  # add animal to array of species
        self.path = []  # path to follow

    # Animal update, to carry out overall behaviour of animal
    # called once a frame
    def update(self):
        # if alive
        if self.alive:
            self.age += 1 / fps  # increase age by time passed in frame
            if not self.mature and self.age >= self.matureAge:  # if reached maturity
                self.mature = True  # set mature to true

                # increase traits
                self.maxSpeed *= 2  # faster
                self.maxHealth *= 2  # more resilient
                self.attack *= 2  # stronger
                self.mass *= 2  # heavier, so will need to eat more food mass

            self.groundOn = groundColourDic[str(ground.get_at((int(self.pos.x), int(self.pos.y))))]
            if self.groundOn == "deepest water":
                self.alive = False
                print("drowned")
                self.delete()

            # attack cooldown
            if not self.canInteract:
                self.attackTimer += 1
                if self.attackTimer >= self.interactInterval:
                    self.canInteract = True
                    self.attackTimer = 0

            # natural changes to desires
            self.hunger += self.hungerIncrease * deltaTime  # +0.1 per second

            if self.hunger < 20:  # mating desire only increases if animal has sufficient food
                self.matingDesire += 0.05 * deltaTime  # +1 per second

            if self.hunger >= 100:
                self.alive = False
                print("starved to death")
                self.delete()

            # "running from danger" takes priority over all other states

            if self.state == "running from danger":
                threatRadiusScalar = 1
            else:
                threatRadiusScalar = 0.5

            threatPositions = []  # holds positions of threats
            # iterate through possible threat objects
            for threatName in self.threatNames:
                for threat in speciesDic[threatName]:
                    distance = self.pos.distance_to(threat.pos)  # find distance to possible threat
                    if threat.targetObject == self and distance < threatRadiusScalar * self.senseRadius:  # if threat close enough
                        threatPositions.append(threat.pos)  # add threat position to array

            if len(threatPositions) != 0:
                self.state = "running from danger"  # if there is a threat, run from it
            elif self.state == "running from danger":
                self.state = "wandering"  # once threat disappears, reset behaviour to wander

                # self.targetPos = randomPositionFromLayer("forest")
            padding = 20

            if self.state == "running from danger":
                # find mean position of all threats
                positionSum = Vector2()  # sum of positions
                for pos in threatPositions:  # iterate through threat positions
                    positionSum += pos  # add position to sum of positions
                meanPosition = positionSum / len(threatPositions)  # mean = sum/N

                xToBorder = mapWidth - self.pos.x  # horizontal distance to border
                if xToBorder < padding:
                    meanPosition.x += padding - xToBorder
                elif self.pos.x < padding:
                    meanPosition.x += self.pos.x - padding

                yToBorder = mapHeight - self.pos.y
                if yToBorder < padding:
                    meanPosition.y += 30 - padding
                elif self.pos.y < padding:
                    meanPosition.y += self.pos.y - padding

                self.moveAwayFromPos(meanPosition, self.maxSpeed)  # move away from mean threat position

            else:
                if self.state not in self.uninterruptibleStates:  # only change state if it can't be interrupted

                    # decide which state based on desires
                    mostDesired = max(self.hunger, self.matingDesire, 40)
                    if mostDesired == self.hunger:  # search for food
                        self.state = "searching"
                        self.objectToFind = "food"
                    elif mostDesired == self.matingDesire:  # search for a mate
                        self.state = "searching"
                        self.objectToFind = "mate"
                    else:
                        self.state = "wandering"  # if no desire is greater than 20, the animal will wander

                # carry out behaviour of state

                # wandering
                if self.state == "wandering":
                    self.wander(wanderInterval=1)

                # searching
                elif self.state == "searching":
                    self.search(self.objectToFind)

                # move to and interact with target object
                elif self.state == "moving to":
                    # self.moveToAndInteract()

                    if self.targetObject not in cameraGroup.sprites() or self.targetObject is None:
                        print("lost object to move towards")
                        self.state = "wandering"
                    else:
                        # move to target object
                        self.targetPos = self.targetObject.pos
                        if self.moveToTarget(self.maxSpeed) and self.canInteract:
                            # (if target object is reached, and, animal hasn't recently interacted)

                            # SPECIAL OBJECTS: food, water, mate
                            # if object is none of these,  do nothing

                            # food -> eat
                            if self.objectToFind == "food":
                                objectType = self.targetObject.__class__.__name__  # get class name of object
                                # if food is an animal
                                if objectType == "Animal":
                                    # if alive, attack
                                    if self.targetObject.alive:
                                        self.targetObject.beAttacked(self.attack)  # attack animal for given damage
                                        self.canInteract = False  # start interact cooldown
                                    # if dead, eat
                                    else:
                                        self.eat(self.targetObject)  # eat animal
                                        self.targetObject = None  # reset target object
                                        self.state = "wandering"  # reset behaviour to wandering

                                # if food is a plant
                                elif objectType == "Plant":
                                    # if plant has no food left
                                    if len(self.targetObject.foodPosArr) == 0:
                                        print(f"tried to eat {self.targetObject.species} but none left")
                                    else:
                                        self.eat(self.targetObject)  # eat plant
                                    self.targetObject = None  # reset target object
                                    self.state = "wandering"  # reset behaviour to wandering

                            # if mate is reached, reproduce
                            elif self.objectToFind == "mate":
                                #print("test")
                                if self.sex == "female":  # if female
                                    self.reproduce(self.numberOfOffspring)  # give birth to offspring

                                self.matingDesire = 0  # reset mating desire
                                self.targetObject = None  # reset target object
                                self.state = "wandering"  # reset behaviour to wandering

    # wander method
    # animal's idle state, causing it to wander around randomly
    # - takes an input for wander interval, determining how frequently an animal chooses to wander to a new position
    def wander(self, wanderInterval):
        # start/stop moving on avg every 'wanderInterval' seconds
        if random.randint(1, wanderInterval * fps) == 1:
            self.wanderMove = not self.wanderMove
            if self.wanderMove:  # when starting to move, choose new random traversable target
                self.targetPos = random.choice(traversableCoordinates)

        if self.wanderMove:
            self.moveToTarget(self.maxSpeed * 0.3)  # move with slower speed while wandering

    # search method
    # behaviour carried out when an animal needs to locate and interact with a particular object,
    # causing the animal to search around and move towards the first object of the input type it sees
    # - takes an input for the type of object to find ("food", "water", or "mate")
    def search(self, objectToFind):
        if self.followPath(self.maxSpeed * 0.5):
            self.path = pathfinding.createPath(posToNode(self.pos), posToNode(randomTraversablePos()), pathfindingGrid,
                                               gridScale)

        # searching for food
        if objectToFind == "food":
            # create array of all objects animal can eat
            foodArr = []
            for foodName in self.foodNames:
                foodArr += speciesDic[foodName]

            # find an object within the animals sense range in the food array
            self.targetObject = findClosestObjectInRadius(self.pos, self.senseRadius, foodArr)

            # if food is found within sense radius
            if self.targetObject is not None:
                if self.targetObject.__class__.__name__ == "Plant" and len(self.targetObject.foodPosArr) == 0:
                    self.targetObject = None
                else:
                    print(f"found {self.targetObject.species}")  # (for testing)
                    self.state = "moving to"  # set state to move to object
                    self.path = []

        elif objectToFind == "mate":
            # create array of own species
            mateArr = speciesDic[self.species]

            # find a mate within sense radius
            self.targetObject = findClosestMate(self.pos, mateArr, self.sex)

            # if found mate of opposite sex, who is also searching for a mate
            if self.targetObject is not None:
                # set state of self and mate to "moving to"
                self.state = "moving to"
                self.targetObject.state = "moving to"
                self.path = []

                self.targetObject.targetObject = self  # set target object of mate to self
                self.targetObject.path = []  # reset path

    # be attacked method, called when an animal takes damage
    # - takes an input for damage, determining how much health is taken away from the animal
    # (will cause animal to die if reaches 0 health)
    def beAttacked(self, damage):
        if random.randint(1, 100) <= 10:  # 10% chance to evade attack
            print("evaded attack")
        else:
            damage = damage*(random.randint(20, 100))/100
            self.health -= damage  # reduce health by given damage
            print(f"took {damage} damage")
            if self.health <= 0:
                self.alive = False  # dies if health reaches 0
                print("died")

    # eat method, called when an animal eats a given food
    # - takes an input for the food object (e.g. rabbit object, or berry object)
    # - reduces hunger of animal in accordance with mass of input food
    def eat(self, food):
        foodMass = food.beEaten(self)  # get mass of food
        hungerChange = 100 * foodMass / self.mass  # hunger increases by fraction of food's mass to animal's mass
        # e.g. if animal eats a mass equal to its own mass, its hunger reduces by 100
        self.hunger = min(max(0, self.hunger - hungerChange), 100)  # bound hunger between 0 and 100
        print(f"ate {food.species}")  # ate message

        self.matingDesire += 0.5*hungerChange

    # be eaten method (FOR ANIMAL), called when an animal is eaten
    # - takes an input for 'eater', to test if correct animal eats the correct food
    # - removes animal from simulation, and returns mass of animal
    def beEaten(self, eater):
        print(f"eaten by {eater.species}")  # eaten by message
        self.delete()  # remove animal from simulation
        return self.mass  # return mass to be eaten

    # reproduce method, causes a number of offspring to spawn in
    # - takes an input for number of offspring, instantiates clones of the parent animal with certain lowered stats
    def reproduce(self, numberOfOffspring):
        # for a given number of offspring,
        for i in range(numberOfOffspring):
            # instantiate animal with same species attributes as parent animal, with some halved traits
            child = Animal(self.species, self.name, self.pos, cameraGroup, self.image, self.colour,
                           0.5 * self.maxSpeed, 0.5 * self.maxHealth, self.senseRadius, 0.5 * self.attack,
                           self.interactInterval, self.trophicLevel, 0.5 * self.mass, self.foodNames, self.threatNames)
            child.hunger = self.hunger  # set hunger of child to hunger of parent, as to conserve energy
            child.matingDesire = 0
            child.mature = False  # set mature to False

    # follow path method, causing animal to move through nodes of path when called
    # - takes an input for speed
    # - returns true if at end of path, returns false if still moving along path
    def followPath(self, speed):
        if len(self.path) == 0:
            return True  # reached end of path
        else:
            self.targetPos = self.path[0]
            if self.moveToTarget(speed):
                self.path.pop(0)

            return False

    # move to target method, called to make animal move toward target
    # - takes an input for speed
    # - returns true if target is reached, returns false if still moving toward target
    def moveToTarget(self, speed):
        if self.pos.distance_to(self.targetPos) > 3:  # if not at target, move to target
            self.direction = (self.targetPos - self.pos).normalize()  # normalise direction so has a magnitude of 1
            self.move(speed)
            return False  # False = not at target
        else:
            return True  # True = reached target

    # move away from position, called to make animal move away from input position
    # - takes inputs for position, and speed
    def moveAwayFromPos(self, pos, speed):
        direction = -(pos - self.pos).normalize()  # direction away from position

        if not self.path:
            self.path = pathfinding.createPath(posToNode(pos), posToNode(self.pos + 100*direction),
                                               pathfindingGrid, gridScale)

        self.followPath(speed)

    # move method, cause animal to move at a speed in its direction
    # - takes input for speed
    def move(self, speed):
        if not self.canInteract:
            speed *= 0.5
        # self.pos = boundPos(self.pos + self.direction * self.speedOnGroundType(speed) * deltaTime)
        speed = speed * (1 - self.hunger / 200)  # at 100% hunger, speed is half
        self.pos = boundPos(self.pos + self.direction * speed * deltaTime)
        self.rect.center = self.pos

    # speed on ground type method, causes different speeds on different ground types
    # - takes input for initial speed
    # - returns fraction of speed determined by ground type animal is on
    def speedOnGroundType(self, speed):
        if self.groundOn == "forest":
            return speed * 0.9
        elif self.groundOn == "mountain":
            return speed * 0.3
        elif self.groundOn == "shallow water":
            return speed * 0.5
        elif self.groundOn == "deeper water" or self.groundOn == "deepest water":
            return speed * 0.1
        return speed

    # delete method, called to permanently remove animal from simulation
    def delete(self):
        self.kill()  # remove from sprite group
        speciesDic[self.species].remove(self)  # remove from array of species
        del self

    # draw method - overrides object draw method
    # - displays animal on screen at position, facing direction of movement
    def draw(self):

        angle = self.direction.angle_to(Vector2(1, 0))  # find angle between animal's direction and the vector (1, 0)

        if self.direction.x < 0:  # if facing left
            image = pygame.transform.flip(self.image, flip_x=False, flip_y=True)  # flip vertically
        else:  # if facing right
            image = self.image  # keep sprite as is

        rotatedImage = pygame.transform.rotate(image, angle)  # rotate image through angle

        if self.mature:  # if mature
            objectSurface.blit(rotatedImage, self.rect)  # draw sprite facing direction
        else:  # if not mature
            objectSurface.blit(pygame.transform.scale_by(rotatedImage, 0.5), self.rect)  # draw smaller sprite

        # self.drawSenseRadius()

    # draws circle for sense radius, enabled when testing
    def drawSenseRadius(self):
        pygame.draw.circle(gizmoSurface, (255, 255, 255, 100), self.pos, self.senseRadius, width=1)

    # draws line in direction animal is facing, enabled when testing
    def drawDirectionGizmo(self, rect):
        pygame.draw.line(objectSurface, (255, 0, 0), self.rect.center, self.rect.center + self.direction * 12)


# Plant class
# containing attributes relating to a plant species' characteristics, graphical attributes,
# draw method to display plant, and update and behaviour methods to carry out actions of plant
class Plant(Object):
    def __init__(self, species,
                 name, pos, group, image,
                 timeToGrow, maxHeight, mass=1,
                 foodMass=0, foodSprite=None, centreAroundFood=None, foodSpawnRadius=None, maxFood=0):
        super().__init__(name, pos, group, image)

        self.species = species

        # constants
        self.timeToGrow = timeToGrow  # time in seconds for plant to grow new food
        self.growthRate = 1 / timeToGrow
        self.maxHeight = maxHeight
        self.mass = mass
        self.trophicLevel = 0

        if self.species in speciesDic.keys():
            speciesDic[self.species].append(self)  # add plant to array of species

        # - food attributes -
        self.foodMass = foodMass  # mass of each food
        self.foodSprite = foodSprite  # food image

        # centre and radius of circle in which food can spawn
        self.centreAroundFood = centreAroundFood
        self.foodSpawnRadius = foodSpawnRadius

        self.maxFood = maxFood  # max food plant can have
        self.foodPosArr = []  # array of positions of food
        # set up initial food positions
        for i in range(random.randint(0, int(0.3 * maxFood))):  # random number of food from 0 to max
            self.addNewFood()

    # plant update - called once per frame
    # carries out overall behaviour of plant
    def update(self):
        if self.maxFood > 0 and random.randint(1, fps * self.timeToGrow) == 1:
            self.addNewFood()  # add new food, on average every 'timeToGrow' seconds

    # draw method - overrides object draw method
    # displays plant sprite, and its individual food sprites, on screen
    def draw(self):
        objectSurface.blit(self.image, self.rect)  # draw plant sprite
        for foodPos in self.foodPosArr:  # iterate through food positions
            objectSurface.blit(self.foodSprite, self.rect.center + foodPos)  # draw food sprite at position on plant

    # be eaten method (FOR PLANTS) - called when an animal eats food from the plant
    # taken an input for 'eater', to test if correct animal eats correct plant
    def beEaten(self, eater):
        print(f"eaten by {eater.species}")  # eaten by message
        self.removeFood()  # reduce food held by plant by 1
        return self.foodMass  # return mass of food

    # add new food method - called to make a new piece of food grow on the plant
    def addNewFood(self):
        # if plant has capacity for more food
        if len(self.foodPosArr) < self.maxFood:
            # add new food at random position on plant
            self.foodPosArr.append(randomPosInSquare(self.centreAroundFood, self.foodSpawnRadius))
            biomassTotals[0] += self.foodMass

    # remove food - called to remove an existing piece of food from the plant
    # (e.g. when an animal eats from the plant)
    def removeFood(self):
        if len(self.foodPosArr) > 0:  # if plant has food
            self.foodPosArr.pop()  # reduce food held by plant by 1
            biomassTotals[0] -= self.foodMass
        else:
            print("error: ate food when none left")  # will only execute if program is not working correctly


# Class for menu buttons
# - attributes for graphical aspects and the action the button carries out when clicked
# - methods to display button (normally and when mouse is hovering over it), and to click button
# instantiate to make a new button, used for navigating between menus
class UIButton:
    def __init__(self, image, scale, pos, text, font, action, colour, selectedColour):
        # - BASE -
        self.pos = pos
        self.hovering = False  # boolean for if mouse is hovering over button
        self.action = action  # action on clicking button e.g. "quit", "simulation", "customise"

        # - VISUAL -
        self.image = pygame.transform.scale_by(image, scale)  # scale image
        self.rect = self.image.get_rect()  # rect of image
        self.rect.center = self.pos  # set position as centre of image

        # create black outline around button
        self.outline = pygame.Surface((self.image.get_width() + 2 * scale,  # 2 pixels thickness
                                       self.image.get_height() + 2 * scale))  # 2 pixels thickness
        self.outline.fill((0, 0, 0))  # set to black
        self.outlineRect = self.outline.get_rect()  # rect of outline
        self.outlineRect.center = self.pos  # set position as centre of image

        # create hovering outline
        self.hoveringOutline = self.outline.copy()  # copy black outline
        self.hoveringOutline.fill(selectedColour)  # set to input colour

        self.text = font.render(text, True, colour)  # render text with font
        # blit text at centre of image
        self.image.blit(self.text, (0.5 * self.image.get_width() - 0.5 * self.text.get_width(),
                                    0.5 * self.image.get_height() - 0.5 * self.text.get_height()))

    # draw method
    # displays button to screen, with outline if mouse is hovering over it
    def draw(self):
        if self.hovering:  # if mouse over button
            displayScreen.blit(self.hoveringOutline, self.outlineRect)  # display hovering outline
        else:  # if mouse not over button
            displayScreen.blit(self.outline, self.outlineRect)  # display black outline
        displayScreen.blit(self.image, self.rect)  # display button image with text

    def checkForHovering(self, mousePos):
        if self.rect.collidepoint(mousePos):  # if input mouse position within button rect
            self.hovering = True  # set hovering to true
        else:
            self.hovering = False  # otherwise, set hovering to false

    # click method
    # carries out action of button if mouse is over it, to be called when mouse is clicked
    def click(self):
        if self.hovering:  # if mouse is over button
            # carry out action of button
            if self.action == "simulation":
                simulation()  # start simulation
            elif self.action == "customise":
                customise()  # open customise menu
            elif self.action == "title":
                title()  # open title screen
            elif self.action == "quit":
                pygame.quit()  # quit program


# Class for input fields - used to allow user to determine organism makeup of ecosystem
# - attributes for graphical aspects and the value within the field
# - methods to display field (normally and when selected)
class UIInputField:
    def __init__(self, image, scale, pos, text, value, font, colour, selectedColour):
        # general attributes
        self.pos = pos
        self.image = pygame.transform.scale_by(image, scale)  # scale image
        self.rect = self.image.get_rect()
        self.rect.midleft = self.pos

        # outline attributes
        self.outline = pygame.Surface((self.image.get_width() + 2 * scale, self.image.get_height() + 2 * scale))
        self.outline.fill((0, 0, 0))
        self.outlineRect = self.outline.get_rect()
        self.outlineRect.center = self.rect.center
        self.selectedOutline = self.outline.copy()
        self.selectedOutline.fill(selectedColour)

        # text attributes
        self.text = str(text)
        self.font = font
        self.colour = colour
        self.textSurface = self.font.render(self.text, True, self.colour)
        self.textRect = self.textSurface.get_rect()
        self.textRect.center = pos + Vector2(-0.5*self.textSurface.get_width()-10, 0)

        self.value = str(value)  # value held in input field
        self.hovering = False  # boolean for if mouse is hovering over field

    # draw method
    # - displays field box and value to screen, with outline if selected
    def draw(self):
        displayScreen.blit(self.image, self.rect)  # display input box
        displayScreen.blit(self.textSurface, self.textRect)  # display relating text

        valueSurface = self.font.render(str(self.value), True, self.colour)  # render value with font
        displayScreen.blit(valueSurface,
                           self.rect.center - 0.5 * Vector2(valueSurface.get_size()))  # display value in input box

    # checks for hovering method
    # - returns true if mouse is over field, false is mouse is not over field
    def checkForHovering(self, mousePos):
        if self.rect.collidepoint(mousePos):
            self.hovering = True
            return True
        else:
            self.hovering = False
            return False

    # draws outline around field, for when it is selected
    def drawSelectedOutline(self):
        displayScreen.blit(self.selectedOutline, self.outlineRect)


# INPUT VALIDATION
# validates if a value is an integer
# - takes input for value, returns true if integer, false if not an integer
def validateInteger(value):
    isInteger = False  # boolean for if value is integer
    try:
        if int(value) == float(value):  # check for integer
            isInteger = True  # set to True if integer
    finally:
        return isInteger  # return True if integer, False if other data type e.g. float, string


# ========================
# ===== SETUP PYGAME =====
# ========================

pygame.init()

# WINDOW
width, height = 800, 600  # resolution, 400x300 pixels
mapWidth, mapHeight = 1024, 1024  # map size, 512x512 pixels
gridSize = 64  # grid size, 64x64
gridScale = int(mapWidth / gridSize)  # converts grid position to pixel position
displayScreen = pygame.display.set_mode((width, height), pygame.NOFRAME)  # borderless window
pygame.display.set_caption("An Ecosystem Simulation")  # set caption

# additional surfaces
screen = displayScreen.copy()
objectSurface = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
gizmoSurface = pygame.Surface((mapWidth, mapHeight)).convert_alpha()

clock = pygame.time.Clock()  # clock to create stable fps
fps = 60  # frames per second of simulation
deltaTime = 1 / fps  # change in time between frames

# === SPRITES ===
noTexture = pygame.image.load("sprites/NoTexture.png").convert_alpha()  # sprite applied when no sprite given

# animal sprites
rabbitSprite = pygame.image.load("sprites/Rabbit.png").convert_alpha()
foxSprite = pygame.image.load("sprites/Fox.png").convert_alpha()

# plant sprites
oakSprite = pygame.image.load("sprites/Oak.png").convert_alpha()
pineSprite = pygame.image.load("sprites/Pine.png").convert_alpha()
appletree = pygame.image.load("sprites/appletree.png").convert_alpha()
apple = pygame.image.load("sprites/Apple.png").convert_alpha()
berrybushSprite = pygame.image.load("sprites/berrybush.png")
redberry = pygame.image.load("sprites/redberry.png")
blueberry = pygame.image.load("sprites/blueberry.png")

# tab sprites
biomassIcon = pygame.image.load("sprites/biomassicon.png").convert_alpha()
biomassSelected = pygame.image.load("sprites/biomassselected.png").convert_alpha()
linegraphIcon = pygame.image.load("sprites/linegraphicon.png").convert_alpha()
linegraphSelected = pygame.image.load("sprites/linegraphselected.png").convert_alpha()
backgroundUI = pygame.image.load("sprites/background.png").convert_alpha()
gridBackground = pygame.image.load("sprites/gridbackground.png").convert_alpha()

# menu sprites
UIButtonSprite = pygame.image.load("sprites/UIButton.png").convert_alpha()
UIButtonQuitSprite = pygame.image.load("sprites/UIButton-quit.png").convert_alpha()
UIFieldSprite = pygame.image.load("sprites/inputfield.png").convert_alpha()
UIFieldsBackground = pygame.image.load("sprites/fieldsbackground.png").convert_alpha()
titleBackground = pygame.transform.scale_by(pygame.image.load("sprites/stackblur.png"), 1.2)

# fonts
font = pygame.font.Font('fonts/RobotoSlab-Bold.ttf', 12)
fontUI = pygame.font.Font('fonts/Pixel.ttf', 12)

# ===== ECOSYSTEM PARAMETERS =====
# Landscape
traversableLayers = ["shallow water", "wet sand", "dry sand", "grassland", "forest"]
levelColours = [(370, (255, 255, 255)), (355, (79, 69, 61)), (330, (92, 69, 54)), (310, (79, 61, 49)),
                (300, (44, 38, 34)), (250, (70, 130, 50)), (170, (168, 202, 88)), (150, (232, 193, 112)),
                (120, (222, 158, 65)), (100, (79, 143, 186)), (80, (60, 94, 139)), (0, (37, 58, 94))]
# (for future - allow parameters to be written into separate file, for customisation of environment)

# Organisms
# (field name : value in field)
fieldDic = {
    "foxes": 2,
    "rabbits": 10,
    "pine trees": 200,
    "oak trees": 5,
    "berry bushes": 20,
    "apple trees": 5
}


# SIMULATION LOOP
# - called to start simulation
def simulation():
    global traversableCoordinates, pathfindingGrid, ground, layerCoordinates, lineGraphButton, biomassButton,\
        gizmos, speciesColourDic, biomassTotals, speciesDic, cameraGroup, populationDic, zoom, mousePosOnMiddleClick

    # ==== SETUP ====

    # GENERATE MAP
    ground, layerCoordinates = noise.generateLandscape(levelColours, mapWidth, mapHeight)  # generate map using noise
    traversableCoordinates = []
    for layer in traversableLayers:  # if layer is traversable
        traversableCoordinates += layerCoordinates[layerDic[layer]]  # add all layer coords to traversable coords

    # GENERATE PATHFINDING GRID
    pathfindingGrid = pathfinding.createTraversableGrid(ground, traversableLayers, mapWidth, gridSize)

    # INITIALISE SPRITE GROUP
    cameraGroup = CameraGroup()

    # INITIALISE BUTTONS
    buttons = ButtonCameraGroup(backgroundUI)
    lineGraphButton = Button(0, 40, "line graph", linegraphIcon, linegraphSelected, 1.05, buttons)
    biomassButton = Button(0, 74, "biomass", biomassIcon, biomassSelected, 1.05, buttons)

    gizmos = False  # if true, will display gizmos for testing

    # SPECIES ARRAYS
    foxArr = []
    hareArr = []
    berryArr = []
    appleArr = []
    speciesDic = {
        "fox": foxArr,
        "hare": hareArr,
        "berry": berryArr,
        "apple tree": appleArr
    }

    # SPECIES POPULATIONS
    foxPopulation = []
    harePopulation = []
    berryPopulation = []
    populationDic = {
        "fox": foxPopulation,
        "hare": harePopulation,
        "berry": berryPopulation
    }
    # colours to display for graphs
    speciesColourDic = {
        "fox": (255, 179, 64),
        "hare": (255, 255, 255),
        "berry": (255, 0, 0)
    }

    # SPAWNING
    biomassTotals = [0, 0, 0, 0]  # [producers, primary consumers, secondary, tertiary... ]
    spawning = True  # if true, spawn organisms in (for testing)
    if spawning:
        # ANIMALS
        sexes = ["male", "female"]
        # foxes
        for i in range(fieldDic["foxes"]):
            pos = randomPositionFromLayer("forest")  # random position in forest
            # instantiate animal object
            fox = Animal("fox", f"fox {i}", pos, cameraGroup, foxSprite, colour=(255, 179, 64),
                         maxSpeed=30, maxHealth=10, attack=5, interactInterval=1, trophicLevel=2, mass=4,
                         senseRadius=50, foodNames=["hare"], numberOfOffspring=1, hungerIncrease=0.35)
            fox.sex = sexes[i%2]
        # rabbits
        for i in range(fieldDic["rabbits"]):
            pos = randomPositionFromLayer("forest")  # random position in grassland
            # instantiate animal object
            hare = Animal("hare", f"hare {i}", pos, cameraGroup, rabbitSprite, colour=(255, 255, 255),
                          maxSpeed=40, maxHealth=2, attack=0, interactInterval=1, trophicLevel=1, mass=2,
                          senseRadius=60,
                          foodNames=["berry", "apple tree"], threatNames=["fox"], numberOfOffspring=3)

        # PLANTS
        # forest trees
        for i in range(fieldDic["pine trees"]):
            pos = randomPositionFromLayer("forest")  # random position in forest
            pine = Plant("pine", f"pine {i}", pos, cameraGroup, pineSprite,
                         timeToGrow=1000, maxHeight=10)
        # grassland trees
        for i in range(fieldDic["oak trees"]):
            pos = randomPositionFromLayer("grassland")  # random position in grassland
            oak = Plant("oak", f"oak {i}", pos, cameraGroup, oakSprite,
                        timeToGrow=1000, maxHeight=8)
        # apple trees
        for i in range(fieldDic["apple trees"]):
            pos = randomPositionFromLayer("grassland")  # random position in grassland
            oak = Plant("apple tree", f"apple tree {i}", pos, cameraGroup, appletree,
                        timeToGrow=1000, maxHeight=8,
                        foodMass=2, foodSprite=apple, centreAroundFood=Vector2(0, -2), foodSpawnRadius=6, maxFood=5)
        # berries
        for i in range(fieldDic["berry bushes"]):
            if random.randint(0, 1) == 1:
                pos = randomPositionFromLayer("forest")  # random position in forest
            else:
                pos = randomPositionFromLayer("grassland")  # random position in forest
            berry = Plant("berry", f"berry bush {i}", pos, cameraGroup, berrybushSprite,
                          timeToGrow=50, maxHeight=1, mass=1,
                          foodMass=0.2, foodSprite=random.choice([blueberry, redberry]), centreAroundFood=Vector2(),
                          foodSpawnRadius=5, maxFood=8)

    zoom = 2  # initial zoom

    while True:
        clock.tick(fps)  # tick clock with frames per second
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == secondTimer:  # every second

                # UPDATE POPULATION DATA
                for species in populationDic.keys():  # iterate through animal species
                    population = len(speciesDic[species])  # get population
                    if population > 0 and speciesDic[species][0].__class__.__name__ == "Plant":
                        population = 0
                        for plant in speciesDic[species]:
                            population += len(plant.foodPosArr)
                    populationData = populationDic[species]  # get list of population data

                    populationData.append(population)  # enqueue data to end of list
                    if len(populationData) > buttons.maxPopulationData:  # if list has reached max size
                        populationData.pop(0)  # dequeue data at front of list

            # mouse middle button to pan
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                mousePosOnMiddleClick = Vector2(pygame.mouse.get_pos())
                # go = not go

            # use mousewheel to zoom
            elif event.type == pygame.MOUSEWHEEL:
                # event.y = 1 when scrolling up, -1 when scrolling down
                zoom *= (1 + 0.1 * event.y)  # so, multiply zoom by 1.1 when scrolling up, 0.9 when scrolling down
                zoom = max(1, min(10, zoom))  # bound zoom between 1x and 10x

            # on left click
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # iterate through buttons
                for sprite in buttons.sprites():
                    sprite.press()  # check if button is pressed and select/unselect it

        # reset surfaces
        objectSurface.fill((0, 0, 0, 0))
        gizmoSurface.fill((0, 0, 0, 0))

        if go:  # if simulation is not paused
            cameraGroup.update()  # update all objects
        cameraGroup.customDraw()  # draw all objects

        displayScreen.blit(pygame.transform.scale_by(screen, zoom), (0, 0))  # scale screen by zoom

        buttons.drawUI()  # draw tabs

        pygame.display.update()  # update screen


# TITLE SCREEN LOOP
# - called to open title screen
def title():
    # code for title screen loop...

    # instantiate title buttons
    startButton = UIButton(UIButtonSprite, 2, 0.5 * Vector2(displayScreen.get_size()) + Vector2(0, -40), "Start", fontUI, "simulation",
                           (255, 255, 255), (255, 255, 255))  # start button
    customiseButton = UIButton(UIButtonSprite, 2, 0.5 * Vector2(displayScreen.get_size()), "Customise",
                               fontUI, "customise", (255, 255, 255), (255, 255, 255))  # customise button
    quitButton = UIButton(UIButtonQuitSprite, 2, 0.5 * Vector2(displayScreen.get_size()) + Vector2(0, 40), "Quit to OS",
                          fontUI, "quit", (255, 255, 255), (255, 255, 255))  # customise button
    buttons = [startButton, customiseButton, quitButton]  # button array

    # title screen loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()  # close program on quit event

            if event.type == pygame.MOUSEBUTTONDOWN:  # when mouse is clicked
                for button in buttons:  # iterate through buttons
                    button.click()  # check if clicked and carry out action

        displayScreen.blit(titleBackground, (0, 0))  # display background image

        menuMousePos = pygame.mouse.get_pos()  # get mouse position
        for button in buttons:  # iterate through buttons
            button.checkForHovering(menuMousePos)  # check if mouse is hovering over button
            button.draw()  # draw button, and outline if hovering

        pygame.display.flip()  # update display surface to screen


# CUSTOMISE MENU LOOP
# - called to open customisation menu
def customise():
    # - set up UI field objects -
    fields = []
    pos = Vector2(0.5 * displayScreen.get_width(), 200)  # position of top-most field
    # instantiate field for each changeable parameter
    for fieldKey in fieldDic.keys():
        fields.append(
            UIInputField(UIFieldSprite, 2, pos, fieldKey, fieldDic[fieldKey], fontUI, (255, 255, 255), (255, 255, 255)))
        pos += Vector2(0, 40)  # position of each field goes down the screen
    selectedField = None  # initially no field is selected

    # set up field box graphical aspects
    fieldsBackground = pygame.transform.scale_by(UIFieldsBackground, 2)  # field box background
    fieldsBackgroundRect = fieldsBackground.get_rect()
    fieldsBackgroundRect.midbottom = pos - Vector2(0, 8)

    # set up navigation buttons
    generateButton = UIButton(UIButtonSprite, 2, pos + Vector2(0, 40), "Generate", fontUI,
                              "simulation", (255, 255, 255), (255, 255, 255))  # button to generate ecosystem

    backButton = UIButton(UIButtonSprite, 2, pos + Vector2(0, 80), "Back", fontUI,
                          "title", (255, 255, 255), (255, 255, 255))  # button to go back to title screen
    buttons = [generateButton, backButton]

    maxFieldLength = 10  # maximum amount of characters in a field

    # START CUSTOMISE MENU LOOP
    while True:
        mousePos = pygame.mouse.get_pos()  # get mouse position

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()  # close program on quit event

            if event.type == pygame.MOUSEBUTTONDOWN:  # on mouse click
                for button in buttons:  # iterate through buttons
                    button.click()  # check if button is clicked and carry out action
                for field in fields:  # iterate through fields
                    if field.checkForHovering(mousePos):  # if field is clicked
                        selectedField = field  # set to selected field
                        break
                    else:
                        selectedField = None  # unselect field if mouse is clicked when hovering over no field

            if event.type == pygame.KEYDOWN and selectedField is not None:  # when key pressed
                if event.key == pygame.K_BACKSPACE:  # if backspace
                    selectedField.value = selectedField.value[:-1]  # remove last character added to string
                else:  # if any other key
                    # input validation: check if input is an integer, and limit number of characters
                    if len(selectedField.value) < maxFieldLength and validateInteger(event.unicode):
                        selectedField.value += event.unicode  # add character to string

                if selectedField.value != "":  # input validation: only update actual value if field isn't empty
                    fieldDic[selectedField.text] = int(selectedField.value)

        displayScreen.blit(titleBackground, (0, 0))  # display background image
        displayScreen.blit(fieldsBackground, fieldsBackgroundRect)  # display input field background container

        menuMousePos = pygame.mouse.get_pos()  # get mouse position
        for button in buttons:  # iterate through buttons
            button.checkForHovering(menuMousePos)  # check if mouse is over button
            button.draw()  # draw button

        if selectedField is not None:
            selectedField.drawSelectedOutline()  # draw selected field outline
        for field in fields:  # iterate through fields
            field.draw()  # draw field

        pygame.display.flip()  # update display surface to screen


go = True  # (true = simulation progresses; false = simulation paused)

# set timer that creates a pygame event every 1 second
secondTimer = pygame.USEREVENT + 1  # timer id
pygame.time.set_timer(event=secondTimer, millis=1000)  # (1000 milliseconds = 1 second)

gameState = "title"  # initial game state

# BEGIN GAME LOOP
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    if gameState == "simulation":
        simulation()  # start simulation
    elif gameState == "title":
        title()  # open title screen
    elif gameState == "customise":
        customise()  # open customisation menu
    else:
        gameState = "title"  # error occurred return to title
