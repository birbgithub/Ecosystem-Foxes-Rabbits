import numpy as np
from perlin_numpy import generate_fractal_noise_2d
import pygame
from pygame import Vector2
from random import randint

# ---NOISE FILE---
# - generates perlin noise map
# - turns noise into terrain


# GENERATE NOISE MAP - to create a 2D array of perlin noise
# -takes inputs-
# width, height, aspect ratio (for monitor resolution)
# octaves, and persistence (for type of noise generated)
# -returns-
# noise as 2D array of floats between 0 and 1
def generateNoiseMap(width=512, height=512, res=(1, 1), octaves=9, persistence=0.6):
    seed = randint(1, 1000000)
    print(seed)
    np.random.seed(846597)
    # create 2D noise array with library
    noise = generate_fractal_noise_2d((width, height), res=res, octaves=octaves, persistence=persistence)

    # conversion to values between 0 and 1
    Max = np.max(noise)
    Min = np.min(noise)
    noise = (noise - Min)/(Max - Min)
    # subtracts every value in array by Min,
    # then divides by the difference between Max and Min
    return noise


# GENERATE LANDSCAPE - to create a procedurally generated landscape
# takes inputs: width, height, and distribution of layers
# returns: image of landscape, and a list of coordinates for each layer
def generateLandscape(levelColours, width, height):
    ground = pygame.Surface((width, height))  # pygame surface to display ground

    noiseArr = 400 * generateNoiseMap(width, height)  # generates noise, 400m is highest point

    # create 2D array to hold coordinates of each layer
    numberOfLayers = len(levelColours)
    layerCoordinates = [[] for i in range(numberOfLayers)]

    # iterate through every value in noise array
    for x in range(width):
        for y in range(height):
            value = noiseArr[x][y]  # noise value at (x, y)
            # iterate through colours of each level - (Height, (R, G, B))
            # e.g. (370, (255, 255, 255)), above 370m there is snow
            for i in range(numberOfLayers):
                colour = levelColours[i]
                if value >= colour[0]:  # 0 = minimum height of colour# 1 = RGB value
                    ground.set_at((x, y), colour[1])  # 1 = RGB value

                    pos = Vector2(x, y)  # vector 2 position of pixel
                    layerCoordinates[i].append(pos)  # add position to list of coordinates of biome
                    break
    return ground, layerCoordinates  # returns image of landscape, and a list of coordinates of each layer
