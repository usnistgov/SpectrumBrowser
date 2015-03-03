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


class center_freq_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the center frequency."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.Bind(wx.EVT_KILL_FOCUS, self.update)
        self.set_value()

    def update(self, event):
        """Set the min freq set by the user."""
        try:
            float_val = float(self.GetValue()) * 1e6
        except ValueError:
            self.set_value()
            return

        if float_val != self.frame.tb.pending_cfg.center_freq:
            self.frame.tb.pending_cfg.center_freq = float_val
            self.frame.tb.pending_cfg.update()
            self.frame.tb.reconfigure(redraw_plot=True)

        self.set_value()

    def set_value(self):
        self.SetValue(str(self.frame.tb.pending_cfg.center_freq / 1e6))


class ctrls(object):
    def __init__(self, frame):
        """Initialize gui controls for adjusting frequency range."""
        box = wx.StaticBox(frame, wx.ID_ANY, "Frequency (MHz)")
        self.center_freq_txtctrl = center_freq_txtctrl(frame)
        self.layout = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        self.layout.Add(self.center_freq_txtctrl, flag=wx.ALL, border=5)
