
import time
import logging
import numpy as np
import matplotlib
# This must be set before import pylab
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt

from gnuradio import gr


class pyplot_sink_f(gr.sync_block):
    def __init__(self, tb, in_size):
        gr.sync_block.__init__(
            self,
            name = "pyplot_sink_f",
            in_sig = [(np.float32, in_size)], # numpy array (vector) of floats, len fft_size
            out_sig = []
        )

        self.tb = tb

        self.logger = logging.getLogger('USRPAnalyzer.pyplot_sink_f')

        fig = plt.figure()

        # gui event handlers
        fig.canvas.mpl_connect('close_event', self.onclose)
        fig.canvas.mpl_connect('button_press_event', self.onclick)
        fig.canvas.mpl_connect('scroll_event', self.onzoom)

        self.zoom_scale = 1.5

        plt.xlabel('Frequency(GHz)')
        plt.ylabel('Power')
        plt.xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        plt.ylim(-120,0)
        plt.yticks(np.arange(-130,0,10))
        plt.xticks(np.arange(self.tb.min_freq, self.tb.max_freq+1,1e8))
        plt.grid(color='.90', linestyle='-', linewidth=1)
        plt.title('Power Spectrum Density')

        self.line, = plt.plot([])
        self.__x = 0
        self.__y = 0

        plt.ion()

        #self.power_adjustment = -10*math.log10(power/tb.fft_size)
        self.bin_start = int(tb.fft_size * ((1 - 0.75) / 2))
        self.bin_stop = int(tb.fft_size - self.bin_start)

        self.start_t = time.time()
        self.nskipped = 0

    def work(self, input_items, output_items):
        noutput_items = 1

        # skip tune_delay frames for each retune
        skip = self.tb.tune_delay
        if self.nskipped <= skip:
            # report that we've handled this item, but don't plot it
            self.nskipped += 1
            return noutput_items
        else:
            # reset and continue plotting
            self.nskipped = 0
            self.tb.rf_retuned = False

        center_freq = self.tb.set_next_freq()

        in_vect = input_items[0][0]
        x = []
        y = []

        for i_bin in range(self.bin_start, self.bin_stop):
            freq = self.bin_freq(i_bin, center_freq)

            dBm = in_vect[i_bin]

            if (dBm > self.tb.squelch_threshold) and (freq >= self.tb.min_freq) and (freq <= self.tb.max_freq):
                x.append(freq)
                y.append(dBm)

        self.logger.info("PLOTTING CENTER FREQ: {0} GHz WITH MAX: {1} dB".format(
            round(center_freq/1e9, 5), int(max(y))
        ))

        x_point = x[y.index(max(y))]
        y_point = max(y)
        self.update_line([x_point, y_point])

        return noutput_items

    def update_line(self, xypair):
        if not plt.isinteractive():
            plt.pause(1) # keep plot alive
            return False

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

        plt.pause(0.005) # let pyplot update and stay responsive
        self.__x = x
        self.__y = y

        return True

    def onclick(self, event):
        self.logger.debug("button={button}, dblclick={dblclick}, xdata={xdata}, ydata={ydata}".format(
            **event.__dict__
        ))
        if event.dblclick:
            plt.interactive(not plt.isinteractive())
            self.logger.debug("plt is {0}".format("interactive" if plt.isinteractive() else "not interactive"))


    def onclose(self, event):
        self.logger.debug("GUI window caught close event")
        self.tb.stop()

    def onzoom(self, event):
        """http://stackoverflow.com/a/11562898"""

        # get the current x and y limits
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1/self.zoom_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = self.zoom_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            # FIXME: logging
            print event.button
        # set new limits
        self.ax.set_xlim([xdata - cur_xrange*scale_factor,
                     xdata + cur_xrange*scale_factor])
        self.ax.set_ylim([ydata - cur_yrange*scale_factor,
                     ydata + cur_yrange*scale_factor])
        plt.draw() # force re-draw

    def bin_freq(self, i_bin, center_freq):
        #hz_per_bin = tb.usrp_rate / tb.fft_size
        freq = center_freq - (self.tb.usrp_rate / 2) + (self.tb.channel_bandwidth * i_bin)
        return freq

