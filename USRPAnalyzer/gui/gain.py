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


class atten_txtctrl(wx.TextCtrl):
    """Input TextCtrl for setting attenuation."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1) , style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_atten)
        self.SetValue(str(frame.tb.get_attenuation()))

    def set_atten(self, event):
        val = self.GetValue()
        try:
            float_val = float(val)
            self.frame.tb.set_attenuation(float_val)
        except ValueError:
            # If we can't cast to float, just reset at current value
            pass
        actual_val = self.frame.tb.get_attenuation()
        self.SetValue(str(actual_val))


class ADC_digi_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting ADC digital gain."""
    def __init__(self, frame):
        wx.TextCtrl.__init__(
            self, frame, wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_ADC_digital_gain)
        self.SetValue(str(frame.tb.get_ADC_digital_gain()))

    def set_ADC_digital_gain(self, event):
        val = self.GetValue()
        try:
            float_val = float(val)
            self.frame.tb.set_ADC_gain(float_val)
        except ValueError:
            # If we can't cast to float, just reset at current value
            pass
        actual_val = self.frame.tb.get_gain()
        self.SetValue(str(actual_val))


def init_ctrls(frame):
    """Initialize gui controls for gain."""
    ctrl_box = wx.StaticBox(frame, wx.ID_ANY, "Gain (dB)")
    ctrls = wx.StaticBoxSizer(ctrl_box, wx.VERTICAL)
    grid = wx.FlexGridSizer(rows=2, cols=2)
    # Attenuation
    atten_txt = wx.StaticText(frame, wx.ID_ANY, "Atten: ")
    atten_hbox = wx.BoxSizer(wx.HORIZONTAL)
    atten_hbox.Add(
        atten_txtctrl(frame), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL
    )
    # ADC digi gain
    ADC_txt = wx.StaticText(frame, wx.ID_ANY, "ADC digi: ")
    grid.Add(atten_txt, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
    grid.Add(atten_hbox, flag=wx.BOTTOM, border=5)
    grid.Add(ADC_txt, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
    grid.Add(ADC_digi_txtctrl(frame), flag=wx.ALIGN_RIGHT)
    ctrls.Add(grid, flag=wx.ALL, border=5)

    return ctrls
