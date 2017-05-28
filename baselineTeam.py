# baselineTeam.py
# ---------------
# Licensing Information:    You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(indexes, num, isRed, names=['OffensiveReflexAgent', 'DefensiveReflexAgent']):
    """
    This function should return a list of three agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.    isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """
    return [eval(name)(index) for name, index in zip(names, indexes)]
    #return [eval(first)(indexes[0]), eval(second)(indexes[1]), eval(third)(indexes[2])]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that chooses score-maximizing actions
    """
 
    def registerInitialState(self, gameState):
        """
        Each agent has two indexes, one for pacman and the other for ghost.
        self.index[0]: pacman
        self.index[1]: ghost
        """
        CaptureAgent.registerInitialState(self, gameState)   
        
        """
        overwrite distancer
        only calculate distance positions which are reachable for self team
        """
        self.red = gameState.isOnRedTeam(self.index[0])#0 or 1 doesn't mater
        wallChar = 'r' if self.red else 'b'
        
        layout = gameState.data.layout.deepCopy()
        walls = layout.walls
        for x in range(layout.width):
            for y in range(layout.height):
                if walls[x][y] is wallChar:
                    walls[x][y] = False
        
        self.distancer = distanceCalculator.Distancer(layout)
        

        # comment this out to forgo maze distance computation and use manhattan distances
        self.distancer.getMazeDistances()
        
        
        self.start = [gameState.getAgentPosition(index) for index in self.index]
        #print('mii')


    def chooseAction(self, gameState):
        if(isinstance(self, OffensiveReflexAgent)):
            return self.chooseActionImpl(gameState, self.index[0])
        else:
            return self.chooseActionImpl(gameState, self.index[1])
#         return random.choice([, ])
    def chooseActionImpl(self, gameState, index):
        """
        Picks among the actions with the highest Q(s,a).
        """
#         isPacman = gameState.getAgentState(index).isPacman
        
        actions = gameState.getLegalActions(index)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        
        act =  random.choice(bestActions)
        return act
    def getSuccessor(self, gameState, action, index):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        return gameState.generateSuccessor(index, action)

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)

        return features

    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.    They can be either
        a counter or a dictionary.
        """
        return {'successorScore': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that seeks food. This is an agent
    we give you to get an idea of what an offensive agent might look like,
    but it is by no means the best or only way to build an offensive agent.
    """
    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action, self.index[0])
        successor = self.getSuccessor(successor, action, self.index[1])
        
        foodList = self.getFood(successor).asListNot()
        features['successorScore'] = -len(foodList)#self.getScore(successor)

        # Compute distance to the nearest food
        myPos = successor.getAgentState(self.index[0]).getPosition()
        if len(foodList) > 0: # This should always be True,    but better safe than sorry
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance
        
        capsulesList = self.getCapsules(successor)
        features['capsule'] = -len(capsulesList)
#         if len(capsulesList) > 0:
#             minDistance = min([self.getMazeDistance(myPos, capsule) for capsule in capsulesList])
#             features['distanceToCapsule'] = minDistance
        
        score = (successor.getScore()-gameState.getScore())
        if(not self.red):
            score=-score;
        features['score'] = score
        
        return features

    def getWeights(self, gameState, action):
        return {'successorScore': 100, 'distanceToFood': -5, 'capsule':150, 'score': 200}

class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.    It is not the best or only way to make
    such an agent.
    """

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action, self.index[0])
        successor = self.getSuccessor(successor, action, self.index[1])
        
        
        myState = successor.getAgentState(self.index[1])
        myPos = myState.getPosition()
        initialPos = gameState.getInitialAgentPosition(self.index[1])



        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        #invaders = [a for a in enemies if a.isPacman and self.getMazeDistance(myPos, a.getPosition())<1000]
        invaders = []
        for enemy in enemies:
            if enemy.isPacman and self.getMazeDistance(initialPos, enemy.getPosition())< 25:
                invaders.append(enemy)
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)
        else:
            features['invaderDistance'] = 0

        if action == Directions.STOP: features['stop'] = 1
#         rev = Directions.REVERSE[myState.configuration.direction]
#         if action == rev: features['reverse'] = 1
        score = (successor.getScore()-gameState.getScore())
        if(not self.red):
            score=-score;
        features['score'] = score
        return features

    def getWeights(self, gameState, action):
        return  {'numInvaders': -100, 'invaderDistance': -5, 'stop': -5, 'score':200}
