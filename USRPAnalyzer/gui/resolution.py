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


class sample_rate_dropdown(wx.ComboBox):
    """Dropdown for selecting available sample rates."""
    def __init__(self, frame, rbw_txt):
        self.frame = frame
        self.rbw_txt = rbw_txt

        self.rate_to_str = {}

        # Add native USRP rates above 1MS/s
        for rate in frame.tb.sample_rates:
            if rate > 1e6:
                self.rate_to_str[rate] = "{:.2f} MS/s".format(rate/1e6)

        # Add LTE rates
        for rate in frame.tb.lte_rates:
            self.rate_to_str[rate] = "{:.2f} MS/s".format(rate/1e6)

        # okay since we should have a 1:1 mapping
        self.str_to_rate = {v: k for k, v in self.rate_to_str.items()}

        numeric_sort = lambda s:float(
            ''.join(c for c in s if c.isdigit() or c == '.')
        )
        rate_strs = self.str_to_rate.keys()
        wx.ComboBox.__init__(
            self, frame, id=wx.ID_ANY,
            choices=sorted(rate_strs, key=numeric_sort),
            style=wx.CB_READONLY
        )

        # Size the dropdown based on longest string
        width, height = self.GetSize()
        dc = wx.ClientDC(self)
        tsize = max(dc.GetTextExtent(s)[0] for s in rate_strs)
        self.SetMinSize((tsize+50, height))

        self.SetStringSelection(
            self.rate_to_str[self.frame.tb.sample_rate]
        )

        self.Bind(wx.EVT_COMBOBOX, self.update)

    def update(self, event):
        """Set the sample rate selected by the user via dropdown."""
        self.frame.tb.pending_cfg.sample_rate = self.str_to_rate[self.GetValue()]
        self.frame.tb.pending_cfg.update_frequencies()
        self.frame.tb.reconfigure = True
        self.rbw_txt.update()


class resolution_bandwidth_txt(wx.StaticText):
    """Text to display the calculated resolution bandwidth in kHz."""
    def __init__(self, frame):
        wx.StaticText.__init__(self, frame, id=wx.ID_ANY, label="")
        self.frame = frame
        self.format_str = "{:.1f} kHz"
        self.update()

    def update(self):
        rbw = float(self.frame.tb.pending_cfg.channel_bandwidth) / 1e3
        self.SetLabel(self.format_str.format(rbw))


class fftsize_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a new fft size."""
    def __init__(self, frame, rbw_txt):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.rbw_txt = rbw_txt
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(frame.tb.pending_cfg.fft_size))

    def update(self, event):
        """Set the sample rate selected by the user via dropdown."""
        try:
            newval = int(self.GetValue())
            self.frame.tb.pending_cfg.set_fft_size(newval)
            self.frame.tb.pending_cfg.update_window()
            self.frame.tb.pending_cfg.update_frequencies()
            self.frame.tb.reconfigure = True
            self.rbw_txt.update()
        except ValueError:
            pass

        self.SetValue(str(self.frame.tb.pending_cfg.fft_size))

def init_ctrls(frame):
    """Initialize gui controls for resolution."""
    ctrl_label = wx.StaticBox(frame, wx.ID_ANY, "Resolution")
    ctrls = wx.StaticBoxSizer(ctrl_label, wx.VERTICAL)
    grid = wx.FlexGridSizer(rows=3, cols=2)
    rbw_label_txt = wx.StaticText(frame, wx.ID_ANY, "RBW: ")
    rbw_txt = resolution_bandwidth_txt(frame)
    samp_rate_label_txt = wx.StaticText(frame, wx.ID_ANY, "Sample Rate: ")
    samp_rate_dd = sample_rate_dropdown(frame, rbw_txt)
    fft_label_txt = wx.StaticText(frame, wx.ID_ANY, "FFT size (bins): ")
    fft_txt = fftsize_txtctrl(frame, rbw_txt)
    grid.Add(
        samp_rate_label_txt,
        proportion=0,
        flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
    )
    grid.Add(
        samp_rate_dd,
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
        rbw_label_txt,
        proportion=0,
        flag=wx.ALIGN_LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL,
        border=5
    )
    grid.Add(
        rbw_txt,
        proportion=0,
        flag=wx.ALIGN_RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL,
        border=5
    )
    ctrls.Add(grid, flag=wx.ALL, border=5)

    return ctrls
