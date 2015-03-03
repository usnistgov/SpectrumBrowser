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

import utils


class sample_rate_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a new sample rate"""
    def __init__(self, frame, deltaf_txt):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.deltaf_txt = deltaf_txt
        self.Bind(wx.EVT_KILL_FOCUS, self.update)
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.format_str = "{:.1f}"
        self.set_value()

    def update(self, event):
        """Set the nearest matching sample rate"""
        val = self.GetValue()
        try:
            float_val = float(val) * 1e6
        except ValueError:
            self.set_value()
            return

        otw_format = self.frame.tb.pending_cfg.wire_format
        if otw_format == "sc16" and float_val >= 25e6:
            # That makes USRP very unhappy
            float_val = 25e6

        rates = self.frame.tb.sample_rates
        nearest_idx = utils.find_nearest(rates, float_val)
        rate = rates[nearest_idx]

        if rate != self.frame.tb.pending_cfg.sample_rate:
            self.frame.tb.pending_cfg.sample_rate = rate
            self.frame.tb.pending_cfg.update()
            self.frame.tb.reconfigure()
            self.deltaf_txt.update()

        self.set_value()

    def set_value(self):
        self.SetValue(
            self.format_str.format(self.frame.tb.pending_cfg.sample_rate / 1e6)
        )


class deltaf_statictxt(wx.StaticText):
    """Text to display the calculated delta f in kHz."""
    def __init__(self, frame):
        wx.StaticText.__init__(self, frame, id=wx.ID_ANY, label="")
        self.frame = frame
        self.format_str = "{:.1f} kHz"
        self.update()

    def update(self):
        deltaf = float(self.frame.tb.pending_cfg.RBW) / 1e3
        self.SetLabel(self.format_str.format(deltaf))


class fftsize_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a new fft size."""
    def __init__(self, frame, deltaf_txt):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.deltaf_txt = deltaf_txt
        self.Bind(wx.EVT_KILL_FOCUS, self.update)
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.set_value()

    def update(self, event):
        """Set the FFT size in bins."""
        try:
            newval = int(self.GetValue())
        except ValueError:
            self.set_value()
            return

        if newval != self.frame.tb.pending_cfg.fft_size:
            self.frame.tb.pending_cfg.set_fft_size(newval)
            current_window = self.frame.tb.pending_cfg.window
            self.frame.tb.pending_cfg.set_window(current_window)
            self.frame.tb.pending_cfg.update()
            self.frame.tb.reconfigure()
            self.deltaf_txt.update()

        self.set_value()

    def set_value(self):
        self.SetValue(str(self.frame.tb.pending_cfg.fft_size))


class ctrls(object):
    def __init__(self, frame):
        """Initialize gui controls for resolution."""
        ctrl_label = wx.StaticBox(frame, wx.ID_ANY, "Resolution")
        self.layout = wx.StaticBoxSizer(ctrl_label, wx.VERTICAL)
        grid = wx.FlexGridSizer(rows=3, cols=2)
        deltaf = u"\u0394" + "f: "
        deltaf_label_txt = wx.StaticText(frame, wx.ID_ANY, deltaf)
        deltaf_txt = deltaf_statictxt(frame)
        samp_rate_label_txt = wx.StaticText(frame, wx.ID_ANY, "Sample Rate (MS/s): ")
        samp_rate_txt = sample_rate_txtctrl(frame, deltaf_txt)
        fft_label_txt = wx.StaticText(frame, wx.ID_ANY, "FFT size (bins): ")
        fft_txt = fftsize_txtctrl(frame, deltaf_txt)
        grid.Add(
            samp_rate_label_txt,
            proportion=0,
            flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        )
        grid.Add(
            samp_rate_txt,
            proportion=0,
            flag=wx.ALIGN_RIGHT
        )
        grid.Add(
            fft_label_txt,
            proportion=0,
            flag=wx.ALIGN_LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL,
            border=5
        )
        grid.Add(
            fft_txt,
            proportion=0,
            flag=wx.ALIGN_RIGHT|wx.TOP,
            border=5
        )
        grid.Add(
            deltaf_label_txt,
            proportion=0,
            flag=wx.ALIGN_LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL,
            border=5
        )
        grid.Add(
            deltaf_txt,
            proportion=0,
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL,
            border=5
        )
        self.layout.Add(grid, flag=wx.ALL, border=5)
