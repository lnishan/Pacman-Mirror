# layout.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

from collections import defaultdict
from util import manhattanDistance
from game import Grid
import os
import random

VISIBILITY_MATRIX_CACHE = {}

class Layout:
    """
    A Layout manages the static information about the game board.
    """

    def __init__(self, layoutText):
        layoutText = self.mirror(layoutText)
        
        self.width = len(layoutText[0])
        self.height= len(layoutText)
        self.walls = Grid(self.width, self.height, False)
        self.food = Grid(self.width, self.height, False)
        self.capsules = []
        self.agentPositions = []
        
        
        self.transport = defaultdict(list)
        
        self.processLayoutText(layoutText)
        self.layoutText = layoutText
        self.totalFood = len(self.food.asList())
        
        
        for char in self.transport.keys():
            posList = self.transport[char]
            self.transport[posList[0]]=posList[1]
            self.transport[posList[1]]=posList[0]
            del self.transport[char]

        # self.initializeVisibilityMatrix()
    def mirrorChar(self, char):
        mirror_dict ={
            'A':'B', 'B':'A', 'C':'D', 'D':'C', 'E':'F', 'F':'E', 
            '1':'2', '2':'1', '3':'4', '4':'3', '5':'6', '6':'5',
            '(':']', ']':'(', '{':'>', '>':'{',
            ')':'[', '[':')', '}':'<', '<':'}',
            'r':'b', 'b':'r'
        }
        if char in mirror_dict:
            return mirror_dict[char]
        else:
            return char
    def mirror(self, layoutText):

        for y in range(len(layoutText)-1, -1, -1):
            next_str = ''
            for char in reversed(layoutText[y]):
                next_str+=self.mirrorChar(char)
            layoutText.append(next_str) 
        return layoutText
    def getNumGhosts(self):
        return len(self.agentPositions)/2

    def initializeVisibilityMatrix(self):
        global VISIBILITY_MATRIX_CACHE
        if reduce(str.__add__, self.layoutText) not in VISIBILITY_MATRIX_CACHE:
            from game import Directions
            vecs = [(-0.5,0), (0.5,0),(0,-0.5),(0,0.5)]
            dirs = [Directions.NORTH, Directions.SOUTH, Directions.WEST, Directions.EAST]
            vis = Grid(self.width, self.height, {Directions.NORTH:set(), Directions.SOUTH:set(), Directions.EAST:set(), Directions.WEST:set(), Directions.STOP:set()})
            for x in range(self.width):
                for y in range(self.height):
                    if self.walls[x][y] == False:
                        for vec, direction in zip(vecs, dirs):
                            dx, dy = vec
                            nextx, nexty = x + dx, y + dy
                            while (nextx + nexty) != int(nextx) + int(nexty) or not self.walls[int(nextx)][int(nexty)] :
                                vis[x][y][direction].add((nextx, nexty))
                                nextx, nexty = x + dx, y + dy
            self.visibility = vis
            VISIBILITY_MATRIX_CACHE[reduce(str.__add__, self.layoutText)] = vis
        else:
            self.visibility = VISIBILITY_MATRIX_CACHE[reduce(str.__add__, self.layoutText)]


    def getRandomLegalPosition(self):
        x = random.choice(range(self.width))
        y = random.choice(range(self.height))
        while self.isWall( (x, y) ):
            x = random.choice(range(self.width))
            y = random.choice(range(self.height))
        return (x,y)

    def getRandomCorner(self):
        poses = [(1,1), (1, self.height - 2), (self.width - 2, 1), (self.width - 2, self.height - 2)]
        return random.choice(poses)

    def getFurthestCorner(self, pacPos):
        poses = [(1,1), (1, self.height - 2), (self.width - 2, 1), (self.width - 2, self.height - 2)]
        dist, pos = max([(manhattanDistance(p, pacPos), p) for p in poses])
        return pos

    def isVisibleFrom(self, ghostPos, pacPos, pacDirection):
        row, col = [int(x) for x in pacPos]
        return ghostPos in self.visibility[row][col][pacDirection]

    def __str__(self):
        return "\n".join(self.layoutText)

    def deepCopy(self):
#          layout = Layout()
#          layout.witdh = self.width
#          layout.height = self.height
#          layout.walls = self.walls
#          layout.food = self.food
#          layout.capsules = self.capsules
#         layout.agentPositions = self.agentPositions
#         layout.transport = self.transport
#         
#         self.processLayoutText(layoutText)
#         self.layoutText = layoutText
#         self.totalFood = len(self.food.asList())
#         
#         
#         for char in self.transport.keys():
#             posList = self.transport[char]
#             self.transport[posList[0]]=posList[1]
#             self.transport[posList[1]]=posList[0]
#             del self.transport[char]
#         
        return Layout(self.layoutText[:self.height/2])
    
#         return self

    def processLayoutText(self, layoutText):
        """
        Coordinates are flipped from the input format to the (x,y) convention here

        The shape of the maze.  Each character
        represents a different type of object.
         % - Wall
         . - Food
         o - Capsule
         G - Ghost
         P - Pacman
		 F - Flag
        Other characters are ignored.
        """
        maxY = self.height - 1
        for y in range(self.height):
            for x in range(self.width):
                layoutChar = layoutText[maxY - y][x]
                self.processLayoutChar(x, y, layoutChar)
        self.agentPositions.sort()
        self.agentPositions = [ ( i<='6', pos) for i, pos in self.agentPositions]

    def processLayoutChar(self, x, y, layoutChar):
        if layoutChar == '%':
            self.walls[x][y] = True
        elif layoutChar in ['r', 'b']:
            self.walls[x][y] = layoutChar
        elif layoutChar == '.':
            self.food[x][y] = 10
        elif layoutChar == '+':
            self.food[x][y] = 50
        elif layoutChar == 'o':
            self.capsules.append((x, y))
        # A~F: ghosts
        elif layoutChar in ['A', 'B', 'C', 'D', 'E', 'F']:
            self.agentPositions.append( (layoutChar, (x, y) ) )
        # 1~6: pacmans
        elif layoutChar in  ['1', '2', '3', '4', '5', '6']:
            self.agentPositions.append( (layoutChar, (x,y)))
            
        elif layoutChar in ['(', ')', '[', ']', '{', '}', '<', '>']:
            self.transport[layoutChar].append((x, y))
            

def getLayout(name, back = 2):
    if name.endswith('.lay'):
        layout = tryToLoad('layouts/' + name)
        if layout == None: layout = tryToLoad(name)
    else:
        layout = tryToLoad('layouts/' + name + '.lay')
        if layout == None: layout = tryToLoad(name + '.lay')
    if layout == None and back >= 0:
        curdir = os.path.abspath('.')
        os.chdir('..')
        layout = getLayout(name, back -1)
        os.chdir(curdir)
    return layout

def tryToLoad(fullname):
    if(not os.path.exists(fullname)): return None
    f = open(fullname)
    try: return Layout([line.strip() for line in f])
    finally: f.close()
