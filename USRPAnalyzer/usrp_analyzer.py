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


import sys
import math
import time
import struct
import threading
import logging
from decimal import Decimal
from copy import copy
import numpy as np
import wx
from optparse import OptionParser, SUPPRESS_HELP

from gnuradio import gr
from gnuradio import blocks as gr_blocks
from gnuradio import fft
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from gnuradio.filter import window

from myblocks import bin_statistics_ff
from usrpanalyzer import skiphead_reset
from gui.main import wxpygui_frame


class configuration(object):
    """Container for configurable settings."""
    def __init__(self, options):
        self.logger = logging.getLogger('USRPAnalyzer')

        # Set the subdevice spec
        self.spec = options.spec
        self.antenna = options.antenna
        self.squelch_threshold = options.squelch_threshold
        self.lo_offset = options.lo_offset

        self.fft_size = None
        self.set_fft_size(options.fft_size)

        self.sample_rate = options.samp_rate

        self.channel_bandwidth = None
        self.update_channel_bandwidth()

        # commented-out windows require extra parameters that we're not set up
        # to handle at this time
        self.windows = {
            "Bartlett":         window.bartlett,
            "Blackman":         window.blackman,
            "Blackman2":        window.blackman2,
            "Blackman3":        window.blackman3,
            "Blackman4":        window.blackman4,
            "Blackman-Harris":  window.blackman_harris,
            "Blackman-Nuttall": window.blackman_nuttal,
            #"Cosine":           window.coswindow,
            #"Exponential":      window.exponential,
            "Flattop":          window.flattop,
            "Hamming":          window.hamming,
            "Hann":             window.hann,
            "Hanning":          window.hanning,
            #"Kaiser":           window.kaiser,
            "Nuttall":          window.nuttal,
            "Nuttall CFD":      window.nuttal_cfd,
            "Parzen":           window.parzen,
            "Rectangular":      window.rectangular,
            "Riemann":          window.riemann,
            "Welch":            window.welch
        }
        self.window_str = None # set by set_window
        self.set_window("Blackman-Harris")
        self.window = None # actual function, set by update_window

        self.update_window()

        # capture at least 1 fft frame
        self.dwell = int(max(1, options.dwell)) # in fft_frames
        self.tune_delay = int(options.tune_delay) # in fft_frames

    def set_fft_size(self, size):
        """Set the fft size in bins (must be a multiple of 64)."""
        if size % 64:
            msg = "Unable to set fft size to {}, must be a multiple of 64"
            self.logger.warn(msg.format(size))
            if self.fft_size is None:
                # likely got passed a bad value via the command line
                # so just set a sane default
                self.fft_size = 1024
        else:
            self.fft_size = size

        self.logger.debug("fft size is {} bins".format(self.fft_size))

    def update_channel_bandwidth(self):
        """Update the channel bandwidth"""
        bw = int(self.sample_rate/self.fft_size)
        self.channel_bandwidth = bw

    def set_window(self, fn_name):
        """Set the window string.

        The actual window is initialized by update_window.
        """
        if fn_name in self.windows.keys():
            self.window_str = fn_name

    def update_window(self):
        """Update the window function"""
        self.window = self.windows[self.window_str](self.fft_size)


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

        self.min_freq = eng_notation.str_to_num(args[0])
        self.max_freq = eng_notation.str_to_num(args[1])

        self.config = configuration(options)
        self.pending_config = copy(self.config)

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

        self.sample_rates = [r.start() for r in self.u.get_samp_rates().iterator()]

        # Default to 0 gain, full attenuation
        if options.gain is None:
            g = self.u.get_gain_range()
            options.gain = g.start()

        self.set_gain(options.gain)
        self.gain = options.gain

        # Holds the most recent tune_result object returned by uhd.tune_request
        self.tune_result = None

        # The main loop clears this every time it makes a call to the gui and
        # the gui's EVT_IDLE event sets it when it done processing that
        # request.  After running the flowgraph, the main loop waits until
        # this is set before looping, allowing us to run the flowgraph as fast
        # as possible, but not faster!
        self.gui_idle = threading.Event()

        # The main loop blocks at the end of the loop until either continuous
        # or single run mode is set.
        self.continuous_run = threading.Event()
        self.single_run = threading.Event()
        if options.continuous_run:
            self.continuous_run.set()

        self.configure_flowgraph()

    def configure_flowgraph(self):
        """Configure or reconfigure the flowgraph"""

        self.disconnect_all()

        # Apply any pending configuration changes
        self.config = copy(self.pending_config)

        if self.config.spec:
            self.u.set_subdev_spec(options.spec, 0)

        # Set the antenna
        if self.config.antenna:
            self.u.set_antenna(options.antenna, 0)

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.
        self.freq_step = self.adjust_sample_rate(
            self.config.sample_rate, self.config.channel_bandwidth
        )

        self.min_center_freq = self.min_freq + (self.freq_step/2)
        self.nsteps = math.floor((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (self.nsteps * self.freq_step)
        self.adjusted_max_freq = self.max_center_freq + (self.freq_step / 2)
        maxfreq_msg = "Max freq adjusted to {0}MHz"
        self.logger.debug(maxfreq_msg.format(int(self.adjusted_max_freq/1e6)))
        # cache a numpy array of bin center frequencies so we don't have to recompute
        self.bin_freqs = np.arange(
            self.min_freq, self.adjusted_max_freq, self.config.channel_bandwidth
        )
        self.bin_start = int(self.config.fft_size * ((1 - 0.75) / 2))
        self.bin_stop = int(self.config.fft_size - self.bin_start)
        self.bin_offset = int(self.config.fft_size * .75 / 2)

        # Start at the beginning
        self.next_freq = self.min_center_freq
        s2v = gr_blocks.stream_to_vector(gr.sizeof_gr_complex, self.config.fft_size)

        # Skip "tune_delay" fft frames, customized to be resetable (like head)
        self.skip = skiphead_reset(
            gr.sizeof_gr_complex * self.config.fft_size, self.config.tune_delay
        )

        # We run the flow graph once at each frequency. head counts the samples
        # and terminates the flow graph when we have what we need.
        self.head = gr_blocks.head(
            gr.sizeof_gr_complex * self.config.fft_size, self.config.dwell
        )

        forward = True
        shift = True
        ffter = fft.fft_vcc(self.config.fft_size, forward, self.config.window, shift)

        c2mag = gr_blocks.complex_to_mag_squared(self.config.fft_size)

        # The flowgraph drops the resulting vector into a thread-friendly
        # message queue where the main loop is listening
        self.msgq = gr.msg_queue(1)
        message_sink = gr_blocks.message_sink(
            # make (size_t itemsize, gr::msg_queue::sptr msgq, bool dont_block)
            gr.sizeof_float*self.config.fft_size, self.msgq, True
        )
        stats = bin_statistics_ff(self.config.fft_size, self.config.dwell)

        power = sum(tap*tap for tap in self.config.window)

        # Divide magnitude-square by a constant to obtain power
        # in Watts. Assumes unit of USRP source is volts.
        impedance = 50.0 # ohms
        Vsq2W_dB = -10.0 * math.log10(self.config.fft_size * power * impedance)
        # Convert from Watts to dBm.
        W2dBm = gr_blocks.nlog10_ff(10.0, self.config.fft_size, 30 + Vsq2W_dB)

        self.reconfigure = False

        # Create the flow graph
        self.connect(self.u, s2v, self.skip, self.head, ffter, c2mag, stats, W2dBm, message_sink)

    def set_sample_rate(self, rate):
        """Set the USRP sample rate"""
        self.u.set_samp_rate(rate)
        self.sample_rate = self.u.get_samp_rate()
        self.logger.debug("sample rate is {} S/s".format(int(rate)))

    def set_next_freq(self):
        """Retune the USRP and calculate our next center frequency."""
        target_freq = self.next_freq
        if not self.set_freq(target_freq):
            self.logger.error("Failed to set frequency to {}".format(target_freq))

        self.next_freq = self.next_freq + self.freq_step
        if self.next_freq > self.max_center_freq:
            self.next_freq = self.min_center_freq

        return target_freq

    def set_freq(self, target_freq):
        """Set the center frequency and LO offset of the USRP."""
        r = self.u.set_center_freq(uhd.tune_request(
            target_freq,
            rf_freq=(target_freq + self.config.lo_offset),
            rf_freq_policy=uhd.tune_request.POLICY_MANUAL
        ))

        #r = self.u.set_center_freq(uhd.tune_request(target_freq, self.config.lo_offset))
        if r:
            self.tune_result = r
            return True
        return False

    def set_gain(self, gain):
        """Let UHD decide how to distribute gain."""
        self.u.set_gain(gain)

    def set_ADC_gain(self, gain):
        """Via uhd_usrp_probe:
        Name: ads62p44 (TI Dual 14-bit 105MSPS ADC)
        Gain range digital: 0.0 to 6.0 step 0.5 dB
        Gain range fine: 0.0 to 0.5 step 0.1 dB
        """
        max_digi = self.u.get_gain_range('ADC-digital').stop()
        max_fine = self.u.get_gain_range('ADC-fine').stop()
        # crop to 0.0 - 6.0
        cropped = Decimal(str(max(0.0, min(max_digi, float(gain)))))
        mod = cropped % Decimal(max_fine)  # ex: 5.7 -> 0.2
        fine = round(mod, 1)               # get fine in terms steps of 0.1
        digi = float(cropped - mod)        # ex: 5.7 - 0.2 -> 5.5
        self.u.set_gain(digi, 'ADC-digital')
        self.u.set_gain(fine, 'ADC-fine')

        return (digi, fine) # return vals for testing

    def get_gain(self):
        """Return total ADC gain as float."""
        return self.u.get_gain('ADC-digital') + self.u.get_gain('ADC-fine')

    def get_gain_range(self, name=None):
        """Return a UHD meta range object for whole range or specific gain.

        Available gains: ADC-digital ADC-fine PGA0
        """
        return self.u.get_gain_range(name if name else "")

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

    @staticmethod
    def adjust_sample_rate(samp_rate, chan_bw):
        """Given a sample rate, reduce its size by 75% and round it.

        The adjusted sample size is used to calculate a smaller frequency step.
        This allows us to overlap the outer 12.% of bins, which are most
        affected by the windowing function.

        The adjusted sample size is then rounded so that a whole number of bins
        of size chan_bw go into it.
        """
        return int(round(samp_rate * 0.75 / chan_bw, 0) * chan_bw)


def main(tb):
    """Run the main loop of the program"""

    def calc_x_points(center_freq):
        """Given a center frequency, find its index in a numpy array of all
        bin center frequencies. Then use bin_offset to calculate the index range
        that will hold all of the appropriate x-values (frequencies) for the
        y-values (power measurements) that we just took at center_freq.
        """
        center_bin = int(np.where(tb.bin_freqs == center_freq)[0][0])
        low_bin = center_bin - tb.bin_offset
        high_bin = center_bin + tb.bin_offset
        return tb.bin_freqs[low_bin:high_bin]

    app = wx.App()
    app.frame = wxpygui_frame(tb)
    app.frame.Show()
    gui = threading.Thread(target=app.MainLoop)
    gui.start()

    logger = logging.getLogger('USRPAnalyzer.pyplot_sink_f')

    freq = tb.set_next_freq() # initialize at min_center_freq

    update_plot = False

    while True:
        last_sweep = freq == tb.max_center_freq
        if last_sweep:
            tb.single_run.clear()

        # Execute flow graph and wait for it to stop
        tb.run()
        # Block here until the flowgraph inserts data into the message queue
        msg = tb.msgq.delete_head()
        # Unpack the binary data into a numpy array of floats
        raw_data = msg.to_string()
        data = np.array(
            struct.unpack('%df' % (tb.config.fft_size,), raw_data), dtype=np.float
        )

        # Process the data and call wx.Callafter to graph it here.
        y_points = data[tb.bin_start:tb.bin_stop]
        x_points = calc_x_points(freq)

        if last_sweep and tb.reconfigure:
            tb.logger.debug("Reconfiguring flowgraph")
            tb.lock()
            tb.configure_flowgraph()
            tb.unlock()
            update_plot = True

        try:
            if app.frame.closed:
                break
            wx.CallAfter(app.frame.update_plot, (x_points, y_points), update_plot)
            tb.gui_idle.clear()
            update_plot = False
        except wx._core.PyDeadObjectError:
            break

        # Tune to next freq, delay, and reset skip and head for next run
        freq = tb.set_next_freq()

        # Sleep as long as necessary to keep a responsive gui
        sleep_count = 0
        while not tb.gui_idle.is_set():
            time.sleep(.01)
            sleep_count += 1
        #if sleep_count > 0:
        #    logger.debug("Slept {0}s waiting for gui".format(sleep_count / 100.0))
        tb.skip.reset()
        tb.head.reset()

        # Block on run mode trigger
        if last_sweep:
            while not (tb.single_run.is_set() or tb.continuous_run.is_set()):
                # check run mode again in 1/2 second
                time.sleep(.5)
                try:
                    if app.frame.closed:
                        break
                except wx._core.PyDeadObjectError:
                    break


def init_parser():
    """Initialize an OptionParser instance, populate it, and return it."""

    usage = "usage: %prog [options] min_freq max_freq"
    parser = OptionParser(option_class=eng_option, usage=usage)
    parser.add_option("-a", "--args", type="string", default="",
                      help="UHD device device address args [default=%default]")
    parser.add_option("", "--spec", type="string", default=None,
                      help="Subdevice of UHD device where appropriate")
    parser.add_option("-A", "--antenna", type="string", default=None,
                      help="select Rx Antenna where appropriate")
    parser.add_option("-s", "--samp-rate", type="eng_float", default=10e6,
                      help="set sample rate [default=%default]")
    parser.add_option("-g", "--gain", type="eng_float", default=None,
                      help="set gain in dB (default is midpoint)")
    parser.add_option("", "--tune-delay", type="eng_float",
                      default=0, metavar="fft frames",
                      help="time to delay (in fft frames) after changing frequency [default=%default]")
    parser.add_option("", "--dwell", type="eng_float",
                      default=1, metavar="fft frames",
                      help="number of passes (with averaging) at a given frequency [default=%default]")
    parser.add_option("-l", "--lo-offset", type="eng_float",
                      default=5000000, metavar="Hz",
                      help="lo_offset in Hz [default=5 MHz]")
    parser.add_option("-q", "--squelch-threshold", type="eng_float",
                      default=None, metavar="dB",
                      help="squelch threshold in dB [default=%default]")
    parser.add_option("-F", "--fft-size", type="int", default=256,
                      help="specify number of FFT bins [default=%default]")
    parser.add_option("-v", "--verbose", action="store_true", default=False,
                      help="extra info printed to stdout")
    parser.add_option("", "--debug", action="store_true", default=False,
                      help=SUPPRESS_HELP)
    parser.add_option("-c", "--continuous-run", action="store_true", default=False,
                      help="Start in continuous run mode [default=%default]")
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
        logging.getLogger('USRPAnalyzer').info("Exiting.")
    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
