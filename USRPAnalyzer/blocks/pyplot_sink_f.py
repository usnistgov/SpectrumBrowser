import time
import wx
import logging
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter


class atten_txtctrl(wx.TextCtrl):
    def __init__(self, frame):
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_atten)
        self.SetValue(str(frame.tb.get_attenuation()))

    def set_atten(self, event):
        val = self.frame.atten_txtctrl.GetValue()
        try:
            float_val = float(val)
            self.frame.tb.set_attenuation(float_val)
        except ValueError:
            # If we can't cast to float, just reset at current value
            pass
        actual_val = self.frame.tb.get_attenuation()
        self.SetValue(str(actual_val))


class ADC_digi_txtctrl(wx.TextCtrl):
    def __init__(self, frame):
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_ADC_digital_gain)
        self.SetValue(str(frame.tb.get_ADC_digital_gain()))

    def set_ADC_digital_gain(self, event):
        val = self.frame.ADC_digi_txtctrl.GetValue()
        try:
            float_val = float(val)
            self.frame.tb.set_ADC_gain(float_val)
        except ValueError:
            # If we can't cast to float, just reset at current value
            pass
        actual_val = self.frame.tb.get_gain()
        self.SetValue(str(actual_val))


class threshold_txtctrl(wx.TextCtrl):
    def __init__(self, frame):
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_threshold)
        self.threshold = "-20" # default threshold in dBm
        self.threshold_lines = []
        self.SetValue(self.threshold)
        self.set_threshold(None)

    def set_threshold(self, event):
        # remove current threshold line
        if self.threshold_lines:
            self.threshold_lines.pop(0).remove()

        if event is None:
            # call from constructor, the TextCtrl isn't initialized yet
            threshold = self.threshold
        else:
            threshold = self.frame.threshold_txtctrl.GetValue()
            try:
                float(threshold) # will raise ValueError if not a number
            except ValueError:
                threshold = self.threshold # reset to last known good value

        # plot the new threshold and add it to our blitted background
        self.threshold_lines = self.frame.subplot.plot(
            [self.frame.tb.min_freq-1e7, self.frame.tb.max_freq+1e7], # x values
            [threshold] * 2, # y values
            color='r',  # red
            zorder = 99 # draw it above the grid lines
        )
        self.frame.canvas.draw()
        self.frame.update_background()

        self.SetValue(threshold)


class  wxpygui_frame(wx.Frame):
    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.init_plot()
        self.threshold_txtctrl = threshold_txtctrl(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plot)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.atten_txtctrl = atten_txtctrl(self)
        self.ADC_digi_txtctrl = ADC_digi_txtctrl(self)

        self.gain_ctrls = self.init_gain_ctrls()
        self.threshold_ctrls = self.init_threshold_ctrls()

        hbox.Add(self.gain_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.threshold_ctrls, 0, wx.ALL, 10)

        vbox.Add(hbox)
        self.SetSizer(vbox)
        self.Fit()

        self.logger = logging.getLogger('USRPAnalyzer.wxpygui_frame')

        # gui event handlers
        self.Bind(wx.EVT_CLOSE, self.close)

        self.canvas.mpl_connect('button_press_event', self.pause_plot)
        #fig.canvas.mpl_connect('scroll_event', self.onzoom)

        self.paused = False

        self.start_t = time.time()

    def init_gain_ctrls(self):
        # FIXME: add flexgridsizer
        gain_box = wx.StaticBox(self, wx.ID_ANY, "Gain")
        gain_ctrls = wx.StaticBoxSizer(gain_box, wx.VERTICAL)
        # Attenuation
        atten_hbox = wx.BoxSizer(wx.HORIZONTAL)
        atten_txt = wx.StaticText(self, wx.ID_ANY, "Atten: 31.5 -")
        atten_hbox.Add(atten_txt)
        atten_hbox.Add(self.atten_txtctrl)
        gain_ctrls.Add(atten_hbox)
        # ADC digi gain
        ADC_hbox = wx.BoxSizer(wx.HORIZONTAL)
        ADC_txt = wx.StaticText(self, wx.ID_ANY, "ADC digi:")
        ADC_hbox.Add(ADC_txt)
        ADC_hbox.Add(self.ADC_digi_txtctrl)
        gain_ctrls.Add(ADC_hbox)

        return gain_ctrls

    def init_threshold_ctrls(self):
        threshold_box = wx.StaticBox(self, wx.ID_ANY, "Threshold")
        threshold_ctrls = wx.StaticBoxSizer(threshold_box, wx.VERTICAL)
        threshold_hbox = wx.BoxSizer(wx.HORIZONTAL)
        threshold_txt = wx.StaticText(self, wx.ID_ANY, "dBm")
        threshold_hbox.Add(threshold_txt)
        threshold_hbox.Add(self.threshold_txtctrl)
        threshold_ctrls.Add(threshold_hbox)

        return threshold_ctrls

    def update_background(self):
        """Force update of the background."""
        self.plot_background = self.canvas.copy_from_bbox(self.subplot.bbox)

    def init_plot(self):
        self.plot = wx.Panel(self, wx.ID_ANY, size=(800,600))
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.plot, -1, self.figure)
        self.subplot = self.format_ax(self.figure.add_subplot(111))
        x_points = self.tb.bin_freqs
        # Just plot a straight line at -100dB to start
        self.line, = self.subplot.plot(
            x_points, [-100]*len(x_points), animated=True
        )
        self.canvas.draw()
        self.plot_background = None
        self.update_background()

    @staticmethod
    def format_mhz(x, pos):
        """Format x ticks (in Hz) to MHz with 0 decimal places."""
        return "{:.0f}".format(x / float(1e6))

    def format_ax(self, ax):
        xaxis_formatter = FuncFormatter(self.format_mhz)
        ax.xaxis.set_major_formatter(xaxis_formatter)
        ax.set_xlabel('Frequency')
        ax.set_ylabel('Power')
        ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        ax.set_ylim(-120,0)
        xtick_step = (self.tb.requested_max_freq - self.tb.min_freq) / 4.0
        ax.set_xticks(
            np.arange(self.tb.min_freq, self.tb.requested_max_freq+xtick_step, xtick_step)
        )
        ax.set_yticks(np.arange(-130, 0, 10))
        ax.grid(color='.90', linestyle='-', linewidth=1)
        ax.set_title('Power Spectrum Density')

        return ax

    def update_line(self, points, new_sweep):
        if self.paused:
            return

        #if new_sweep:
        #    # log secs per sweep
        #    start_t = self.start_t
        #    self.start_t = stop_t = time.time()
        #    self.logger.info("Completed sweep in {} seconds".format(int(stop_t-start_t)))

        self.canvas.restore_region(self.plot_background)
        line_xs, line_ys = self.line.get_data()
        xs, ys = points

        # index of the start and stop of our current data
        xs_start = np.where(line_xs==xs[0])[0]
        xs_stop = np.where(line_xs==xs[-1])[0] + 1
        np.put(line_ys, range(xs_start, xs_stop), ys)
        self.line.set_ydata(line_ys)

        self.subplot.draw_artist(self.line)
        self.canvas.blit(self.subplot.bbox)

    def pause_plot(self, event):
        if event.dblclick:
            self.paused = not self.paused
            paused = "paused" if self.paused else "unpaused"
            self.logger.info("Plotting {0}.".format(paused))

    def close(self, event):
        self.logger.debug("GUI closing.")
        self.tb.stop()
        self.Destroy()
