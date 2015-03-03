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


import wx
import numpy as np

import utils


class mkr_peaksearch_btn(wx.Button):
    """A button to move the marker to the current peak power."""
    def __init__(self, frame, marker, txtctrl):
        wx.Button.__init__(
            self, frame, wx.ID_ANY, "Peak", style=wx.BU_EXACTFIT
        )
        self.Bind(
            wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.peak_search(evt, txt)
        )


class mkr_left_btn(wx.Button):
    """A button to step the marker one bin to the left."""
    def __init__(self, frame, marker, txtctrl, label):
        wx.Button.__init__(
            self, frame, wx.ID_ANY, label=label, style=wx.BU_EXACTFIT
        )
        self.Bind(
            wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.step_left(evt, txt)
        )


class mkr_right_btn(wx.Button):
    """A button to step the marker one bin to the right."""
    def __init__(self, frame, marker, txtctrl, label):
        wx.Button.__init__(
            self, frame, wx.ID_ANY, label=label, style=wx.BU_EXACTFIT
        )
        self.Bind(
            wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.step_right(evt, txt)
        )


class mkr_clear_btn(wx.Button):
    """A button to clear the marker."""
    def __init__(self, frame, marker, txtctrl):
        wx.Button.__init__(
            self, frame, wx.ID_ANY, "Clear", style=wx.BU_EXACTFIT
        )
        self.Bind(
            wx.EVT_BUTTON, lambda evt, txt=txtctrl: marker.clear(evt, txt)
        )


class mkr_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a marker frequency."""
    def __init__(self, frame, marker, id_):
        wx.TextCtrl.__init__(self, frame, id=id_, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_KILL_FOCUS, marker.jump)
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
        bin_freqs = self.frame.tb.cfg.bin_freqs
        idx = self.frame.tb.cfg.find_nearest(bin_freqs, value)
        return (idx, bin_freqs[idx])

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

        bin_freqs = self.frame.tb.cfg.bin_freqs
        idx = utils.find_nearest(bin_freqs, temp_freq)
        freq = bin_freqs[idx]

        if freq != self.freq:
            self.bin_idx = idx
            self.freq = freq
            self.plot()

        evt_obj.SetValue(self.get_freq_str())

    def get_freq_str(self):
        """Format the current marker's freq with 2 digits precision."""
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
                visible = False # marker is invisible until update_line sets y
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
        """Step the marker 1 bin to the left."""
        if self.bin_idx: #is not None or 0
            self.bin_idx -= 1
            self.freq = self.frame.tb.cfg.bin_freqs[self.bin_idx]
            txtctrl.SetValue(self.get_freq_str())
            self.plot()

    def step_right(self, event, txtctrl):
        """Step the marker 1 bin to the right."""
        if (self.bin_idx is not None and
            self.bin_idx < len(self.frame.tb.cfg.bin_freqs) - 1):

            self.bin_idx += 1
            self.freq = self.frame.tb.cfg.bin_freqs[self.bin_idx]
            txtctrl.SetValue(self.get_freq_str())
            self.plot()

    def clear(self, event, txtctrl):
        """Clear a marker."""
        self.unplot()
        txtctrl.Clear()

    def peak_search(self, event, txtctrl):
        """Find the point of max power in the whole plot or within a span."""
        bin_freqs = self.frame.tb.cfg.bin_freqs
        if self.frame.span_left and self.frame.span_right:
            left_idx = utils.find_nearest(bin_freqs, self.frame.span_left)
            right_idx = utils.find_nearest(bin_freqs, self.frame.span_right)
            power_data = self.frame.line.get_ydata()[left_idx:right_idx]
        else:
            left_idx = 0
            right_idx = utils.find_nearest(bin_freqs, self.frame.tb.cfg.max_freq)
            power_data = self.frame.line.get_ydata()[:right_idx]
        try:
            relative_idx = np.where(power_data == np.amax(power_data))[0][0]
        except ValueError:
            # User selected an area with no data in it; do nothing
            return
        # add the left index offset to get the absolute index
        self.bin_idx = relative_idx + left_idx
        self.freq = self.frame.tb.cfg.bin_freqs[self.bin_idx]
        txtctrl.SetValue(self.get_freq_str())
        self.plot()


class mkr1_ctrls(object):
    def __init__(self, frame):
        """Initialize gui controls for mkr1."""
        mkr1 = frame.mkr1
        mkr1_txtctrl = mkr_txtctrl(frame, mkr1, 1)
        mkr1_box = wx.StaticBox(frame, wx.ID_ANY, "Marker 1 (MHz)")
        self.layout = wx.StaticBoxSizer(mkr1_box, wx.VERTICAL)
        self.layout.Add(
            mkr_peaksearch_btn(frame, mkr1, mkr1_txtctrl),
            proportion=0,
            flag=wx.ALL|wx.ALIGN_CENTER,
            border=5
        )
        mkr1_hbox = wx.BoxSizer(wx.HORIZONTAL)
        mkr1_hbox.Add(
            mkr_left_btn(frame, mkr1, mkr1_txtctrl, '<'),
            flag=wx.LEFT,
            border=5
        )
        mkr1_hbox.Add(
            mkr1_txtctrl,
            proportion=1,
            flag=wx.EXPAND,
            border=1
        )
        mkr1_hbox.Add(
            mkr_right_btn(frame, mkr1, mkr1_txtctrl, '>'),
            flag=wx.RIGHT,
            border=5
        )
        self.layout.Add(mkr1_hbox, flag=wx.ALIGN_CENTER)
        self.layout.Add(
            mkr_clear_btn(frame, mkr1, mkr1_txtctrl),
            proportion=0,
            flag=wx.ALL|wx.ALIGN_CENTER,
            border=5
        )


class mkr2_ctrls(object):
    def __init__(self, frame):
        """Initialize gui controls for mkr2."""
        mkr2 = frame.mkr2
        mkr2_txtctrl = mkr_txtctrl(frame, mkr2, 2)
        mkr2_box = wx.StaticBox(frame, wx.ID_ANY, "Marker 2 (MHz)")
        self.layout = wx.StaticBoxSizer(mkr2_box, wx.VERTICAL)
        self.layout.Add(
            mkr_peaksearch_btn(frame, mkr2, mkr2_txtctrl),
            proportion=0,
            flag=wx.ALL|wx.ALIGN_CENTER,
            border=5
        )
        mkr2_hbox = wx.BoxSizer(wx.HORIZONTAL)
        mkr2_hbox.Add(
            mkr_left_btn(frame, mkr2, mkr2_txtctrl, '<'),
            flag=wx.LEFT,
            border=5
        )
        mkr2_hbox.Add(
            mkr2_txtctrl,
            proportion=1,
            flag=wx.EXPAND,
            border=1
        )
        mkr2_hbox.Add(
            mkr_right_btn(frame, mkr2, mkr2_txtctrl, '>'),
            flag=wx.RIGHT,
            border=5
        )
        self.layout.Add(mkr2_hbox, flag=wx.ALIGN_CENTER)
        self.layout.Add(
            mkr_clear_btn(frame, mkr2, mkr2_txtctrl),
            proportion=0,
            flag=wx.ALL|wx.ALIGN_CENTER,
            border=5
        )
