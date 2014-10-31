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


class lo_offset_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the LO offset."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(frame.tb.pending_config.lo_offset / 1e6))

    def update(self, event):
        """Set the sample rate selected by the user via dropdown."""
        try:
            newval = int(self.GetValue())
            self.frame.tb.pending_config.lo_offset = newval * 1e6
            self.frame.tb.reconfigure = True
        except ValueError:
            pass
            
        self.SetValue(str(self.frame.tb.pending_config.lo_offset / 1e6))
