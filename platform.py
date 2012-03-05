from draw import Segment

class Platform(object):

    length = 22

    def __init__(self, station, number, direction, offset, platform_side, line):
        self.station = station
        self.number = number
        self.direction = direction
        self.offset = offset
        self.line = line
        self.platform_side = platform_side
        self.drawn = False
        # Calculate positions
        self.half_length = self.direction.vector * (self.length / 2.0)

    @property
    def start_point(self):
        return self.station.offset + self.offset - self.half_length

    @property
    def end_point(self):
        return self.station.offset + self.offset + self.half_length

    @property
    def mid_point(self):
        return self.station.offset + self.offset

    def __repr__(self):
        return "<Platform %s %s>" % (self.number, self.station)

    def draw(self, ctx):
        "Draws this platform on the map"
        # Draw the main platform segment
        if self.line.code != "none":
            Segment(
                self.start_point,
                self.direction,
                self.end_point,
                self.direction,
                self.line.colors,
                platform = self.platform_side,
            ).draw(ctx)
        self.drawn = True


class PointsPlatform(Platform):
    "Zero-length platform used for points."

    length = 0

    def draw(self, ctx):
        "Draws this platform on the map"
        pass
