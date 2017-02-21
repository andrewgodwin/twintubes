import cairo
import os
import sys
import argparse
from vector import Vector
from draw import Direction, Segment
from datastructures import SortedDict
from station import Station, Points, Depot, Sidings, DisusedStation


class Line(object):

    def __init__(self, code, colors):
        self.code = code
        self.colors = colors


class Map(object):

    padding = 50

    def __init__(self):
        pass

    def load(self, filename):
        self.stations = SortedDict()
        self.lines = SortedDict()
        self.extents = [0, 0, 0, 0]
        self.outbounds = []
        draw_last = []
        draw_first = []
        with open(filename) as fh:
            for lineno, line in enumerate(fh):
                line = line.strip()
                if line and line[0] != "#":
                    # Get the parts
                    parts = line.split()
                    type, parts = parts[0], parts[1:]
                    # What kind of line is it?
                    if type == "line":
                        # Line definition
                        code = parts[0]
                        colors = [(
                            int(part[0:2], 16) / 255.0,
                            int(part[2:4], 16) / 255.0,
                            int(part[4:8], 16) / 255.0,
                        ) for part in parts[1].split(",")]
                        self.lines[code] = Line(code, colors)

                    # Track segment
                    elif type in ("track", "subtrack"):
                        # It's a station-to-station description
                        station_code, platform_number = parts[0].split("-", 1)
                        dest_code, dest_number = parts[1].split("-", 1)
                        station = self.stations[station_code]
                        # Check for reverses
                        leaves_start = False
                        if platform_number[-1] == "!":
                            leaves_start = True
                            platform_number = platform_number[:-1]
                        finishes_end = False
                        if dest_number[-1] == "!":
                            finishes_end = True
                            dest_number = dest_number[:-1]
                        # Add it
                        try:
                            self.add_outbound(
                                station.platforms[platform_number],
                                self.stations[dest_code].platforms[dest_number],
                                self.lines[parts[2]],
                                leaves_start = leaves_start,
                                finishes_end = finishes_end,
                                subtrack = (type == "subtrack"),
                            )
                        except:
                            print "Error context: %s, %s" % (station, parts)
                            raise

                    # Station/waypoint record
                    elif type in ("station", "waypoint", "depot", "sidings", "disstation"):
                        # It's a station or points definition
                        code = parts[0]
                        index = 1
                        while "," not in parts[index]:
                            index += 1
                        name = " ".join(parts[1:index])
                        # Work out the coordinates
                        coord_parts = parts[index].split(",")
                        coords = Vector(*map(float, coord_parts[-2:])) * 10
                        if len(coord_parts) == 3:
                            relative_to = self.stations[coord_parts[0]]
                        else:
                            relative_to = None
                        if type == "station":
                            station_class = Station
                        elif type == "depot":
                            station_class = Depot
                        elif type == "sidings":
                            station_class = Sidings
                        elif type == "disstation":
                            station_class = DisusedStation
                        else:
                            station_class = Points
                        last_station = self.stations[code] = station_class(
                            code,
                            name,
                            coords,
                            relative_to = relative_to,
                        )
                        self.extents[0] = min(coords.x, self.extents[0])
                        self.extents[1] = max(coords.x, self.extents[1])
                        self.extents[2] = min(coords.y, self.extents[2])
                        self.extents[3] = max(coords.y, self.extents[3])

                    # Platform record
                    elif type == "platform":
                        # Add a platform to the last station
                        direction = getattr(Direction, parts[1])
                        try:
                            line = self.lines[parts[2]]
                        except (IndexError, KeyError):
                            line = self.lines["error"]
                        try:
                            platform_side_code = parts[3]
                            platform_side = {
                                "L": Segment.PLATFORM_LEFT,
                                "R": Segment.PLATFORM_RIGHT,
                                "B": Segment.PLATFORM_BOTH,
                                "N": Segment.PLATFORM_NONE,
                            }[platform_side_code.upper()]
                        except IndexError:
                            platform_side = Segment.PLATFORM_BOTH
                        self.stations[code].add_platform(parts[0], direction, line, platform_side)

                    # Drawing order modifiers
                    elif type == "draw":
                        if parts[0] == "first":
                            draw_first.append(last_station)
                        elif parts[0] == "last":
                            draw_last.append(last_station)
                        else:
                            raise ValueError("Unknown draw position %r" % parts[0])

                    # Label placement modifiers
                    elif type == "label":
                        last_station.label_direction = getattr(Direction, parts[0])
                    elif type == "label_offset":
                        last_station.label_offset = Vector(map(int, parts[0].split(",")))

                    # Unknown
                    else:
                        raise ValueError("Unknown line type %r" % type)
        # Now reorder those with special draw clauses
        for station in draw_first:
            self.stations.insert(0, station.code, station)
        for station in draw_last:
            self.stations.insert(len(self.stations), station.code, station)

    def save_offsets(self, filename):
        """
        Opens up the file, reads it, and writes new offsets if needs be.
        """
        with open(filename) as in_file:
            with open(filename + ".new", "w") as out_file:
                for lineno, line in enumerate(in_file):
                    line = line.strip()
                    parts = line.split()
                    type = parts[0] if parts else None
                    # What kind of line is it?
                    if type in ("station", "waypoint", "depot", "sidings", "disstation"):
                        # Get the code
                        code = parts[1]
                        # Get the real station
                        station = self.stations[code]
                        if station.relative_to:
                            coords = "%s,%.1f,%.1f" % (
                                station.relative_to.code,
                                (station._offset.x // 5) / 2.0,
                                (station._offset.y // 5) / 2.0,
                            )
                        else:
                            coords = "%.1f,%.1f" % (
                                (station._offset.x // 5) / 2.0,
                                (station._offset.y // 5) / 2.0,
                            )
                        out_file.write("%(type)s %(code)s %(name)s %(coords)s\n" % {
                            "type": type,
                            "code": code,
                            "name": station.name,
                            "coords": coords,
                        })
                    else:
                        out_file.write(line + "\n")
        os.rename(filename + ".new", filename)

    def nearest_station(self, coords):
        """
        Finds the nearest station to the coords, and returns it along with the
        distance to it.
        """
        nearest = (None, 100000000)
        for station in self.stations.values():
            distance = abs(station.offset - coords)
            if distance < nearest[1]:
                nearest = (station, distance)
        return nearest

    def stations_inside_bounds(self, tl, br):
        """
        Finds the nearest station to the coords, and returns it along with the
        distance to it.
        """
        for station in self.stations.values():
            if tl.x <= station.offset.x <= br.x and \
               tl.y <= station.offset.y <= br.y:
                if not station.relative_to:
                    yield station

    def add_outbound(self, platform, destination, line, subtrack=False, leaves_start=False, finishes_end=False):
        self.outbounds.append((
            platform,
            destination,
            line,
            subtrack,
            leaves_start,
            finishes_end,
        ))
                            
    def draw(self, ctx):
        """
        Draws the entire map.
        """
        for station in self.stations.values():
            for platform in station.platforms.values():
                platform.drawn = False
        self.draw_outbound(ctx)
        for station in self.stations.values():
            station.draw(ctx)

    def draw_debug(self, ctx, highlighted=set()):
        """
        Draws debug hints for stations and platforms.
        """
        for station in self.stations.values():
            station.draw_debug(ctx, highlighted)

    def draw_outbound(self, ctx):
        # Draw outbound segments
        for platform, destination, line, subtrack, leaves_start, finishes_end in self.outbounds:
            # Draw the ends if they've not been done yet.
            if not platform.drawn:
                platform.draw(ctx)
            if not destination.drawn:
                destination.draw(ctx)
            # Make sure which ends we're using
            if leaves_start:
                start_point = platform.start_point
                start_dir = platform.direction.left.left.left.left
            else:
                start_point = platform.end_point
                start_dir = platform.direction
            if finishes_end:
                end_point = destination.end_point
                end_dir = destination.direction.left.left.left.left
            else:
                end_point = destination.start_point
                end_dir = destination.direction
            # Draw!
            Segment(
                start_point,
                start_dir,
                end_point,
                end_dir,
                line.colors,
                subtrack = subtrack,
            ).draw(ctx)

    def to_pdf(self, filename):
        width = (self.extents[1] - self.extents[0]) + self.padding * 2
        height = (self.extents[3] - self.extents[2]) + self.padding * 2
        surface = cairo.PDFSurface(filename, width, height)
        ctx = cairo.Context(surface)
        ctx.translate(
            self.padding - self.extents[0],
            self.padding - self.extents[2],
        )
        self.draw(ctx)
        surface.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Twin Tubes map")
    parser.add_argument('in_file', help='The source file for the map')
    parser.add_argument('-o', '--out-file', help='The output file name')
    args = parser.parse_args()
    if args.out_file == None:
        args.out_file = os.path.splitext(args.in_file)[0] + '.pdf'

    m = Map()
    m.load(args.in_file)
    m.to_pdf(args.out_file)
