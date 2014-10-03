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


class marker_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a marker frequency."""
    def __init__(self, frame, marker, ID):
        wx.TextCtrl.__init__(self, frame, ID, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, marker.plot)


class marker(object):
    """A SpecAn-style visual marker that follows the power level at a freq."""
    def __init__(self, frame, color, shape):
        self.frame = frame
        self.color = color
        self.shape = shape
        self.size = 8
        self.point = None
        self.text_label = None
        self.text_power = None
        self.freq = None
        self.bin_idx = None

    @staticmethod
    def find_nearest(array, value):
        """Find the index of the closest matching value in an array."""
        #http://stackoverflow.com/a/2566508
        idx = np.abs(array - value).argmin()
        return (idx, array[idx])

    def unplot(self):
        self.freq = None
        self.bin_idx = None
        if self.point is not None:
            self.point.remove()
            self.frame.figure.texts.remove(self.text_label)
            self.frame.figure.texts.remove(self.text_power)
            self.point = self.text_label = self.text_power = None

    def plot(self, event):
        """Set the marker at a frequency."""
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

        bin_idx, nearest_freq = self.find_nearest(self.frame.tb.bin_freqs, temp_freq)
        self.bin_idx = bin_idx

        mkr_num = "MKR{}".format(evt_obj.Id) # evt_obj.Id set to 1 or 2
        freq = "{:.1f}".format(nearest_freq / 1e6)
        units = "MHz"
        label = mkr_num + '\n ' + freq + ' ' + units

        mkr_xcoords = [0, 0.15, 0.77]

        if self.point is None:
            self.point, = self.frame.subplot.plot(
                [nearest_freq], # x value
                [0], # temp y value, update_line will adjust with each sweep
                marker = self.shape,
                markerfacecolor = self.color,
                markersize = self.size,
                zorder = 99,  # draw it above the grid lines
                animated = True,
                visible = False # make the marker invisible until update_line sets y
            )
            self.text_label = self.frame.figure.text(
                mkr_xcoords[evt_obj.Id], # x
                0.83, # y
                label, # static text to display
                color = 'green',
                animated = True,
                visible = False,
                size = 11
            )
            self.text_power = self.frame.figure.text(
                mkr_xcoords[evt_obj.Id], # x
                0.80, # y location
                "", # update_plot replaces this text
                color = 'green',
                visible = False,
                animated = True,
                size = 11
            )
        else:
            self.point.set_xdata([nearest_freq])
            self.text_label.set_text(label)

        evt_obj.SetValue(freq)
        self.freq = nearest_freq


class  wxpygui_frame(wx.Frame):
    """The main gui frame."""

    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.init_plot()
        self.threshold = threshold(self, None)
        self.threshold_txtctrl = threshold_txtctrl(self, self.threshold)
        self.marker1 = marker(self, '#00FF00', 'd') # thin green diamond
        self.marker2 = marker(self, '#00FF00', 'd') # thin green diamond
        self.marker1_txtctrl = marker_txtctrl(self, self.marker1, 1)
        self.marker2_txtctrl = marker_txtctrl(self, self.marker2, 2)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plot)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.atten_txtctrl = atten_txtctrl(self)
        self.ADC_digi_txtctrl = ADC_digi_txtctrl(self)

        self.gain_ctrls = self.init_gain_ctrls()
        self.threshold_ctrls = self.init_threshold_ctrls()
        self.marker1_ctrls = self.init_marker1_ctrls()
        self.marker2_ctrls = self.init_marker2_ctrls()

        hbox.Add(self.gain_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.threshold_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.marker1_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.marker2_ctrls, 0, wx.ALL, 10)

        vbox.Add(hbox)
        self.SetSizer(vbox)
        self.Fit()

        self.logger = logging.getLogger('USRPAnalyzer.wxpygui_frame')

        # gui event handlers
        self.Bind(wx.EVT_CLOSE, self.close)
        self.Bind(wx.EVT_IDLE, self.idle_notifier)

        self.canvas.mpl_connect('button_press_event', self.pause_plot)
        #fig.canvas.mpl_connect('scroll_event', self.onzoom)

        self.paused = False

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

    def init_marker1_ctrls(self):
        """Initialize gui controls for marker1."""
        marker1_box = wx.StaticBox(self, wx.ID_ANY, "Marker 1")
        marker1_ctrls = wx.StaticBoxSizer(marker1_box, wx.VERTICAL)
        marker1_hbox = wx.BoxSizer(wx.HORIZONTAL)
        marker1_txt = wx.StaticText(self, wx.ID_ANY, "MHz")
        marker1_hbox.Add(self.marker1_txtctrl)
        marker1_hbox.Add(marker1_txt)
        marker1_ctrls.Add(marker1_hbox)

        return marker1_ctrls

    def init_marker2_ctrls(self):
        """Initialize gui controls for marker2."""
        marker2_box = wx.StaticBox(self, wx.ID_ANY, "Marker 2")
        marker2_ctrls = wx.StaticBoxSizer(marker2_box, wx.VERTICAL)
        marker2_hbox = wx.BoxSizer(wx.HORIZONTAL)
        marker2_txt = wx.StaticText(self, wx.ID_ANY, "MHz")
        marker2_hbox.Add(self.marker2_txtctrl)
        marker2_hbox.Add(marker2_txt)
        marker2_ctrls.Add(marker2_hbox)

        return marker2_ctrls

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
        m1bin = self.marker1.bin_idx
        m2bin = self.marker2.bin_idx
        # Update marker1 if it's set and we're currently updating its freq range
        if ((self.marker1.freq is not None) and (m1bin >= xs_start) and (m1bin < xs_stop)):
            marker1_power = ys[m1bin - xs_start]
            self.marker1.point.set_ydata(marker1_power)
            self.marker1.point.set_visible(True) # make visible
            self.marker1.text_label.set_visible(True)
            self.marker1.text_power.set_text("{:.1f} dBm".format(marker1_power[0]))
            self.marker1.text_power.set_visible(True)
        # Update marker2 if it's set and we're currently updating its freq range
        if ((self.marker2.freq is not None) and (m2bin >= xs_start) and (m2bin < xs_stop)):
            marker2_power = ys[m2bin - xs_start]
            self.marker2.point.set_ydata(marker2_power)
            self.marker2.point.set_visible(True) # make visible
            self.marker2.text_label.set_visible(True)
            self.marker2.text_power.set_text("{:.1f} dBm".format(marker2_power[0]))
            self.marker2.text_power.set_visible(True)

        # Redraw markers
        if self.marker1.freq is not None:
            self.subplot.draw_artist(self.marker1.point)
            self.figure.draw_artist(self.marker1.text_label)
            self.figure.draw_artist(self.marker1.text_power)
        if self.marker2.freq is not None:
            self.subplot.draw_artist(self.marker2.point)
            self.figure.draw_artist(self.marker2.text_label)
            self.figure.draw_artist(self.marker2.text_power)

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

    def pause_plot(self, event):
        """Pause/resume plot updates if the plot area is double clicked."""
        if event.dblclick:
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
