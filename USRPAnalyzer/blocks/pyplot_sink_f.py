
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

    def update_line(self, points):
        xs, ys = points
        if (max(xs) > self.__x):
            for x, y in zip(*points):
                self.line.set_data(
                    np.append(self.line.get_xdata(), x),
                    np.append(self.line.get_ydata(), y)
                )
        else:
            # restarted sweep, clear line
            self.line.set_data(xs, ys)
            # log secs per sweep
            start_t = self.start_t
            self.start_t = stop_t = time.time()
            # Current benchmark ~42s/sweep
            self.logger.info("Completed sweep in {0} seconds".format(stop_t-start_t))

        self.__x = xs[-1]
        self.__y = ys[-1]

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

        #self.power_adjustment = -10*math.log10(power/tb.fft_size)
        self.bin_start = int(tb.fft_size * ((1 - 0.75) / 2))
        self.bin_stop = int(tb.fft_size - self.bin_start)

        self.nskipped = 0

    def work(self, input_items, output_items):
        noutput_items = 1
        ninput_items = len(input_items[0])

        # skip tune_delay frames for each retune
        skips_total = self.tb.tune_delay
        if self.nskipped < skips_total:
            # dump as many items from the input buffer as we can
            skips_left = skips_total - self.nskipped
            skips_this_cycle = min(ninput_items, skips_left)
            self.nskipped += skips_this_cycle
            return skips_this_cycle
        else:
            # reset and continue plotting
            self.nskipped = 0

        center_freq = self.tb.set_next_freq()
        y_points = input_items[0][0][self.bin_start:self.bin_stop]
        x_points = self.bin_freqs(y_points, center_freq)
        wx.CallAfter(self.app.frame.update_line, [x_points, y_points])

        return noutput_items

    def bin_freqs(self, y_points, center_freq):
        i_bin = lambda x: np.where(y_points==x)[0][0] + self.bin_start
        freqs = np.array([
            center_freq - (self.tb.usrp_rate / 2) +
            (self.tb.channel_bandwidth * i_bin(y)) for
            y in y_points
        ])
        return freqs

    def bin_freq(self, i_bin, center_freq):
        #hz_per_bin = tb.usrp_rate / tb.fft_size
        freq = center_freq - (self.tb.usrp_rate / 2) + (self.tb.channel_bandwidth * i_bin)
        return freq
