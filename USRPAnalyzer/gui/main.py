#!/usr/bin/env python

# USRPAnalyzer - spectrum sweep functionality for USRP and GNURadio
# Copyright (C) Douglas Anderson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import wx
import logging
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from gui import gain, lotuning, marker, resolution, threshold, trigger, window


class  wxpygui_frame(wx.Frame):
    """The main gui frame."""

    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.init_mpl_canvas()
        self.configure_mpl_plot()

        # Setup a threshold level at None
        self.threshold = threshold.threshold(self, None)

        # Init markers (visible=False)
        self.mkr1 = marker.marker(self, 1, '#00FF00', 'd') # thin green diamond
        self.mkr2 = marker.marker(self, 2, '#00FF00', 'd') # thin green diamond

        # Sizers/Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plot, flag=wx.ALIGN_CENTER)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.gain_ctrls = gain.init_ctrls(self)
        self.threshold_ctrls = threshold.init_ctrls(self)
        self.mkr1_ctrls = marker.init_mkr1_ctrls(self)
        self.mkr2_ctrls = marker.init_mkr2_ctrls(self)
        self.res_ctrls = resolution.init_ctrls(self)
        self.windowfn_ctrls = window.init_ctrls(self)
        self.lo_offset_ctrls = lotuning.init_ctrls(self)
        
        hbox.Add(self.gain_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.threshold_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.mkr1_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.mkr2_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.res_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.windowfn_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.lo_offset_ctrls, flag=wx.ALL, border=10)
        
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.trigger_ctrls = trigger.init_ctrls(self)

        hbox2.Add(self.trigger_ctrls, flag=wx.ALL, border=10)
        
        vbox.Add(hbox, flag=wx.ALIGN_CENTER, border=0)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER, border=0)        
        
        self.SetSizer(vbox)
        self.Fit()

        self.logger = logging.getLogger('USRPAnalyzer.wxpygui_frame')

        # gui event handlers
        self.Bind(wx.EVT_CLOSE, self.close)
        self.Bind(wx.EVT_IDLE, self.idle_notifier)

        self.canvas.mpl_connect('button_press_event', self.on_mousedown)
        self.canvas.mpl_connect('button_release_event', self.on_mouseup)

        # Used to peak search within range
        self.span = None       # the actual matplotlib patch
        self.span_left = None  # left bound x coordinate
        self.span_right = None # right bound x coordinate

        self.paused = False
        self.last_click_evt = None

        self.closed = False

        self.start_t = time.time()

    ####################
    # GUI Initialization
    ####################

    def init_mpl_canvas(self):
        """Initialize a matplotlib plot."""
        self.plot = wx.Panel(self, wx.ID_ANY, size=(800,600))
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.plot, -1, self.figure)

    def configure_mpl_plot(self):
        """Configure or reconfigure the matplotlib plot"""
        if hasattr(self, 'subplot'):
            self.subplot = self.format_ax(self.subplot)
        else:
            self.subplot = self.format_ax(self.figure.add_subplot(111))

        x_points = self.tb.bin_freqs
        # self.line in a numpy array in the form [[x-vals], [y-vals]], where
        # x-vals are bin center frequencies and y-vals are powers. So once
        # we initialize a power at each freq, we never have to modify the
        # array of x-vals, just find the index of the frequency that a
        # measurement was taken at, and insert it into the corresponding
        # index in y-vals.
        if hasattr(self, 'line'):
            self.line.remove()
        self.line, = self.subplot.plot(
            x_points, [-100.00]*len(x_points), animated=True, antialiased=True,
            linestyle='-', color='b'
        )
        self.canvas.draw()
        self.plot_background = None
        self._update_background()

    def format_ax(self, ax):
        """Set the formatting of the plot axes."""
        xaxis_formatter = FuncFormatter(self.format_mhz)
        ax.xaxis.set_major_formatter(xaxis_formatter)
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Power (dBm)')
        ax.set_xlim(self.tb.min_freq-2e7, self.tb.max_freq+2e7)
        ax.set_ylim(-130, 0)
        xtick_step = (self.tb.max_freq - self.tb.min_freq) / 4.0
        tick_range = np.arange(
            self.tb.min_freq, self.tb.max_freq+xtick_step, xtick_step
        )
        ax.set_xticks(tick_range)
        ax.set_yticks(np.arange(-130, 0, 10))
        ax.grid(color='.90', linestyle='-', linewidth=1)
        ax.set_title('Power Spectrum Density')

        return ax

    @staticmethod
    def format_mhz(x, pos):
        """Format x ticks (in Hz) to MHz with 0 decimal places."""
        return "{:.0f}".format(x / float(1e6))

    ####################
    # Plotting functions
    ####################

    def update_plot(self, points, update_plot):
        """Update the plot."""
        # It can be useful to "pause" the plot updates
        if self.paused:
            return

        # Required for plot blitting
        self.canvas.restore_region(self.plot_background)

        xs, ys = points # new points to plot

        # Index the start and stop of our current power data
        line_xs, line_ys = self.line.get_data() # currently plotted points
        xs_start = np.where(line_xs==xs[0])[0]
        xs_stop = np.where(line_xs==xs[-1])[0] + 1

        self._draw_span()
        self._draw_line(line_ys, xs_start, xs_stop, ys)
        self._draw_markers(xs_start, xs_stop, ys)
        self._check_threshold(xs, ys)

        # blit canvas
        self.canvas.blit(self.subplot.bbox)

        if update_plot:
            self.logger.debug("Reconfiguring matplotlib plot")
            self.configure_mpl_plot()

    def _update_background(self):
        """Force update of the plot background."""
        self.plot_background = self.canvas.copy_from_bbox(self.subplot.bbox)

    def _draw_span(self):
        """Draw a span to bound the peak search functionality."""
        if self.span is not None:
            self.subplot.draw_artist(self.span)

    def _draw_line(self, line_ys, xs_start, xs_stop, ys):
        """Draw the latest chunk of line data."""
        # Replace y-vals in the measured range with the new power data
        np.put(line_ys, range(xs_start, xs_stop), ys)
        self.line.set_ydata(line_ys)

        # Draw the new line only
        self.subplot.draw_artist(self.line)

    def _draw_markers(self, xs_start, xs_stop, ys):
        """Draw power markers at a specific frequency."""
        # Update marker
        m1bin = self.mkr1.bin_idx
        m2bin = self.mkr2.bin_idx

        # Update mkr1 if it's set and we're currently updating its freq range
        if ((self.mkr1.freq is not None) and
            (m1bin >= xs_start) and
            (m1bin < xs_stop)):
            mkr1_power = ys[m1bin - xs_start]
            self.mkr1.point.set_ydata(mkr1_power)
            self.mkr1.point.set_visible(True) # make visible
            self.mkr1.text_label.set_visible(True)
            self.mkr1.text_power.set_text("{:.1f} dBm".format(mkr1_power[0]))
            self.mkr1.text_power.set_visible(True)

        # Update mkr2 if it's set and we're currently updating its freq range
        if ((self.mkr2.freq is not None) and
            (m2bin >= xs_start) and
            (m2bin < xs_stop)):
            mkr2_power = ys[m2bin - xs_start]
            self.mkr2.point.set_ydata(mkr2_power)
            self.mkr2.point.set_visible(True) # make visible
            self.mkr2.text_label.set_visible(True)
            self.mkr2.text_power.set_text("{:.1f} dBm".format(mkr2_power[0]))
            self.mkr2.text_power.set_visible(True)

        # Redraw mkr1
        if self.mkr1.freq is not None:
            self.subplot.draw_artist(self.mkr1.point)
            self.figure.draw_artist(self.mkr1.text_label)
            self.figure.draw_artist(self.mkr1.text_power)

        # Redraw mkr2
        if self.mkr2.freq is not None:
            self.subplot.draw_artist(self.mkr2.point)
            self.figure.draw_artist(self.mkr2.text_label)
            self.figure.draw_artist(self.mkr2.text_power)

    def _check_threshold(self, xs, ys):
        """Warn to stdout if the threshold level has been crossed."""
        # Update threshold
        # indices of where the y-value is greater than self.threshold.level
        if self.threshold.level is not None:
            overloads, = np.where(ys > self.threshold.level)
            if overloads.size: # is > 0
                self.log_threshold_overloads(overloads, xs, ys)

    def log_threshold_overloads(self, overloads, xs, ys):
        """Outout threshold violations to the logging system."""
        logheader = "============= Overload at {} ============="
        self.logger.warning(logheader.format(int(time.time())))
        logmsg = "Exceeded threshold {0:.0f}dBm ({1:.2f}dBm) at {2:.2f}MHz"
        for i in overloads:
            self.logger.warning(
                logmsg.format(self.threshold.level, ys[i], xs[i] / 1e6)
            )

    ################
    # Event handlers
    ################

    def on_mousedown(self, event):
        """store event info for single click."""
        self.last_click_evt = event

    def on_mouseup(self, event):
        """Determine if mouse event was single click or click-and-drag."""
        if abs(self.last_click_evt.x - event.x) >= 5:
            # moused moved more than 5 pxls, set a span
            self.span = self.subplot.axvspan(
                self.last_click_evt.xdata, event.xdata, color='red', alpha=0.2,
                animated=True # "animated" makes span play nice with blitting
            )
            xdata_points = [self.last_click_evt.xdata, event.xdata]
            # always set left bound as lower value
            self.span_left, self.span_right = sorted(xdata_points)
        else:
            # caught single click, clear span
            if self.subplot.patches:
                self.span.remove()
                self.span = self.span_left = self.span_right = None

    def autoscale_yaxis(self, event):
        """Rescale the y-axis depending on current power values."""
        #FIXME: this needs a lot more work
        self.subplot.relim()
        self.subplot.autoscale_view(scalex=False, scaley=True)
        self.subplot.autoscale()

    def idle_notifier(self, event):
        self.tb.gui_idle.set()

    def set_run_continuous(self, event):
        self.tb.single_run.clear()
        self.tb.continuous_run.set()

    def set_run_single(self, event):
        self.tb.continuous_run.clear()
        self.tb.single_run.set()

    def close(self, event):
        """Handle a closed gui window."""
        self.closed = True
        self.tb.wait()
        self.tb.stop()
        self.Destroy()
        self.logger.debug("GUI closing.")
