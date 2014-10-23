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

from marker import (marker, mkr_txtctrl, mkr_peaksearch_btn, mkr_left_btn,
                    mkr_right_btn, mkr_clear_btn)

class atten_txtctrl(wx.TextCtrl):
    """Input TextCtrl for setting attenuation."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1) , style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_atten)
        self.SetValue(str(frame.tb.get_attenuation()))

    def set_atten(self, event):
        val = self.GetValue()
        try:
            float_val = float(val)
            self.frame.tb.set_attenuation(float_val)
        except ValueError:
            # If we can't cast to float, just reset at current value
            pass
        actual_val = self.frame.tb.get_attenuation()
        self.SetValue(str(actual_val))


class ADC_digi_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting ADC digital gain."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_ADC_digital_gain)
        self.SetValue(str(frame.tb.get_ADC_digital_gain()))

    def set_ADC_digital_gain(self, event):
        val = self.frame.ADC_digi_txtctrl.GetValue()
        try:
            float_val = float(val)
            self.frame.tb.set_ADC_gain(float_val)
        except ValueError:
            # If we can't cast to float, just reset at current value
            pass
        actual_val = self.frame.tb.get_gain()
        self.SetValue(str(actual_val))


class threshold_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a threshold power level."""
    def __init__(self, frame, threshold):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.Bind(wx.EVT_TEXT_ENTER, threshold.set_level)
        if threshold.level:
            self.SetValue(str(threshold.level))


class threshold(object):
    """A horizontal line to indicate user-defined overload threshold."""
    def __init__(self, frame, level):
        self.frame = frame
        self.lines = []
        self.level = level # default level in dBm or None

    def set_level(self, event):
        """Set the level to a user input value."""
        evt_obj = event.GetEventObject()

        # remove current threshold line
        if self.lines:
            self.lines.pop(0).remove()

        threshold_txtctrl_value = evt_obj.GetValue()

        redraw_needed = False
        try:
            # will raise ValueError if not a number
            self.level = float(threshold_txtctrl_value)
            redraw_needed = True
        except ValueError:
            if threshold_txtctrl_value == "" and self.level is not None:
                # Let the user remove the threshold line
                redraw_needed = True
                self.level = None

        if redraw_needed:
            # plot the new threshold and add it to our blitted background
            self.lines = self.frame.subplot.plot(
                [self.frame.tb.min_freq-1e7, self.frame.tb.max_freq+1e7], # xs
                [self.level] * 2, # ys
                color='red',
                zorder = 90 # draw it above the grid lines
            )
            self.frame.canvas.draw()
            self.frame._update_background()

        evt_obj.SetValue(str(self.level) if self.level else "")


class autoscale_btn(wx.Button):
    """A button to autoscale y."""
    def __init__(self, frame):
        wx.Button.__init__(self, frame, wx.ID_ANY, "Autoscale y")
        self.Bind(wx.EVT_BUTTON, frame.autoscale_yaxis)

        
class  wxpygui_frame(wx.Frame):
    """The main gui frame."""

    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.init_plot()

        # Init threshold line
        self.threshold = threshold(self, None)

        # Init markers (visible=False)
        self.mkr1 = marker(self, 1, '#00FF00', 'd') # thin green diamond
        self.mkr2 = marker(self, 2, '#00FF00', 'd') # thin green diamond

        # TextCtrls
        self.atten_txtctrl = atten_txtctrl(self)
        self.ADC_digi_txtctrl = ADC_digi_txtctrl(self)
        self.threshold_txtctrl = threshold_txtctrl(self, self.threshold)
        self.mkr1_txtctrl = mkr_txtctrl(self, self.mkr1, 1)
        self.mkr2_txtctrl = mkr_txtctrl(self, self.mkr2, 2)

        # Buttons
        self.mkr1_left_btn = mkr_left_btn(
            self, self.mkr1, self.mkr1_txtctrl, '<'
        )
        self.mkr1_right_btn = mkr_right_btn(
            self, self.mkr1, self.mkr1_txtctrl, '>'
        )
        self.mkr1_peaksearch_btn = mkr_peaksearch_btn(
            self, self.mkr1, self.mkr1_txtctrl
        )
        self.mkr1_clear_btn = mkr_clear_btn(
            self, self.mkr1, self.mkr1_txtctrl
        )
        self.mkr2_left_btn = mkr_left_btn(
            self, self.mkr2, self.mkr2_txtctrl, '<'
        )
        self.mkr2_right_btn = mkr_right_btn(
            self, self.mkr2, self.mkr2_txtctrl, '>'
        )
        self.mkr2_peaksearch_btn = mkr_peaksearch_btn(
            self, self.mkr2, self.mkr2_txtctrl
        )
        self.mkr2_clear_btn = mkr_clear_btn(
            self, self.mkr2, self.mkr2_txtctrl
        )

        self.autoscale_y_btn = autoscale_btn(self)
        
        # Sizers/Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plot, flag=wx.ALIGN_CENTER)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.gain_ctrls = self.init_gain_ctrls()
        self.threshold_ctrls = self.init_threshold_ctrls()
        self.mkr1_ctrls = self.init_mkr1_ctrls()
        self.mkr2_ctrls = self.init_mkr2_ctrls()

        hbox.Add(self.gain_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.threshold_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.mkr1_ctrls, flag=wx.ALL, border=10)
        hbox.Add(self.mkr2_ctrls, flag=wx.ALL, border=10)

        vbox.Add(hbox, flag=wx.ALIGN_CENTER, border=0)
        vbox.Add(self.autoscale_y_btn)
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

    def init_gain_ctrls(self):
        """Initialize gui controls for gain."""
        gain_box = wx.StaticBox(self, wx.ID_ANY, "Gain (dB)")
        gain_ctrls = wx.StaticBoxSizer(gain_box, wx.VERTICAL)
        gain_grid = wx.GridSizer(rows=2, cols=2)
        # Attenuation
        atten_txt = wx.StaticText(self, wx.ID_ANY, "Atten: ")
        gain_grid.Add(atten_txt, flag=wx.ALIGN_LEFT)
        atten_hbox = wx.BoxSizer(wx.HORIZONTAL)
        max_atten_txt = wx.StaticText(
            self, wx.ID_ANY, "{}-".format(self.tb.get_gain_range('PGA0').stop())
        )
        atten_hbox.Add(
            max_atten_txt, flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL
        )
        atten_hbox.Add(
            self.atten_txtctrl, flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL
        )
        gain_grid.Add(atten_hbox, flag=wx.BOTTOM, border=5)
        # ADC digi gain
        ADC_txt = wx.StaticText(self, wx.ID_ANY, "ADC digi: ")
        gain_grid.Add(ADC_txt, flag=wx.ALIGN_LEFT)
        gain_grid.Add(self.ADC_digi_txtctrl, flag=wx.ALIGN_RIGHT)
        gain_ctrls.Add(gain_grid, flag=wx.ALL, border=5)

        return gain_ctrls

    def init_threshold_ctrls(self):
        """Initialize gui controls for threshold."""
        threshold_box = wx.StaticBox(self, wx.ID_ANY, "Threshold (dBm)")
        threshold_ctrls = wx.StaticBoxSizer(threshold_box, wx.VERTICAL)
        threshold_grid = wx.GridSizer(rows=1, cols=2)
        atten_txt = wx.StaticText(self, wx.ID_ANY, "Overload: ")
        threshold_grid.Add(atten_txt, flag=wx.ALIGN_LEFT)
        threshold_grid.Add(self.threshold_txtctrl, flag=wx.ALIGN_RIGHT)
        threshold_ctrls.Add(threshold_grid, flag=wx.ALL, border=5)

        return threshold_ctrls

    def init_mkr1_ctrls(self):
        """Initialize gui controls for mkr1."""
        mkr1_box = wx.StaticBox(self, wx.ID_ANY, "Marker 1 (MHz)")
        mkr1_ctrls = wx.StaticBoxSizer(mkr1_box, wx.VERTICAL)
        mkr1_ctrls.Add(self.mkr1_peaksearch_btn, proportion=0,
                       flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        mkr1_hbox = wx.BoxSizer(wx.HORIZONTAL)
        mkr1_hbox.Add(self.mkr1_left_btn, flag=wx.LEFT, border=5)
        mkr1_hbox.Add(self.mkr1_txtctrl, proportion=1, flag=wx.EXPAND, border=1)
        mkr1_hbox.Add(self.mkr1_right_btn, flag=wx.RIGHT, border=5)
        mkr1_ctrls.Add(mkr1_hbox, flag=wx.ALIGN_CENTER)
        mkr1_ctrls.Add(self.mkr1_clear_btn, proportion=0,
                       flag=wx.ALL|wx.ALIGN_CENTER, border=5)

        return mkr1_ctrls

    def init_mkr2_ctrls(self):
        """Initialize gui controls for mkr2."""
        mkr2_box = wx.StaticBox(self, wx.ID_ANY, "Marker 2 (MHz)")
        mkr2_ctrls = wx.StaticBoxSizer(mkr2_box, wx.VERTICAL)
        mkr2_ctrls.Add(self.mkr2_peaksearch_btn, proportion=0,
                       flag=wx.ALL|wx.ALIGN_CENTER, border=5)
        mkr2_hbox = wx.BoxSizer(wx.HORIZONTAL)
        mkr2_hbox.Add(self.mkr2_left_btn, flag=wx.LEFT, border=5)
        mkr2_hbox.Add(self.mkr2_txtctrl, proportion=1, flag=wx.EXPAND, border=1)
        mkr2_hbox.Add(self.mkr2_right_btn, flag=wx.RIGHT, border=5)
        mkr2_ctrls.Add(mkr2_hbox, flag=wx.ALIGN_CENTER)
        mkr2_ctrls.Add(self.mkr2_clear_btn, proportion=0,
                       flag=wx.ALL|wx.ALIGN_CENTER, border=5)

        return mkr2_ctrls

    def init_plot(self):
        """Initialize a matplotlib plot."""
        self.plot = wx.Panel(self, wx.ID_ANY, size=(800,600))
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.plot, -1, self.figure)
        self.subplot = self.format_ax(self.figure.add_subplot(111))
        x_points = self.tb.bin_freqs
        # self.line in a numpy array in the form [[x-vals], [y-vals]], where
        # x-vals are bin center frequencies and y-vals are powers. So once
        # we initialize a power at each freq, we never have to modify the
        # array of x-vals, just find the index of the frequency that a
        # measurement was taken at, and insert it into the corresponding
        # index in y-vals.
        self.line, = self.subplot.plot(
            x_points, [-100.00]*len(x_points), animated=True, antialiased=True,
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
        ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        ax.set_ylim(-130, 0)
        xtick_step = (self.tb.requested_max_freq - self.tb.min_freq) / 4.0
        tick_range = np.arange(
            self.tb.min_freq, self.tb.requested_max_freq+xtick_step, xtick_step
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

    def update_plot(self, points, new_sweep):
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
        """Handle a double click event, or store event info for single click."""
        if event.dblclick:
            self.pause_plot(event)
        else:
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
        
    def pause_plot(self, event):
        """Pause/resume plot updates if the plot area is double clicked."""
        self.paused = not self.paused
        paused = "paused" if self.paused else "unpaused"
        self.logger.info("Plotting {0}.".format(paused))

    def idle_notifier(self, event):
        self.tb.gui_idle = True

    def close(self, event):
        """Handle a closed gui window."""
        self.closed = True
        self.tb.wait()
        self.tb.stop()
        self.Destroy()
        self.logger.debug("GUI closing.")
