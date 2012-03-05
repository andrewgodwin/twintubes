Twin Tubes
==========

This is the software that powers the Series Of Twin Tubes map - more information
at http://www.aeracode.org/projects/twintubes/. It's a bit rough around the edges,
but I figure it's better to get it released than let it linger on my hard drive.

Requirements
------------

 - Python 2.6 or 2.7
 - Pycairo (python-cairo package on Debian/Ubuntu systems)
 - PyGTK (for the GUI editor only)

Usage
-----

To render the map, run (making sure you're in the directory)::

    python main.py

It will spit out a raw PDF called "london.pdf". It should probably take parameters.

To use the GUI tool, first ensure you have GTK around and working properly (which
probably means using a Linux system, or possibly the X emulation on OSX), then run:

    python gui.py

The refresh rate on the drawing is pretty slow with the full London map, as it does
all the calculations every time, but it's still better than text. It'll auto-load the
london.txt file, and if you press "save" it will **SAVE OVER your london.txt file with
no prompting** (but keeping the comments intact). You can't create stations in the GUI;
the workflow I used was to put them roughly correct in the text file, and then smarten
it up in the GUI to get it all to fit.

File Format
-----------

The london.txt file is in a custom format (of course) and defines the lines and platforms.
Line drawing is mostly automatic, but in some cases to help get a non-natural curve in
(e.g. Jubilee south of Waterloo) or to push points to the right end, there's waypoints as well.

The available keywords are:

 - line <name> <color>: Defines a line. Name is symbolic only.

 - station <code> <title> [<relative_to>,]<x>,<y>: Starts a station stanza. Code is used to refer to it later.
 - waypoint <code> [<relative_to>,]<x>,<y>: Alternative to station with 0-length platforms. For routing.
 - label <dir>: Where <dir> is one of N, NE, E, etc. Defines where the label is relative to the station.
 - label_offset <x> <y>: For fine-tuning of label placement on the trickier stations.
 - platform <number> <dir> <line> <side>: A platform called "number" (can be any string), with direction <dir>
   on line <line> and with the platform on <side>: N (none, for straight-through lines), L, R or B (both)

 - track <station>-<platform> <station>-<platform> <line>: A section of track. Will layer on top of
   anything behind it with an outline effect.
 - subtrack <station>-<platform> <station>-<platform> <line>: Like track, but will not use an outline and so
   will merge with things behind it. For points, generally.

London-specific notes
---------------------

Some of the station codes are made up if we couldn't find a reasonably official source for them;
this map also probably misses out a few points, and has some detail wrong especially at the end
of the Metropolitan line. Contributions are welcome.

License
-------

The code (i.e. every file apart from london.txt) is released under a BSD 3-clause license;
a copy of the text is available at http://www.opensource.org/licenses/BSD-3-Clause.

The london.txt file is made available under CC BY-NC-SA 3.0, whose summary and text is
available here: http://creativecommons.org/licenses/by-nc-sa/3.0/

