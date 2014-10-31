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
    def __init__(self, frame):
        self.frame = frame

        self.rate_to_str = {}
        for rate in frame.tb.sample_rates:
            if rate > 1e6:
                self.rate_to_str[rate] = "{:.1f} MS/s".format(rate/1e6)
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
            self.rate_to_str[self.frame.tb.config.sample_rate]
        )

        self.Bind(wx.EVT_COMBOBOX, self.update)
        
    def update(self, event):
        """Set the sample rate selected by the user via dropdown."""
        self.frame.tb.pending_config.sample_rate = self.str_to_rate[self.GetValue()]
        self.frame.tb.pending_config.update_channel_bandwidth()
        self.frame.tb.reconfigure = True
        self.frame.rbw_txt.update()
        

class resolution_bandwidth_txt(wx.StaticText):
    """Text to display the calculated resolution bandwidth in kHz."""
    def __init__(self, frame):
        wx.StaticText.__init__(self, frame, id=wx.ID_ANY, label="")
        self.frame = frame
        self.format_str = "{:.1f} kHz"
        self.update()

    def update(self):
        rbw = float(self.frame.tb.pending_config.channel_bandwidth) / 1e3  
        self.SetLabel(self.format_str.format(rbw))

        
class fftsize_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a new fft size."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.update)
        self.SetValue(str(frame.tb.pending_config.fft_size))

    def update(self, event):
        """Set the sample rate selected by the user via dropdown."""
        try:
            newval = int(self.GetValue())
            self.frame.tb.pending_config.set_fft_size(newval)
            self.frame.tb.pending_config.update_channel_bandwidth()
            self.frame.tb.pending_config.update_window()
            self.frame.tb.reconfigure = True
            self.frame.rbw_txt.update()
        except ValueError:
            pass
            
        self.SetValue(str(self.frame.tb.pending_config.fft_size))

        
