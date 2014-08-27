
import time
import threading
import wx
import wx.aui
import logging
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

from gnuradio import gr


class wxpygui_frame(wx.Frame):
    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, size=(800,630), title="USRPAnalyzer")
        self.tb = tb
        self._mgr = wx.aui.AuiManager(self)

        self.main_panel = wx.Panel(self)
        self.notebook = wx.aui.AuiNotebook(self.main_panel)

        self.create_live_page()

        self.__x = 0
        self.__y = 0

        sizer = wx.BoxSizer()
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.main_panel.SetSizer(sizer)
        #sizer.Fit(self)

        self.logger = logging.getLogger('USRPAnalyzer.wxpygui_frame')

        # gui event handlers
        self.Bind(wx.EVT_CLOSE, self.close)

        self.live_fig.canvas.mpl_connect('button_press_event', self.live_fig_click)
        #fig.canvas.mpl_connect('scroll_event', self.onzoom)

        self.start_t = time.time()

    def create_live_page(self):
        self.live_page = wx.Panel(self.notebook)
        self.live_fig = Figure(figsize=(8, 6), dpi=100)
        self.live_ax = self.format_ax(self.live_fig.add_subplot(111))
        self.live_canvas = FigureCanvas(self.live_page, 01, self.live_fig)
        self.line, = self.live_ax.plot([])
        self.notebook.AddPage(self.live_page, "Live")

    def create_static_page(self):
        self.static_page = wx.Panel(self.notebook)
        self.static_fig = Figure(figsize=(8, 6), dpi=100)
        self.static_ax = self.format_ax(self.static_fig.add_subplot(111))
        self.static_canvas = FigureCanvas(self.static_page, 01, self.static_fig)
        self.static_line = self.static_ax.add_line(self.line)
        self.notebook.AddPage(self.static_page, "Static")
        # automatically switch to the newest created tab
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)

    def format_ax(self, ax):
        ax.set_xlabel('Frequency(GHz)')
        ax.set_ylabel('Power')
        ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        ax.set_ylim(-120,0)
        ax.set_xticks(np.arange(self.tb.min_freq, self.tb.max_freq+1,1e8))
        ax.set_yticks(np.arange(-130,0,10))
        ax.grid(color='.90', linestyle='-', linewidth=1)
        ax.set_title('Power Spectrum Density')

        return ax

    def live_fig_click(self, event):
        if event.dblclick:
            self.create_static_page()

    def update_line(self, points, reset):
        xs, ys = points
        if reset:
            # restarted sweep, clear line
            self.line.set_data(xs, ys)
            # log secs per sweep
            start_t = self.start_t
            self.start_t = stop_t = time.time()
            # Current benchmark ~42s/sweep
            self.logger.info("Completed sweep in {0} seconds".format(int(stop_t-start_t)))
        else:
            for x, y in zip(*points):
                self.line.set_data(
                    np.append(self.line.get_xdata(), x),
                    np.append(self.line.get_ydata(), y)
                )

        try:
            self.live_ax.figure.canvas.draw()
        except wx._core.PyDeadObjectError:
            self.close(None)

        return True

    def close(self, event):
        self.tb.stop()
        self.Destroy()


class pyplot_sink_f(gr.sync_block):
    def __init__(self, tb, in_size):
        gr.sync_block.__init__(
            self,
            name = "pyplot_sink_f",
            in_sig = [(np.float32, in_size)], # numpy array (vector) of floats, len fft_size
            out_sig = []
        )

        self.tb = tb

        self.app = wx.App()
        self.app.frame = wxpygui_frame(tb)
        self.app.frame.Show()
        self.gui = threading.Thread(target=self.app.MainLoop)
        self.gui.start()

        self.logger = logging.getLogger('USRPAnalyzer.pyplot_sink_f')

        self.skip = tb.tune_delay
        self.freq = self.last_freq = tb.set_next_freq() # initialize at min_center_freq
        self._bin_freqs = np.arange(self.tb.min_freq, self.tb.max_freq, self.tb.channel_bandwidth)

        self.bin_start = int(self.tb.fft_size * ((1 - 0.75) / 2))
        self.bin_stop = int(self.tb.fft_size - self.bin_start)
        self.bin_offset = self.tb.fft_size * .75 / 2

    def work(self, input_items, output_items):
        noutput_items = 1
        ninput_items = len(input_items[0])

        if self.skip:
            skipping = min(self.skip, ninput_items)
            self.skip -= skipping
            return skipping
        else:
            self.skip = self.tb.tune_delay

        y_points = input_items[0][0][self.bin_start:self.bin_stop]
        x_points = self.calc_x_points(self.freq)
        wx.CallAfter(self.app.frame.update_line, (x_points, y_points), self.freq < self.last_freq)
        self.last_freq = self.freq
        self.freq = self.tb.set_next_freq()

        return noutput_items

    def calc_x_points(self, center_freq):
        center_bin = np.where(self._bin_freqs==center_freq)[0][0]
        low_bin = center_bin - self.bin_offset
        high_bin = center_bin + self.bin_offset
        return self._bin_freqs[low_bin:high_bin]
