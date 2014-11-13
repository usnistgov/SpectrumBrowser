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


class min_freq_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the minimum frequency."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(frame.tb.pending_config.min_freq / 1e6))

    def update(self, event):
        """Set the min freq set by the user."""
        try:
            newval = float(self.GetValue())
            self.frame.tb.pending_config.min_freq = newval * 1e6
            self.frame.tb.reconfigure = True
        except ValueError:
            pass

        self.frame.tb.pending_config.update_freq_range()
        self.SetValue(str(self.frame.tb.pending_config.min_freq / 1e6))


class max_freq_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the maximum frequency."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(frame.tb.pending_config.max_freq / 1e6))

    def update(self, event):
        """Set the max freq set by the user."""
        try:
            newval = float(self.GetValue())
            self.frame.tb.pending_config.max_freq = newval * 1e6
            self.frame.tb.reconfigure = True
        except ValueError:
            pass

        self.frame.tb.pending_config.update_freq_range()
        self.SetValue(str(self.frame.tb.pending_config.max_freq / 1e6))


def init_ctrls(frame):
    """Initialize gui controls for adjusting frequency range."""
    box = wx.StaticBox(frame, wx.ID_ANY, "Freq Range (MHz)")
    ctrls = wx.StaticBoxSizer(box, wx.VERTICAL)
    ctrls.Add(min_freq_txtctrl(frame), flag=wx.ALL, border=5)
    ctrls.Add(max_freq_txtctrl(frame), flag=wx.ALL, border=5)
    return ctrls
