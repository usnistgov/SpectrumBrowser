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

from gui import (delay, dwell, export, frequency, gain, lotuning, marker,
                 power, resolution, threshold, trigger, window, stream, span)


class wxpygui_frame(wx.Frame):
    """The main gui frame."""

    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.min_power = -120 # dBm
        self.max_power = 0 # dBm

        self.init_mpl_canvas()
        self.configure_mpl_plot()

        # Setup a threshold level at None
        self.threshold = threshold.threshold(self, None)

        # Init markers (visible=False)
        self.mkr1 = marker.marker(self, 1, '#00FF00', 'd') # thin green diamond
        self.mkr2 = marker.marker(self, 2, '#00FF00', 'd') # thin green diamond

        # init control boxes
        self.gain_ctrls = gain.init_ctrls(self)
        self.threshold_ctrls = threshold.init_ctrls(self)
        self.mkr1_ctrls = marker.init_mkr1_ctrls(self)
        self.mkr2_ctrls = marker.init_mkr2_ctrls(self)
        self.res_ctrls = resolution.init_ctrls(self)
        self.windowfn_ctrls = window.init_ctrls(self)
        self.lo_offset_ctrls = lotuning.init_ctrls(self)
        self.dwell_ctrls = dwell.init_ctrls(self)
        self.delay_ctrls = delay.init_ctrls(self)
        self.frequency_ctrls = frequency.init_ctrls(self)
        self.span_ctrls = span.init_ctrls(self)
        self.trigger_ctrls = trigger.init_ctrls(self)
        self.power_ctrls = power.init_ctrls(self)
        self.export_ctrls = export.init_ctrls(self)
        self.stream_ctrls = stream.init_ctrls(self)

        self.set_layout()

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

        self.last_click_evt = None

        self.closed = False

        ####################
        # GUI Sizers/Layout
        ####################

    def set_layout(self):
        """Setup frame layout and sizers"""
        # front panel to hold plot and constrol stack side-by-side
        frontpanel = wx.BoxSizer(wx.HORIZONTAL)

        # control stack to hold control clusters vertically
        controlstack = wx.BoxSizer(wx.VERTICAL)

        # first cluster - usrp state

        usrpstate_outline = wx.StaticBox(self, wx.ID_ANY, "USRP State")
        usrpstate_cluster = wx.StaticBoxSizer(usrpstate_outline, wx.HORIZONTAL)

        usrpstate_row1 = wx.BoxSizer(wx.HORIZONTAL)
        usrpstate_row1.Add(self.trigger_ctrls, flag=wx.ALL, border=5)
        usrpstate_row1.Add(self.stream_ctrls, flag=wx.ALL, border=5)

        usrpstate_row2 = wx.BoxSizer(wx.HORIZONTAL)
        usrpstate_row2.Add(
            self.frequency_ctrls,
            proportion=1,
            flag=wx.ALL,#|wx.EXPAND,
            border=5
        )
        usrpstate_row2.Add(
            self.span_ctrls,
            proportion=1,
            flag=wx.ALL,#|wx.EXPAND,
            border=5
        )

        usrpstate_col1 = wx.BoxSizer(wx.VERTICAL)
        usrpstate_col1.Add(usrpstate_row1)
        usrpstate_col1.Add(usrpstate_row2, flag=wx.EXPAND)

        usrpstate_col2 = wx.BoxSizer(wx.VERTICAL)
        usrpstate_col2.Add(self.gain_ctrls, flag=wx.ALL, border=5)
        usrpstate_col2.Add(self.lo_offset_ctrls, flag=wx.ALL|wx.EXPAND, border=5)

        # col 1
        usrpstate_cluster.Add(usrpstate_col1)
        # col 2
        usrpstate_cluster.Add(usrpstate_col2)

        # second cluster - display controls

        display_outline = wx.StaticBox(self, wx.ID_ANY, "Display")
        display_cluster = wx.StaticBoxSizer(display_outline, wx.HORIZONTAL)

        dwelldelaybox = wx.BoxSizer(wx.HORIZONTAL)
        dwelldelaybox.Add(
            self.dwell_ctrls,
            proportion=1,
            flag=wx.ALL,
            border=5
        )
        dwelldelaybox.Add(
            self.delay_ctrls,
            proportion=1,
            flag=wx.ALL,
            border=5
        )

        display_col1 = wx.BoxSizer(wx.VERTICAL)
        display_col1.Add(self.res_ctrls, flag=wx.ALL, border=5)
        display_col1.Add(dwelldelaybox, flag=wx.EXPAND)

        display_col2 = wx.BoxSizer(wx.VERTICAL)
        display_col2.Add(self.windowfn_ctrls, flag=wx.ALL, border=5)
        display_col2.Add(self.power_ctrls, flag=wx.ALL|wx.EXPAND, border=5)

        # col 1
        display_cluster.Add(display_col1)
        # col 2
        display_cluster.Add(display_col2)

        # third cluster - data controls

        data_outline = wx.StaticBox(self, wx.ID_ANY, "Data")
        data_cluster = wx.StaticBoxSizer(data_outline, wx.HORIZONTAL)

        data_col3 = wx.BoxSizer(wx.VERTICAL)
        data_col3.Add(self.threshold_ctrls)
        data_col3.Add(self.export_ctrls)

        # col 1
        data_cluster.Add(self.mkr1_ctrls, flag=wx.ALL, border=5)
        # col 2
        data_cluster.Add(self.mkr2_ctrls, flag=wx.ALL, border=5)
        # col 3
        data_cluster.Add(data_col3, flag=wx.ALL, border=5)

        # put everything together

        # Add control clusters vertically to control stack
        controlstack.Add(
            usrpstate_cluster,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5
        )
        controlstack.Add(
            display_cluster,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5
        )
        controlstack.Add(
            data_cluster,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5
        )

        # Add plot and control stack side-by-side on the front panel
        frontpanel.Add(self.plot, flag=wx.ALIGN_CENTER_VERTICAL)
        frontpanel.Add(controlstack, flag=wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(frontpanel)
        self.Fit()

    ####################
    # GUI Initialization
    ####################

    def init_mpl_canvas(self):
        """Initialize a matplotlib plot."""
        self.plot = wx.Panel(self, wx.ID_ANY, size=(700,600))
        self.figure = Figure(figsize=(7, 6), dpi=100)
        self.figure.subplots_adjust(right=.95)
        self.canvas = FigureCanvas(self.plot, -1, self.figure)

    def configure_mpl_plot(self, adjust_freq_range=True):
        """Configure or reconfigure the matplotlib plot"""
        if hasattr(self, 'subplot'):
            self.subplot = self.format_ax(self.subplot)
        else:
            self.subplot = self.format_ax(self.figure.add_subplot(111))

        maxbin = self.tb.cfg.max_plotted_bin
        x_points = self.tb.cfg.bin_freqs[:maxbin]
        # self.line in a numpy array in the form [[x-vals], [y-vals]], where
        # x-vals are bin center frequencies and y-vals are powers. So once we
        # initialize a power at each freq, just find the index of the
        # frequency that a measurement was taken at, and insert it into the
        # corresponding index in y-vals.
        if adjust_freq_range:
            if hasattr(self, 'mkr1'):
                self.mkr1.unplot()
            if hasattr(self, 'mkr2'):
                self.mkr2.unplot()
            if hasattr(self, 'line'):
                self.line.remove()

            self.line, = self.subplot.plot(
                x_points, [-100.00]*len(x_points), animated=True,
                antialiased=True, linestyle='-', color='b'
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
        cf = self.tb.cfg.center_freq
        lowest_xtick = cf - (self.tb.cfg.span / 2)
        highest_xtick = cf + (self.tb.cfg.span / 2)
        ax.set_xlim(lowest_xtick-1e6, highest_xtick+1e6)
        ax.set_ylim(self.min_power+1, self.max_power-1)
        xticks = np.linspace(lowest_xtick, highest_xtick, 5, endpoint=True)
        ax.set_xticks(xticks)
        ax.set_yticks(np.arange(self.min_power, self.max_power, 10))
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

    def update_plot(self, points, reconfigure_plot, keep_alive):
        """Update the plot."""

        if reconfigure_plot:
            self.logger.debug("Reconfiguring matplotlib plot")
            self.configure_mpl_plot()

        # Required for plot blitting
        self.canvas.restore_region(self.plot_background)

        if keep_alive:
            # Just keep markers and span alive after single run
            xs_start = 0
            xs_stop = len(self.tb.cfg.bin_freqs) + 1
            ys = self.line.get_ydata()
            self.subplot.draw_artist(self.line)
        else:
            xs, ys = points # new points to plot

            # Index the start and stop of our current power data
            line_xs, line_ys = self.line.get_data() # currently plotted points
            xs_start = np.where(line_xs==xs[0])[0][0]
            xs_stop = np.where(line_xs==xs[-1])[0][0] + 1

            self._draw_line(line_ys, xs_start, xs_stop, ys)
            self._check_threshold(xs, ys)

        self._draw_span()
        self._draw_markers(xs_start, xs_stop, ys)

        # blit canvas
        self.canvas.blit(self.subplot.bbox)

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
            self.mkr1.text_power.set_text("{:.1f} dBm".format(mkr1_power))
            self.mkr1.text_power.set_visible(True)

        # Update mkr2 if it's set and we're currently updating its freq range
        if ((self.mkr2.freq is not None) and
            (m2bin >= xs_start) and
            (m2bin < xs_stop)):
            mkr2_power = ys[m2bin - xs_start]
            self.mkr2.point.set_ydata(mkr2_power)
            self.mkr2.point.set_visible(True) # make visible
            self.mkr2.text_label.set_visible(True)
            self.mkr2.text_power.set_text("{:.1f} dBm".format(mkr2_power))
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
                self.subplot.patches = []
                self.span = self.span_left = self.span_right = None

    def idle_notifier(self, event):
        self.tb.gui_idle.set()

    def set_run_continuous(self, event):
        self.tb.single_run.clear()
        self.tb.continuous_run.set()

    def set_run_single(self, event):
        self.tb.continuous_run.clear()
        self.tb.single_run.set()

    def export_iq_data(self, event):
        self.tb.save_iq_data_to_file()

    def export_fft_data(self, event):
        self.tb.save_fft_data_to_file()

    def close(self, event):
        """Handle a closed gui window."""
        self.closed = True
        self.tb.wait()
        self.tb.stop()
        self.Destroy()
        self.logger.debug("GUI closing.")
