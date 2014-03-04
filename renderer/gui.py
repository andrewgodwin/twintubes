from main import Map
from vector import Vector

import sys
import pygtk
pygtk.require('2.0')
import gtk
import cairo


class Gui(object):

    def __init__(self, filename):
        self.filename = filename
        self.make_window()
        self.map = Map()
        self.map.load(self.filename)
        self.aa = True
        self.markings = True

    def make_window(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Series Of Tubes")

        # create all the basic widgets.
        self.vbox = gtk.VBox()

        self.menubar = gtk.MenuBar()
        self.create_map_menu()

        self.renderer = Renderer(self)

        self.vbox.pack_start(self.menubar, expand=False)
        self.vbox.pack_start(self.renderer, expand=True)

        # exit the app on window close
        self.window.connect("delete_event", self.quit)

        self.window.add(self.vbox)
        self.window.show_all()

    def create_map_menu(self):
        "Makes the 'map' menu."
        menu = gtk.Menu()
        main_item = gtk.MenuItem("Map")

        self.aa_item = gtk.MenuItem("Antialiasing Off")
        self.aa_item.connect("activate", self.aa_toggle)
        menu.append(self.aa_item)

        self.markings_item = gtk.MenuItem("Markings Off")
        self.markings_item.connect("activate", self.markings_toggle)
        menu.append(self.markings_item)

        save_item = gtk.MenuItem("Reload")
        save_item.connect("activate", self.reload)
        menu.append(save_item)

        save_item = gtk.MenuItem("Save")
        save_item.connect("activate", self.save)
        menu.append(save_item)

        quit_item = gtk.MenuItem("Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        main_item.set_submenu(menu)

        self.menubar.append(main_item)

    def aa_toggle(self, *args):
        "Callback to turn antialiasing on and off."
        self.aa = not self.aa
        if self.aa:
            self.aa_item.get_child().set_text("Antialiasing Off")
        else:
            self.aa_item.get_child().set_text("Antialiasing On")
        self.renderer.queue_draw()

    def markings_toggle(self, *args):
        "Callback to turn markings on and off."
        self.markings = not self.markings
        if self.markings:
            self.markings_item.get_child().set_text("Markings Off")
        else:
            self.markings_item.get_child().set_text("Markings On")
        self.renderer.queue_draw()

    def reload(self, *args, **kwds):
        self.map.load(self.filename)
        self.renderer.queue_draw()

    def save(self, *args, **kwds):
        self.map.save_offsets(self.filename)

    def quit(self, *args, **kwds):
        "Exit the app when the main window is closed."
        gtk.main_quit()
        return False

    def main(self):
        gtk.main()


class Renderer(gtk.DrawingArea):

    # How many pixels before we consider it a drag, not a click
    CLICK_WIBBLE = 3
    CLICK_FUZZY = 10

    # Draw in response to an expose-event
    __gsignals__ = {"expose-event": "override"}

    def __init__(self, gui):
        gtk.DrawingArea.__init__(self)
        self.gui = gui
        self.set_size_request(800, 400)
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)

        # Set initial scale and position
        self.scale = 150
        self.x, self.y = -5, -5
        self.zoomstep = 1.5

        # Connect button presses
        self.connect("button-press-event", self.mouse_pressed)
        self.connect("button-release-event", self.mouse_released)
        self.connect("motion-notify-event", self.mouse_moved)
        self.connect("scroll-event", self.scrolled)
        self.pressed = None
        self.select_pressed = None
        self.selected = []

    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        "Called when something needs drawing."

        # Create the cairo context
        cr = self.window.cairo_create()

        # Turn antialiasing off if needed
        if self.gui.aa:
            cr.set_antialias(cairo.ANTIALIAS_GRAY)
        else:
            cr.set_antialias(cairo.ANTIALIAS_NONE)

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())

    def mouse_pressed(self, widget, event):
        "Callback for the mouse being pressed."
        # If left mouse button pressed...
        if event.button == 1:
            # Store drag start
            if self.selected:
                self.pressed = (
                    Vector(event.x, event.y),
                    [item._offset for item in self.selected],
                )
            else:
                self.pressed = (
                    Vector(event.x, event.y),
                    Vector(self.x, self.y),
                )
        elif event.button == 3:
            # Store select box start
            self.select_pressed = (
                Vector(event.x, event.y),
                Vector(self.window_to_space(event.x, event.y, self.gui.window)),
            )

    def mouse_released(self, widget, event):
        "Callback for the mouse being released."
        # When left mouse button is released...
        if event.button == 1 and self.pressed:
            new_mouse_pos = Vector(event.x, event.y)
            # See if they clicked & released inside a small area; that's a click
            orig_mouse_pos = self.pressed[0]
            if abs(orig_mouse_pos - new_mouse_pos) < self.CLICK_WIBBLE:
                self.mouse_clicked(widget, event)
            # We're no longer pressing.
            self.pressed = None
            self.dragged_corner = None
        elif event.button == 3 and self.select_pressed:
            # Work out the region they selected
            here = Vector(self.window_to_space(event.x, event.y, self.gui.window))
            min_x = min(here.x, self.select_pressed[1].x)
            min_y = min(here.y, self.select_pressed[1].y)
            max_x = max(here.x, self.select_pressed[1].x)
            max_y = max(here.y, self.select_pressed[1].y)
            self.selected = list(self.gui.map.stations_inside_bounds(
                Vector(min_x, min_y),
                Vector(max_x, max_y),
            ))
            self.select_pressed = None
            self.queue_draw()

    def mouse_moved(self, widget, event):
        "Callback for when the mouse is moved."
        if self.pressed:
            new_mouse_pos = Vector(event.x, event.y)
            unit = self.unit_from_window(event.window)
            # Are we dragging a selected thing?
            if self.selected:
                orig_mouse_pos, orig_poss = self.pressed
                for item, orig_pos in zip(self.selected, orig_poss):
                    item._offset = orig_pos + (new_mouse_pos - orig_mouse_pos) / unit
                    item._offset = (item._offset / 5).floor() * 5
            # No, just pan.
            else:
                orig_mouse_pos, orig_window_pos = self.pressed
                new_window_pos = (orig_window_pos - (new_mouse_pos - orig_mouse_pos) / unit)
                self.x = new_window_pos.x
                self.y = new_window_pos.y
            self.queue_draw()

    def mouse_clicked(self, widget, event):
        "Callback for when mouse is clicked."
        # Is there a station near the click event?
        world_coords = self.window_to_space(event.x, event.y, self.window)
        # Find the nearest station
        nearest_station, distance = self.gui.map.nearest_station(Vector(*world_coords))
        if distance < self.CLICK_FUZZY:
            self.selected = [nearest_station]
        else:
            self.selected = []
        self.queue_draw()

    def scrolled(self, widget, event):
        "Callback for when mouse is scrolled."
        # What was our worldpos before scaling?
        x, y = event.x, event.y
        # Based on scroll direction, pick a zoom factor
        if event.direction == gtk.gdk.SCROLL_DOWN:
            factor = self.zoomstep
        elif event.direction == gtk.gdk.SCROLL_UP:
            factor = 1.0 / self.zoomstep
            if self.scale < 0.2:  # Don't go down too far!
                factor = 1
        # Move by orig - (orig / scale)
        self.scale *= factor
        # Work out new position (zoom is centred on mouse
        unit = self.unit_from_window(event.window)
        self.x -= (x - (x / factor)) / unit
        self.y -= (y - (y / factor)) / unit
        # Redraw window
        self.queue_draw()

    def unit_from_window(self, window):
        "Returns the current 'unit' size for the World -> window transform."
        mindim = 200
        return max(float(mindim / self.scale), 0.0001)

    def window_to_space(self, x, y, window):
        "Converts from pixel coords on the window to coords in the World."
        unit = self.unit_from_window(window)
        sx = (x / unit) + self.x
        sy = (y / unit) + self.y
        return sx, sy

    def draw(self, cr, width, height):

        # Work out the current scale
        unit = self.unit_from_window(self.window)

        # Fill the background with white
        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        # Draw the current map
        cr.save()
        cr.scale(unit, unit)
        cr.translate(-self.x, -self.y)
        self.gui.map.draw(cr)
        if self.gui.markings:
            self.gui.map.draw_debug(cr, set(self.selected))
        cr.restore()


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print "You must supply a file to work from."
        sys.exit(1)
    Gui(filename).main()
