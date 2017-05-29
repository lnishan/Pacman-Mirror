# myTeam.py
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


from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, math
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(indexes, num, isRed, names=['HahaAgent','HahaAgent']):
    """
    This function should return a list of agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.    isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments, which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.
    return [eval(name)(index) for name, index in zip(names, indexes)]

##########
# Agents #
##########

class SmileAgent(CaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

        self.red = gameState.isOnRedTeam(self.index[0])
        wallChars = ['r', 'b']

        layout = gameState.data.layout.deepCopy()
        walls = layout.walls
        for x in range(layout.width):
            for y in range(layout.height):
                if walls[x][y] in wallChars:
                    walls[x][y] = False

        self.distancer = distanceCalculator.Distancer(layout)
        self.distancer.getMazeDistances()

        self.start = [gameState.getAgentPosition(index) for index in self.index]

    # (isRedSide = True) the higher, the better for (blue) pacmans
    def evaluationFunction(self, currentGameState, isRedSide = True, agent = 0, action = Directions.STOP):

        nextGameState = currentGameState.generateSuccessor(agent, action)

        # base scores of [Food, Capsule, Ghost]
        baseScores = [-100.0, -150.0, -75.0] if agent <= 3 else [-50.0, -100.0, -300000.0]
        decayFacts = [0.3, 0.3, 0.1]  if agent <= 3 else [0.3, 0.3, 0.01]
        # pos = currentGameState.getPacmanPosition()
        pacmanIndices = [1, 3] if isRedSide else [0, 2]
        ghostIndices = [4, 6] if isRedSide else [5, 7]
        currentPacmanPositions = [currentGameState.getAgentPosition(p) for p in pacmanIndices]
        nextPacmanPositions = [nextGameState.getAgentPosition(p) for p in pacmanIndices]
        currentGhostPositions = [currentGameState.getAgentPosition(g) for g in ghostIndices]
        nextGhostPositions = [nextGameState.getAgentPosition(g) for g in ghostIndices]

        score = 0.0

        score += nextGameState.getScore()
        if not isRedSide: score = -1.0 * score

        foodList = nextGameState.getRedFood().asListNot() if isRedSide else nextGameState.getBlueFood().asListNot()
        score -= 200.0 * len(foodList)

        for food in foodList:
            minDist = min(self.getMazeDistance(p, food) for p in nextPacmanPositions)
            # minDist = min(util.manhattanDistance(p, food) for p in pacmanPositions)
            score += baseScores[0] * (1.0 - math.exp(-1.0 * decayFacts[0] * minDist))

        # capsuleList = currentGameState.data.capsules
        capsuleList = nextGameState.getCapsules()
        for capsule in capsuleList:
            minDist = sum(self.getMazeDistance(p, capsule) for p in nextPacmanPositions)
            # minDist = min(util.manhattanDistance(p, capsule) for p in pacmanPositions)
            score += baseScores[1] * (1 - math.exp(-1.0 * decayFacts[1] * minDist))

        # ghostList = currentGameState.getGhostPositions()
        for ghost in nextGhostPositions:
            minDistNaive = min(self.getMazeDistance(p, ghost) for p in currentPacmanPositions)
            minDist = min(self.getMazeDistance(p, ghost) for p in currentPacmanPositions + nextPacmanPositions)
            # minDist = min(util.manhattanDistance(p, ghost) for p in pacmanPositions)
            baseScore = baseScores[2] if minDist >= 4 else -1e6
            score += baseScore * math.exp(-1.0 * decayFacts[2] * minDist)

        if action == Directions.STOP: score -= 300.0

        return score

    def chooseAction(self, gameState):
        bestScore = -1e100
        bestActions = []
        decisions = []
        # for i in range(2):
        # i = 0 => move pacman
        i = 0 if self.index[0] <= 1 else 1
        actions = gameState.getLegalActions(self.index[i])
        for action in actions:
            score = self.evaluationFunction(gameState, self.red ^ (i == 0), self.index[i], action)
            if i == 1: score = -1.0 * score
            if score > bestScore:
                bestScore = score
                bestActions = [action]
            elif score == bestScore:
                bestActions.append(action)
            decisions.append( (score, action) )
        # if i == 1: print(decisions)
        return random.choice(bestActions)


class HahaAgent(CaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

        self.red = gameState.isOnRedTeam(self.index[0])
        wallChars = ['r', 'b']

        layout = gameState.data.layout.deepCopy()
        walls = layout.walls
        for x in range(layout.width):
            for y in range(layout.height):
                if walls[x][y] in wallChars:
                    walls[x][y] = False

        self.distancer = distanceCalculator.Distancer(layout)
        self.distancer.getMazeDistances()

        self.start = [gameState.getAgentPosition(index) for index in self.index]

    # (isRedSide = True) the higher, the better for (blue) pacmans
    def evaluationFunction(self, currentGameState, isRedSide=True):

        # base scores of [Food, Capsule, Ghost]
        baseScores = [-50.0, -100.0, -1000.0]
        decayFacts = [0.3, 0.3, 0.15]
        # pos = currentGameState.getPacmanPosition()
        pacmanIndices = [1, 3] if isRedSide else [0, 2]
        ghostIndices = [4, 6] if isRedSide else [5, 7]
        currentPacmanPositions = [currentGameState.getAgentPosition(p) for p in pacmanIndices]
        currentGhostPositions = [currentGameState.getAgentPosition(g) for g in ghostIndices]

        score = 0.0

        score += 10.0 * currentGameState.getScore()
        if not isRedSide: score = -1.0 * score

        foodList = currentGameState.getRedFood().asListNot() if isRedSide else currentGameState.getBlueFood().asListNot()
        score -= 200.0 * len(foodList)

        for food in foodList:
            minDist = min(self.getMazeDistance(p, food) for p in currentPacmanPositions)
            # minDist = min(util.manhattanDistance(p, food) for p in pacmanPositions)
            score += baseScores[0] * (1.0 - math.exp(-1.0 * decayFacts[0] * minDist))

        # capsuleList = currentGameState.data.capsules
        capsuleList = currentGameState.getCapsules()
        for capsule in capsuleList:
            minDist = sum(self.getMazeDistance(p, capsule) for p in currentPacmanPositions)
            # minDist = min(util.manhattanDistance(p, capsule) for p in pacmanPositions)
            score += baseScores[1] * (1 - math.exp(-1.0 * decayFacts[1] * minDist))

        # ghostList = currentGameState.getGhostPositions()
        for ghost in currentGhostPositions:
            minDist = min(self.getMazeDistance(p, ghost) for p in currentPacmanPositions)
            # minDist = min(util.manhattanDistance(p, ghost) for p in pacmanPositions)
            baseScore = baseScores[2] if minDist >= 2 else -1e6
            score += baseScore * math.exp(-1.0 * decayFacts[2] * minDist)

        return score

    def evaluationFunctionAll(self, currentGameState):
        return max(self.evaluationFunction(currentGameState, True), self.evaluationFunction(currentGameState, False))

    """
    Only 4-multiple depths (to be fixed)
    Minimax Tree
    - Max (depth % 4 = 0) Starting Agent
    - Max (depth % 4 = 3) Teammate
    - Min (depth % 4 = 2) Opponent Agent 1
    - Min (depth % 4 = 1) Opponent Agent 2
    """
    def minimax(self, state, depth, a, b, agent):
        if depth == 0 or state.isOver():
            return self.evaluationFunctionAll(state), Directions.STOP
        actions = state.getLegalActions(agent)
        mod4 = depth % 4
        maximizing = mod4 in [0, 3]
        if maximizing:
            bestScore = -1e40
            bestActions = []
            for action in actions:
                nextState = state.generateSuccessor(agent, action)
                nextIndices = []
                if mod4 is 0:
                    nextIndices = [2, 6] if agent in [0, 4] else [3, 7]
                else:
                    nextIndices = [1, 5] if agent in [2, 6] else [0, 4]
                score = max(self.minimax(nextState, depth - 1, a, b, i)[0] for i in nextIndices)
                a = max(a, score)
                if score > bestScore:
                    bestScore = score
                    bestActions = [action]
                elif score == bestScore:
                    bestActions.append(action)
                if bestScore > b: break
            return bestScore, random.choice(bestActions)
        else:
            bestScore = 1e40
            bestActions = []
            for action in actions:
                nextState = state.generateSuccessor(agent, action)
                nextIndices = []
                if mod4 is 2:
                    nextIndices = [2, 6] if agent in [0, 4] else [3, 7]
                else:
                    nextIndices = [1, 5] if agent in [2, 6] else [0, 4]
                score = min(self.minimax(nextState, depth - 1, a, b, i)[0] for i in nextIndices)
                b = min(b, score)
                if score < bestScore:
                    bestScore = score
                    bestActions = [action]
                elif score == bestScore:
                    bestActions.append(action)
                if a > bestScore: break
            return bestScore, random.choice(bestActions)

    def chooseAction(self, gameState):
        decisions = [self.minimax(gameState, 4, -1e40, 1e40, i) for i in self.index]
        # print(decisions)
        return decisions[0][1] if decisions[0][0] > decisions[1][0] else decisions[1][1]


class DummyAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).

        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)

        IMPORTANT: This method may run for at most 15 seconds.
        """
        
        
        """
    	you can have your own distanceCalculator. (you can even have multiple distanceCalculators, if you need.)
    	reference the registerInitialState function in captureAgents.py and baselineTeam.py to understand more about the distanceCalculator. 
    	"""

        """
        Each agent has two indexes, one for pacman and the other for ghost.
        self.index[0]: pacman
        self.index[1]: ghost
        """

        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        CaptureAgent.registerInitialState(self, gameState)

        '''
        Your initialization code goes here, if you need any.
        '''


    def chooseAction(self, gameState):
        """
        Picks among actions randomly.
        """
        actions = gameState.getLegalActions(self.index[0])

        '''
        You should change this in your own agent.
        '''

        return random.choice(actions)

