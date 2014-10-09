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

from __future__ import absolute_import

import time
import wx
import logging
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from matplotlib.widgets import SpanSelector


class atten_txtctrl(wx.TextCtrl):
    """Input TextCtrl for setting attenuation."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
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
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
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
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
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
                [self.frame.tb.min_freq-1e7, self.frame.tb.max_freq+1e7], # x values
                [self.level] * 2, # y values
                color='red',
                zorder = 90 # draw it above the grid lines
            )
            self.frame.canvas.draw()
            self.frame.update_background()

        evt_obj.SetValue(str(self.level) if self.level else "")


class mkr_peaksearch_btn(wx.Button):
    """A button to step the marker one bin to the right."""
    def __init__(self, frame, marker, txtctrl):
        wx.Button.__init__(self, frame, wx.ID_ANY, "Peak Search", style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.peak_search(evt, txt))


class mkr_left_btn(wx.Button):
    """A button to step the marker one bin to the left."""
    def __init__(self, frame, marker, txtctrl, label):
        wx.Button.__init__(self, frame, wx.ID_ANY, label=label, style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.step_left(evt, txt))


class mkr_right_btn(wx.Button):
    """A button to step the marker one bin to the right."""
    def __init__(self, frame, marker, txtctrl, label):
        wx.Button.__init__(self, frame, wx.ID_ANY, label=label, style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.step_right(evt, txt))


class mkr_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a marker frequency."""
    def __init__(self, frame, marker, id_):
        wx.TextCtrl.__init__(self, frame, id=id_, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, marker.jump)


class marker(object):
    """A SpecAn-style visual marker that follows the power level at a freq."""
    def __init__(self, frame, id_, color, shape):
        self.frame = frame
        self.color = color
        self.shape = shape
        self.n = id_ # 1 for MKR1, 2 for MKR2
        self.units = "MHz"
        self.size = 8
        self.point = None
        self.text_label = None
        self.text_power = None
        self.freq = None
        self.bin_idx = None

    def find_nearest(self, value):
        """Find the index of the closest matching value in an array."""
        #http://stackoverflow.com/a/2566508
        idx = np.abs(self.frame.tb.bin_freqs - value).argmin()
        return (idx, self.frame.tb.bin_freqs[idx])

    def unplot(self):
        """Remove marker and related text from the plot."""
        self.freq = None
        self.bin_idx = None
        if self.point is not None:
            self.point.remove()
            self.frame.figure.texts.remove(self.text_label)
            self.frame.figure.texts.remove(self.text_power)
            self.point = self.text_label = self.text_power = None

    def jump(self, event):
        """Handle frequency change from the marker TxtCtrl."""
        evt_obj = event.GetEventObject()
        temp_freq = evt_obj.GetValue()
        try:
            # MHz to Hz. Will raise ValueError if not a number
            temp_freq = float(temp_freq) * 1e6
        except ValueError:
            if temp_freq == "":
                # Let the user remove the marker
                self.unplot()
                return
            else:
                temp_freq = self.freq # reset to last known good value
                if temp_freq is None:
                    return

        self.bin_idx, self.freq = self.find_nearest(temp_freq)
        self.plot()
        evt_obj.SetValue(self.get_freq_str())

    def get_freq_str(self):
        freq = "{:.2f}".format(self.freq / 1e6)
        return freq

    def plot(self):
        """Plot the marker and related text."""

        mkr_num = "MKR{}".format(self.n) # self.n is set to 1 or 2
        label = mkr_num + '\n ' + self.get_freq_str() + ' ' + self.units

        mkr_xcoords = [0, 0.15, 0.77]

        if self.point is None:
            self.point, = self.frame.subplot.plot(
                [self.freq], # x value
                [0], # temp y value, update_line will adjust with each sweep
                marker = self.shape,
                markerfacecolor = self.color,
                markersize = self.size,
                zorder = 99,  # draw it above the grid lines
                animated = True,
                visible = False # make the marker invisible until update_line sets y
            )
            self.text_label = self.frame.figure.text(
                mkr_xcoords[self.n], # x
                0.83, # y
                label, # static text to display
                color = 'green',
                animated = True,
                visible = False,
                size = 11
            )
            self.text_power = self.frame.figure.text(
                mkr_xcoords[self.n], # x
                0.80, # y location
                "", # update_plot replaces this text
                color = 'green',
                visible = False,
                animated = True,
                size = 11
            )
        else:
            self.point.set_xdata([self.freq])
            self.text_label.set_text(label)


    def step_left(self, event, txtctrl):
        if self.bin_idx: #is not None or 0
            self.bin_idx -= 1
            self.freq = self.frame.tb.bin_freqs[self.bin_idx]
            txtctrl.SetValue(self.get_freq_str())
            self.plot()

    def step_right(self, event, txtctrl):
        if (self.bin_idx is not None and self.bin_idx < len(self.frame.tb.bin_freqs)-1):
            self.bin_idx += 1
            self.freq = self.frame.tb.bin_freqs[self.bin_idx]
            txtctrl.SetValue(self.get_freq_str())
            self.plot()

    def peak_search(self, event, txtctrl):
        left_bound_idx = 0
        if self.frame.span_left and self.frame.span_right:
            left_bound_idx = self.find_nearest(self.frame.span_left)[0]
            right_bound_idx = self.find_nearest(self.frame.span_right)[0]
            power_data = self.frame.line.get_ydata()[left_bound_idx:right_bound_idx]
        else:
            power_data = self.frame.line.get_ydata()
        self.bin_idx = np.where(power_data == np.amax(power_data))[0][0] + left_bound_idx
        self.freq = self.frame.tb.bin_freqs[self.bin_idx]
        txtctrl.SetValue(self.get_freq_str())
        self.plot()


class  wxpygui_frame(wx.Frame):
    """The main gui frame."""

    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.init_plot()
        self.threshold = threshold(self, None)
        self.threshold_txtctrl = threshold_txtctrl(self, self.threshold)
        self.mkr1 = marker(self, 1, '#00FF00', 'd') # thin green diamond
        self.mkr2 = marker(self, 2, '#00FF00', 'd') # thin green diamond
        self.mkr1_txtctrl = mkr_txtctrl(self, self.mkr1, 1)
        self.mkr2_txtctrl = mkr_txtctrl(self, self.mkr2, 2)
        self.mkr1_left_btn = mkr_left_btn(
            self, self.mkr1, self.mkr1_txtctrl, '<'
        )
        self.mkr1_right_btn = mkr_right_btn(
            self, self.mkr1, self.mkr1_txtctrl, '>'
        )
        self.mkr2_left_btn = mkr_left_btn(
            self, self.mkr2, self.mkr2_txtctrl, '<'
        )
        self.mkr2_right_btn = mkr_right_btn(
            self, self.mkr2, self.mkr2_txtctrl, '>'
        )
        self.mkr1_peaksearch_btn = mkr_peaksearch_btn(self, self.mkr1, self.mkr1_txtctrl)
        self.mkr2_peaksearch_btn = mkr_peaksearch_btn(self, self.mkr2, self.mkr2_txtctrl)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plot)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.atten_txtctrl = atten_txtctrl(self)
        self.ADC_digi_txtctrl = ADC_digi_txtctrl(self)

        self.gain_ctrls = self.init_gain_ctrls()
        self.threshold_ctrls = self.init_threshold_ctrls()
        self.mkr1_ctrls = self.init_mkr1_ctrls()
        self.mkr2_ctrls = self.init_mkr2_ctrls()

        hbox.Add(self.gain_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.threshold_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.mkr1_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.mkr2_ctrls, 0, wx.ALL, 10)

        vbox.Add(hbox)
        self.SetSizer(vbox)
        self.Fit()

        self.logger = logging.getLogger('USRPAnalyzer.wxpygui_frame')

        # gui event handlers
        self.Bind(wx.EVT_CLOSE, self.close)
        self.Bind(wx.EVT_IDLE, self.idle_notifier)

        self.canvas.mpl_connect('button_press_event', self.on_clickdown)
        self.canvas.mpl_connect('button_release_event', self.on_clickup)

        # Used to peak search within range
        self.span = None
        self.span_left = None
        self.span_right = None

        self.paused = False
        self.last_click_evt = None

        self.start_t = time.time()


    def init_gain_ctrls(self):
        """Initialize gui controls for gain."""
        # FIXME: add flexgridsizer
        gain_box = wx.StaticBox(self, wx.ID_ANY, "Gain")
        gain_ctrls = wx.StaticBoxSizer(gain_box, wx.VERTICAL)
        # Attenuation
        atten_hbox = wx.BoxSizer(wx.HORIZONTAL)
        atten_txt = wx.StaticText(self, wx.ID_ANY, "Atten: 31.5 -")
        atten_hbox.Add(atten_txt)
        atten_hbox.Add(self.atten_txtctrl)
        gain_ctrls.Add(atten_hbox)
        # ADC digi gain
        ADC_hbox = wx.BoxSizer(wx.HORIZONTAL)
        ADC_txt = wx.StaticText(self, wx.ID_ANY, "ADC digi:")
        ADC_hbox.Add(ADC_txt)
        ADC_hbox.Add(self.ADC_digi_txtctrl)
        gain_ctrls.Add(ADC_hbox)

        return gain_ctrls

    def init_threshold_ctrls(self):
        """Initialize gui controls for threshold."""
        threshold_box = wx.StaticBox(self, wx.ID_ANY, "Threshold")
        threshold_ctrls = wx.StaticBoxSizer(threshold_box, wx.VERTICAL)
        threshold_hbox = wx.BoxSizer(wx.HORIZONTAL)
        threshold_txt = wx.StaticText(self, wx.ID_ANY, "dBm")
        threshold_hbox.Add(self.threshold_txtctrl)
        threshold_hbox.Add(threshold_txt)
        threshold_ctrls.Add(threshold_hbox)

        return threshold_ctrls

    def init_mkr1_ctrls(self):
        """Initialize gui controls for mkr1."""
        mkr1_box = wx.StaticBox(self, wx.ID_ANY, "Marker 1")
        mkr1_ctrls = wx.StaticBoxSizer(mkr1_box, wx.VERTICAL)
        mkr1_hbox = wx.BoxSizer(wx.HORIZONTAL)
        mkr1_txt = wx.StaticText(self, wx.ID_ANY, "MHz")
        mkr1_hbox.Add(self.mkr1_left_btn)
        mkr1_hbox.Add(self.mkr1_txtctrl)
        mkr1_hbox.Add(self.mkr1_right_btn)
        mkr1_hbox.Add(mkr1_txt)
        mkr1_ctrls.Add(self.mkr1_peaksearch_btn)
        mkr1_ctrls.Add(mkr1_hbox)

        return mkr1_ctrls

    def init_mkr2_ctrls(self):
        """Initialize gui controls for mkr2."""
        mkr2_box = wx.StaticBox(self, wx.ID_ANY, "Marker 2")
        mkr2_ctrls = wx.StaticBoxSizer(mkr2_box, wx.VERTICAL)
        mkr2_hbox = wx.BoxSizer(wx.HORIZONTAL)
        mkr2_txt = wx.StaticText(self, wx.ID_ANY, "MHz")
        mkr2_hbox.Add(self.mkr2_left_btn)
        mkr2_hbox.Add(self.mkr2_txtctrl)
        mkr2_hbox.Add(self.mkr2_right_btn)
        mkr2_hbox.Add(mkr2_txt)
        mkr2_ctrls.Add(self.mkr2_peaksearch_btn)
        mkr2_ctrls.Add(mkr2_hbox)

        return mkr2_ctrls

    def update_background(self):
        """Force update of the plot background."""
        self.plot_background = self.canvas.copy_from_bbox(self.subplot.bbox)

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
            x_points, [-100]*len(x_points), animated=True, antialiased=False,
        )
        self.canvas.draw()
        self.plot_background = None
        self.update_background()

    @staticmethod
    def format_mhz(x, pos):
        """Format x ticks (in Hz) to MHz with 0 decimal places."""
        return "{:.0f}".format(x / float(1e6))

    def format_ax(self, ax):
        """Set the formatting of the plot axes."""
        xaxis_formatter = FuncFormatter(self.format_mhz)
        ax.xaxis.set_major_formatter(xaxis_formatter)
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Power (dBm)')
        ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        ax.set_ylim(-120,0)
        xtick_step = (self.tb.requested_max_freq - self.tb.min_freq) / 4.0
        ax.set_xticks(
            np.arange(self.tb.min_freq, self.tb.requested_max_freq+xtick_step, xtick_step)
        )
        ax.set_yticks(np.arange(-130, 0, 10))
        ax.grid(color='.90', linestyle='-', linewidth=1)
        ax.set_title('Power Spectrum Density')

        return ax

    def update_plot(self, points, new_sweep):
        """Update the plot."""

        # It can be useful to "pause" the plot updates
        if self.paused:
            return

        # Required for plot blitting
        self.canvas.restore_region(self.plot_background)

        if self.span is not None:
            self.subplot.draw_artist(self.span)

        line_xs, line_ys = self.line.get_data() # currently plotted points
        xs, ys = points # new points to plot

        # Update line
        # Index the start and stop of our current power data
        xs_start = np.where(line_xs==xs[0])[0]
        xs_stop = np.where(line_xs==xs[-1])[0] + 1
        # Replace y-vals in the measured range with the new power data
        np.put(line_ys, range(xs_start, xs_stop), ys)
        self.line.set_ydata(line_ys)

        # Draw the new line only
        self.subplot.draw_artist(self.line)

        # Update marker
        m1bin = self.mkr1.bin_idx
        m2bin = self.mkr2.bin_idx
        # Update mkr1 if it's set and we're currently updating its freq range
        if ((self.mkr1.freq is not None) and (m1bin >= xs_start) and (m1bin < xs_stop)):
            mkr1_power = ys[m1bin - xs_start]
            self.mkr1.point.set_ydata(mkr1_power)
            self.mkr1.point.set_visible(True) # make visible
            self.mkr1.text_label.set_visible(True)
            self.mkr1.text_power.set_text("{:.1f} dBm".format(mkr1_power[0]))
            self.mkr1.text_power.set_visible(True)
        # Update mkr2 if it's set and we're currently updating its freq range
        if ((self.mkr2.freq is not None) and (m2bin >= xs_start) and (m2bin < xs_stop)):
            mkr2_power = ys[m2bin - xs_start]
            self.mkr2.point.set_ydata(mkr2_power)
            self.mkr2.point.set_visible(True) # make visible
            self.mkr2.text_label.set_visible(True)
            self.mkr2.text_power.set_text("{:.1f} dBm".format(mkr2_power[0]))
            self.mkr2.text_power.set_visible(True)

        # Redraw markers
        if self.mkr1.freq is not None:
            self.subplot.draw_artist(self.mkr1.point)
            self.figure.draw_artist(self.mkr1.text_label)
            self.figure.draw_artist(self.mkr1.text_power)
        if self.mkr2.freq is not None:
            self.subplot.draw_artist(self.mkr2.point)
            self.figure.draw_artist(self.mkr2.text_label)
            self.figure.draw_artist(self.mkr2.text_power)

        # Update threshold
        # indices of where the y-value is greater than self.threshold.level
        if self.threshold.level is not None:
            overload, = np.where(ys > self.threshold.level)
            if overload.size: # is > 0
                logheader = "============= Overload at {} ============="
                self.logger.warning(logheader.format(int(time.time())))
                logmsg = "Exceeded threshold {0:.0f}dBm ({1:.2f}dBm) at {2:.2f}MHz"
                for i in overload:
                    self.logger.warning(
                        logmsg.format(self.threshold.level, ys[i], xs[i] / 1e6)
                    )

        # blit canvas
        self.canvas.blit(self.subplot.bbox)

    def on_clickdown(self, event):
        if event.dblclick:
            self.pause_plot(event)
        else:
            self.last_click_evt = event

    def on_clickup(self, event):
        if abs(self.last_click_evt.x - event.x) >= 5: # moused moved more than 5 pxls
            self.span = self.subplot.axvspan(
                self.last_click_evt.xdata, event.xdata, color='red', alpha=0.2
            )
            self.span_left, self.span_right  = sorted([self.last_click_evt.xdata, event.xdata])
        else: # caught single click, clear span
            if self.subplot.patches:
                self.span.remove()
                self.span = self.span_left = self.span_right = None


    def pause_plot(self, event):
        """Pause/resume plot updates if the plot area is double clicked."""
        self.paused = not self.paused
        paused = "paused" if self.paused else "unpaused"
        self.logger.info("Plotting {0}.".format(paused))

    def idle_notifier(self, event):
        self.tb.gui_idle = True

    def close(self, event):
        """Handle a closed gui window."""
        self.logger.debug("GUI closing.")
        self.tb.stop()
        self.Destroy()
