# Extra module downloaded from: https://www.pygame.org/wiki/GettingStarted
import pygame
from pygame.locals import *
import math
import random

# Adapted from: https://www.cs.cmu.edu/~112/notes/hw10.html, homework template
def almostEqual(d1, d2, epsilon=10**-5):
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

class Player(object):
    def __init__(self, cx, cy, speed):
        self.cx = cx
        self.cy = cy
        self.scrollX = 0
        self.scrollY = 0
        self.r = 10 # for display purpose
        self.color = (255, 255, 255) # for display purpose
        self.speed = speed
        self.walkingNumPaths = 20
        self.silentNumPaths = 16
        self.shoutNumPaths = 27
        self.passOrFailNumPaths = 90
        self.triggerSwitchPaths = 12

    def checkRectAreas(self, dx, dy, echoPathsList, rectAreasList, lineBoundariesList):
        for rectArea in rectAreasList:
            if self.inRectArea(rectArea):
                if isinstance(rectArea, Water):
                    (dx, dy) = (dx/2, dy/2)
                elif isinstance(rectArea, Redzone):
                    self.failLevel(echoPathsList)
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(screaming_sound)
                    pygame.time.wait(1500)
                    pygame.quit()
                elif isinstance(rectArea, Switch):
                    cx = (rectArea.lineBoundary.x0 + rectArea.lineBoundary.x1)/2
                    cy = (rectArea.lineBoundary.y0 + rectArea.lineBoundary.y1)/2
                    lineBoundariesList.remove(rectArea.lineBoundary)
                    rectAreasList.remove(rectArea)
                    self.triggerSwitch(cx, cy, echoPathsList)
                elif isinstance(rectArea, Destination):
                    self.passLevel(echoPathsList)
                    pygame.mixer.music.stop()
                    pygame.mixer.Sound.play(door_closing_sound)
                    pygame.time.wait(2000)
                    pygame.quit()
        return dx, dy

    def move(self, mousePos, speed, echoPathsList, rectAreasList, lineBoundariesList):
        moveMargin = 15
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
                slope = -(my - self.cy)/(mx - self.cx)
                angle = math.atan(slope)
                if (self.cx > mx):
                    angle += math.pi
            # player move towards the position of mouse on canvas
            dx, dy = speed*math.cos(angle), -speed*math.sin(angle)
            dx, dy = self.checkRectAreas(dx, dy, echoPathsList, rectAreasList, lineBoundariesList)
            self.cx += dx
            self.cy += dy
            self.scrollX += dx
            self.scrollY += dy

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
            echoPath = EchoPath(self.cx, self.cy, 1, firstAngle+i*2*math.pi/self.silentNumPaths,
                                (100, 100, 100), 2, 40, (2, 2, 2))
            echoPathsList.append(echoPath)

    # travel further is mouse is been pressed longer
    def shout(self, echoPathsList):
        shoutMargin = 15
        mx, my = mousePos[0]+self.scrollX, mousePos[1]+self.scrollY
        if ((self.cx-moveMargin <= mx <= self.cx+moveMargin) and
            (self.cy-moveMargin <= my <= self.cy+moveMargin)):
            pass # not finished yet

    def triggerSwitch(self, cx, cy, echoPathsList):
        for i in range(0, self.triggerSwitchPaths):
            echoPath = EchoPath(cx, cy, 2, i*2*math.pi/self.triggerSwitchPaths,
                                (180, 180, 180), 2, 60, (2, 2, 2))
            echoPathsList.append(echoPath)

    def failLevel(self, echoPathsList):
        for i in range(0, self.passOrFailNumPaths):
            echoPath = EchoPath(self.cx, self.cy, 2, i*2*math.pi/self.passOrFailNumPaths,
                                (255, 0, 0), 4, 400, (2, 0, 0))
            echoPathsList.append(echoPath)

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
                           (255, 0, 0), 
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
                (self.angle == other.angel))

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

    # Adapted from: https://www.pygame.org/wiki/IntersectingLineDetection
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

            if self.inDetectionRange(line):
                # both the echo and the line are vertical
                if (echoSlope == None) and (lineSlope == None):
                    return None
                # only the echo is vertical
                elif (echoSlope == None):
                    b2 = line.y0 - (lineSlope*line.x0)
                    x = self.cx
                    y = lineSlope*x + b2
                # only the line is vertical
                elif (lineSlope == None):
                    b1 = self.cy - (echoSlope*self.cx)
                    x = line.x0
                    y = echoSlope*x + b1
                # the echo is parallel with the line
                elif almostEqual(echoSlope, lineSlope):
                    return None
                else:
                    b1 = self.cy - (echoSlope*self.cx)
                    b2 = line.y0 - (lineSlope*line.x0)
                    x = (b2 - b1) / (echoSlope - lineSlope)
                    y = echoSlope*x + b1
                return (x, y)

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
        self.speed = 1
        self.pursuedEcho = None

    def awakened(self, echoPathsList):
        awakenedMargin = 20
        for echoPath in echoPathsList:
            if ((self.cx-awakenedMargin <= echoPath.cx <= self.cx+awakenedMargin) and
                (self.cy-awakenedMargin <= echoPath.cy <= self.cy+awakenedMargin)):
                self.pursuedEcho = echoPath

    # the enemy persistently pursue the origin of an echo that awakens it,
    # ignoreing any boundary or special region
    def pursue(self):
        pursueMargin = 3
        if (self.pursuedEcho != None):
            tx, ty = self.pursuedEcho.ox, self.pursuedEcho.oy
            if not ((tx-pursueMargin <= self.cx <= tx+pursueMargin) and
                    (ty-pursueMargin <= self.cy <= ty+pursueMargin)):
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

class DarkEchoGame:
    def __init__(self):
        # initializes game windows
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((800, 500))
        self.display.set_caption("Dark Echo")
        self.clock = pygame.time.Clock()
        self.running = True

    def new(self):
        pass

pygame.init()

screen = pygame.display.set_mode((800, 500))

pygame.display.set_caption("Dark Echo Sample Level")

# Purchased from www.soundsnap.comsearchaudiofootstepscore2secpage=2
# Blastwave FX
footstep_soundA = pygame.mixer.Sound("footstep_soundA.wav")

# Purchased from httpswww.soundsnap.comsearchaudiofoodstepscore2secpage=4
# SFX Bible
#footstep_soundB = pygame.mixer.Sound("footstep_soundB.wav")

# Purchased from httpswww.soundsnap.comsearchaudiofoodstepscore2sec 
# Airborne Sound
#footstep_soundC = pygame.mixer.Sound("footstep_soundC.wav")

# Downloaded from www.freesoundeffects.comfree-soundsdoors-10030
door_closing_sound = pygame.mixer.Sound("door_closing_sound.wav")

# Downloaded from www.freesoundeffects.comfree-soundsscreams-10094
screaming_sound = pygame.mixer.Sound("screaming_sound.wav")

clock = pygame.time.Clock()

pl = Player(400, 250, 1)

line1 = LineBoundary(0, 100, 600, 100)
line2 = LineBoundary(0, 500, 600, 500)
line3 = LineBoundary(0, 100, 0, 500)
line4 = LineBoundary(1000, 250, 1000, 350)
line5 = LineBoundary(600, 100, 900, 250)
line6 = LineBoundary(600, 500, 900, 350)
line7 = LineBoundary(900, 250, 1000, 250)
line8 = LineBoundary(900, 350, 1000, 350)
line9 = LineBoundary(900, 250, 900, 350)

enemy1 = Enemy(50, 300)

water = Water(600, 100, 200, 400)
switch = Switch(825, 275, 50, 50, line9)
redzone1 = Redzone(0, 100, 600, 100)
redzone2 = Redzone(0, 400, 600, 100)
destination = Destination(900, 250, 100, 100)

lineBoundariesList = [line1, line2, line3, line4, line5, line6, line7, line8, line9]
echoPathsList = []
rectAreasList = [water, redzone1, redzone2, destination, switch]

LEFT = 0
MIDDLE = 1
RIGHT = 2

walkInterval = 500
silentStepInterval = 800
lastWalk = 0
lastThrowRock = 0

running = True

while running:

    clock.tick(100)

    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN: 
            if (event.button == LEFT) or (event.button == RIGHT):
                lastWalk = pygame.time.get_ticks()
            elif event.button == MIDDLE:
                mousePos = event.pos
                lastThrowRock = pygame.time.get_ticks()
                pl.throwRock(mousePos, echoPathsList)

    mouses = pygame.mouse.get_pressed()
    if (mouses[LEFT] == 1):
        mousePos = event.pos
        pl.move(mousePos, pl.speed, echoPathsList, rectAreasList, lineBoundariesList)
        now = pygame.time.get_ticks()
        if (now - lastWalk) >= walkInterval:
            lastWalk = now
            pl.walk(echoPathsList)
            pygame.mixer.music.stop()
            pygame.mixer.Sound.play(footstep_soundA)
    elif (mouses[RIGHT] == 1):
        mousePos = event.pos
        pl.move(mousePos, pl.speed/2, echoPathsList, rectAreasList, lineBoundariesList)
        now = pygame.time.get_ticks()
        if (now - lastWalk) >= silentStepInterval:
            lastWalk = now
            pl.silentStep(echoPathsList)

    #water.draw(screen, pl)
    #redzone1.draw(screen, pl)
    #redzone2.draw(screen, pl)

    enemy1.awakened(echoPathsList)
    enemy1.pursue()
    enemy1.draw(screen, pl)

    for echoPath in echoPathsList:
        echoPath.move(rectAreasList)
        for line in lineBoundariesList:
        	echoPath.reflect(line)
        echoPath.draw(screen, pl)

    if (echoPathsList != []):
        for echoPath in echoPathsList:
            if echoPath.color[0] == 0:
                echoPathsList.remove(echoPath)
            
    #for line in lineBoundariesList:
        #line.draw(screen, pl)

    pl.draw(screen)

    pygame.display.update()

pygame.quit()




