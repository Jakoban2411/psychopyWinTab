# -*- coding: utf-8 -*-
"""
Wintab util objects / functions for stylus, position traces.
"""

import math

from psychopy import visual
from psychopy.visual.basevisual import MinimalStim

class WintabBrush(MinimalStim):
    
    def __init__(self,
                 win,
                 lineWidth=2,
                 lineColor=(0.0, 0.0, 0.0),
                 lineColorSpace='rgb',
                 opacity=1.0,
                 closeShape=False,
                 buttonRequired=True,
                 name=None,
                 depth=-10000,
                 traceDepth=-1000,
                 autoLog=False,
                 autoDraw=False,
                 min_opacity=0.0, hover_color=(0, 0, 255),
                 touching_color=(0, 255, 0), tiltline_color=(255, 255, 0),
                 tiltline_width=1,
                 min_size=0.033, size_range=0.033, tiltline_scalar=1.0,
                 colorSpace='rgb255',
                 maxlen=256
                 ):

        super(WintabBrush, self).__init__(name=name,
                                    autoLog=False)

        self.win = win
        self.name = name
        self.depth = depth
        self.traceDepth = traceDepth
        self.lineColor = lineColor
        self.lineColorSpace = lineColorSpace
        self.lineWidth = lineWidth
        self.opacity = opacity
        self.closeShape = closeShape
        self.buttonRequired = buttonRequired
        self.shapes = []

        self.autoLog = autoLog
        self.autoDraw = autoDraw
        self.penPos = PenPositionStim(win, min_opacity, hover_color, 
                                      touching_color, tiltline_color, 
                                      tiltline_width, min_size, size_range, 
                                      tiltline_scalar, name, autoLog, depth, 
                                      colorSpace)
        self.penTrace = PenTracesStim(win, lineWidth, lineColor, 
                                               opacity, maxlen, name, autoLog, 
                                               traceDepth)
        if self.autoLog:
            logging.exp("Created {name} = {obj}".format(name=self.name,
                                                        obj=str(self)))
            
    def updateFromEvents(self,wtab_events):
        self.penPos.updateFromEvent(wtab_events)
        self.penTrace.updateFromEvents(wtab_events)

    def draw(self):
        self.penPos.draw()
        self.penTrace.draw()

    def reset(self):
        self.penPos.clear()
        self.penTrace.clear()

            
class PenPositionStim(MinimalStim):
    """Draws the current pen x,y position with graphics that represent the
    pressure, z axis, and tilt data for the wintab sample used."""

    def __init__(self, win, min_opacity=0.0, hover_color=(0, 0, 255),
                touching_color=(0, 255, 0), tiltline_color=(255, 255, 0),
                tiltline_width=1,
                min_size=0.033, size_range=0.033, tiltline_scalar=1.0,
                name=None, autoLog=False, depth=-10000, colorSpace='rgb255'):
        self.win = win
        self.depth = depth
        super(PenPositionStim, self).__init__(name, autoLog)

        # Pen Hovering Related

        # Opaticy is changed based on pen's z axis if data for z axis
        # is available. Opacity of min_opacity is used when pen is at the
        # furthest hover distance (z value) supported by the device.
        # Opacity of 1.0 is used when z value == 0, meaning pen is touching
        # digitizer surface.
        self.min_opacity = min_opacity
        # If z axis is supported, hover_color specifies the color of the pen
        # position dot when z val > 0.
        self.hover_color = hover_color

        # Pen Pressure Related

        # Smallest radius (in norm units) that the pen position gaussian blob
        # will have, which occurs when pen pressure value is 0
        self.min_size = min_size
        # As pen pressure value increases, so does position gaussian blob
        # radius (in norm units). Max radius is reached when pressure is
        # at max device pressure value, and is equal to min_size+size_range
        self.size_range = size_range
        # Color of pen position blob when pressure > 0.
        self.touching_color = touching_color

        # Pen tilt Related

        # Color of line graphic used to represent the pens tilt relative to
        # the digitizer surface.
        self.tiltline_color = tiltline_color
        self.tiltline_width = tiltline_width
        self.tiltline_scalar = tiltline_scalar
        # Create a Gaussian blob stim to use for pen position graphic
        self.pen_guass = visual.GratingStim(win, units='norm', tex='none',
                                        mask='gauss', pos=(0, 0),
                                        colorSpace='rgb255',
                                        size=(self.min_size, self.min_size),
                                        color=self.hover_color,
                                        autoLog=False,
                                        opacity=0.0)

        # Create a line stim to use for pen position graphic
        self.pen_tilt_line = visual.Line(win, units='norm', start=[0, 0],
                                        lineWidth=self.tiltline_width,
                                        end=[0, 0],
                                        colorSpace='rgb255',
                                        lineColor=self.tiltline_color,
                                        autoLog=False,
                                        opacity=0.0)
        # self.pen_tilt_line.opacity=0.0

    def updateFromEvent(self, evt):
        """Update the pen position and tilt graphics based on the data from
        a wintab sample event.

        :param evt: iohub wintab sample event
        :return:
        """
        last_evt = evt[-1]
        # update the pen position stim based on
        # the last tablet event's data
        if last_evt.pressure > 0:
            # pen is touching tablet surface
            self.pen_guass.color = self.touching_color
        else:
            # pen is hovering just above tablet surface
            self.pen_guass.color = self.hover_color

        if last_evt.device.axis['pressure']['supported']:
            # change size of pen position blob based on samples pressure
            # value
            pnorm = last_evt.pressure / last_evt.device.axis['pressure']['range']
            self.pen_guass.size = self.min_size + pnorm * self.size_range

        # set the position of the gauss blob to be the pen x,y value converted
        # to norm screen coords.
        self.pen_guass.pos = last_evt.getNormPos()

        # if supported, update all graphics opacity based on the samples z value
        # otherwise opacity is always 1.0
        if last_evt.device.axis['z']['supported']:
            z = last_evt.device.axis['z']['range'] - last_evt.z
            znorm = z / last_evt.device.axis['z']['range']
            sopacity = self.min_opacity + znorm * (1.0 - self.min_opacity)
            self.pen_guass.opacity = self.pen_tilt_line.opacity = sopacity
        else:
            self.pen_guass.opacity = self.pen_tilt_line.opacity = 1.0

        # Change the tilt line start position to == pen position
        self.pen_tilt_line.start = self.pen_guass.pos

        # Change the tilt line end position based on samples tilt value
        # If tilt is not supported, it will always return 0,0
        # so no line is drawn.
        t1, t2 = last_evt.tilt
        pen_tilt_xy = 0, 0
        if t1 != t2 != 0:
            pen_tilt_xy = t1 * math.sin(t2), t1 * math.cos(t2)

        pen_pos = self.pen_guass.pos
        tiltend = (pen_pos[0] + pen_tilt_xy[0] * self.tiltline_scalar,
                pen_pos[1] + pen_tilt_xy[1] * self.tiltline_scalar)
        self.pen_tilt_line.end = tiltend

    def draw(self):
        """Draw the PenPositionStim to the opengl back buffer. This needs
        to be called prior to calling win.flip() for the stim is to be
        displayed.

        :return: None

        """
        self.pen_guass.draw()
        self.pen_tilt_line.draw()

    def clear(self):
        """Hide the graphics on the screen, even if they are drawn, by
        setting opacity to 0.

        :return: None

        """
        self.pen_guass.opacity = 0.0
        self.pen_tilt_line.opacity = 0.0

    def __del__(self):
        self.win = None


class PenTracesStim(MinimalStim):
    """Graphics representing where the pen has been moved on the digitizer
    surface. Positions where sample pressure > 0 are included.

    Implemented as a list of visual.ShapeStim, each representing a
    single pen trace/segment (series on pen samples with pressure >
    0). For improved performance, a single pen trace can have
    max_trace_len points before a new ShapeStim is created and made
    the 'current' pen trace'.
    """

    def __init__(self, win, lineWidth=2, lineColor=(0, 0, 0), opacity=1.0,
                maxlen=256, name=None, autoLog=False, depth=-1000):
        self.depth = depth
        self.win = win
        super(PenTracesStim, self).__init__(name, autoLog)
        # A single pen trace can have at most max_trace_len points.
        self.max_trace_len = maxlen
        # The list of ShapeStim representing pen traces
        self.pentracestim = []
        # The ShapeStim state new / upcoming position points will be added to.
        self.current_pentrace = None
        # A list representation of the current_pentrace.vertices
        self.current_points = []
        # The last pen position added to a pen trace.
        self.last_pos = [0, 0]
        self.autoLog = autoLog

        self.lineWidth = lineWidth
        self.lineColor = lineColor
        self.opacity = opacity

    @property
    def traces(self):
        """List of np arrays, each np array is the set of vertices for one
        pen trace.

        :return: list

        """
        return [pts.vertices for pts in self.pentracestim]

    def updateFromEvents(self, sample_events):
        """
        Update the stim graphics based on 0 - n pen sample events.
        :param sample_events:
        :return: None
        """
        for pevt in sample_events:
            if 'FIRST_ENTER' in pevt.status:
                self.end()
            if pevt.pressure > 0:
                lpx, lpy = self.last_pos
                px, py = pevt.getPixPos(self.win)
                if lpx != px or lpy != py:
                    if len(self.current_points) >= self.max_trace_len:
                        self.end()
                        self.append((lpx, lpy))
                    self.last_pos = (px, py)
                    self.append(self.last_pos)
            else:
                self.end()

    def draw(self):
        """Draws each pen trace ShapeStim to the opengl back buffer. This
        method must be called prior to calling win.flip() if it is to
        appear on the screen.

        :return: None
        """
        for pts in self.pentracestim:
            pts.draw()

    def start(self, first_point):
        """Start a new pen trace, by creating a new ShapeStim, adding it to
        the pentracestim list, and making it the current_pentrace.

        :param first_point: the first point in the ShapStim being created.
        :return: None
        """
        self.end()
        self.current_points.append(first_point)
        self.current_pentrace = visual.ShapeStim(self.win,
                                                units='pix',
                                                lineWidth=self.lineWidth,
                                                color=self.lineColor,
                                                lineColorSpace='rgb255',
                                                vertices=self.current_points,
                                                closeShape=False,
                                                pos=(0, 0),
                                                size=1,
                                                ori=0.0,
                                                opacity=self.opacity,
                                                autoLog=self.autoLog,
                                                interpolate=True)
        self.pentracestim.append(self.current_pentrace)

    def end(self):
        """Stop using the current_pentrace ShapeStim. Next time a pen
        sample position is added to the PenTracesStim instance, a new
        ShapeStim will created and added to the pentracestim list.

        :return: None
        """
        self.current_pentrace = None
        self.current_points = []
        self.last_pos = [0, 0]

    def append(self, pos):
        """Add a pen position (in pix coords) to the current_pentrace
        ShapeStim vertices.

        :param pos: (x,y) tuple
        :return: None
        """
        if self.current_pentrace is None:
            self.start(pos)
        else:
            self.current_points.append(pos)
            self.current_pentrace.vertices = self.current_points

    def clear(self):
        """Remove all ShapStim being used. Next time this stim is drawn, no
        pen traces will exist.

        :return:
        """
        self.end()
        del self.pentracestim[:]

    def __del__(self):
        self.clear()
        self.win = None
