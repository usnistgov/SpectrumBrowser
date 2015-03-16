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
import threading

from gui.main import wxpygui_frame

class plot_interface(object):
    def __init__(self, tb):
        self.tb = tb
        self.app = wx.App()
        self.app.frame = wxpygui_frame(tb)
        self.app.frame.Show()
        self.gui = threading.Thread(target=self.app.MainLoop)

        self.redraw_plot = threading.Event()

        self.gui.daemon = True
        self.gui.start()

    def keep_alive(self):
        return self.update(None)

    def update(self, points):
        # if we don't have points to plot, just keep gui alive
        keep_alive = points is None
        redraw = self.redraw_plot.is_set() and not keep_alive
        try:
            if self.app.frame.closed:
                return False
            wx.CallAfter( # thread-safe call to wx gui
                self.app.frame.update_plot,
                points,
                redraw,
                keep_alive
            )
            if redraw:
                self.redraw_plot.clear()
            return True
        except wx._core.PyDeadObjectError:
            return False

    def is_alive(self):
        try:
            if self.app.frame.closed:
                return False
            return True
        except wx._core.PyDeadObjectError:
            return False

    def set_gui_idle(self):
        self.tb.copy_if_gui_idle.set_enabled(True)
