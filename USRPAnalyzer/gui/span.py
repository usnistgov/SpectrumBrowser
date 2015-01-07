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


class span_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for adjusting the span."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(frame.tb.pending_cfg.span / 1e6))

    def update(self, event):
        """Set the max freq set by the user."""
        evt_obj = event.GetEventObject()
        txtctrl_value = evt_obj.GetValue()

        try:
            newval = float(txtctrl_value)
            self.frame.tb.pending_cfg.requested_span = newval * 1e6
            self.frame.tb.reconfigure = True
        except ValueError:
            if txtctrl_value == "":
                self.frame.tb.pending_cfg.requested_span = None
                self.frame.tb.reconfigure = True

        self.frame.tb.pending_cfg.update_frequencies()
        self.SetValue(str(self.frame.tb.pending_cfg.span / 1e6))


def init_ctrls(frame):
    """Initialize gui controls for adjusting span."""
    box = wx.StaticBox(frame, wx.ID_ANY, "Span (MHz)")
    ctrls = wx.StaticBoxSizer(box, wx.HORIZONTAL)
    ctrls.Add(span_txtctrl(frame), flag=wx.ALL, border=5)
    return ctrls
