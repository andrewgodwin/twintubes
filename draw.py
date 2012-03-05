"""
Drawing functions.
"""

import cairo
import math
from vector import Vector

class Direction(object):

    VECS = {
        0: Vector(0, -1),
        1: Vector(1, -1),
        2: Vector(1, 0),
        3: Vector(1, 1),
        4: Vector(0, 1),
        5: Vector(-1, 1),
        6: Vector(-1, 0),
        7: Vector(-1, -1),
    }

    def __init__(self, direction):
        self.direction = direction

    @property
    def vector(self):
        return self.VECS[self.direction].normalize()

    @property
    def left(self):
        return Direction((self.direction - 1) % 8)

    @property
    def angle(self):
        return (self.direction / 4.0) * math.pi

    @property
    def right(self):
        return Direction((self.direction + 1) % 8)

    @property
    def normalized(self):
        return Direction(self.direction % 4)

    def __eq__(self, other):
        return self.direction == other.direction

    def __hash__(self):
        return hash(self.direction)

    def delta(self, other):
        if other.direction == self.direction:
            return 0
        delta = other.direction - self.direction
        if delta > 4:
            return delta - 8
        elif delta < -4:
            return delta + 8
        else:
            return delta


Direction.N = Direction(0)
Direction.NE = Direction(1)
Direction.E = Direction(2)
Direction.SE = Direction(3)
Direction.S = Direction(4)
Direction.SW = Direction(5)
Direction.W = Direction(6)
Direction.NW = Direction(7)


class Segment(object):
    """
    Represents a (stylistic Tube) line on the canvas.
    Only has a start and end point/direction; the rest is determined automatically.
    """

    width = 3
    radius = 7
    min_length = 15
    platform_distance = 3.5
    platform_width = 2
    back_width = 5
    platform_back_width = 4

    PLATFORM_NONE = 0
    PLATFORM_LEFT = 1
    PLATFORM_RIGHT = 2
    PLATFORM_BOTH = 3

    def __init__(self, start_point, start_dir, end_point, end_dir, colors=None, platform=0, subtrack=False):
        self.start_point = start_point
        self.start_dir = start_dir
        self.end_point = end_point
        self.end_dir = end_dir
        self.colors = colors or [(0, 0, 0, 0)]
        self.platform = platform
        self.subtrack = subtrack

    def draw(self, ctx):
        "Draws the actual line on the given Cairo context"
        point = self.start_point
        dir = self.start_dir
        path = [(self.start_point, None)]
        while point != self.end_point:
            # Work out if the endpoint is to the left, right, or straight on
            # (done using dot product).
            toend = self.end_point - point
            # See if the result is directly ahead.
            if round(toend.projonto(dir.vector), 1) == round(abs(toend), 1):
                path.append((self.end_point, dir))
                break
            # Work out left and right dot projections
            left_proj = toend.projonto(dir.left.vector)
            right_proj = toend.projonto(dir.right.vector)
            if left_proj > right_proj:
                bend = lambda x: x.left
                proj_value = left_proj
            else:
                bend = lambda x: x.right
                proj_value = right_proj
            # Does it match a known pattern?
            # Single bend
            if self.end_dir == bend(dir) and proj_value > 0:
                # Work out the intersection point
                first_vector = dir.vector
                second_vector = bend(dir).vector
                p = Vector(second_vector.y, -second_vector.x)
                h = ((self.end_point - point).dot(p)) / first_vector.dot(p)
                if h > 0:
                    intersects = point + (first_vector * h)
                    # Go there.
                    path.append((intersects, dir))
                    path.append((self.end_point, bend(dir)))
                    break
                else:
                    # We can't make that. Go min length then turn
                    path.append((
                        (point + dir.vector * self.min_length),
                        dir,
                    ))
                    point = path[-1][0]
                    dir = bend(dir)
            # Double bend
            elif self.end_dir == bend(bend(dir)) and proj_value > 0:
                # Work out the intersection point
                first_vector = dir.vector
                second_vector = bend(bend(dir)).vector
                p = Vector(second_vector.y, -second_vector.x)
                h = ((self.end_point - point).dot(p)) / first_vector.dot(p)
                if h > 0:
                    intersects = point + (first_vector * h)
                    # Go up to it but not quite, so we get a nice corner
                    offset = min(
                        abs((self.end_point - intersects).projonto(second_vector)),
                        abs((self.start_point - intersects).projonto(first_vector)),
                    )
                    path.append((intersects - (first_vector * (offset - self.min_length)), dir))
                    point = path[-1][0]
                    dir = bend(dir)
                else:
                    # We can't make that. Go min length then turn
                    path.append((
                        (point + dir.vector * self.min_length),
                        dir,
                    ))
                    point = path[-1][0]
                    dir = bend(dir)
            # Dogleg
            elif self.end_dir == dir and proj_value > 0:
                # Work out the midpoint
                mid = (self.start_point + self.end_point) / 2.0
                # Work out the intersection
                first_vector = dir.vector
                second_vector = bend(dir).vector
                p = Vector(second_vector.y, -second_vector.x)
                h = ((mid - point).dot(p)) / first_vector.dot(p)
                intersects = point + (first_vector * h)
                # Turn at that point
                path.append((intersects, dir))
                point = path[-1][0]
                dir = bend(dir)
            # Too much already?
            elif len(path) > 10:
                break
            # Nope. Go for the min length and turn.
            else:
                path.append((
                    (point + dir.vector * self.min_length),
                    dir,
                ))
                point = path[-1][0]
                dir = bend(dir)
        if not self.subtrack:
            # Draw the white background to do crossovers nicely
            self.draw_path(ctx, path, back=True)
        # Possibly draw the platform highlights too
        if self.platform & 1:
            ctx.save()
            ctx.translate(*(self.start_dir.left.left.vector * self.platform_distance))
            if not self.subtrack:
                self.draw_path(
                    ctx,
                    path,
                    True,
                    back = True,
                )
            self.draw_path(
                ctx,
                path,
                True,
            )
            ctx.restore()
        if self.platform & 2:
            ctx.save()
            ctx.translate(*(self.start_dir.right.right.vector * self.platform_distance))
            if not self.subtrack:
                self.draw_path(
                    ctx,
                    path,
                    True,
                    back = True,
                )
            self.draw_path(
                ctx,
                path,
                True,
            )
            ctx.restore()
        # Now, draw the main path.
        self.draw_path(ctx, path)

    def draw_path(self, ctx, path, platform=False, debug=False, back=False):
        ctx.move_to(*path[0][0])
        for (corner, dir), (next_corner, next_dir) in zip(path[1:], path[2:]):
            # Work out where the center of the arc is
            out_vector = (dir.vector + next_dir.vector.flip()).normalize().flip()
            dir_delta = dir.delta(next_dir)
            center_point = corner + (out_vector * (self.radius / math.cos(dir_delta * math.pi * 0.125)))
            if dir_delta  > 0:
                ctx.arc(
                    center_point.x,
                    center_point.y,
                    self.radius,
                    (next_dir.angle + (math.pi * 0.75)) % (math.pi*2),
                    (dir.angle - (math.pi * 0.75)) % (math.pi*2),
                )
            else:
                ctx.arc_negative(
                    center_point.x,
                    center_point.y,
                    self.radius,
                    (next_dir.angle + (math.pi * 0.25)) % (math.pi*2),
                    (dir.angle - (math.pi * 0.25)) % (math.pi*2),
                )
        # Overshoot slightly to stop artifacts, if this isn't the white bit
        if not back:
            ctx.line_to(*(path[-1][0] + self.end_dir.vector * 0.5))
        else:
            ctx.line_to(*path[-1][0])
        if platform and back:
            #ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
            ctx.set_source_rgb(1, 1, 1)
            ctx.set_line_width(self.platform_back_width)
        elif platform:
            ctx.set_source_rgb(0.5, 0.5, 0.5)
            ctx.set_line_width(self.platform_width)
        elif back:
            ctx.set_source_rgb(1, 1, 1)
            ctx.set_line_width(self.back_width)
        else:
            ctx.set_source_rgb(*self.colors[0])
            ctx.set_line_width(self.width)
        # Draw
        ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        # Possible debug
        if debug:
            ctx.move_to(*path[0][0])
            for (corner, dir), (next_corner, next_dir) in zip(path[1:], path[2:]):
                ctx.line_to(*corner)
            ctx.line_to(*(path[-1][0] + self.end_dir.vector * 0.5))
            ctx.set_source_rgb(1, 0, 1)
            ctx.set_line_width(0.5)
            ctx.stroke()


