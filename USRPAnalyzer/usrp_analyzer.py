#!/usr/bin/env python


import sys
import math
import time
import struct
import threading
import logging
from decimal import Decimal
import numpy as np
import wx
from wx.lib.agw import flatnotebook as fnb
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from optparse import OptionParser, SUPPRESS_HELP

from gnuradio import gr
from gnuradio import blocks as gr_blocks
from gnuradio import filter as gr_filters
from gnuradio import fft
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option

from myblocks import bin_statistics_ff
from blocks import wxpygui_frame


class top_block(gr.top_block):
    def __init__(self, options, args):
        gr.top_block.__init__(self)

        self.logger = logging.getLogger('USRPAnalyzer')
        console_handler = logging.StreamHandler()
        logfmt = logging.Formatter("%(levelname)s:%(funcName)s: %(message)s")
        console_handler.setFormatter(logfmt)
        self.logger.addHandler(console_handler)
        if options.debug:
            loglvl = logging.DEBUG
        elif options.verbose:
            loglvl = logging.INFO
        else:
            loglvl = logging.WARNING
        self.logger.setLevel(loglvl)

        self.channel_bandwidth = options.channel_bandwidth

        self.min_freq = eng_notation.str_to_num(args[0])
        self.max_freq = eng_notation.str_to_num(args[1])

        if self.min_freq > self.max_freq:
            # swap them
            self.min_freq, self.max_freq = self.max_freq, self.min_freq

        realtime = False
        if options.real_time:
            # Attempt to enable realtime scheduling
            r = gr.enable_realtime_scheduling()
            if r == gr.RT_OK:
                realtime = True
            else:
                self.logger.warning("failed to enable realtime scheduling")

        # build graph
        self.u = uhd.usrp_source(device_addr=options.args,
                                 stream_args=uhd.stream_args('fc32'))
        # Set the subdevice spec
        if options.spec:
            self.u.set_subdev_spec(options.spec, 0)

        # Set the antenna
        if options.antenna:
            self.u.set_antenna(options.antenna, 0)

        self.u.set_samp_rate(options.samp_rate)
        self.usrp_rate = usrp_rate = self.u.get_samp_rate()

        if options.lo_offset is None:
            self.lo_offset = usrp_rate / 2.0
        else:
            self.lo_offset = options.lo_offset

        if options.fft_size:
            self.fft_size = options.fft_size
        else:
            self.fft_size = int(self.usrp_rate/self.channel_bandwidth)

        if options.channel_bandwidth:
            self.channel_bandwidth = int(options.channel_bandwidth)
        else:
            self.channel_bandwidth = int(self.usrp_rate/self.fft_size)

        self.squelch_threshold = options.squelch_threshold

        s2v = gr_blocks.stream_to_vector(gr.sizeof_gr_complex, self.fft_size)

        dwell = max(1, options.dwell) # in fft_frames
        tune_delay = int(options.tune_delay)
        m_in_n = gr_blocks.keep_m_in_n(
            gr.sizeof_gr_complex * self.fft_size, # vectors of fft_size complex samples as 1 unit
            dwell,                                # keep "dwell" units
            tune_delay + dwell,                   # out of each tune_delay + dwell units
            tune_delay                            # skipping tune_delay units initial offset
        )
        self.head = gr_blocks.head(gr.sizeof_gr_complex * self.fft_size, dwell)
        forward = True
        window = gr_filters.window.blackmanharris(self.fft_size)
        shift = True

        ffter = fft.fft_vcc(self.fft_size, forward, window, shift)

        c2mag = gr_blocks.complex_to_mag_squared(self.fft_size)

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.

        self.freq_step = self.nearest_freq((0.75 * self.usrp_rate), self.channel_bandwidth)
        self.min_center_freq = self.min_freq + (self.freq_step/2)
        self.nsteps = math.floor((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (self.nsteps * self.freq_step)
        self.requested_max_freq = self.max_freq # used to set xticks in matplotlib
        self.max_freq = self.max_center_freq + (self.freq_step / 2)
        self.logger.info("Max freq adjusted to {0}MHz".format(int(self.max_freq/1e6)))
        self.bin_freqs = np.arange(self.min_freq, self.max_freq, self.channel_bandwidth)

        self.next_freq = self.min_center_freq

        stats = bin_statistics_ff(self.fft_size, dwell)

        power = sum(tap*tap for tap in window)

        # Divide magnitude-square by a constant to obtain power
        # in Watts. Assumes unit of USRP source is volts.
        impedance = 50.0 # ohms
        Vsq2W_dB = -10.0 * math.log10(self.fft_size * power * impedance)
        # Convert from Watts to dBm.
        W2dBm = gr_blocks.nlog10_ff(10.0, self.fft_size, 30 + Vsq2W_dB)

        self.msgq = gr.msg_queue(1)
        message_sink = gr_blocks.message_sink(
            # make (size_t itemsize, gr::msg_queue::sptr msgq, bool dont_block)
            gr.sizeof_float*self.fft_size, self.msgq, True
        )
        self.connect(self.u, s2v, m_in_n, self.head, ffter, c2mag, stats, W2dBm, message_sink)

        if options.gain is None:
            # if no gain was specified, use the 0 gain
            g = self.u.get_gain_range()
            #options.gain = float(g.start()+g.stop())/2.0
            options.gain = g.start()

        self.set_gain(options.gain)
        self.gain = options.gain

        self.tune_result = None

    def set_next_freq(self):
        target_freq = self.next_freq
        if not self.set_freq(target_freq):
            self.logger.error("Failed to set frequency to {0}".format(target_freq))


        self.next_freq = self.next_freq + self.freq_step
        if self.next_freq > self.max_center_freq:
            self.next_freq = self.min_center_freq

        return target_freq

    def set_freq(self, target_freq):
        r = self.u.set_center_freq(uhd.tune_request(target_freq, self.lo_offset))
        if r:
            self.tune_result = r
            return True
        return False

    def set_gain(self, gain):
        self.u.set_gain(gain)

    def set_ADC_gain(self, gain):
        """Via uhd_usrp_probe:
        Name: ads62p44 (TI Dual 14-bit 105MSPS ADC)
        Gain range digital: 0.0 to 6.0 step 0.5 dB
        Gain range fine: 0.0 to 0.5 step 0.1 dB

        ti.com has slightly different numbers for ADS62P44:
        "3.5 dB Coarse Gain and Programmable Fine Gain
        up to 6 dB for SNR/SFDR Trade-Off
        Fine Gain Correction, in Steps of 0.05 dB"

        This function uses the steps given by uhd_usrp_probe.
        """
        cropped = Decimal(str(max(0.0, min(6.0, float(gain))))) # crop to 0 - 6
        mod = cropped % Decimal('0.5')     # ex: 5.7 -> 0.2
        fine = round(mod, 1)               # get fine in terms steps of 0.1
        digi = float(cropped - mod)        # ex: 5.7 - 0.2 -> 5.5
        self.u.set_gain(digi, 'ADC-digital')
        self.u.set_gain(fine, 'ADC-fine')

        return (digi, fine) # return vals for ease of testing

    def get_gain(self):
        return self.u.get_gain('ADC-digital') + self.u.get_gain('ADC-fine')

    def get_ADC_digital_gain(self):
        return self.u.get_gain('ADC-digital')

    def get_ADC_fine_gain(self):
        return self.u.get_gain('ADC-fine')

    def get_attenuation(self):
        return self.u.get_gain('PGA0')

    def set_attenuation(self, atten):
        """Adjust level on Hittite HMC624LP4E Digital Attenuator.

        UHD driver increases gain by removing attenuation, so to:
        - add 10dB attenuation, we need to remove 10dB gain from PGA0
        - remove 10dB attenuation, we need to add 10dB gain to PGA0

        Specs: Range 0 - 31.5 dB, 0.5 dB step
        NOTE: uhd driver handles range input for the attenuator
        """
        self.u.set_gain(atten, 'PGA0')

    def nearest_freq(self, freq, channel_bandwidth):
        freq = int(round(freq / channel_bandwidth, 0) * channel_bandwidth)
        return freq


def main(tb):
    """Run the main loop of the program"""

    bin_start = int(tb.fft_size * ((1 - 0.75) / 2))
    bin_stop = int(tb.fft_size - bin_start)
    bin_offset = int(tb.fft_size * .75 / 2)

    def calc_x_points(center_freq):
        center_bin = int(np.where(tb.bin_freqs == center_freq)[0][0])
        low_bin = center_bin - bin_offset
        high_bin = center_bin + bin_offset
        return tb.bin_freqs[low_bin:high_bin]

    app = wx.App()
    app.frame = wxpygui_frame(tb)
    app.frame.Show()
    gui = threading.Thread(target=app.MainLoop)
    gui.start()

    logger = logging.getLogger('USRPAnalyzer.pyplot_sink_f')

    freq = last_freq = tb.set_next_freq() # initialize at min_center_freq

    while True:
        # Execute flow graph and wait for it to stop
        tb.start()
        msg = tb.msgq.delete_head() # blocks if no message available
        tb.wait()

        raw_data = msg.to_string()
        data = np.array(struct.unpack('%df' % (tb.fft_size,), raw_data), dtype=np.float)

        # Process the data and call wx.Callafter to graph it here.
        y_points = data[bin_start:bin_stop]
        x_points = calc_x_points(freq)
        try:
            wx.CallAfter(app.frame.update_line, (x_points, y_points), freq < last_freq)
        except wx._core.PyDeadObjectError:
            break

        last_freq = freq

        # Tune to next freq, delay, and reset head for next flowgraph run
        freq = tb.set_next_freq()
        time.sleep(.05)  # FIXME: This is necessary to keep the gui responsive
        tb.head.reset()


def init_parser():
    usage = "usage: %prog [options] min_freq max_freq"
    parser = OptionParser(option_class=eng_option, usage=usage)
    parser.add_option("-a", "--args", type="string", default="",
                      help="UHD device device address args [default=%default]")
    parser.add_option("", "--spec", type="string", default=None,
                      help="Subdevice of UHD device where appropriate")
    parser.add_option("-A", "--antenna", type="string", default=None,
                      help="select Rx Antenna where appropriate")
    parser.add_option("-s", "--samp-rate", type="eng_float", default=1e7,
                      help="set sample rate [default=%default]")
    parser.add_option("-g", "--gain", type="eng_float", default=None,
                      help="set gain in dB (default is midpoint)")
    parser.add_option("", "--tune-delay", type="eng_float",
                      default=5, metavar="fft frames",
                      help="time to delay (in seconds) after changing frequency [default=%default]")
    parser.add_option("", "--dwell", type="eng_float",
                      default=1, metavar="fft frames",
                      help="number of passes (with averaging) at a given frequency [default=%default]")
    parser.add_option("-b", "--channel-bandwidth", type="eng_float",
                      default=None, metavar="Hz",
                      help="channel bandwidth of fft bins in Hz [default=sample-rate/fft-size]")
    parser.add_option("-l", "--lo-offset", type="eng_float",
                      default=None, metavar="Hz",
                      help="lo_offset in Hz [default=half the sample rate]")
    parser.add_option("-q", "--squelch-threshold", type="eng_float",
                      default=None, metavar="dB",
                      help="squelch threshold in dB [default=%default]")
    parser.add_option("-F", "--fft-size", type="int", default=1024,
                      help="specify number of FFT bins [default=%default]")
    parser.add_option("-v", "--verbose", action="store_true", default=False,
                      help="extra info printed to stdout")
    parser.add_option("", "--debug", action="store_true", default=False,
                      help=SUPPRESS_HELP)
    parser.add_option("", "--real-time", action="store_true", default=False,
                      help="Attempt to enable real-time scheduling")

    return parser


if __name__ == '__main__':
    parser = init_parser()
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    tb = top_block(options, args)
    try:
        main(tb)
        tb.stop()
        tb.wait()
        logging.getLogger('USRPAnalyzer').info("Exiting.")
    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
