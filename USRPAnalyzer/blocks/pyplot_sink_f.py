
import time
import threading
import wx
import logging
import numpy as np
import matplotlib
# This must be set before import pylab
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

from gnuradio import gr


class wxpygui_frame(wx.Frame):
    def __init__(self, tb):
        wx.Frame.__init__(self, None, -1, "USRPAnalyzer") # TODO: what's going on here?
        self.tb = tb

        self.main_panel = wx.Panel(self)
        self.notebook = wx.Notebook(self.main_panel)
        
        self.live_page = self.create_live_page()
        self.notebook.AddPage(self.live_page, "Live")

        sizer = wx.BoxSizer()
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.main_panel.SetSizer(sizer)
        sizer.Fit(self)

        self.logger = logging.getLogger('USRPAnalyzer.wxpygui_frame')

        # gui event handlers
        self.Bind(wx.EVT_CLOSE, self.close)

        #fig.canvas.mpl_connect('button_press_event', self.onclick)
        #fig.canvas.mpl_connect('scroll_event', self.onzoom)

        self.start_t = time.time()

    def create_main_panel(self):
        
        return main_panel

    def create_live_page(self):
        live_page = wx.Panel(self.notebook)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(live_page, 01, self.fig)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Frequency(GHz)')
        self.ax.set_ylabel('Power')
        self.ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        self.ax.set_ylim(-120,0)
        self.ax.set_xticks(np.arange(self.tb.min_freq, self.tb.max_freq+1,1e8))
        self.ax.set_yticks(np.arange(-130,0,10))
        self.ax.grid(color='.90', linestyle='-', linewidth=1)
        self.ax.set_title('Power Spectrum Density')

        self.line, = self.ax.plot([])
        self.__x = 0
        self.__y = 0

        return live_page

    def update_line(self, xypair):
        x, y = xypair
        if x > self.__x:
            self.line.set_data(
                np.append(self.line.get_xdata(), x),
                np.append(self.line.get_ydata(), y)
            )
        else:
            # restarted sweep, clear line
            self.line.set_data([x], [y])
            # log secs per sweep
            start_t = self.start_t
            self.start_t = stop_t = time.time()
            # Current benchmark ~42s/sweep
            self.logger.info("Completed sweep in {0} seconds".format(stop_t-start_t))

        #plt.pause(0.005) # let pyplot update and stay responsive
        self.__x = x
        self.__y = y

        self.ax.figure.canvas.draw()

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

        in_vect = input_items[0][0][self.bin_start:self.bin_stop]
        y_point = max(in_vect)
        i_bin = np.where(in_vect==y_point)[0]+self.bin_start
        x_point = self.bin_freq(i_bin, center_freq)
        wx.CallAfter(self.app.frame.update_line, [x_point, y_point])

        return noutput_items


    def bin_freq(self, i_bin, center_freq):
        #hz_per_bin = tb.usrp_rate / tb.fft_size
        freq = center_freq - (self.tb.usrp_rate / 2) + (self.tb.channel_bandwidth * i_bin)
        return freq

