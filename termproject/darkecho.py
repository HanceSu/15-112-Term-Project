# Extra module downloaded from: https://www.pygame.org/wiki/GettingStarted
import pygame
from pygame.locals import *
import math
import random

# Adapted from: https://www.cs.cmu.edu/~112/notes/hw10.html, homework template
def almostEqual(d1, d2, epsilon=10**-5):
	# note: use math.isclose() outside 15-112 with Python version 3.5 or later
	return (abs(d2 - d1) < epsilon)

# Adapted from: https://www.pygame.org/wiki/IntersectingLineDetection
def calculateIntersection(p1, p2, slope1, slope2):
	if (slope1 == None) and (slope2 == None):
		return None
	# only one line is vertical
	elif (slope1 == None):
		b2 = p2[1] - (slope2*p2[0])
		x = p1[0]
		y = slope2*x + b2
	# when the other line is vertical
	elif (slope2 == None):
		b1 = p1[1] - (slope1*p1[0])
		x = p2[0]
		y = slope1*x + b1
	# the two lines are equal
	elif almostEqual(slope1, slope2):
		return None
	# neither line is vertical
	else:
		b1 = p1[1] - (slope1*p1[0])
		b2 = p2[1] - (slope2*p2[0])
		x = (b2 - b1) / (slope1 - slope2)
		y = slope1*x + b1
	return (x, y)

class Player(object):
	def __init__(self, cx, cy, speed, game):
		self.cx = cx
		self.cy = cy
		self.scrollX = 0
		self.scrollY = 0
		self.r = 5
		self.color = (0, 255, 0)
		self.speed = speed
		self.game = game
		self.walkingNumPaths = 20
		self.silentNumPaths = 16
		self.shoutNumPaths = 27
		self.passOrFailNumPaths = 90
		self.triggerSwitchPaths = 12

	# perform different actions when the player is in a special rectArea
	def checkRectAreas(self, dx, dy, echoPathsList, rectAreasList, lineBoundariesList):
		for rectArea in rectAreasList:
			if self.inRectArea(rectArea):
				# walk slower when the player is in water region
				if isinstance(rectArea, Water):
					(dx, dy) = (dx/2, dy/2)
				# restarts the level when the player dies to redzone
				elif isinstance(rectArea, Redzone):
					self.failLevel(echoPathsList)
					pygame.mixer.music.stop()
					pygame.mixer.Sound.play(self.game.screaming_sound)
					pygame.time.delay(1500)
					self.game.playing = False
					self.game.newLevel()
				# removes the switch and a line boundary when it's triggered
				elif isinstance(rectArea, Switch):
					cx = (rectArea.lineBoundary.x0 + rectArea.lineBoundary.x1)/2
					cy = (rectArea.lineBoundary.y0 + rectArea.lineBoundary.y1)/2
					lineBoundariesList.remove(rectArea.lineBoundary)
					rectAreasList.remove(rectArea)
					self.triggerSwitch(cx, cy, echoPathsList)
				# returns to level screen when the player passes a level
				elif isinstance(rectArea, Destination):
					self.passLevel(echoPathsList)
					pygame.mixer.music.stop()
					pygame.mixer.Sound.play(self.game.door_closing_sound)
					pygame.time.wait(2000)
					self.game.playing = False
					self.game.level = -1
					self.game.levelsScreen()
		return dx, dy

	# check if an enemy kills the player
	def checkEnemies(self, enemiesList):
		pursuedMargin = 12
		for enemy in enemiesList:
			if ((self.cx-pursuedMargin <= enemy.cx <= self.cx+pursuedMargin) and
				(self.cy-pursuedMargin <= enemy.cy <= self.cy+pursuedMargin)):
				pygame.mixer.music.stop()
				pygame.mixer.Sound.play(self.game.screaming_sound)
				pygame.time.delay(1500)
				self.game.playing = False
				self.game.newLevel()

	# press mouse to move the player
	def move(self, mousePos, speed, echoPathsList, rectAreasList, lineBoundariesList, enemiesList):
		moveMargin = 15
		angle = 0
		# retrive the absolute positions of mouse
		mx, my = mousePos[0]+self.scrollX, mousePos[1]+self.scrollY
		# only moves when the mouse is outside of a certain area
		if not ((self.cx-moveMargin <= mx <= self.cx+moveMargin) and
				(self.cy-moveMargin <= my <= self.cy+moveMargin)):
			# special case when mx equals self.cx, and the formula of slope
			# need to be non-zero division
			if (self.cx == mx):
				if (self.cy < my):
					angle = math.pi/2
				elif (self.cy < my):
					angle = -math.pi/2
			else:
				plSlope = -(my-self.cy)/(mx-self.cx)
				angle = math.atan(plSlope)
				if (self.cx > mx):
					angle += math.pi

				# player move towards the position of mouse on canvas
			dx, dy = speed*math.cos(angle), -speed*math.sin(angle)
			if not self.crossBoundary(dx, dy, lineBoundariesList):
				self.checkEnemies(enemiesList)
				dx, dy = self.checkRectAreas(dx, dy, echoPathsList, rectAreasList, lineBoundariesList)
				self.cx += dx
				self.cy += dy
				self.scrollX += dx
				self.scrollY += dy

	# only check when the player is close to a line boundary
	def inDetectionRange(self, line):
		result = False
		detectMargin = 5
		minY, maxY = min(line.y0, line.y1), max(line.y0, line.y1)
		if (line.slope == None):
			if (minY <= self.cy <= maxY):
				result = True
		elif (((line.x0-detectMargin) <= self.cx <= (line.x1+detectMargin)) and 
			  ((minY-detectMargin) <= self.cy <= (maxY+detectMargin))):
			result = True
		return result

	# check if the predicted path of player will cross a line boundary
	# formula adapted from https://www.intmath.com/plane-analytic-geometry/perpendicular-distance-point-line.php
	def crossBoundary(self, dx, dy, lineBoundariesList):
		result = False
		m, n = self.cx+3*dx, self.cy+3*dy
		for line in lineBoundariesList:
			if self.inDetectionRange(line):
				if (line.slope == None):
					lineSlope = None
				else:
					lineSlope = line.slope

				# special case when the line is vertical
				if (lineSlope == None):
					distance = abs(m-line.x0)
				else:
					C = -line.y0+(-lineSlope*line.x0)
					A = lineSlope
					distance = abs(A*m+n+C)/math.sqrt(1+A**2)

				if distance <= 5:
					result = True

		return result

	# check whether the plyaer is in a special area (water, redzone, switch, etc.)
	def inRectArea(self, rectArea):
		return ((rectArea.left <= self.cx <= rectArea.left+rectArea.width) and
				(rectArea.top <= self.cy <= rectArea.top+rectArea.height))

	def walk(self, echoPathsList):
		# randomly chooses the first angle
		firstAngleIndex = random.randrange(-3, 4)
		firstAngle = firstAngleIndex*math.pi/18
		# generate echoPaths around the player
		for i in range(0, self.walkingNumPaths):
			echoPath = EchoPath(self.cx, self.cy, 2, firstAngle+i*2*math.pi/self.walkingNumPaths,
								(255, 255, 255), 2, 100, (3, 3, 3))
			echoPathsList.append(echoPath)

	# silent walking generates weaker echoes that travel shorter distances
	def silentStep(self, echoPathsList):
		firstAngleIndex = random.randrange(-3, 4)
		firstAngle = firstAngleIndex*math.pi/18
		for i in range(0, self.silentNumPaths):
			echoPath = SilentEchoPath(self.cx, self.cy, 1, firstAngle+i*2*math.pi/self.silentNumPaths,
								(140, 140, 140), 2, 60, (2, 2, 2))
			echoPathsList.append(echoPath)

	# travel further is mouse is been pressed longer
	def shout(self, echoPathsList):
		shoutMargin = 15
		mx, my = mousePos[0]+self.scrollX, mousePos[1]+self.scrollY
		if ((self.cx-moveMargin <= mx <= self.cx+moveMargin) and
			(self.cy-moveMargin <= my <= self.cy+moveMargin)):
			pass # not finished yet

	# the switch is triggered when the player steps onto it
	def triggerSwitch(self, cx, cy, echoPathsList):
		for i in range(0, self.triggerSwitchPaths):
			echoPath = EchoPath(cx, cy, 2, i*2*math.pi/self.triggerSwitchPaths,
								(180, 180, 180), 2, 60, (2, 2, 2))
			echoPathsList.append(echoPath)

	# fail the level when enemy reaches player or the player steps inside danger zone
	def failLevel(self, echoPathsList):
		for i in range(0, self.passOrFailNumPaths):
			echoPath = EchoPath(self.cx, self.cy, 2, i*2*math.pi/self.passOrFailNumPaths,
								(255, 0, 0), 4, 400, (2, 0, 0))
			echoPathsList.append(echoPath)

	# pass the level when the player reaches the destination
	def passLevel(self, echoPathsList):
		for i in range(0, self.passOrFailNumPaths):
			echoPath = EchoPath(self.cx, self.cy, 2, i*2*math.pi/self.passOrFailNumPaths,
								(0, 255, 0), 4, 400, (0, 2, 0))
			echoPathsList.append(echoPath)

	# throw a rock in the mouse pressed direction, used for checking environments
	def throwRock(self, mousePos, echoPathsList):
		throwMargin = 100
		mx, my = mousePos[0]+self.scrollX, mousePos[1]+self.scrollY
		if not ((self.cx-throwMargin <= mx <= self.cx+throwMargin) and
				(self.cy-throwMargin <= my <= self.cy+throwMargin)):
			slope = -(my - self.cy)/(mx - self.cx)
			angle = math.atan(slope)
			if (self.cx > mx):
				angle += math.pi
			rockPath = EchoPath(self.cx, self.cy, 3, angle, (255, 255, 255), 3, 200, (3, 3, 3))
			echoPathsList.append(rockPath)

	# currently visualized with a circle
	def draw(self, screen):
		pygame.draw.circle(screen, 
						   self.color, 
						   (int(self.cx - self.scrollX), int(self.cy - self.scrollY)), 
						   self.r)

class EchoPath(object):
	def __init__(self, cx, cy, speed, angle, color, width, fadeLength, fadeRate):
		self.cx = cx
		self.cy = cy
		self.ox = cx # this stores the origin of this echo path, won't change
		self.oy = cy # this store the origin of this echo path, won't change
		self.speed = speed
		self.angle = angle
		self.dx = speed*math.cos(self.angle)
		self.dy = -speed*math.sin(self.angle)
		self.color = color
		self.width = width
		self.segmentPos = [[self.cx, self.cy, (255, 255, 255), 2]] # stores a number of positions on its path
		self.segmentPosList = [] # different segments of the echo path
		self.fadeLength = fadeLength # maximum length of the fading line
		self.fadeRate = fadeRate # the rate that colors are changing
		self.last = pygame.time.get_ticks()
		self.cooldown = 10

	def __eq__(self, other):
		return ((isinstance(other, EchoPath)) and
				(self.cx == other.cx) and
				(self.cy == other.cy) and
				(self.angle == other.angle))

	def __hash__(self):
		return hash((self.cx, self.cy, self.angle))

	def inRectArea(self, rectArea):
		return ((rectArea.left <= self.cx <= rectArea.left+rectArea.width) and
				(rectArea.top <= self.cy <= rectArea.top+rectArea.height))

	def addNextPos(self, rectAreasList):
		# no two rectangular areas will overlap, so the current position
		# of echo path can only be in one rectangular area at most
		inAnyRectArea = False
		for rectArea in rectAreasList:
			if self.inRectArea(rectArea):
				inAnyRectArea = True
				if isinstance(rectArea, Water):
					self.segmentPos.append([self.cx, self.cy, (0, 0, self.color[2]), 2])
				elif isinstance(rectArea, Redzone):
					self.segmentPos.append([self.cx, self.cy, (self.color[0], 0, 0), 2])
				elif isinstance(rectArea, Switch):
					self.segmentPos.append([self.cx, self.cy, (self.color[0], self.color[1], 0), 2])
				elif isinstance(rectArea, Destination):
					self.segmentPos.append([self.cx, self.cy, (0, self.color[1], 0), 4])
				elif isinstance(rectArea, Shadow):
					self.segmentPos.append([self.cx, self.cy, self.color, 2])
		if not inAnyRectArea:
			self.segmentPos.append([self.cx, self.cy, self.color, 2])

	def move(self, rectAreasList):
		now = pygame.time.get_ticks()
		if (now - self.last) >= self.cooldown:
			self.last = now
			self.cx += self.dx
			self.cy += self.dy
			self.addNextPos(rectAreasList)
			if (len(self.segmentPos) > (self.fadeLength//self.speed+1)):
				self.segmentPos.pop(0) # delete the first position when fadeLength is reached
				self.color = tuple(map(lambda x, y: x - y, self.color, self.fadeRate))
				if (self.color[0] < 0):
					# delete this echo path when it turns completely dark
					self.color = (0, 0, 0)
				for pos in self.segmentPos:
					# pos[2] is always the color of this segment
					if (pos[2][0] == 0) and (pos[2][1] == 0):
						pos[2] = (0, 0, self.color[2])
					elif (pos[2][1] == 0) and (pos[2][2] == 0):
						pos[2] = (self.color[0], 0, 0)
					elif (pos[2][0] == 0) and (pos[2][2] == 0):
						pos[2] = (0, self.color[1], 0)
					elif (pos[2][2] == 0):
						pos[2] = (self.color[0], self.color[1], 0)
					else:
						pos[2] = self.color

	# only checks the intersection points when this echo path is in a certain range
	# with the line, reduces unnecessary running time
	def inDetectionRange(self, line):
		detectMargin = 3
		minY, maxY = min(line.y0, line.y1), max(line.y0, line.y1)
		if (((line.x0-detectMargin) <= self.cx <= (line.x1+detectMargin)) and 
			((minY-detectMargin) <= self.cy <= (maxY+detectMargin))):
			return True
		return False

	# get the predicted intersection between the echo path and the line boundary
	def getIntersectPoint(self, line):
		if (len(self.segmentPos) > 1):
			(cx0, cy0) = self.segmentPos[-2][0], self.segmentPos[-2][1]
			(cx1, cy1) = self.segmentPos[-1][0], self.segmentPos[-1][1]

			# get the slope of this current echo path
			if (almostEqual(cx0, cx1)):
				echoSlope = None
			else:
				echoSlope = (cy1 - cy0)/(cx1 - cx0)

			# get the slope of the line 
			if (line.slope == None):
				lineSlope = None
			else:
				lineSlope = -line.slope

			echoPoint = (self.cx, self.cy)
			linePoint = (line.x0, line.y0)

			if self.inDetectionRange(line):
				return calculateIntersection(echoPoint, linePoint, echoSlope, lineSlope)

	# the echo path is reflected from line boundaries
	def reflect(self, line):
		if (self.getIntersectPoint(line) != None):
			(x, y) = self.getIntersectPoint(line)
			(cx0, cy0) = self.segmentPos[-1][0], self.segmentPos[-1][1]
			(cx1, cy1) = (self.cx + self.dx, self.cy + self.dy)
			if ((min(cx0, cx1) <= x <= max(cx0, cx1)) and
				(min(cy0, cy1) <= y <= max(cy0, cy1))):
				newAngle = 2*line.angle - self.angle # this calculation is done in my notebook
				if (newAngle > math.pi):
					self.angle = newAngle - 2*math.pi
				elif (newAngle < -math.pi):
					self.angle = newAngle + 2*math.pi
				else:
					self.angle = newAngle

				# assigns the new slope after the echo is reflected
				if almostEqual(self.angle, -math.pi/2) or almostEqual(self.angle, math.pi/2):
					self.slope = None
				else:
					self.slope = -math.tan(self.angle)
				# calculate the new dx and dy with new slope
				(self.dx, self.dy) = (self.speed*math.cos(self.angle), 
									  -self.speed*math.sin(self.angle))

	def draw(self, screen, player):
		# ignore when there's only one tuple in self.segmentPos
		if (len(self.segmentPos) == 2):
			# the case when there are only two tuples
			startPos = (self.segmentPos[0][0]-player.scrollX, self.segmentPos[0][1]-player.scrollY)
			endPos = (self.segmentPos[1][0]-player.scrollX, self.segmentPos[1][1]-player.scrollY)
			pygame.draw.line(screen, self.segmentPos[1][2], startPos, endPos, self.segmentPos[1][3])
		if (len(self.segmentPos) > 2):
			lowIndex = 0
			highIndex = 2
			while highIndex < len(self.segmentPos):
				# check if both the colors and widths at two neighbouring positions are the same
				# and draw all the segments of this echo path
				if not ((self.segmentPos[highIndex][2] == self.segmentPos[highIndex-1][2]) and
						(self.segmentPos[highIndex][3] == self.segmentPos[highIndex-1][3])):
					drawSegmentPos = []
					for pos in self.segmentPos[lowIndex:highIndex]:
						drawPos = (pos[0]-player.scrollX, pos[1]-player.scrollY)
						drawSegmentPos.append(drawPos)
					pygame.draw.lines(screen, 
									  self.segmentPos[highIndex-1][2], 
									  False, 
									  drawSegmentPos, 
									  self.segmentPos[highIndex-1][3])
					lowIndex = highIndex-1
				highIndex += 1
				if (highIndex == len(self.segmentPos)-1):
					drawSegmentPos = []
					for pos in self.segmentPos[lowIndex:]:
						drawPos = (pos[0]-player.scrollX, pos[1]-player.scrollY)
						drawSegmentPos.append(drawPos)
					pygame.draw.lines(screen, 
									  self.segmentPos[-2][2], 
									  False, 
									  drawSegmentPos, 
									  self.segmentPos[-2][3])
					break

# echo path except it doesn't trigger the enemies
class SilentEchoPath(EchoPath):
	def move(self, rectAreasList):
		now = pygame.time.get_ticks()
		if (now - self.last) >= self.cooldown:
			self.last = now
			self.cx += self.dx
			self.cy += self.dy
			self.addNextPos(rectAreasList)
			self.color = tuple(map(lambda x, y: x - y, self.color, self.fadeRate))
			if (self.color[0] < 0):
				# delete this echo path when it turns completely dark
				self.color = (0, 0, 0)
			for pos in self.segmentPos:
				# pos[2] is always the color of this segment
				if (pos[2][0] == 0) and (pos[2][1] == 0):
					pos[2] = (0, 0, self.color[2])
				elif (pos[2][1] == 0) and (pos[2][2] == 0):
					pos[2] = (self.color[0], 0, 0)
				elif (pos[2][0] == 0) and (pos[2][2] == 0):
					pos[2] = (0, self.color[1], 0)
				elif (pos[2][2] == 0):
					pos[2] = (self.color[0], self.color[1], 0)
				else:
					pos[2] = self.color

# echo path except only enemy generates this kind of echo that 
# doesn't reflect on boundaries
class EnemyEchoPath(EchoPath):
	def move(self):
		now = pygame.time.get_ticks()
		if (now - self.last) >= self.cooldown:
			self.last = now
			self.cx += self.dx
			self.cy += self.dy
			self.segmentPos.append([self.cx, self.cy, (self.color[0], 0, 0), 2])
			self.color = tuple(map(lambda x, y: x - y, self.color, self.fadeRate))
			if (self.color[0] < 0):
				# delete this echo path when it turns completely dark
				self.color = (0, 0, 0)
			for pos in self.segmentPos:
				# pos[2] is always the color of this segment
				pos[2] = (self.color[0], 0, 0)
		   
class LineBoundary(object):
	def __init__(self, x0, y0, x1, y1):
		# make sure that x0 is always less than x1
		if (x1 < x0):
			self.x0, self.y0 = x1, y1
			self.x1, self.y1 = x0, y0
		else:
			self.x0, self.y0 = x0, y0
			self.x1, self.y1 = x1, y1

		# get the slope of this line
		if (x1 == x0):
			self.slope = None
			self.angle = math.pi/2
		else:
			self.slope = -(y1-y0)/(x1-x0)

		# get the angle of the line with its slope
		if (self.slope != None):
			angle = math.atan(self.slope)
			if (angle < 0):
				self.angle = angle + math.pi
			else:
				self.angle = angle

	def __eq__(self, other):
		return ((isinstance(other, LineBoundary)) and
				(self.x0 == other.x0) and
				(self.y0 == other.y0) and
				(self.x1 == other.x1) and
				(self.y1 == other.y1))

	def __hash__(self):
		return hash((self.x0, self.y0, self.x1, self.y1))

	def __repr__(self):
		return(str(self.x0)+str(self.y0)+str(self.x1)+str(self.y1))

	def draw(self, screen, player):
		pygame.draw.line(screen, 
						 (0, 255, 255),  # for display purposes
						 (self.x0-player.scrollX, self.y0-player.scrollY), 
						 (self.x1-player.scrollX, self.y1-player.scrollY),
						 3)

class Enemy(object):
	def __init__(self, cx, cy):
		self.cx = cx
		self.cy = cy
		self.color = (255, 0, 0)
		self.enemyNumPaths = 5
		self.speed = 0.9
		self.pursuedEcho = None
		self.isAwakened = False
		self.lastMove = -1

	def awakened(self, echoPathsList):
		awakenedMargin = 15
		for echoPath in echoPathsList:
			if echoPath.color[0] > 80:
				if ((self.cx-awakenedMargin <= echoPath.cx <= self.cx+awakenedMargin) and
					(self.cy-awakenedMargin <= echoPath.cy <= self.cy+awakenedMargin)):
					self.isAwakened = True
					self.pursuedEcho = echoPath

	# the enemy persistently pursue the origin of an echo that awakens it,
	# ignoreing any boundary or special region
	def pursue(self):
		pursueMargin = 5
		angle = 0
		tx, ty = self.pursuedEcho.ox, self.pursuedEcho.oy
		if ((tx-pursueMargin <= self.cx <= tx+pursueMargin) and (ty-pursueMargin <= self.cy <= ty+pursueMargin)):
			self.pursuedEcho = None
			self.isAwakened = False
		else:
			# special case when tx equals self.cx, and the formula of slope
			# need to be non-zero division
			if (self.cx == tx):
				if (self.cy < ty):
					angle = math.pi/2
				elif (self.cy < ty):
					angle = -math.pi/2
			else:
				slope = -(ty - self.cy)/(tx - self.cx)
				angle = math.atan(slope)
				if (self.cx > tx):
					angle += math.pi
			# enemy move towards the origin of echo on canvas
			(dx, dy) = (self.speed*math.cos(angle), -self.speed*math.sin(angle))
			self.cx += dx
			self.cy += dy

	def move(self, echoPathsList):
		firstAngleIndex = random.randrange(-3, 4)
		firstAngle = firstAngleIndex*math.pi/18
		for i in range(self.enemyNumPaths):
			echoPath = EnemyEchoPath(self.cx, self.cy, 2, firstAngle + i*2*math.pi/self.enemyNumPaths,
									 (255, 0, 0), 2, 40, (4, 0, 0))
			echoPathsList.append(echoPath)

	def draw(self, screen, player):
		pygame.draw.circle(screen, (255, 0, 0), (int(self.cx-player.scrollX), int(self.cy-player.scrollY)), 5)

class RectArea(object):
	def __init__(self, left, top, width, height, color):
		self.left = left
		self.top = top
		self.width = width
		self.height = height
		self.color = color

	def draw(self, screen, player):
		left, top = self.left-player.scrollX, self.top-player.scrollY
		pygame.draw.rect(screen, self.color, Rect((left, top), (self.width, self.height)))

class Water(RectArea):
	def __init__(self, left, top, width, height):
		super().__init__(left, top, width, height, (0, 0, 255))

class Shadow(RectArea):
	def __init__(self, left, top, width, height):
		super().__init__(left, top, width, height, (0, 0, 0))

class Redzone(RectArea):
	def __init__(self, left, top, width, height):
		super().__init__(left, top, width, height, (255, 0, 0))

class Destination(RectArea):
	def __init__(self, left, top, width, height):
		super().__init__(left, top, width, height, (0, 255, 0))

class Switch(RectArea):
	def __init__(self, left, top, width, height, lineBoundary):
		super().__init__(left, top, width, height, (255, 255, 0))
		self.lineBoundary = lineBoundary

# for mouse presses
LEFT = 0
MIDDLE = 1
RIGHT = 2

# levels are inspired by the original Dark Echo game on AppStore, you can buy the original game 
# here: https://play.google.com/store/apps/details?id=com.rac7.DarkEcho&hl=en_US
# or here: https://store.steampowered.com/app/368650/Dark_Echo/
levels = {
0:
"""
line 200 200 500 200
line 200 300 500 300
line 500 200 800 0
line 500 300 800 500
line 800 0 850 100
line 800 500 850 400
line 850 100 700 200
line 850 400 700 300
line 1000 200 1000 300
line 700 300 1000 300
line 700 200 1000 200
line 200 200 200 300
destination 900 200 100 100
""",
1:
"""
line 200 200 500 200
line 200 300 500 300
line 200 200 200 300
line 500 200 700 0
line 700 0 900 0
line 850 100 900 0
line 750 100 850 100
line 650 200 750 100
line 500 300 700 500
line 700 500 700 600
line 700 600 900 600
line 900 600 900 500
line 900 500 1000 300
line 650 300 750 400
line 750 400 850 400
line 850 400 900 300
line 650 300 900 300
line 650 200 1100 200
line 1000 300 1100 300
line 1100 300 1150 350
line 1150 350 1250 350
line 1250 350 1300 300
line 1300 300 1400 300
line 1100 200 1150 150
line 1150 150 1250 150
line 1250 150 1300 200
line 1300 200 1400 200
line 1400 200 1400 300
redzone 650 200 250 100
redzone 700 500 200 100
redzone 1100 150 200 50
redzone 1100 300 200 50
destination 1350 200 50 100
""",
2:
"""
line 350 200 500 200
line 350 200 350 300
line 350 300 500 300
line 500 300 550 350
line 550 350 700 350
line 700 350 750 300
line 500 200 550 150
line 550 150 700 150
line 700 150 750 200
line 750 200 850 200
line 850 200 800 125
line 800 125 850 50
line 850 50 950 200
line 750 300 1100 300
line 1100 300 1200 400
line 1200 400 1150 400
line 1150 400 1150 450
line 1150 450 1300 450
line 1300 450 1300 400
line 1100 200 1250 350
line 950 200 1100 200
line 1250 350 1400 200
line 1300 400 1500 200
line 1400 200 1250 50
line 1500 200 1300 0
line 1200 0 1300 0
line 1150 50 1200 0
line 1150 100 1150 50
line 1150 100 1200 100
line 1200 100 1250 50
destination 1150 50 50 50
redzone 500 150 250 50
redzone 500 300 250 50
enemy 850 100
enemy 1175 425
""",
3:
"""
line 300 200 650 200
line 300 200 300 300
line 300 300 550 300
line 550 300 400 450
line 650 300 800 450
line 800 450 600 650
line 400 450 600 650
line 600 350 500 450
line 500 450 600 550
line 600 550 700 450
line 700 450 600 350
line 650 200 700 150
line 700 150 1100 150
line 1100 150 1150 200
line 1150 200 1200 200
line 1200 200 1200 300
line 650 300 1200 300
water 650 150 500 150
destination 1150 200 50 100
enemy 875 175

""",
4:
"""
line 350 200 385 200
line 385 200 385 100
line 385 100 415 100
line 415 100 415 200
line 415 200 450 200
line 450 200 450 235
line 450 265 450 300
line 350 200 350 300
line 350 300 385 300
line 385 300 385 400
line 415 300 415 400
line 415 300 450 300
line 350 400 385 400
line 350 400 350 500
line 350 500 450 500
line 450 465 450 500
line 415 400 450 400
line 450 400 450 435
line 450 235 550 235
line 450 265 550 265
line 550 235 550 200
line 550 200 585 200
line 585 200 585 100
line 585 100 615 100
line 615 100 615 200
line 615 200 650 200
line 650 200 650 235
line 650 265 650 300
line 650 235 750 235
line 750 235 750 265
line 650 265 750 265
line 550 265 550 300
line 550 300 585 300
line 615 300 650 300
line 585 300 585 400
line 615 300 615 400
line 550 400 585 400
line 550 400 550 435
line 550 465 550 500
line 550 500 585 500
line 585 500 585 575
line 585 575 615 575
line 615 575 615 500
line 615 500 650 500
line 450 435 550 435
line 450 465 550 465
line 650 435 750 435
line 650 465 750 465
line 615 400 650 400
line 650 400 650 435
line 650 465 650 500
line 550 235 550 265
line 385 400 415 400
line 750 435 750 465
line 450 435 450 465
line 585 575 585 625
line 585 625 700 625
line 615 575 700 575
line 700 625 700 575
line 585 400 615 400
switch 585 300 30 100 585 400 615 400
switch 450 235 100 30 550 235 550 265
switch 385 300 30 100 385 400 415 400
switch 585 100 30 100 585 100 615 100
switch 650 435 100 30 750 435 750 465
switch 450 435 100 30 450 435 450 465
switch 585 500 30 100 585 575 615 575
water 350 400 100 100
redzone 450 -100 300 200
redzone 750 300 300 300 
destination 650 575 50 50
""",
5:
"""
line 375 200 525 200
line 525 200 525 100
line 525 100 725 100
line 725 100 725 800
line 375 200 375 800
line 375 800 725 800
line 425 650 525 650
line 425 650 425 750
line 425 750 525 750
line 525 650 525 750
line 575 650 675 650
line 575 650 575 750
line 575 750 675 750
line 675 650 675 750
line 575 150 675 150
line 675 150 675 200
line 575 150 575 200
line 575 200 675 200
redzone 525 650 50 100
redzone 425 200 100 450
redzone 575 200 100 450
shadow 520 200 60 400
shadow 625 100 110 100
destination 525 600 50 50
"""}

class DarkEchoGame:
	def __init__(self):
		# initializes game windows
		pygame.init()
		pygame.mixer.init()
		self.screen = pygame.display.set_mode((800, 500))
		pygame.display.set_caption("Dark Echo")
		self.clock = pygame.time.Clock()
		self.level = 1
		self.running = True
		self.playing = False
		# Purchased from www.soundsnap.comsearchaudiofootstepscore2secpage=2
		# Blastwave FX
		self.footstep_soundA = pygame.mixer.Sound("footstep_soundA.wav")
		# Downloaded from www.freesoundeffects.comfree-soundsdoors-10030
		self.door_closing_sound = pygame.mixer.Sound("door_closing_sound.wav")
		# Downloaded from www.freesoundeffects.comfree-soundsscreams-10094
		self.screaming_sound = pygame.mixer.Sound("screaming_sound.wav")
		# Downloaded from freesound.org/people/LittleRobotSoundFactory/sounds/270428/
		#self.water_footstep_sound = pygame.mixer.Sound("footstep_water_soundA")

	@staticmethod
	# read the long strings in levels and constructs the map for this level
	def levelReader(levelStr, rectAreasList, lineBoundariesList, enemiesList):
		for line in levelStr.splitlines():
			if (line != ""):
				l = line.split()
				objClass = l[0]
				if objClass.startswith('line'):
					newLineBoundary = LineBoundary(int(l[1]), int(l[2]), int(l[3]), int(l[4]))
					lineBoundariesList.append(newLineBoundary)
				elif objClass.startswith('enemy'):
					newEnemy = Enemy(int(l[1]), int(l[2]))
					enemiesList.append(newEnemy)
				elif objClass.startswith('water'):
					newWater = Water(int(l[1]), int(l[2]), int(l[3]), int(l[4]))
					rectAreasList.append(newWater)
				elif objClass.startswith('switch'):
					controlledLine = LineBoundary(int(l[5]), int(l[6]), int(l[7]), int(l[8]))
					newSwitch = Switch(int(l[1]), int(l[2]), int(l[3]), int(l[4]), controlledLine)
					rectAreasList.append(newSwitch)
				elif objClass.startswith('redzone'):
					newRedzone = Redzone(int(l[1]), int(l[2]), int(l[3]), int(l[4]))
					rectAreasList.append(newRedzone)
				elif objClass.startswith('shadow'):
					newShadow = Shadow(int(l[1]), int(l[2]), int(l[3]), int(l[4]))
					rectAreasList.append(newShadow)
				elif objClass.startswith('destination'):
					newDest = Destination(int(l[1]), int(l[2]), int(l[3]), int(l[4]))
					rectAreasList.append(newDest)

	def newLevel(self):
		self.pl = Player(400, 250, 1, self)
		self.walkInterval = 500
		self.silentStepInterval = 800
		self.enemyMoveInterval = 200
		self.lastWalk = 0
		self.lastThrowRock = 0
		self.rectAreasList = []
		self.lineBoundariesList = []
		self.enemiesList = []
		self.silentPathsList = []
		self.echoPathsList = []
		self.enemyEchoPathsList = []
		self.silentEchoPathsList = []
		self.visible = False
		DarkEchoGame.levelReader(levels[self.level], self.rectAreasList, self.lineBoundariesList, self.enemiesList)
		self.runGame()
		
	def runGame(self):
		# main game loop
		self.playing = True

		while self.playing:

			self.clock.tick(100)

			self.screen.fill((0, 0, 0))

			# check for mouse pressed and key presses
			for event in pygame.event.get():
				if event.type == QUIT:
					self.playing = False
					self.running = False
				elif event.type == pygame.KEYDOWN:
					if (event.key == pygame.K_q):
						self.levelsScreen()
						self.playing = False
					elif (event.key == pygame.K_v):
						self.visible = not self.visible
				elif event.type == pygame.MOUSEBUTTONDOWN: 
					if event.button == 1:
						self.lastWalk = pygame.time.get_ticks()
						self.pl.walk(self.echoPathsList)
					elif event.button == 3:
						self.lastWalk = pygame.time.get_ticks()
						self.pl.silentStep(self.silentEchoPathsList)
					elif event.button == 2:
						mousePos = event.pos
						self.lastThrowRock = pygame.time.get_ticks()
						self.pl.throwRock(mousePos, self.echoPathsList)

		    # hold mouse buttons to move the player
			mouses = pygame.mouse.get_pressed()
			if (mouses[LEFT] == 1):
				mousePos = event.pos
				self.pl.move(mousePos, 
					         self.pl.speed, 
					         self.echoPathsList, 
					         self.rectAreasList, 
					         self.lineBoundariesList, 
					         self.enemiesList)
				now = pygame.time.get_ticks()
				if (now - self.lastWalk) >= self.walkInterval:
					self.lastWalk = now
					self.pl.walk(self.echoPathsList)
					pygame.mixer.music.stop()
					pygame.mixer.Sound.play(self.footstep_soundA)
			elif (mouses[RIGHT] == 1):
				mousePos = event.pos
				self.pl.move(mousePos, 
					         self.pl.speed/2 , 
					         self.echoPathsList, 
					         self.rectAreasList, 
					         self.lineBoundariesList, 
					         self.enemiesList)
				now = pygame.time.get_ticks()
				if (now - self.lastWalk) >= self.silentStepInterval:
					self.lastWalk = now
					self.pl.silentStep(self.silentEchoPathsList)

			# only draws the following features when self.visible is turned on
			if (self.visible):
				for line in self.lineBoundariesList:
					line.draw(self.screen, self.pl)
				for enemy in self.enemiesList:
					enemy.draw(self.screen, self.pl)
				for rectArea in self.rectAreasList:
					rectArea.draw(self.screen, self.pl)

			for echoPath in self.echoPathsList:
				echoPath.move(self.rectAreasList)
				for line in self.lineBoundariesList:
					echoPath.reflect(line)
				echoPath.draw(self.screen, self.pl)

			for silentEchoPath in self.silentEchoPathsList:
				silentEchoPath.move(self.rectAreasList)
				for line in self.lineBoundariesList:
					silentEchoPath.reflect(line)
				silentEchoPath.draw(self.screen, self.pl)

			for enemyEchoPath in self.enemyEchoPathsList:
				enemyEchoPath.move()
				enemyEchoPath.draw(self.screen, self.pl)

			if (self.echoPathsList != []):
				for echoPath in self.echoPathsList:
					if echoPath.color[0] == 0:
						self.echoPathsList.remove(echoPath)

			if (self.silentEchoPathsList != []):
				for silentEchoPath in self.silentEchoPathsList:
					if silentEchoPath.color[0] == 0:
						self.silentEchoPathsList.remove(silentEchoPath)

			if (self.enemyEchoPathsList != []):
				for enemyEchoPath in self.enemyEchoPathsList:
					if enemyEchoPath.color[0] == 0:
						self.enemyEchoPathsList.remove(enemyEchoPath)

			# the movement of enemies
			for enemy in self.enemiesList:
				enemy.awakened(self.echoPathsList)
				if not enemy.isAwakened:
					enemy.lastMove = pygame.time.get_ticks()
				else:
					enemy.pursue()
					now = pygame.time.get_ticks()
					if (now - enemy.lastMove) >= self.enemyMoveInterval:
						enemy.lastMove = now
						enemy.move(self.enemyEchoPathsList)

			self.pl.draw(self.screen)

			# draw the shadows to cover put of the map
			for rectArea in self.rectAreasList:
				if (isinstance(rectArea, Shadow)):
					rectArea.draw(self.screen, self.pl)

			pygame.display.update()

	# the first screen user sees when he runs the game
	def startScreen(self):
		font1 = pygame.font.SysFont("consolas", 72)
		font2 = pygame.font.SysFont("consolas", 36)

		waiting = True

		while waiting:

			self.clock.tick(100)

			self.screen.fill((0, 0, 0))

			text1 = font1.render("Dark Echo", True, (255, 255, 255))
			self.screen.blit(text1, (400-text1.get_width()//2, 200-text1.get_height()//2))
			text2 = font2.render("Press Enter to start", True, (200, 200, 200))
			self.screen.blit(text2, (400-text2.get_width()//2, 300-text2.get_height()//2))

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					waiting = False
					self.running = False
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_RETURN:
						waiting = False
						self.levelsScreen()

			pygame.display.update()
			
	@staticmethod
	def inRectArea(pos, rect):
		if ((rect[0] <= pos[0] <= (rect[0]+rect[2])) and (rect[1] <= pos[1] <= (rect[1]+rect[3]))):
			return True
		else:
			return False

    # choose different levels on this screen
	def levelsScreen(self):

		font1 = pygame.font.SysFont("consolas", 36)
		font2 = pygame.font.SysFont("consolas", 24)

		levelsWaiting = True

		while levelsWaiting:

			self.clock.tick(100)

			self.screen.fill((0, 0, 0))

			helpText = font2.render("Press h for help", True, (255, 255, 255))
			self.screen.blit(helpText, (400-helpText.get_width()//2, 450-helpText.get_height()//2))

			rect1 = Rect((80, 100), (160, 100))
			rect2 = Rect((320, 100), (160, 100))
			rect3 = Rect((560, 100), (160, 100))
			rect4 = Rect((80, 300), (160, 100))
			rect5 = Rect((320, 300), (160, 100))
			rect6 = Rect((560, 300), (160, 100))

			text1 = font1.render("I", True, (50, 50, 50))
			text2 = font1.render("II", True, (50, 50, 50))
			text3 = font1.render("III", True, (50, 50, 50))
			text4 = font1.render("IV", True, (50, 50, 50))
			text5 = font1.render("V", True, (50, 50, 50))
			text6 = font1.render("VI", True, (50, 50, 50))

			pos1 = (160-text1.get_width()//2, 150-text1.get_height()//2)
			pos2 = (400-text2.get_width()//2, 150-text2.get_height()//2)
			pos3 = (640-text3.get_width()//2, 150-text3.get_height()//2)
			pos4 = (160-text4.get_width()//2, 350-text4.get_height()//2)
			pos5 = (400-text5.get_width()//2, 350-text5.get_height()//2)
			pos6 = (640-text6.get_width()//2, 350-text6.get_height()//2)

			rectsList = [(rect1, text1, pos1), (rect2, text2, pos2), (rect3, text3, pos3), 
			             (rect4, text4, pos4), (rect5, text5, pos5), (rect6, text6, pos6)]

			for rect in rectsList:
				pygame.draw.rect(self.screen, (200, 200, 200), rect[0])
				self.screen.blit(rect[1], rect[2])

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					levelsWaiting = False
					self.running = False
				if event.type == pygame.KEYDOWN:
					if (event.key == pygame.K_h):
						self.helpScreen()
						levelsWaiting = False
				elif event.type == pygame.MOUSEBUTTONDOWN:
					if (event.button == 1):
						mousePos = event.pos
						for i in range(len(rectsList)):
							if DarkEchoGame.inRectArea(mousePos, rectsList[i][0]):
								levelsWaiting = False
								self.level = i
								pygame.time.delay(1000)
								self.newLevel()

			pygame.display.update()

	# get help from this screen if you are stuck
	def helpScreen(self):
		# pygame doesn't read long strings so I have to do it this way
		textMessages = ["Your goal is to reach the destination (in green)",
					    "Left hold mouse on screen to let the player walk", 
		                "Right hold mouse on screen to let the player silently walk", 
		                "Middle click mouse to throw a rock",
		                "Redzone (in red) and the enemies (in red) will kill the player",
		                "You will return to the beginning of current level upon getting killed",
		                "Water (in blue) slows the player down",
		                "Switch (in yellow) unlocks new areas",
		                "Enemies are invisible until they are awakened",
		                "Press r to return to levels screen",
		                "Press q in game to quit a level",
		                "Press v in game to show boundaries and areas",
		                "Press v again to make the above features invisible"]

		font = pygame.font.SysFont("consolas", 18)

		helpWaiting = True

		while helpWaiting:

			self.clock.tick(100)

			self.screen.fill((0, 0, 0))

			for i in range(len(textMessages)):
				text = font.render(textMessages[i], True, (255, 255, 255))
				self.screen.blit(text, (400-text.get_width()//2, 30+40*i-text.get_height()//2))

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					helpWaiting = False
					self.running = False
				if event.type == pygame.KEYDOWN:
					if (event.key == pygame.K_r):
						self.levelsScreen()
						helpWaiting = False

			pygame.display.update()

# runs the main game
g = DarkEchoGame()

g.startScreen()

if not g.running:
	pygame.quit()

