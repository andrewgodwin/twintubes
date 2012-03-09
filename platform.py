from draw import Segment


class Platform(object):

    length = 22
    color = (0.5, 0.5, 0.5)

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
                platform_color = self.color,
            ).draw(ctx)
        self.drawn = True


class PointsPlatform(Platform):
    "Zero-length platform used for points."

    length = 0

    def draw(self, ctx):
        "Draws this platform on the map"
        pass


class DepotPlatform(Platform):
    "Long dashed platform for depots."

    length = 14

    def draw(self, ctx):
        "Draws this platform on the map"
        if self.line.code != "none":
            Segment(
                self.start_point,
                self.direction,
                self.end_point,
                self.direction,
                self.line.colors,
                platform = 0,
                dashed = True,
            ).draw(ctx)
        self.drawn = True


class SidingsPlatform(DepotPlatform):
    "Short dashed line for sidings."

    length = 6


class DisusedPlatform(Platform):
    "A platform that is no longer in use"

    color = (0.8, 0.8, 0.8)
