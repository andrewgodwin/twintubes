import cairo
from datastructures import SortedDict
from draw import Segment, Direction
from platform import Platform, PointsPlatform
from vector import Vector

class Station(object):
    """
    A place on the map that lines go to and from.
    """

    station_gap = 10
    platform_class = Platform
    label_color = (0, 51/255.0, 102/255.0)
    label_size = 12
    label_distance = Vector(6, 4)

    def __init__(self, code, name, offset, relative_to=None):
        self.code = code
        self.name = name
        self._offset = offset
        self.relative_to = relative_to
        self.platforms = SortedDict()
        self.placed = SortedDict()
        self.label_direction = None
        self.label_offset = Vector(0, 0)

    @property
    def offset(self):
        if self.relative_to:
            return self.relative_to.offset + self._offset
        else:
            return self._offset

    def add_platform(self, number, direction, line, platform_side):
        # Work out its coords
        norm_direction = direction.normalized
        self.placed[norm_direction] = self.placed.get(norm_direction, 0) + 1
        # Make it
        self.platforms[number] = self.platform_class(
            station = self,
            number = number,
            direction = direction,
            offset = Vector(0, 0),
            line = line,
            platform_side = platform_side,
        )
        self.platforms[number].offset_number = self.placed[norm_direction] - 1
        # Recalculate all platform locations
        for platform in self.platforms.values():
            norm_direction = platform.direction.normalized
            platform.offset = (
                norm_direction.right.right.vector *
                (platform.offset_number + 0.5 - (self.placed[norm_direction] / 2.0)) *
                self.station_gap
            )

    def __repr__(self):
        return "<Station %s (%s)>" % (self.code, self.name)

    def decide_label_direction(self):
        self.label_direction = Direction.W

    def draw(self, ctx):
        """
        Draws the station and its platforms.
        """
        for platform in self.platforms.values():
            if not platform.drawn:
                platform.draw(ctx)
        if not self.label_direction:
            self.decide_label_direction()
        self.draw_label(ctx)

    def draw_debug(self, ctx, highlighted):
        """
        Draws a debug symbol for this station.
        """
        # Draw a cross on the station
        ctx.save()
        if self in highlighted:
            ctx.set_source_rgba(100, 0, 0, 0.9)
        else:
            ctx.set_source_rgba(255, 0, 255, 0.6)
        ctx.translate(*self.offset)
        ctx.move_to(-5, -5)
        ctx.line_to(5, 5)
        ctx.move_to(5, -5)
        ctx.line_to(-5, 5)
        ctx.set_line_width(2)
        ctx.stroke()
        # Draw a dot on each platform
        for platform in self.platforms.values():
            ctx.save()
            ctx.translate(*platform.offset)
            ctx.arc(0, 0, 3, 0, 7)
            ctx.fill()
            ctx.restore()
        # Draw a number on each platform
        for platform in self.platforms.values():
            ctx.save()
            ctx.translate(*platform.offset)
            ctx.set_source_rgb(0, 0, 100)
            ctx.select_font_face(
                "LondonTwo",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL,
            )
            ctx.set_font_size(4)
            ctx.move_to(-1, 1)
            ctx.show_text(platform.number)
            ctx.restore()
        ctx.restore()


    def draw_label(self, ctx):
        if self.name:
            # Work out the bounding box of the platforms
            x_range = [0, 0]
            y_range = [0, 0]
            platform_directions = set()
            label_dir = self.label_direction
            for platform in self.platforms.values():
                platform_directions.add(platform.direction)
                # Diagonal platforms perpendicular to label direction
                # get put closer
                if platform.direction == label_dir.right.right or \
                   platform.direction == label_dir.left.left:
                    ends = [platform.mid_point]
                    if platform.platform_side & Segment.PLATFORM_LEFT:
                        ends.append(
                            platform.mid_point +
                            (platform.direction.left.left.vector * Segment.platform_distance)
                        )
                    if platform.platform_side & Segment.PLATFORM_RIGHT:
                        ends.append(
                            platform.mid_point +
                            (platform.direction.right.right.vector * Segment.platform_distance)
                        )
                # Use bounding box
                else:
                    ends = [platform.start_point, platform.end_point]
                    if platform.platform_side & Segment.PLATFORM_LEFT:
                        ends.append(
                            platform.start_point +
                            (platform.direction.left.left.vector * Segment.platform_distance)
                        )
                        ends.append(
                            platform.end_point +
                            (platform.direction.left.left.vector * Segment.platform_distance)
                        )
                    if platform.platform_side & Segment.PLATFORM_RIGHT:
                        ends.append(
                            platform.start_point +
                            (platform.direction.right.right.vector * Segment.platform_distance)
                        )
                        ends.append(
                            platform.end_point +
                            (platform.direction.right.right.vector * Segment.platform_distance)
                        )
                for end in ends:
                    end = end - self.offset
                    x_range[0] = min(end.x, x_range[0])
                    y_range[0] = min(end.y, y_range[0])
                    x_range[1] = max(end.x, x_range[1])
                    y_range[1] = max(end.y, y_range[1])
            ctx.set_source_rgb(*self.label_color)
            ctx.select_font_face(
                "LondonTwo",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL,
            )
            ctx.set_font_size(self.label_size)
            lines = [{"text": x.strip()} for x in self.name.split("\\n")]
            # Work out the size of the entire label
            dir_vector = self.label_direction.vector
            width = 0
            height = 0
            for line in lines:
                x_bearing, y_bearing, this_width, this_height = \
                    ctx.text_extents(line['text'])[:4]
                width = max(width, this_width)
                height += this_height
                line['y'] = height
                line['height'] = this_height
                line['width'] = this_width
                line['x_bearing'] = x_bearing
                line['y_bearing'] = y_bearing
                height += 1
            height -= 1
            # Work out where to place it, using the text midpoint as the origin
            if dir_vector.x < 0:
                x_offset = x_range[0] - width / 2.0
                x_mult = 1
            elif dir_vector.x == 0:
                x_offset = 0
                x_mult = 0.5
            else:
                x_offset = x_range[1] + width / 2.0
                x_mult = 0
            if dir_vector.y < 0:
                y_offset = y_range[0] - height / 2.0
                y_delta = -ctx.font_extents()[1] * 0.6
            elif dir_vector.y == 0:
                y_offset = 0
                y_delta = 0
            else:
                y_offset = y_range[1] + height / 2.0
                y_delta = 0
            y_offset -= (self.label_size / 8.0)
            # Draw!
            for line in lines:
                line_x = -line['x_bearing'] + (-width/2.0) - (line['width'] - width) * x_mult
                line_y = y_delta + line['y'] - (height / 2.0)
                position = (
                    Vector(x_offset, y_offset) +
                    Vector(line_x, line_y) +
                    Vector(
                        dir_vector.x * self.label_distance.x,
                        dir_vector.y * self.label_distance.y,
                    ) +
                    self.offset +
                    self.label_offset
                )
                ctx.move_to(*position)
                ctx.show_text(line['text'])
            if False: # debug
                ctx.fill()
                ctx.set_source_rgb(0,1,1)
                ctx.arc(self.offset.x + x_offset, self.offset.y + y_offset, 2, 0, 7)
                ctx.fill()
                ctx.set_source_rgb(0,0.5,1)
                ctx.arc(self.offset.x + x_range[1], self.offset.y + y_range[1], 2, 0, 7)
                ctx.fill()
                ctx.set_source_rgb(1,0,1)
                ctx.arc(self.offset.x + x_range[0], self.offset.y + y_range[0], 2, 0, 7)
                ctx.fill()


class Points(Station):
    """
    A zero-length Station.
    """

    platform_class = PointsPlatform

