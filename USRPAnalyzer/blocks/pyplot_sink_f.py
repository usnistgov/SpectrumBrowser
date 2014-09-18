import time
import wx
from wx.lib.agw import flatnotebook as fnb
import logging
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure


class atten_txtctrl(wx.TextCtrl):
    def __init__(self, frame):
        wx.TextCtrl.__init__(self, frame, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.frame = frame
        self.Bind(wx.EVT_TEXT_ENTER, self.set_atten)
        self.SetValue(str(frame.tb.get_attenuation()))

    def set_atten(self, event):
        val = self.frame.atten_txtctrl.GetValue()
        self.frame.tb.set_attenuation(float(val))
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
        self.frame.tb.set_ADC_gain(float(val))
        actual_val = self.frame.tb.get_gain()
        self.SetValue(str(actual_val))


class wxpygui_frame(wx.Frame):
    def __init__(self, tb):
        wx.Frame.__init__(self, parent=None, id=-1, title="USRPAnalyzer")
        self.tb = tb

        self.notebook = fnb.FlatNotebook(self, wx.ID_ANY, agwStyle=(
            fnb.FNB_NO_X_BUTTON | fnb.FNB_X_ON_TAB | fnb.FNB_NO_NAV_BUTTONS))

        self.init_live_page()

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.notebook)

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

        self.live_fig.canvas.mpl_connect('button_press_event', self.live_fig_click)
        #fig.canvas.mpl_connect('scroll_event', self.onzoom)

        self.start_t = time.time()

    def init_gain_ctrls(self):
        gain_box = wx.StaticBox(self, wx.ID_ANY, "Gain")
        gain_ctrls = wx.StaticBoxSizer(gain_box, wx.VERTICAL)
        # Attenuation
        atten_hbox = wx.BoxSizer(wx.HORIZONTAL)
        atten_txt = wx.StaticText(self, wx.ID_ANY, "Atten")
        atten_hbox.Add(atten_txt)
        atten_hbox.Add(self.atten_txtctrl)
        gain_ctrls.Add(atten_hbox)
        # ADC digi gain
        ADC_hbox = wx.BoxSizer(wx.HORIZONTAL)
        ADC_txt = wx.StaticText(self, wx.ID_ANY, "ADC digi")
        ADC_hbox.Add(ADC_txt)
        ADC_hbox.Add(self.ADC_digi_txtctrl)        
        gain_ctrls.Add(ADC_hbox)

        return gain_ctrls

    def init_threshold_ctrls(self):
        threshold_box = wx.StaticBox(self, wx.ID_ANY, "Threshold")
        threshold_ctrls = wx.StaticBoxSizer(threshold_box, wx.VERTICAL)
        atten_hbox = wx.BoxSizer(wx.HORIZONTAL)
        atten_txt = wx.StaticText(self, wx.ID_ANY, "Atten")
        atten_txtctrl = wx.TextCtrl(self, wx.ID_ANY)
        atten_hbox.Add(atten_txt)
        atten_hbox.Add(atten_txtctrl)
        threshold_ctrls.Add(atten_hbox)

        return threshold_ctrls

    def init_live_page(self):
        self.live_page = wx.Panel(self.notebook, wx.ID_ANY, size=(800,600))
        self.live_fig = Figure(figsize=(8, 6), dpi=100)
        self.live_ax = self.format_ax(self.live_fig.add_subplot(111))
        self.live_canvas = FigureCanvas(self.live_page, 01, self.live_fig)
        self.line, = self.live_ax.plot([])
        self.notebook.AddPage(self.live_page, "Live")

    def init_static_page(self):
        self.static_page = wx.Panel(self.notebook, wx.ID_ANY)
        self.static_fig = Figure(figsize=(8, 6), dpi=100)
        self.static_ax = self.format_ax(self.static_fig.add_subplot(111))
        self.static_canvas = FigureCanvas(self.static_page, 01, self.static_fig)
        self.static_line = self.static_ax.add_line(self.line)
        self.notebook.AddPage(self.static_page, "Static")
        # automatically switch to the newest created tab
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)

    def format_ax(self, ax):
        ax.set_xlabel('Frequency(MHz)')
        ax.set_ylabel('Power')
        ax.set_xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        ax.set_ylim(-120,0)
        xtick_step = (self.tb.requested_max_freq - self.tb.min_freq) / 4.0
        ax.set_xticks(
            np.arange(self.tb.min_freq, self.tb.requested_max_freq+xtick_step, xtick_step)
        )
        ax.set_yticks(np.arange(-130,0, 10))
        ax.grid(color='.90', linestyle='-', linewidth=1)
        ax.set_title('Power Spectrum Density')

        return ax

    def live_fig_click(self, event):
        if event.dblclick:
            self.init_static_page()

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
