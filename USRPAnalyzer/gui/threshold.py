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


class threshold_txtctrl(wx.TextCtrl):
    """Input TxtCtrl for setting a threshold power level."""
    def __init__(self, frame, threshold):
        wx.TextCtrl.__init__(
            self, frame, id=wx.ID_ANY, size=(60, -1), style=wx.TE_PROCESS_ENTER
        )
        self.Bind(wx.EVT_TEXT_ENTER, threshold.set_level)
        if threshold.level:
            self.SetValue(str(threshold.level))


class threshold(object):
    """A horizontal line to indicate user-defined overload threshold."""
    def __init__(self, frame, level):
        self.frame = frame
        self.lines = []
        self.level = level # default level in dBm or None

    def set_level(self, event):
        """Set the level to a user input value."""
        evt_obj = event.GetEventObject()

        # remove current threshold line
        if self.lines:
            self.lines.pop(0).remove()

        threshold_txtctrl_value = evt_obj.GetValue()

        redraw_needed = False
        try:
            # will raise ValueError if not a number
            self.level = float(threshold_txtctrl_value)
            redraw_needed = True
        except ValueError:
            if threshold_txtctrl_value == "" and self.level is not None:
                # Let the user remove the threshold line
                redraw_needed = True
                self.level = None

        if redraw_needed:
            # plot the new threshold and add it to our blitted background
            self.lines = self.frame.subplot.plot(
                [self.frame.tb.min_freq-1e7, self.frame.tb.max_freq+1e7], # xs
                [self.level] * 2, # ys
                color='red',
                zorder = 90 # draw it above the grid lines
            )
            self.frame.canvas.draw()
            self.frame._update_background()

        evt_obj.SetValue(str(self.level) if self.level else "")

