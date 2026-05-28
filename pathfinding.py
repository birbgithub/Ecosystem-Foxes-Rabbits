import pygame
from pygame import Vector2
import math

# ---PATHFINDING---
# Contains:
# - node class
# - grid creation functions
# - A* algorithm


# Class for node in pathfinding grid
# Contains attributes for position, G cost, Heuristic, previous node, and a boolean for if it can be traversed
# Method to get the final cost, method to reset the node
class Node:
    def __init__(self, pos):
        self.pos = pos  # 2D vector position
        self.G = 0  # G cost (distance from start)
        self.H = 0  # heuristic (estimate of distance to end)
        self.prevNode = None  # previous node in path
        self.traversable = True  # can node be traversed?

    # call to get final cost of node (G cost + Heuristic)
    def getCost(self):
        return self.G + self.H  # cost = distance from start + estimated distance to end

    # call to reset node to default values
    def reset(self):
        self.G = 0  # reset G cost
        self.H = 0  # reset Heuristic
        self.prevNode = None  # reset previous node


# Initialises 2D array of empty nodes
# - takes input for size (width and height of grid), and returns grid as 2D array
def createGrid(size):
    # size must be a factor of the pixel size of the simulation
    grid = []
    for x in range(size):
        row = []
        for y in range(size):
            row.append(Node(Vector2(x, y)))  # instantiate new node at (x, y) in grid
        grid.append(row)
    return grid


# Creates final pathfinding grid from generated landscape,
# where nodes are set to untraversable if they intersect with impassable areas of terrain (e.g. mountains, ocean)
# - takes inputs for ground surface, traversable layers, map size, and grid size
# - returns grid of nodes as 2D array
def createTraversableGrid(ground, traversableLayers, mapSize, gridSize):
    grid = createGrid(gridSize)  # create base grid of nodes
    scale = mapSize / gridSize  # scalar of grid to map size

    for x in range(mapSize):
        for y in range(mapSize):
            value = ground.get_at((x, y))  # get colour of ground at (x, y)
            if groundDic[str(value)] not in traversableLayers:  # if ground is not traversable
                xGrid, yGrid = int(x/scale), int(y/scale)  # convert map position to grid position
                grid[xGrid][yGrid].traversable = False  # set node at grid to be untraversable
    return grid


# Creates path between start node and target node
# - takes inputs for start node, target node, 2D grid of nodes, and grid scale
# - returns path of coordinates (2D array of vector2s in terms of pixels)
def createPath(startNode, targetNode, grid, gridScale):
    Open = [startNode]  # available nodes to visit
    Closed = []  # visited nodes
    gridSize = len(grid)
    while True:
        # Finds node with lowest cost in 'open'
        cost = math.inf  # arbitrarily large number
        currentNode = None
        # iterates through available nodes
        for node in Open:
            if node.getCost() < cost:  # if cost is less than current lowest cost,
                currentNode = node  # set as current cheapest node
                cost = node.getCost()

        if currentNode is None:
            print("searched every node, can't reach target")
            for node in Open + Closed:
                node.reset()
            return []

        # Visits node with lowest cost
        Open.remove(currentNode)
        Closed.append(currentNode)

        # If target is reached, go backwards through nodes to return path
        if currentNode == targetNode:
            path = []
            # previous node of start node is None, so stop loop once start node is reached
            while currentNode is not None:
                path.append(currentNode.pos * gridScale)  # add node position to path
                currentNode = currentNode.prevNode  # go back to previous node

            # reset all nodes
            for node in Open + Closed:
                node.reset()

            return path[::-1]  # reverses path, so it is in correct order of Start to End node

        # If target isn't reached, continue algorithm
        else:
            # Loop through neighbours of current node
            for i in range(3):
                for j in range(3):
                    neighbourPos = currentNode.pos + Vector2(i-1, j-1)
                    x, y = neighbourPos.x, neighbourPos.y
                    if y >= gridSize or y < 0 or x >= gridSize or x < 0:
                        continue  # ignore if node is outside grid

                    neighbour = grid[int(x)][int(y)]  # neighbour node of current node

                    if not neighbour.traversable or neighbour in Closed:
                        continue  # ignore if neighbour node is untraversable or already visited

                    if abs(i) == abs(j):
                        d = 1.42  # diagonal distance
                    else:
                        d = 1  # vertical/horizontal distance

                    newG = d + currentNode.G  # G cost of neighbour = d + G cost of current node

                    if newG < neighbour.G:  # if new cost smaller than current cost
                        neighbour.G = newG  # set cost to new cost
                        neighbour.prevNode = currentNode  # set previous node of neighbour to current node

                    elif neighbour.G == 0:  # if node isn't  in Open, G will be its default of 0
                        neighbour.H = heuristic(neighbour.pos.x, neighbour.pos.y,
                                                 targetNode.pos.x, targetNode.pos.y)  # estimate heuristic with pythagoras
                        neighbour.G = newG  # set cost to new cost
                        neighbour.prevNode = currentNode  # set previous node of neighbour to current node
                        Open.append(neighbour)  # add node to Open


# displays path on screen
# (for testing)
# - takes inputs for path of coords, and gizmo surface
# - returns updated gizmo surface with path drawn on
def drawPath(path, gizmoSurface):
    prevPos = path[0]
    for i in range(len(path) - 1):  # iterates through points along path
        pos = path[i+1]  # next adjacent point to previous point
        pygame.draw.line(gizmoSurface, (255, 255, 255, 200), (prevPos.x + 2, prevPos.y + 2),
                         (pos.x + 2, pos.y + 2), width=1)  # Draw line
        pygame.draw.rect(gizmoSurface, (255, 255, 255, 200), pygame.Rect(pos.x, pos.y, 4, 4))  # Draw waypoint
        prevPos = pos
    return gizmoSurface


# heuristic calculation: to find an estimate of the distance from a node to the end node
# - takes inputs for x and y positions of two nodes
# - returns the straight distance between them with pythagoras
def heuristic(x1, y1, x2, y2):
    return ((x2-x1)**2 + (y2-y1)**2)**0.5  # pythagoras


# displays input pathfinding grid (for testing)
# where traversable nodes are white, and untraversable nodes are black
def displayGridMap(grid):
    size = len(grid)  # size of grid
    gridSurface = pygame.Surface((size, size))  # set up surface
    # iterate through nodes
    for x in range(size):
        for y in range(size):
            if grid[x][y].traversable:  # if node is traversable
                gridSurface.set_at((x, y), (255, 255, 255))  # set to white
            else:  # if node is not traversable
                gridSurface.set_at((x, y), (0, 0, 0))  # set to black
    return gridSurface  # return black-white grid surface

# converts pixel colour to landscape layer
groundDic = {
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
