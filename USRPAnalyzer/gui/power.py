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


class min_power_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the minimum power."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_KILL_FOCUS, self.update)
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.set_value()

    def update(self, event):
        """Set the min power set by the user."""
        try:
            newval = float(self.GetValue())
        except ValueError:
            self.set_value()
            return

        if newval != self.frame.min_power:
            self.frame.min_power = newval
            self.frame.format_axis()

        self.set_value()

    def set_value(self):
        self.SetValue(str(int(self.frame.min_power)))


class max_power_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the maximum power."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_KILL_FOCUS, self.update)
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.set_value()

    def update(self, event):
        """Set the max power set by the user."""
        try:
            newval = float(self.GetValue())
        except ValueError:
            self.set_value()
            return

        if newval != self.frame.max_power:
            self.frame.max_power = newval
            self.frame.format_axis()

        self.set_value()

    def set_value(self):
        self.SetValue(str(int(self.frame.max_power)))


class ctrls(object):
    def __init__(self, frame):

        """Initialize gui controls for adjusting power range."""
        box = wx.StaticBox(frame, wx.ID_ANY, "Power Range (dBm)")
        self.layout = wx.StaticBoxSizer(box, wx.VERTICAL)
        low_txt = wx.StaticText(frame, wx.ID_ANY, "low: ")
        high_txt = wx.StaticText(frame, wx.ID_ANY, "high: ")
        self.max_power_txtctrl = max_power_txtctrl(frame)
        self.min_power_txtctrl = min_power_txtctrl(frame)
        grid = wx.FlexGridSizer(rows=2, cols=2)
        grid.Add(high_txt, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.max_power_txtctrl, flag=wx.BOTTOM, border=5)
        grid.Add(low_txt, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.min_power_txtctrl, flag=wx.ALIGN_RIGHT)
        self.layout.Add(grid, flag=wx.ALL|wx.EXPAND, border=5)
