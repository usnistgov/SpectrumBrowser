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


class export_time_data_btn(wx.Button):
    """A button to export I/Q data to a file."""
    def __init__(self, frame):
        wx.Button.__init__(
            self, frame, wx.ID_ANY, label="Time data"#, style=wx.BU_EXACTFIT
        )
        self.Bind(wx.EVT_BUTTON, frame.export_time_data)


class export_fft_data_btn(wx.Button):
    """A button to export FFT data to a file."""
    def __init__(self, frame):
        wx.Button.__init__(
            self, frame, wx.ID_ANY, label="FFT data"#, style=wx.BU_EXACTFIT
        )
        self.Bind(wx.EVT_BUTTON, frame.export_fft_data)


def init_ctrls(frame):
    """Initialize gui controls for exporting data to a file"""
    ctrl_label = wx.StaticBox(frame, wx.ID_ANY, "Export")
    ctrls = wx.StaticBoxSizer(ctrl_label, wx.VERTICAL)
    grid = wx.GridSizer(rows=2, cols=1)
    grid.Add(export_time_data_btn(frame))
    grid.Add(export_fft_data_btn(frame))
    ctrls.Add(grid, flag=wx.ALL, border=5)

    return ctrls
