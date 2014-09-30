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
        self.threshold = str(frame.threshold) # default threshold in dBm
        self.threshold_lines = []
        self.SetValue(self.threshold)
        self.set_threshold(None)

    #FIXME: make this its own class like marker/marker_txtctrl
    def set_threshold(self, event):
        # remove current threshold line
        if self.threshold_lines:
            self.threshold_lines.pop(0).remove()

        if event is None:
            # call from constructor, the TextCtrl isn't initialized yet
            threshold = self.threshold
        else:
            threshold = self.GetValue()
            try:
                float(threshold) # will raise ValueError if not a number
            except ValueError:
                threshold = self.threshold # reset to last known good value

        # plot the new threshold and add it to our blitted background
        self.threshold_lines = self.frame.subplot.plot(
            [self.frame.tb.min_freq-1e7, self.frame.tb.max_freq+1e7], # x values
            [threshold] * 2, # y values
            color='red',
            zorder = 90 # draw it above the grid lines
        )
        self.frame.canvas.draw()
        self.frame.update_background()

        self.SetValue(threshold)
        self.frame.threshold = float(threshold)


class marker_txtctrl(wx.TextCtrl):
    def __init__(self, frame, marker):
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.frame = frame
        self.marker = marker
        self.Bind(wx.EVT_TEXT_ENTER, marker.set_freq)


class marker(object):
    def __init__(self, frame, color, shape):
        self.frame = frame
        self.color = color
        self.shape = shape
        self.size = 8
        self.point = None
        self.text_label = None
        self.text_power = None
        self.freq = None
        self.bin_idx = None

    @staticmethod
    def find_nearest(array, value):
        #http://stackoverflow.com/a/2566508
        idx = np.abs(array - value).argmin()
        return (idx, array[idx])

    def set_freq(self, event):
        evt_obj = event.GetEventObject()
        temp_freq = evt_obj.GetValue()
        try:
            # MHz to Hz. Will raise ValueError if not a number
            temp_freq = float(temp_freq) * 1e6
        except ValueError:
            temp_freq = self.freq # reset to last known good value

        bin_idx, nearest_freq = self.find_nearest(self.frame.tb.bin_freqs, temp_freq)
        self.bin_idx = bin_idx

        freq_str = "{:.2f}".format(nearest_freq / 1e6)

        if self.point is None:
            self.point, = self.frame.subplot.plot(
                [nearest_freq], # x value
                [0], # temp y value, update_line will adjust with each sweep
                marker = self.shape,
                markerfacecolor = self.color,
                markersize = self.size,
                zorder = 99,  # draw it above the grid lines
                alpha = 0     # make the marker invisible until update_line sets y
            )
            self.text_label = self.frame.subplot.text(
                0.5, # x
                0.5, # y
                freq_str, # text
                color = self.color,
                alpha = 0
            )
            self.text_dbm = self.frame.subplot.text(
                1, # x location
                1, # y location
                "", # update_plot replaces this text
                color = self.color,
                alpha = 0
            )
        else:
            self.point.set_xdata([nearest_freq])
            self.text_label.set_text(freq_str)

        evt_obj.SetValue(freq_str)
        self.freq = nearest_freq


class  wxpygui_frame(wx.Frame):
    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.init_plot()
        self.threshold = -20
        self.threshold_txtctrl = threshold_txtctrl(self)
        self.marker1 = marker(self, 'white', 'd') # white thin diamond
        self.marker2 = marker(self, 'white', 'd') # white thin diamond
        self.marker1_txtctrl = marker_txtctrl(self, self.marker1)
        self.marker2_txtctrl = marker_txtctrl(self, self.marker2)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plot)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.atten_txtctrl = atten_txtctrl(self)
        self.ADC_digi_txtctrl = ADC_digi_txtctrl(self)

        self.gain_ctrls = self.init_gain_ctrls()
        self.threshold_ctrls = self.init_threshold_ctrls()
        self.marker1_ctrls = self.init_marker1_ctrls()
        self.marker2_ctrls = self.init_marker2_ctrls()

        hbox.Add(self.gain_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.threshold_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.marker1_ctrls, 0, wx.ALL, 10)
        hbox.Add(self.marker2_ctrls, 0, wx.ALL, 10)

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
        threshold_hbox.Add(self.threshold_txtctrl)
        threshold_hbox.Add(threshold_txt)
        threshold_ctrls.Add(threshold_hbox)

        return threshold_ctrls

    def init_marker1_ctrls(self):
        marker1_box = wx.StaticBox(self, wx.ID_ANY, "Marker 1")
        marker1_ctrls = wx.StaticBoxSizer(marker1_box, wx.VERTICAL)
        marker1_hbox = wx.BoxSizer(wx.HORIZONTAL)
        marker1_txt = wx.StaticText(self, wx.ID_ANY, "MHz")
        marker1_hbox.Add(self.marker1_txtctrl)
        marker1_hbox.Add(marker1_txt)
        marker1_ctrls.Add(marker1_hbox)

        return marker1_ctrls

    def init_marker2_ctrls(self):
        marker2_box = wx.StaticBox(self, wx.ID_ANY, "Marker 2")
        marker2_ctrls = wx.StaticBoxSizer(marker2_box, wx.VERTICAL)
        marker2_hbox = wx.BoxSizer(wx.HORIZONTAL)
        marker2_txt = wx.StaticText(self, wx.ID_ANY, "MHz")
        marker2_hbox.Add(self.marker2_txtctrl)
        marker2_hbox.Add(marker2_txt)
        marker2_ctrls.Add(marker2_hbox)

        return marker2_ctrls

    def update_background(self):
        """Force update of the background."""
        self.plot_background = self.canvas.copy_from_bbox(self.subplot.bbox)

    def init_plot(self):
        self.plot = wx.Panel(self, wx.ID_ANY, size=(800,600))
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.plot, -1, self.figure)
        self.subplot = self.format_ax(self.figure.add_subplot(111, axisbg='black'))
        x_points = self.tb.bin_freqs
        # Just plot a straight line at -100dB to start
        self.line, = self.subplot.plot(
            x_points, [-100]*len(x_points), animated=True, antialiased=False,
            color='#00BB00' # green
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
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Power (dBm)')
        ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        ax.set_ylim(-120,0)
        xtick_step = (self.tb.requested_max_freq - self.tb.min_freq) / 4.0
        ax.set_xticks(
            np.arange(self.tb.min_freq, self.tb.requested_max_freq+xtick_step, xtick_step)
        )
        ax.set_yticks(np.arange(-130, 0, 10))
        ax.grid(color='.10', linestyle='-', linewidth=1)
        ax.set_title('Power Spectrum Density')

        return ax

    def update_plot(self, points, new_sweep):
        if self.paused:
            return

        self.canvas.restore_region(self.plot_background)
        line_xs, line_ys = self.line.get_data()
        xs, ys = points

        # Line
        # index of the start and stop of our current data
        xs_start = np.where(line_xs==xs[0])[0]
        xs_stop = np.where(line_xs==xs[-1])[0] + 1
        np.put(line_ys, range(xs_start, xs_stop), ys)
        self.line.set_ydata(line_ys)

        self.subplot.draw_artist(self.line)

        # Marker
        m1bin = self.marker1.bin_idx
        m2bin = self.marker2.bin_idx
        if ((self.marker1.freq is not None) and (m1bin >= xs_start) and (m1bin < xs_stop)):
            marker1_power = ys[m1bin - xs_start]
            self.marker1.point.set_ydata(marker1_power)
            self.marker1.point.set_alpha(1) # make visible
            self.marker1.text_label.set_alpha(1)
            self.marker1.text_dbm.set_text("{:.1f}".format(marker1_power[0]))
            self.marker1.text_dbm.set_alpha(1)
        if ((self.marker2.freq is not None) and (m2bin >= xs_start) and (m2bin < xs_stop)):
            marker2_power = ys[m2bin - xs_start]
            self.marker2.point.set_ydata(marker2_power)
            self.marker2.point.set_alpha(1) # make visible
            self.marker2.text_dbm.set_text("{:.1f}".format(marker2_power[0]))
            self.marker2.text_dbm.set_alpha(1)

        if self.marker1.freq is not None:
            self.subplot.draw_artist(self.marker1.point)
            self.subplot.draw_artist(self.marker1.text_label)
            self.subplot.draw_artist(self.marker1.text_dbm)
        if self.marker2.freq is not None:
            self.subplot.draw_artist(self.marker2.point)
            self.subplot.draw_artist(self.marker2.text_label)
            self.subplot.draw_artist(self.marker2.text_dbm)

        # Threshold
        # indices of where the y-value is greater than self.threshold
        overload, = np.where(ys > self.threshold)
        if overload.size:
            logheader = "============= Overload at {} ============="
            self.logger.warning(logheader.format(int(time.time())))
            logmsg = "Exceeded threshold {0:.0f}dBm ({1:.2f}dBm) at {2:.2f}MHz"
            for i in overload:
                self.logger.warning(logmsg.format(self.threshold, ys[i], xs[i] / 1e6))

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
