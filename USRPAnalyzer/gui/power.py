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
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(int(frame.min_power)))

    def update(self, event):
        """Set the min power set by the user."""
        try:
            newval = float(self.GetValue())
            self.frame.min_power = newval
            self.frame.format_ax
        except ValueError:
            pass

        self.frame.configure_mpl_plot(adjust_freq_range=False)
        self.SetValue(str(int(self.frame.min_power)))


class max_power_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the maximum power."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(int(frame.max_power)))

    def update(self, event):
        """Set the max power set by the user."""
        try:
            newval = float(self.GetValue())
            self.frame.max_power = newval
        except ValueError:
            pass

        self.frame.configure_mpl_plot(adjust_freq_range=False)
        self.SetValue(str(int(self.frame.max_power)))


def init_ctrls(frame):
    """Initialize gui controls for adjusting power range."""
    box = wx.StaticBox(frame, wx.ID_ANY, "Power Range (dBm)")
    ctrls = wx.StaticBoxSizer(box, wx.VERTICAL)
    low_txt = wx.StaticText(frame, wx.ID_ANY, "low: ")
    high_txt = wx.StaticText(frame, wx.ID_ANY, "high: ")
    grid = wx.FlexGridSizer(rows=2, cols=2)
    grid.Add(high_txt, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
    grid.Add(max_power_txtctrl(frame), flag=wx.BOTTOM, border=5)
    grid.Add(low_txt, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
    grid.Add(min_power_txtctrl(frame), flag=wx.ALIGN_RIGHT)
    ctrls.Add(grid, flag=wx.ALL|wx.EXPAND, border=5)

    return ctrls
