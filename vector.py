import math

class Vector(object):
    
    """
    A 2D vector class.
    """
    
    def __init__(self, x, y=None):
        if y == None:
            if isinstance(x, Vector):
                self.x, self.y = x.x, x.y
            elif len(x) == 2:
                self.x, self.y = x
            else:
                raise ValueError("Please pass either a tuple of (x, y), a Vector, or two parameters.")
        else:
            self.x = x
            self.y = y
    
    def __add__(self, other):
        return Vector(self.x+other.x, self.y+other.y)
    
    def __sub__(self, other):
        return Vector(self.x-other.x, self.y-other.y)
    
    def __mul__(self, num):
        return Vector(self.x*num, self.y*num)
    
    def __div__(self, num):
        return self * (1.0 / num)
    
    def __len__(self):
        return 2
    
    def __abs__(self):
        "Cartesian distance of this vector"
        return (self.x**2 + self.y**2) ** 0.5
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if not isinstance(other, Vector):
            return False
        return (self.x == other.x) and (self.y == other.y)
    
    def __iter__(self):
        return iter(self.tuple())

    def tuple(self):
        "Returns the x and y parts of the vector raw."
        return self.x, self.y
    
    def __repr__(self):
        return "<%s,%s>" % (self.x, self.y)

    def dot(self, other):
        return (self.x * other.x) + (self.y * other.y)

    def projonto(self, other):
        return self.dot(other) / abs(other)

    def normalize(self):
        return self / abs(self)
    
    def floor(self):
        "Returns this vector with components floored to the nearest integer"
        return Vector(int(math.floor(self.x)), int(math.floor(self.y)))

    def flip(self):
        return self * -1
    
