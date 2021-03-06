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

def createTeam(indexes, num, isRed, names=['SmileAgent','SmileAgent']):
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

class SlidingWindow:

    def __init__(self, windowSize = 100, default = 0):
        self.list = [default] * windowSize

    # DO NOT use in public
    def pop(self):
        self.list.pop()

    def insert(self, item):
        self.pop()
        self.list.insert(0, item)

    def front(self):
        return self.list[-1]

    def sum(self):
        return sum(self.list)

    def size(self):
        return len(self.list)


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

        self.role = 0 if self.index[0] <= 1 else 1

        self.foodEatenHistory = SlidingWindow(130, 1)
        self.foodEatenHistorySum = self.foodEatenHistory.sum()

        self.isStalling = False


    def isPacman(self, agent):
        return agent <= 3

    def isGhost(self, agent):
        return agent > 4

    def scoreDiff(self, currentGameState, nextGameState):
        currentScore = currentGameState.getScore()
        if not self.red: currentScore *= -1
        nextScore = nextGameState.getScore()
        if not self.red: nextScore *= -1
        return nextScore - currentScore

    def isGhostScared(self, gameState, ghost):
        # 8 actions until the next turn, 3 moves for safety margins
        return gameState.getAgentState(ghost).scaredTimer - 8 * 3 > 0

    def evaluationPacman(self, currentGameState, pacman = 0, action = Directions.STOP):
        nextGameState = currentGameState.generateSuccessor(pacman, action)
        baseScores = [-300.0, -1800.0, -100.0]
        decayFacts = [0.3, 0.3, 0.3]

        ghostIndices = [5, 7] if self.red else [4, 6]
        currentPacmanPosition = currentGameState.getAgentPosition(pacman)
        nextPacmanPosition = nextGameState.getAgentPosition(pacman)
        currentGhostPositions = [currentGameState.getAgentPosition(g) for g in ghostIndices]
        nextGhostPositions = [nextGameState.getAgentPosition(g) for g in ghostIndices]

        score = 0.0

        if self.scoreDiff(currentGameState, nextGameState) <= -100: # got eaten
            return -1e7

        if self.isStalling:
            minDist = min([self.getMazeDistance(nextPacmanPosition, g) for g in currentGhostPositions])
            score -= 1e7 * math.exp(-0.1 * minDist)
            if action == Directions.STOP:
                score -= 30000.0
            return score

        score += 10.0 * nextGameState.getScore()
        if not self.red: score = -1.0 * score

        foodList = nextGameState.getBlueFood().asListNot() if self.red else nextGameState.getRedFood().asListNot()
        capsuleList = nextGameState.getCapsules()
        numGhostScared = sum(self.isGhostScared(currentGameState, g) for g in ghostIndices)

        """
        (Bug)
        Originally written this way to account for eaten food for this action
        Since the length of the list is unreliable, we try to use hasFood instead
        score -= 300.0 * len(foodList)
        """
        if currentGameState.hasFood(nextPacmanPosition[0], nextPacmanPosition[1]) == 50:
            score += 300.0
        if numGhostScared > 0:
            score -= 900.0 * numGhostScared
        else:
            score -= 1800.0 * len(capsuleList)
            for capsule in capsuleList:
                dist = self.getMazeDistance(nextPacmanPosition, capsule)
                score += baseScores[1] * (1.0 - math.exp(-1.0 * decayFacts[1] * dist))
        for food in foodList:
            dist = self.getMazeDistance(nextPacmanPosition, food)
            score += baseScores[0] * (1.0 - math.exp(-1.0 * decayFacts[0] * dist))
        # for ghost in currentGhostPositions:
        for i in range(2):
            ghost = currentGhostPositions[i]
            dist = self.getMazeDistance(nextPacmanPosition, ghost)
            if self.isGhostScared(currentGameState, ghostIndices[i]):
                baseScore = 90000.0 if dist >= 3 else 900000.0
            else:
                baseScore = baseScores[2] if dist >= 3 else -2e6
            score += baseScore * math.exp(-1.0 * decayFacts[2] * dist)
        if action == Directions.STOP: score -= 2e5

        return score

    def evaluationGhost(self, currentGameState, ghost, action = Directions.STOP):
        nextGameState = currentGameState.generateSuccessor(ghost, action)
        baseScores = [-300.0, -1800.0, -90000.0]
        decayFacts = [0.3, 0.3, 0.3]

        pacmanIndices = [1, 3] if self.red else [0, 2]
        currentPacmanPositions = [currentGameState.getAgentPosition(p) for p in pacmanIndices]
        nextPacmanPositions = [nextGameState.getAgentPosition(p) for p in pacmanIndices]
        nextGhostPosition = nextGameState.getAgentPosition(ghost)

        score = 0.0

        score += 10.0 * nextGameState.getScore()
        if not self.red: score = -1.0 * score

        foodList = nextGameState.getRedFood().asListNot() if self.red else nextGameState.getBlueFood().asListNot()
        capsuleList = nextGameState.getCapsules()

        threats = []
        for pacman in currentPacmanPositions: # calculate threat -> the lower, the worse for ghost
            threats.append( sum(baseScores[0] * math.exp(-1.0 * decayFacts[0] * self.getMazeDistance(pacman, food)) for food in foodList) )
            # threatCalibrated = threat * (1.0 - math.exp(-1.0 * decayFacts[2] * self.getMazeDistance(nextGhostPosition, pacman)))
            # print('{} = {} => {} '.format(pacman, threat, threatCalibrated))
            # score -= threatCalibrated

        dist = 0
        if threats[0] < threats[1]:
            dist = self.getMazeDistance(nextGhostPosition, currentPacmanPositions[0])
        else:
            dist = self.getMazeDistance(nextGhostPosition, currentPacmanPositions[1])
        score += baseScores[2] * math.exp(decayFacts[2] * dist)
        """ Do not consider capsules temporarily
        for capsule in capsuleList:
            minDist = min(self.getMazeDistance(p, capsule) for p in nextPacmanPositions)
            score += baseScores[1] * (math.exp(-1.0 * decayFacts[1] * minDist))
        """

        # print('ghost index = {}, score of {} is {}'.format(ghost, action, score))

        return score

    def chooseActionGhostNaive(self, gameState, ghost, pacman):
        actions = gameState.getLegalActions(ghost)
        minDist = 1e100
        minDecisions = []
        for action in actions:
            successorGameState = gameState.generateSuccessor(ghost, action)
            ghostPos = successorGameState.getAgentPosition(ghost)
            dist = self.getMazeDistance(ghostPos, gameState.getAgentPosition(pacman))
            if dist < minDist:
                minDist = dist
                minDecisions = [(successorGameState, minDist)]
            elif dist == minDist:
                minDecisions.append((successorGameState, minDist))
        return random.choice(minDecisions)

        # want to optimize this through raw map data in gameState

    def chooseActionPacmanNaive(self, gameState, agent):
        """
        This function assumes agent is an index belonging to a pacman
        """
        bestScore = -1e100
        bestActions = []
        actions = gameState.getLegalActions(agent)
        for action in actions:
            score = self.evaluationPacman(gameState, self.index[0], action)
            if score > bestScore:
                bestScore = score
                bestActions = [action]
            elif score == bestScore:
                bestActions.append(action)

        actionTaken = random.choice(bestActions)
        return (gameState.generateSuccessor(agent, actionTaken), bestScore)
        # print(ghostIndices)

    def chooseActionPacmanSafer(self, gameState, agent, depth = 3):
        ghostIndices = [i for i in self.getOpponents(gameState) if i >= 4]
        actions = gameState.getLegalActions(agent)
        scoresCalibrated = []
        # decisions = []
        # print('-')
        for action in actions:
            s = gameState.generateSuccessor(agent, action)
            score = self.evaluationPacman(gameState, self.index[0], action)
            depthSurvive = 1e10
            # print('-- action: {}'.format(action))
            for i in range(depth):
                result = self.chooseActionGhostNaive(s, ghostIndices[0], agent)
                if result[1] == 0:
                    depthSurvive = i
                    break
                result = self.chooseActionGhostNaive(result[0], ghostIndices[1], agent)
                if result[1] == 0:
                    depthSurvive = i
                    break
                # print('--- depth {}: {} {} {}'.format(i, result[0].getAgentPosition(agent), result[0].getAgentPosition(ghostIndices[0]), result[0].getAgentPosition(ghostIndices[1])))
                previousGameState = result[0]
                result = self.chooseActionPacmanNaive(result[0], agent)
                if self.scoreDiff(previousGameState, result[0]) <= -100: # got eaten
                    depthSurvive = i + 1
                    break
                s = result[0]
            scoresCalibrated.append( score - 2e6 * math.exp(-0.5 * depthSurvive) ) # can use something other than e as long as it's > 1
            # decisions.append((action, score, scoresCalibrated[-1]))
        # if self.isStalling: print(decisions)
        bestScore = max(scoresCalibrated)
        bestIndices = [i for i in range(len(scoresCalibrated)) if scoresCalibrated[i] == bestScore]
        return actions[random.choice(bestIndices)]

    def recordHistory(self, currentGameState, action):
        foodList = currentGameState.getBlueFood().asListNot() if self.red else currentGameState.getRedFood().asListNot()
        nextGameState = currentGameState.generateSuccessor(self.index[self.role], action)
        self.foodEatenHistorySum -= self.foodEatenHistory.front()
        if nextGameState.getAgentPosition(self.index[self.role]) in foodList:
            self.foodEatenHistory.insert(1)
            self.foodEatenHistorySum += 1
        else:
            self.foodEatenHistory.insert(0)
        # if self.role == 0: print((self.foodEatenHistorySum, self.foodEatenHistory.list))

    def respondHistory(self, gameState):
        if self.role == 0:
            ghostIndices = [i for i in self.getOpponents(gameState) if i >= 4]
            ghostPositions = [gameState.getAgentPosition(g) for g in ghostIndices]
            minDist = min([self.getMazeDistance(gameState.getAgentPosition(self.index[self.role]), g) for g in ghostPositions])
            if self.isStalling:
                if minDist >= 15 or self.foodEatenHistorySum > 20:
                    self.isStalling = False
                    self.foodEatenHistory = SlidingWindow(self.foodEatenHistory.size(), 1)
                    self.foodEatenHistorySum = self.foodEatenHistory.sum()
            elif self.foodEatenHistorySum <= 5 and minDist < 15: # 5/100 => less than or equal to 5%
                self.isStalling = True
            # print(self.isStalling)

    def chooseAction(self, gameState):
        bestScore = -1e100
        bestActions = []
        # decisions = []
        # role = 0 => move pacman
        if self.role == 0:
            action = self.chooseActionPacmanSafer(gameState, self.index[0], 3)
        else:
            actions = gameState.getLegalActions(self.index[self.role])
            for action in actions:
                score = self.evaluationGhost(gameState, self.index[self.role], action)
                if self.isGhostScared(gameState, self.index[self.role]): score = -1.0 * score
                if score > bestScore:
                    bestScore = score
                    bestActions = [action]
                elif score == bestScore:
                    bestActions.append(action)
                # decisions.append( (score, action) )
            # if self.role == 0: print(decisions)
            action = random.choice(bestActions)
        self.recordHistory(gameState, action)
        self.respondHistory(gameState)
        return action


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

