import math


class Point(object):
    '''Creates a point on a coordinate plane with values x and y.'''

    COUNT = 0

    def __init__(self, x, y):
        '''Defines x and y variables'''
        self.x = x
        self.y = y

    def move(self, dx, dy):
        '''Determines where x and y move'''
        self.x = self.x + dx
        self.y = self.y + dy

    def __str__(self):
        return "Point(%s,%s)"%(self.x, self.y)


    def getx(self):
        return self.x

    def gety(self):
        return self.y

    def distance(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx**2 + dy**2)
    

class Rect:

    def __init__(self, x, y, w, h):

       self.x = x
       self.y = y
       self.w = w
       self.h = h

    def complete(self):
        return self.x,self.y,self.w,self.h


    def right(self):
        return self.x + self.w

    def __str__(self):
        return('Rectangle(' + str(self.x) + ',' + str(self.y) + ','
                    + str(self.w) + ',' + str(self.h)+')')

    def bottom(self):
        return self.y + self.h

    def __str__(self):
        return('Rectangle(' + str(self.x) + ',' + str(self.y) + ','
               + str(self.w) + ',' + str(self.h) + ')')
    def size(self):
        return self.w,self.h

    def position(self):
        return self.x,self.y

    def area(self):
        return self.w * self.h

    def center(self):
        return Point(self.x + int(self.w//2), self.y + int(self.h//2))

    def ltP(self):
        return Point(self.x, self.y)

    def rtP(self):
        return Point(self.right(), self.y)

    def lbP(self):
        return Point(self.x, self.bottom())

    def rbP(self):
        return Point(self.right(), self.bottom())

    def dist(self, rect):
        import math
        return math.sqrt((self.center().x - rect.center().x) ** 2 + (self.center().y - rect.center().y) ** 2)


def doOverlap(l1, r1, l2, r2):
    # If one rectangle is on left side of other
    if (l1.x >= r2.x or l2.x >= r1.x):
        return False

    # If one rectangle is above other
    if (l1.y <= r2.y or l2.y <= r1.y):
        return False

    return True

def isoverlap(rt1, rt2):
    cond1 = max(rt1.x, rt2.x) < min(rt1.right(), rt2.right())
    cond2 = max(rt1.y, rt2.y) < min(rt1.bottom(), rt2.bottom())

    if cond1 and cond2:
        return True
    else:
        return False
    # rrt = rt2 if lrt == rt1 else rt1
    #
    # dx = rrt.right() - lrt.x
    # dy1 = rrt.bottom() - lrt.y
    # dy2 = lrt.bottom() - rrt.y
    #
    # if dx <= lrt.w + rrt.w and dy1 <= lrt.h + rrt.h and dy2 <= lrt.h + rrt.h:
    #     return True
    #
    # return False


def LineIntersectsLine(l1p1, l1p2, l2p1, l2p2):
    q = (l1p1.y - l2p1.y) * (l2p2.x - l2p1.x) - (l1p1.x - l2p1.x) * (l2p2.y - l2p1.y)
    d = (l1p2.x - l1p1.x) * (l2p2.y - l2p1.y) - (l1p2.y - l1p1.y) * (l2p2.x - l2p1.x)

    if (d == 0):
        return False
    r = q / d
    q = (l1p1.y - l2p1.y) * (l1p2.x - l1p1.x) - (l1p1.x - l2p1.x) * (l1p2.y - l1p1.y)
    s = q / d
    if (r < 0 or r > 1 or s < 0 or s > 1):
        return False
    return True


# rect1 = Rect(84,90,50,34)
# rect2 = Rect(84,90,50,34)
# ret = isoverlap(rect1, rect2)
# dist = rect1.dist(rect2)
# a = 3