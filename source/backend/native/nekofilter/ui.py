#!/usr/bin/env python
#
# Copyright (C) 2008,2009 Nedko Arnaudov <nedko@arnaudov.name>
# Copyright (C) 2006 Leonard Ritter <contact@leonard-ritter.com>
# Filter response code by Fons Adriaensen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.

import sys
import os
import fcntl
import gtk
import gobject
import cairo
from math import pi, sin, cos, atan2, log, sqrt, hypot, log10
from colorsys import hls_to_rgb, rgb_to_hls

def map_coords_linear(x,y):
    return x,1.0-y

def map_coords_spheric(x,y):
    nx = cos(x * 2 * pi) * y
    ny = -sin(x * 2 * pi) * y
    return nx, ny

def get_peaks(f, tolerance=0.01, maxd=0.01, mapfunc=map_coords_linear):
    corners = 360
    yc = 1.0/corners
    peaks = []
    x0,y0 = 0.0,0.0
    t0 = -9999.0
    i0 = 0
    for i in xrange(int(corners)):
        p = i*yc
        a = f(p)
        x,y = mapfunc(p, a)
        if i == 0:
            x0,y0 = x,y
        t = atan2((y0 - y), (x0 - x)) / (2*pi)
        td = t - t0
        if (abs(td) >= tolerance):
            t0 = t
            peaks.append((x,y))
        x0,y0 = x,y
    return peaks

def make_knobshape(gaps, gapdepth):
    def knobshape_func(x):
        x = (x*gaps)%1.0
        w = 0.5
        g1 = 0.5 - w*0.5
        g2 = 0.5 + w*0.5
        if (x >= g1) and (x < 0.5):
            x = (x-g1)/(w*0.5)
            return 0.5 - gapdepth * x * 0.9
        elif (x >= 0.5) and (x < g2):
            x = (x-0.5)/(w*0.5)
            return 0.5 - gapdepth * (1-x) * 0.9
        else:
            return 0.5
    return get_peaks(knobshape_func, 0.03, 0.05, map_coords_spheric)

def hls_to_color(h,l,s):
    r,g,b = hls_to_rgb(h,l,s)
    return gtk.gdk.color_parse('#%04X%04X%04X' % (int(r*65535),int(g*65535),int(b*65535)))

def color_to_hls(color):
    string = color.to_string()
    r = int(string[1:5], 16) / 65535.0
    g = int(string[5:9], 16) / 65535.0
    b = int(string[9:13], 16) / 65535.0
    return rgb_to_hls(r, g, b)

MARKER_NONE = ''
MARKER_LINE = 'line'
MARKER_ARROW = 'arrow'
MARKER_DOT = 'dot'

LEGEND_NONE = ''
LEGEND_DOTS = 'dots' # painted dots
LEGEND_LINES = 'lines' # painted ray-like lines
LEGEND_RULER = 'ruler' # painted ray-like lines + a circular one
LEGEND_RULER_INWARDS = 'ruler-inwards' # same as ruler, but the circle is on the outside
LEGEND_LED_SCALE = 'led-scale' # an LCD scale
LEGEND_LED_DOTS = 'led-dots' # leds around the knob

class KnobTooltip:
    def __init__(self):
        self.tooltip_window = gtk.Window(gtk.WINDOW_POPUP)
        self.tooltip = gtk.Label()
        #self.tooltip.modify_fg(gtk.STATE_NORMAL, hls_to_color(0.0, 1.0, 0.0))
        self.tooltip_timeout = None
        vbox = gtk.VBox()
        vbox2 = gtk.VBox()
        vbox2.add(self.tooltip)
        vbox2.set_border_width(2)
        vbox.add(vbox2)
        self.tooltip_window.add(vbox)
        vbox.connect('expose-event', self.on_tooltip_expose)

    def show_tooltip(self, knob):
        text = knob.format_value()
        rc = knob.get_allocation()
        x,y = knob.window.get_origin()
        self.tooltip_window.show_all()
        w,h = self.tooltip_window.get_size()
        wx,wy = x+rc.x-w, y+rc.y+rc.height/2-h/2
        self.tooltip_window.move(wx,wy)
        rc = self.tooltip_window.get_allocation()
        self.tooltip_window.window.invalidate_rect((0,0,rc.width,rc.height), False)
        self.tooltip.set_text(text)
        if self.tooltip_timeout:
            gobject.source_remove(self.tooltip_timeout)
        self.tooltip_timeout = gobject.timeout_add(500, self.hide_tooltip)

    def hide_tooltip(self):
        self.tooltip_window.hide_all()

    def on_tooltip_expose(self, widget, event):
        ctx = widget.window.cairo_create()
        rc = widget.get_allocation()
        #ctx.set_source_rgb(*hls_to_rgb(0.0, 0.0, 0.5))
        #ctx.paint()
        ctx.set_source_rgb(*hls_to_rgb(0.0, 0.0, 0.5))
        ctx.translate(0.5, 0.5)
        ctx.set_line_width(1)
        ctx.rectangle(rc.x, rc.y,rc.width-1,rc.height-1)
        ctx.stroke()
        return False



knob_tooltip = None
def get_knob_tooltip():
    global knob_tooltip
    if not knob_tooltip:
        knob_tooltip = KnobTooltip()
    return knob_tooltip

class SmartAdjustment(gtk.Adjustment):
    def __init__(self, log=False, value=0, lower=0, upper=0, step_incr=0, page_incr=0, page_size=0):
        self.log = log
        gtk.Adjustment.__init__(self, value, lower, upper, step_incr, page_incr, page_size)
        self.normalized_value = self.real2norm(self.value)

    def real2norm(self, value):
        if self.log:
            return log(value / self.lower, self.upper / self.lower)
        else:
            return (value - self.lower) / (self.upper - self.lower)

    def norm2real(self, value):
        if self.log:
            return self.lower * pow(self.upper / self.lower, value)
        else:
            return value * (self.upper - self.lower) + self.lower

    def set_value(self, value):
        self.normalized_value = self.real2norm(value)
        gtk.Adjustment.set_value(self, value)

    def get_normalized_value(self):
        return self.normalized_value

    def set_normalized_value(self, value):
        self.normalized_value = value

        if self.normalized_value < 0.0:
            self.normalized_value = 0.0
        elif self.normalized_value > 1.0:
            self.normalized_value = 1.0

        self.set_value(self.norm2real(self.normalized_value))

class Knob(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.gapdepth = 4
        self.gaps = 10
        self.value = 0.0
        self.min_value = 0.0
        self.max_value = 127.0
        self.fg_hls = 0.0, 0.7, 0.0
        self.legend_hls = None
        self.dragging = False
        self.start = 0.0
        self.digits = 2
        self.segments = 13
        self.label = ''
        self.marker = MARKER_LINE
        self.angle = (3.0/4.0) * 2 * pi
        self.knobshape = None
        self.legend = LEGEND_DOTS
        self.lsize = 2
        self.lscale = False
        self.set_double_buffered(True)
        self.connect('realize', self.on_realize)
        self.connect("size_allocate", self.on_size_allocate)
        self.connect('expose-event', self.on_expose)
        self.set_border_width(6)
        self.set_size_request(50, 50)
        self.tooltip_enabled = False
        self.adj = None

    def set_adjustment(self, adj):
        self.min_value = 0.0
        self.max_value = 1.0
        self.value = adj.get_normalized_value()
        if self.adj:
            self.adj.disconnect(self.adj_id)
        self.adj = adj
        self.adj_id = adj.connect("value-changed", self.on_adj_value_changed)

    def is_sensitive(self):
        return self.get_property("sensitive")

    def format_value(self):
        if self.adj:
            value = self.adj.value
        else:
            value = self.value
        return ("%%.%if" % self.digits) % value

    def show_tooltip(self):
        if self.tooltip_enabled:
            get_knob_tooltip().show_tooltip(self)

    def on_realize(self, widget):
        self.root = self.get_toplevel()
        self.root.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.root.connect('scroll-event', self.on_mousewheel)
        self.root.connect('button-press-event', self.on_left_down)
        self.root.connect('button-release-event', self.on_left_up)
        self.root.connect('motion-notify-event', self.on_motion)
        self.update_knobshape()

    def update_knobshape(self):
        rc = self.get_allocation()
        b = self.get_border_width()
        size = min(rc.width, rc.height) - 2*b
        gd = float(self.gapdepth*0.5) / size
        self.gd = gd
        self.knobshape = make_knobshape(self.gaps, gd)

    def set_legend_scale(self, scale):
        self.lscale = scale
        self.refresh()

    def set_legend_line_width(self, width):
        self.lsize = width
        self.refresh()

    def set_segments(self, segments):
        self.segments = segments
        self.refresh()

    def set_marker(self, marker):
        self.marker = marker
        self.refresh()

    def set_range(self, minvalue, maxvalue):
        self.min_value = minvalue
        self.max_value = maxvalue
        self.set_value(self.value)

    def quantize_value(self, value):
        scaler = 10**self.digits
        value = int((value*scaler)+0.5) / float(scaler)
        return value

    def on_adj_value_changed(self, adj):
        new_value = adj.get_normalized_value()
        if self.value != new_value:
            self.value = new_value
            self.refresh()

    def set_value(self, value):
        oldval = self.value
        self.value = min(max(self.quantize_value(value), self.min_value), self.max_value)
        if self.value != oldval:
            if self.adj:
                self.adj.set_normalized_value(value)
            self.refresh()

    def get_value(self):
        return self.value

    def set_top_color(self, h, l, s):
        self.fg_hls = h,l,s
        self.refresh()

    def set_legend_color(self, h, l, s):
        self.legend_hls = h,l,s
        self.refresh()

    def get_top_color(self):
        return self.fg_hls

    def set_gaps(self, gaps):
        self.gaps = gaps
        self.knobshape = None
        self.refresh()

    def get_gaps(self):
        return self.gaps

    def set_gap_depth(self, gapdepth):
        self.gapdepth = gapdepth
        self.knobshape = None
        self.refresh()

    def get_gap_depth(self):
        return self.gapdepth

    def set_angle(self, angle):
        self.angle = angle
        self.refresh()

    def get_angle(self):
        return self.angle

    def set_legend(self, legend):
        self.legend = legend
        self.refresh()

    def get_legend(self):
        return self.legend

    def on_left_down(self, widget, event):
        #print "on_left_down"

        # dont drag insensitive widgets
        if not self.is_sensitive():
            return False

        if not sum(self.get_allocation().intersect((int(event.x), int(event.y), 1, 1))):
            return False
        if event.button == 1:
            #print "start draggin"
            self.startvalue = self.value
            self.start = event.y
            self.dragging = True
            self.show_tooltip()
            self.grab_add()
            return True
        return False

    def on_left_up(self, widget, event):
        #print "on_left_up"
        if not self.dragging:
            return False
        if event.button == 1:
            #print "stop draggin"
            self.dragging = False
            self.grab_remove()
            return True
        return False

    def on_motion(self, widget, event):
        #print "on_motion"

        # dont drag insensitive widgets
        if not self.is_sensitive():
            return False

        if self.dragging:
            x,y,state = self.window.get_pointer()
            rc = self.get_allocation()
            range = self.max_value - self.min_value
            scale = rc.height
            if event.state & gtk.gdk.SHIFT_MASK:
                scale = rc.height*8
            value = self.startvalue - ((y - self.start)*range)/scale
            oldval = self.value
            self.set_value(value)
            self.show_tooltip()
            if oldval != self.value:
                self.start = y
                self.startvalue = self.value
            return True
        return False

    def on_mousewheel(self, widget, event):

        # dont move insensitive widgets
        if not self.is_sensitive():
            return False

        if not sum(self.get_allocation().intersect((int(event.x), int(event.y), 1, 1))):
            return
        range = self.max_value - self.min_value
        minstep = 1.0 / (10**self.digits)
        if event.state & (gtk.gdk.SHIFT_MASK | gtk.gdk.BUTTON1_MASK):
            step = minstep
        else:
            step = max(self.quantize_value(range/25.0), minstep)
        value = self.value
        if event.direction == gtk.gdk.SCROLL_UP:
            value += step
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            value -= step
        self.set_value(value)
        self.show_tooltip()

    def on_size_allocate(self, widget, allocation):
        #print allocation.x, allocation.y, allocation.width, allocation.height
        self.update_knobshape()

    def draw_points(self, ctx, peaks):
        ctx.move_to(*peaks[0])
        for peak in peaks[1:]:
            ctx.line_to(*peak)

    def draw(self, ctx):
        if not self.legend_hls:
            self.legend_hls = color_to_hls(self.style.fg[gtk.STATE_NORMAL])

        if not self.knobshape:
            self.update_knobshape()
        startangle = pi*1.5 - self.angle*0.5
        angle = ((self.value - self.min_value) / (self.max_value - self.min_value)) * self.angle + startangle
        rc = self.get_allocation()
        size = min(rc.width, rc.height)

        kh = self.get_border_width() # knob height

        ps = 1.0/size # pixel size
        ps2 = 1.0 / (size-(2*kh)-1) # pixel size inside knob
        ss = ps * kh # shadow size
        lsize = ps2 * self.lsize # legend line width
        # draw spherical
        ctx.translate(rc.x, rc.y)
        ctx.translate(0.5,0.5)
        ctx.translate(size*0.5, size*0.5)
        ctx.scale(size-(2*kh)-1, size-(2*kh)-1)
        if self.legend == LEGEND_DOTS:
            ctx.save()
            ctx.set_source_rgb(*hls_to_rgb(*self.legend_hls))
            dots = self.segments
            for i in xrange(dots):
                s = float(i)/(dots-1)
                a = startangle + self.angle*s
                ctx.save()
                ctx.rotate(a)
                r = lsize*0.5
                if self.lscale:
                    r = max(r*s,ps2)
                ctx.arc(0.5+lsize, 0.0, r, 0.0, 2*pi)
                ctx.fill()
                ctx.restore()
            ctx.restore()
        elif self.legend in (LEGEND_LINES, LEGEND_RULER, LEGEND_RULER_INWARDS):
            ctx.save()
            ctx.set_source_rgb(*hls_to_rgb(*self.legend_hls))
            dots = self.segments
            n = ps2*(kh-1)
            for i in xrange(dots):
                s = float(i)/(dots-1)
                a = startangle + self.angle*s
                ctx.save()
                ctx.rotate(a)
                r = n*0.9
                if self.lscale:
                    r = max(r*s,ps2)
                ctx.move_to(0.5+ps2+n*0.1, 0.0)
                ctx.line_to(0.5+ps2+n*0.1+r, 0.0)
                ctx.set_line_width(lsize)
                ctx.stroke()
                ctx.restore()
            ctx.restore()
            if self.legend == LEGEND_RULER:
                ctx.save()
                ctx.set_source_rgb(*hls_to_rgb(*self.legend_hls))
                ctx.set_line_width(lsize)
                ctx.arc(0.0, 0.0, 0.5+ps2+n*0.1, startangle, startangle+self.angle)
                ctx.stroke()
                ctx.restore()
            elif self.legend == LEGEND_RULER_INWARDS:
                ctx.save()
                ctx.set_source_rgb(*hls_to_rgb(*self.legend_hls))
                ctx.set_line_width(lsize)
                ctx.arc(0.0, 0.0, 0.5+ps2+n, startangle, startangle+self.angle)
                ctx.stroke()

        # draw shadow only for sensitive widgets that have height
        if self.is_sensitive() and kh:
            ctx.save()
            ctx.translate(ss, ss)
            ctx.rotate(angle)
            self.draw_points(ctx, self.knobshape)
            ctx.close_path()
            ctx.restore()
            ctx.set_source_rgba(0,0,0,0.3)
            ctx.fill()

        if self.legend in (LEGEND_LED_SCALE, LEGEND_LED_DOTS):
            ch,cl,cs = self.legend_hls
            n = ps2*(kh-1)
            ctx.save()
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_source_rgb(*hls_to_rgb(ch,cl*0.2,cs))
            ctx.set_line_width(lsize)
            ctx.arc(0.0, 0.0, 0.5+ps2+n*0.5, startangle, startangle+self.angle)
            ctx.stroke()
            ctx.set_source_rgb(*hls_to_rgb(ch,cl,cs))
            if self.legend == LEGEND_LED_SCALE:
                ctx.set_line_width(lsize-ps2*2)
                ctx.arc(0.0, 0.0, 0.5+ps2+n*0.5, startangle, angle)
                ctx.stroke()
            elif self.legend == LEGEND_LED_DOTS:
                dots = self.segments
                dsize = lsize-ps2*2
                seg = self.angle/dots
                endangle = startangle + self.angle
                for i in xrange(dots):
                    s = float(i)/(dots-1)
                    a = startangle + self.angle*s
                    if ((a-seg*0.5) > angle) or (angle == startangle):
                        break
                    ctx.save()
                    ctx.rotate(a)
                    r = dsize*0.5
                    if self.lscale:
                        r = max(r*s,ps2)
                    ctx.arc(0.5+ps2+n*0.5, 0.0, r, 0.0, 2*pi)
                    ctx.fill()
                    ctx.restore()
            ctx.restore()
        pat = cairo.LinearGradient(-0.5, -0.5, 0.5, 0.5)
        pat.add_color_stop_rgb(1.0, 0.2,0.2,0.2)
        pat.add_color_stop_rgb(0.0, 0.3,0.3,0.3)
        ctx.set_source(pat)
        ctx.rotate(angle)
        self.draw_points(ctx, self.knobshape)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgba(0.1,0.1,0.1,1)
        ctx.save()
        ctx.identity_matrix()
        ctx.set_line_width(1.0)
        ctx.stroke()
        ctx.restore()

        ctx.arc(0.0, 0.0, 0.5-self.gd, 0.0, pi*2.0)
        ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], max(self.fg_hls[1]*0.4,0.0), self.fg_hls[2]))
        ctx.fill()
        ctx.arc(0.0, 0.0, 0.5-self.gd-ps, 0.0, pi*2.0)
        ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], min(self.fg_hls[1]*1.2,1.0), self.fg_hls[2]))
        ctx.fill()
        ctx.arc(0.0, 0.0, 0.5-self.gd-(2*ps), 0.0, pi*2.0)
        ctx.set_source_rgb(*hls_to_rgb(*self.fg_hls))
        ctx.fill()

        # dont draw cap for insensitive widgets
        if not self.is_sensitive():
            return

        #~ ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        #~ ctx.move_to(0.5-0.3-self.gd-ps, 0.0)
        #~ ctx.line_to(0.5-self.gd-ps*5, 0.0)

        if self.marker == MARKER_LINE:
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            ctx.move_to(0.5-0.3-self.gd-ps, 0.0)
            ctx.line_to(0.5-self.gd-ps, 0.0)
            ctx.save()
            ctx.identity_matrix()
            ctx.translate(0.5,0.5)
            ctx.set_line_width(5)
            ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], min(self.fg_hls[1]*1.2,1.0), self.fg_hls[2]))
            ctx.stroke_preserve()
            ctx.set_line_width(3)
            ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], max(self.fg_hls[1]*0.4,0.0), self.fg_hls[2]))
            ctx.stroke()
            ctx.restore()
        elif self.marker == MARKER_DOT:
            ctx.arc(0.5-0.05-self.gd-ps*5, 0.0, 0.05, 0.0, 2*pi)
            ctx.save()
            ctx.identity_matrix()
            ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], min(self.fg_hls[1]*1.2,1.0), self.fg_hls[2]))
            ctx.stroke_preserve()
            ctx.set_line_width(1)
            ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], max(self.fg_hls[1]*0.4,0.0), self.fg_hls[2]))
            ctx.fill()
            ctx.restore()
        elif self.marker == MARKER_ARROW:
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            ctx.move_to(0.5-0.3-self.gd-ps, 0.1)
            ctx.line_to(0.5-0.1-self.gd-ps, 0.0)
            ctx.line_to(0.5-0.3-self.gd-ps, -0.1)
            ctx.close_path()
            ctx.save()
            ctx.identity_matrix()
            #~ ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], min(self.fg_hls[1]*1.2,1.0), self.fg_hls[2]))
            #~ ctx.stroke_preserve()
            ctx.set_line_width(1)
            ctx.set_source_rgb(*hls_to_rgb(self.fg_hls[0], max(self.fg_hls[1]*0.4,0.0), self.fg_hls[2]))
            ctx.fill()
            ctx.restore()

    def refresh(self):
        rect = self.get_allocation()
        if self.window:
            self.window.invalidate_rect(rect, False)
        return True

    def on_expose(self, widget, event):
        self.context = self.window.cairo_create()
        self.draw(self.context)
        return False

class filter_band:
    def __init__(self, sample_rate):
        self.fsamp = sample_rate

    def set_params(self, freq, bandw, gain):
        freq_ratio = freq / self.fsamp
        gain2 = pow(10.0, 0.05 * gain)
        b = 7 * bandw * freq_ratio / sqrt(gain2)
        self.gn = 0.5 * (gain2 - 1)
        self.v1 = -cos(2 * pi * freq_ratio)
        self.v2 = (1 - b) / (1 + b)
        self.v1 *= (1 + self.v2)
        self.gn *= (1 - self.v2)

    def get_response(self, freq):
        w = 2 * pi * (freq / self.fsamp)
        c1 = cos(w)
        s1 = sin(w)
        c2 = cos(2 * w)
        s2 = sin(2 * w)

        x = c2 + self.v1 * c1 + self.v2
        y = s2 + self.v1 * s1
        t1 = hypot(x, y)
        x += self.gn * (c2 - 1)
        y += self.gn * s2
        t2 = hypot(x, y)

        #return t2 / t1
        return 20 * log10(t2 / t1)

class frequency_response(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)

        self.connect("expose-event", self.on_expose)
        self.connect("size-request", self.on_size_request)
        self.connect("size_allocate", self.on_size_allocate)

        self.color_bg = gtk.gdk.Color(0,0,0)
        self.color_value = gtk.gdk.Color(int(65535 * 0.8), int(65535 * 0.7), 0)
        self.color_mark = gtk.gdk.Color(int(65535 * 0.3), int(65535 * 0.3), int(65535 * 0.3))
        self.color_sum = gtk.gdk.Color(int(65535 * 1.0), int(65535 * 1.0), int(65535 * 1.0))
        self.width = 0
        self.height = 0
        self.margin = 10
        self.db_range = 30
        self.master_gain = 0.0
        self.master_enabled = False

        self.filters = {}

    def on_expose(self, widget, event):
        cairo_ctx = widget.window.cairo_create()

        # set a clip region for the expose event
        cairo_ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        cairo_ctx.clip()

        self.draw(cairo_ctx)

        return False

    def on_size_allocate(self, widget, allocation):
        #print allocation.x, allocation.y, allocation.width, allocation.height
        self.width = float(allocation.width)
        self.height = float(allocation.height)
        self.font_size = 10

    def on_size_request(self, widget, requisition):
        #print "size-request, %u x %u" % (requisition.width, requisition.height)
        requisition.width = 150
        requisition.height = 150
        return

    def invalidate_all(self):
        self.queue_draw_area(0, 0, int(self.width), int(self.height))

    def get_x(self, hz):
        width = self.width - 3.5 * self.margin
        #x = self.margin + width * (hz - 20) / (20000 - 20)
        x = 2.5 * self.margin + width * log(hz / 20.0, 1000.0)
        #print x
        return x

    def get_freq(self, x):
        width = self.width - 3.5 * self.margin
        return 20 * pow(1000, (x - 2.5 * self.margin) / width)

    def get_y(self, db):
        height = self.height - 2.5 * self.margin
        y = self.margin + height * (self.db_range - db) / (self.db_range * 2)
        #print y
        return y

    def draw_db_grid(self, cairo_ctx, db):
        x = self.get_x(20)
        y = self.get_y(db)
        cairo_ctx.move_to(x, y)
        cairo_ctx.line_to(self.get_x(20000), y)

        if db % 10 == 0:
            x -= 20
            y += 3
            cairo_ctx.move_to(x, y)
            label = "%+d" % db
            if db == 0:
                label = " " + label
            cairo_ctx.show_text(label)

        cairo_ctx.stroke()

    def invalidate_all(self):
        self.queue_draw_area(0, 0, int(self.width), int(self.height))

    def draw(self, cairo_ctx):
        cairo_ctx.select_font_face("Fixed")

        cairo_ctx.set_source_color(self.color_bg)
        cairo_ctx.rectangle(0, 0, self.width, self.height)
        cairo_ctx.fill()

        cairo_ctx.set_source_color(self.color_mark)
        cairo_ctx.set_line_width(1);

        for hz in range(20, 101, 10) + range(100, 1001, 100) + range(1000, 10001, 1000) + range(10000, 20001, 10000):
            if hz >= 10000:
                label = "%dk" % int(hz / 1000)
            elif hz >= 1000:
                label = "%dk" % int(hz / 1000)
            else:
                label = "%d" % int(hz)
            first_digit = int(label[0])
            if first_digit > 5 or (first_digit > 3 and (len(label) == 3)):
                label = None

            x = self.get_x(hz)
            cairo_ctx.move_to(x, self.get_y(self.db_range))
            y = self.get_y(-self.db_range)
            cairo_ctx.line_to(x, y)
            if label:
                y += 10
                if hz == 20000:
                    x -= 15
                elif hz != 20:
                    x -= 3
                cairo_ctx.move_to(x, y)
                cairo_ctx.show_text(label)
            cairo_ctx.stroke()

        for db in range(0, self.db_range + 1, 5):
            self.draw_db_grid(cairo_ctx, db)

            if db != 0:
                self.draw_db_grid(cairo_ctx, -db)

        curves = [[x, {}, self.master_gain, self.get_freq(x)] for x in range(int(self.get_x(20)), int(self.get_x(20e3)))]
        #print repr(curves)

        # calculate filter responses
        for label, filter in self.filters.items():
            if not filter.enabled:
                continue

            for point in curves:
                db = filter.get_response(point[3])
                point[1][label] = [self.get_y(db), db]

        # calculate sum curve
        for point in curves:
            for label, filter_point in point[1].items():
                point[2] += filter_point[1]
            #print point

        # draw filter curves
        for label, filter in self.filters.items():
            if not filter.enabled:
                continue

            cairo_ctx.set_source_color(filter.color)
            cairo_ctx.move_to(curves[0][0], curves[0][1][label][0])
            for point in curves:
                cairo_ctx.line_to(point[0], point[1][label][0])
            cairo_ctx.stroke()

        if self.master_enabled:
            # draw sum curve
            cairo_ctx.set_source_color(self.color_sum)
            cairo_ctx.set_line_width(2);
            cairo_ctx.move_to(curves[0][0], self.get_y(curves[0][2]))
            for point in curves:
                cairo_ctx.line_to(point[0], self.get_y(point[2]))
            cairo_ctx.stroke()

        # draw base point markers
        for label, filter in self.filters.items():
            if not filter.enabled:
                continue

            cairo_ctx.set_source_color(self.color_value)
            x = self.get_x(filter.adj_hz.value)
            y = self.get_y(filter.adj_db.value)

            cairo_ctx.move_to(x, y)
            cairo_ctx.show_text(label)
            cairo_ctx.stroke()

    def add_filter(self, label, sample_rate, adj_hz, adj_db, adj_bw, color):
        #print "filter %s added (%.2f Hz, %.2f dB, %.2f bw)" % (label, adj_hz.value, adj_db.value, adj_bw.value)
        filter = filter_band(sample_rate)
        filter.enabled = False
        filter.label = label
        filter.color = color
        filter.set_params(adj_hz.value, adj_bw.value, adj_db.value)
        adj_hz.filter = filter
        adj_db.filter = filter
        adj_bw.filter = filter
        filter.adj_hz = adj_hz
        filter.adj_db = adj_db
        filter.adj_bw = adj_bw
        adj_hz.connect("value-changed", self.on_value_change_request)
        adj_db.connect("value-changed", self.on_value_change_request)
        adj_bw.connect("value-changed", self.on_value_change_request)
        self.filters[label] = filter

    def enable_filter(self, label):
        filter = self.filters[label]
        #print "filter %s enabled (%.2f Hz, %.2f dB, %.2f bw)" % (label, filter.adj_hz.value, filter.adj_db.value, filter.adj_bw.value)
        filter.enabled = True
        self.invalidate_all()

    def disable_filter(self, label):
        filter = self.filters[label]
        #print "filter %s disabled (%.2f Hz, %.2f dB, %.2f bw)" % (label, filter.adj_hz.value, filter.adj_db.value, filter.adj_bw.value)
        filter.enabled = False
        self.invalidate_all()

    def on_value_change_request(self, adj):
        #print "adj changed"
        adj.filter.set_params(adj.filter.adj_hz.value, adj.filter.adj_bw.value, adj.filter.adj_db.value)
        self.invalidate_all()

    def master_enable(self):
        self.master_enabled = True;
        self.invalidate_all()

    def master_disable(self):
        self.master_enabled = False;
        self.invalidate_all()

    def set_master_gain(self, gain):
        self.master_gain = gain;
        self.invalidate_all()

class filter_ui:
    def __init__(self, argv):
        self.fake = len(argv) == 1

        if self.fake:
            self.shown = False
            self.sample_rate  = 48e3
        else:
            self.sample_rate  = float(argv[1])
            self.recv_pipe_fd = int(argv[2])
            self.send_pipe_fd = int(argv[3])

            oldflags = fcntl.fcntl(self.recv_pipe_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.recv_pipe_fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

            self.recv_pipe = os.fdopen(self.recv_pipe_fd, 'r')
            self.send_pipe = os.fdopen(self.send_pipe_fd, 'w')

        self.port_base = 0
        #self.lv2logo = gtk.gdk.pixbuf_new_from_file(self.bundle_path + "/lv2logo.png")

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #self.window.set_size_request(600, 400)
        self.window.set_title("NekoFilter (GUI)")
        self.window.set_role("plugin_ui")

        self.top_vbox = gtk.VBox()
        self.top_vbox.set_spacing(10)

        align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        align.set_padding(10, 10, 10, 10)
        align.add(self.top_vbox)

        self.window.add(align)

        self.fr = frequency_response()
        self.fr.set_size_request(400, 200)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        frame.add(self.fr)

        self.top_vbox.pack_start(frame, True, True)

        self.param_hbox = gtk.HBox()
        self.top_vbox.pack_start(self.param_hbox)

        self.param_hbox.set_spacing(10)

        self.initator = False

        self.ports = []

        misc_box = gtk.VBox()
        misc_box.set_spacing(5)

        master_frame = gtk.Frame("Master")
        master_frame.set_label_align(0.5, 0.5)

        master_box = gtk.VBox()
        master_box.set_spacing(5)

        port = {'index': 0, 'name': 'Active', 'type': 'toggle'}
        self.ports.append(port)
        self.add_param_box(master_box, self.create_toggle_box(port))

        port = {'index': 1, 'name': 'Gain', 'type': 'knob', 'min': -20.0, 'max': 20.0, 'unit': 'dB', 'log': False}
        self.ports.append(port)
        self.add_param_box(master_box, self.create_knob_box(port))

        master_frame.add(master_box)
        misc_box.pack_start(master_frame, False, False)

        #logo = gtk.Image()
        #logo.set_from_pixbuf(self.lv2logo)
        #misc_box.pack_start(logo, True, True)

        button_box = gtk.VBox()

        button = gtk.Button(stock=gtk.STOCK_ABOUT)
        button.connect("clicked", self.on_about)
        button_box.pack_start(button)

        button = gtk.Button(stock=gtk.STOCK_CLOSE)
        button.connect("clicked", self.on_window_closed)
        button_box.pack_start(button)

        align = gtk.Alignment(0.5, 1.0, 1.0, 0.0)
        align.add(button_box)
        misc_box.pack_start(align, True, True)

        band_parameters = [
            {'name': 'Active', 'type': 'toggle'},
            {'name': 'Frequency', 'type': 'knob', 'unit': 'Hz', 'log': True},
            {'name': 'Bandwidth', 'type': 'knob', 'min': 0.125, 'max': 8.0, 'unit': '', 'log': True},
            {'name': 'Gain', 'type': 'knob', 'min': -20.0, 'max': 20.0, 'unit': 'dB', 'log': False}]

        freq_min = [  20.0,   40.0,   100.0,   200.0]
        freq_max = [2000.0, 4000.0, 10000.0, 20000.0]

        port_index = 2

        filter_colors = [gtk.gdk.Color(int(65535 * 1.0), int(65535 * 0.6), int(65535 * 0.0)),
                         gtk.gdk.Color(int(65535 * 0.6), int(65535 * 1.0), int(65535 * 0.6)),
                         gtk.gdk.Color(int(65535 * 0.0), int(65535 * 0.6), int(65535 * 1.0)),
                         gtk.gdk.Color(int(65535 * 0.9), int(65535 * 0.0), int(65535 * 0.5))]

        for i in [0, 1, 2, 3]:
            band_frame = gtk.Frame("Band %d" % (i + 1))
            band_frame.set_label_align(0.5, 0.5)

            band_box = gtk.VBox()
            band_box.set_spacing(5)

            for parameter in band_parameters:

                port = parameter.copy()
                port['index'] = port_index
                port_index += 1

                if port['name'] == 'Frequency':
                    port['min'] = freq_min[i]
                    port['max'] = freq_max[i]

                self.ports.append(port)

                #param_box.set_spacing(5)
                if port['type'] == 'knob':
                    self.add_param_box(band_box, self.create_knob_box(port))
                elif port['type'] == 'toggle':
                    self.add_param_box(band_box, self.create_toggle_box(port))

            self.fr.add_filter(
                str(i + 1),
                self.sample_rate,
                self.ports[port_index - 3]['adj'], # frequency
                self.ports[port_index - 1]['adj'], # gain
                self.ports[port_index - 2]['adj'], # bandwidth
                filter_colors[i])

            band_frame.add(band_box)

            self.param_hbox.pack_start(band_frame, True, True)

        self.param_hbox.pack_start(misc_box, True, True)

        self.initator = True

    def on_about(self, widget):
        about = gtk.AboutDialog()
        about.set_transient_for(self.window)
        about.set_name("4-band parametric filter")
        #about.set_website(program_data['website'])
        about.set_authors(["Nedko Arnaudov - LV2 plugin and GUI", 'Fons Adriaensen - DSP code'])
        about.set_artists(["LV2 logo has been designed by Thorsten Wilms, based on a concept from Peter Shorthose."])
        #about.set_logo(self.lv2logo)
        about.show()
        about.run()
        about.hide()

    def create_knob_box(self, port):
        param_box = gtk.VBox()
        step = (port['max'] - port['min']) / 100
        adj = SmartAdjustment(port['log'], port['min'], port['min'], port['max'], step, step * 20)
        adj.port = port
        port['adj'] = adj

        adj.connect("value-changed", self.on_adj_value_changed)

        knob = Knob()
        knob.set_adjustment(adj)
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.set_padding(0, 0, 20, 20)
        align.add(knob)
        param_box.pack_start(align, False)

        adj.label = gtk.Label(self.get_adj_value_text(adj)[0])
        param_box.pack_start(adj.label, False)
        #spin = gtk.SpinButton(adj, 0.0, 2)
        #param_box.pack_start(spin, False)

        label = gtk.Label(port['name'])
        param_box.pack_start(label, False)
        return param_box

    def create_toggle_box(self, port):
        param_box = gtk.VBox()
        button = gtk.CheckButton(port['name'])
        button.port = port
        port['widget'] = button

        button.connect("toggled", self.on_button_toggled)

        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(button)
        param_box.pack_start(align, False)
        return param_box

    def add_param_box(self, container, param_box):
        align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        align.set_padding(10, 10, 10, 10)
        align.add(param_box)

        container.pack_start(align, True)

    def get_adj_value_text(self, adj):
        value = adj.get_value()
        if value >= 10000:
            format = "%.0f"
        elif value >= 1000:
            format = "%.1f"
        else:
            format = "%.2f"
        text = format % value
        unit = adj.port['unit']
        if unit:
            text += " " + unit

        return value, text

    def on_adj_value_changed(self, adj):
        value, text = self.get_adj_value_text(adj)
        adj.label.set_text(text)

        if adj.port['index'] == 1:
            #print "Master gain = %.2f dB" % adj.get_value()
            self.fr.set_master_gain(adj.get_value())

        if self.initator:
            #print adj.port, adj.get_value()
            self.send_port_value(adj.port['index'] + self.port_base, value)

    def on_button_toggled(self, widget):
        port_index = widget.port['index']
        band_no = (port_index - 2) / 4 + 1
        if widget.get_active():
            value = 1.0
            if band_no > 0:
                self.fr.enable_filter(str(band_no))
            else:
                self.fr.master_enable()
        else:
            value = 0.0
            if band_no > 0:
                self.fr.disable_filter(str(band_no))
            else:
                self.fr.master_disable()

        if self.initator:
            self.send_port_value(port_index + self.port_base, value)

    def send(self, lines):
        if self.fake:
            return

        for line in lines:
            #print 'send: "' + line + '"'
            self.send_pipe.write(line + "\n")
            self.send_pipe.flush()

    def send_close(self):
        self.send(["close"])

    def send_exiting(self):
        self.send(["exiting"])

    def send_port_value(self, port_index, value):
        self.send(["port_value", str(port_index), "%.10f" % value])

    def send_hi(self):
        self.send([""])         # send empty line (just newline char)

    def recv_line(self):
        return self.recv_pipe.readline().strip()

    def recv_command(self):
        try:
            msg = self.recv_line()

            if msg == "port_value":
                port_index = int(self.recv_line())
                port_value = float(self.recv_line())
                #print "port_value_change recevied: %d %f" % (port_index, port_value)
                self.on_port_value_changed(port_index, port_value)
            elif msg == "show":
                self.on_show()
            elif msg == "hide":
                self.on_hide()
            elif msg == "quit":
                self.on_quit()
            else:
                print 'unknown message: "' + msg + '"'

            return True
        except IOError:
            return False

    def on_recv(self, fd, cond):
        #print "on_recv"
        if cond == gobject.IO_HUP:
            gtk.main_quit()
            return False

        while True:
            if not self.recv_command():
                break

        return True

    def run(self):
        self.window.connect("destroy", self.on_window_closed)

        if self.fake:
            if not self.shown:
                self.shown = True
                self.on_show()
        else:
            self.send_hi()
            gobject.io_add_watch(self.recv_pipe_fd, gobject.IO_IN | gobject.IO_HUP, self.on_recv)

        gtk.main()

    def on_port_value_changed(self, port_index, port_value):
        #print "port %d set to %f" % (port_index, port_value)
        port_index -= self.port_base
        port = self.ports[port_index]
        #print repr(port)
        port_type = port['type']
        if port_type == 'knob':
            self.initator = False
            port['adj'].set_value(port_value)
            self.initator = True
        elif port_type == 'toggle':
            if port_value > 0.0:
                toggled = True
            else:
                toggled = False

            self.initator = False
            port['widget'].set_active(toggled)
            self.initator = True

    def on_show(self):
        self.window.show_all()

    def on_hide(self):
        self.window.hide_all()

    def on_quit(self):
        gtk.main_quit()

    def on_window_closed(self, arg):
        self.window.hide_all()
        self.send_close()
        #self.send_exiting()
        #gtk.main_quit()

def main():
    filter_ui(sys.argv).run()
    #print "main done"

if __name__ == '__main__':
    main()