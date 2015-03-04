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


class wirefmt_dropdown(wx.ComboBox):
    """Dropdown for setting the USRP's wire format."""
    def __init__(self, frame, args):
        self.frame = frame
        self.args_txtctrl = args

        formats = ("sc8", "sc16")

        wx.ComboBox.__init__(
            self, frame, id=wx.ID_ANY,
            choices=formats,
            style=wx.CB_READONLY
        )

        # Size the dropdown based on longest string
        width, height = self.GetSize()
        dc = wx.ClientDC(self)
        tsize = max(dc.GetTextExtent(s)[0] for s in formats)
        self.SetMinSize((tsize+45, height))

        self.SetStringSelection(
            self.frame.tb.cfg.wire_format
        )
        self.Bind(wx.EVT_COMBOBOX, self.update)

    def update(self, event):
        """Set the window function selected by the user via dropdown."""
        fmt = self.GetValue()
        self.frame.tb.pending_cfg.set_wire_format(fmt)
        self.frame.tb.reconfigure(reset_stream_args=True)

        if fmt == "sc8":
            self.args_txtctrl.Enable(True)
        else:
            self.args_txtctrl.Enable(False)


class args_txtctrl(wx.TextCtrl):
    """Input TextCtrl for setting stream args."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1) , style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_KILL_FOCUS, self.update)
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(frame.tb.cfg.stream_args)

        if frame.tb.cfg.wire_format != "sc8":
            self.Enable(False)

    def update(self, event):
        args = self.GetValue()

        if args != self.frame.tb.pending_cfg.stream_args:
            self.frame.tb.pending_cfg.stream_args = str(args)
            self.frame.tb.reconfigure(reset_stream_args=True)

        self.SetValue(self.frame.tb.pending_cfg.stream_args)


class ctrls(object):
    def __init__(self, frame):
        """Initialize gui controls for stream args."""
        ctrl_label = wx.StaticBox(frame, wx.ID_ANY, "Stream Settings")
        self.layout = wx.StaticBoxSizer(ctrl_label, wx.VERTICAL)
        grid = wx.FlexGridSizer(rows=2, cols=2)
        args_label_txt = wx.StaticText(frame, wx.ID_ANY, "Args: ")
        self.args_txt = args_txtctrl(frame)
        wirefmt_label_txt = wx.StaticText(frame, wx.ID_ANY, "Wire Fmt: ")
        self.wirefmt_dd = wirefmt_dropdown(frame, self.args_txt)
        grid.Add(
            wirefmt_label_txt,
            proportion=0,
            flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        )
        grid.Add(
            self.wirefmt_dd,
            proportion=0,
            flag=wx.ALIGN_RIGHT
        )
        grid.Add(
            args_label_txt,
            proportion=0,
            flag=wx.ALIGN_LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL,
            border=5
        )
        grid.Add(
            self.args_txt,
            proportion=1,
            flag=wx.ALIGN_RIGHT|wx.TOP|wx.EXPAND,
            border=5
        )
        self.layout.Add(grid, flag=wx.ALL, border=5)
