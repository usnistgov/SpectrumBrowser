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


class export_time_data_btn(wx.ToggleButton):
    """A toggle button to export I/Q data to a file."""
    def __init__(self, frame):
        wx.ToggleButton.__init__(
            self, frame, wx.ID_ANY, label="Time data"#, style=wx.BU_EXACTFIT
        )
        self.Bind(wx.EVT_BUTTON, frame.export_time_data)


class export_fft_data_btn(wx.ToggleButton):
    """A toggle button to export FFT data to a file."""
    def __init__(self, frame):
        wx.ToggleButton.__init__(
            self, frame, wx.ID_ANY, label="FFT data"#, style=wx.BU_EXACTFIT
        )
        self.Bind(wx.EVT_BUTTON, frame.export_fft_data)


class ctrls(object):
    def __init__(self, frame):
        """Initialize gui controls for exporting data to a file"""
        ctrl_label = wx.StaticBox(frame, wx.ID_ANY, "Export")
        self.layout = wx.StaticBoxSizer(ctrl_label, wx.VERTICAL)
        grid = wx.GridSizer(rows=2, cols=1)
        self.time_btn = export_time_data_btn(frame)
        self.fft_btn = export_fft_data_btn(frame)
        grid.Add(self.time_btn)
        grid.Add(self.fft_btn)
        self.layout.Add(grid, flag=wx.ALL, border=5)
