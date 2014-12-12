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


import os
import sys
import math
import time
import threading
import logging
import numpy as np
import scipy.io as sio # export to matlab file support
import wx
from copy import copy
from decimal import Decimal
from itertools import izip
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
    def __init__(self, options, args):
        self.logger = logging.getLogger('USRPAnalyzer')

        # Set the subdevice spec
        self.spec = options.spec
        self.antenna = options.antenna
        self.squelch_threshold = options.squelch_threshold
        self.lo_offset = options.lo_offset

        self.fft_size = None
        self.set_fft_size(options.fft_size)

        self.sample_rate = options.samp_rate

        self.min_freq = eng_notation.str_to_num(args[0])
        self.max_freq = eng_notation.str_to_num(args[1])

        # configuration variables set by update_frequencies:
        self.channel_bandwidth = None  # width in Hz of one fft bin
        self.freq_step = None          # step in Hz between center frequencies
        self.min_center_freq = None    # lowest tuned frequency
        self.max_center_freq = None    # highest tuned frequency
        self.adjusted_max_freq = None  # max_freq adjusted for freq_step
        self.center_freqs = None       # cached nparray of center (tuned) freqs
        self.nsteps = None             # number of rf frontend retunes required
        self.bin_freqs = None          # cached nparray of all sampled freqs
        self.bin_start = None          # array index of first usable bin
        self.bin_stop = None           # array index of last usable bin
        self.bin_offset = None         # offset of start/stop index from center
        self.next_freq = None          # holds the next freq to be tuned
        self.update_frequencies()

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
        self.tune_delay = int(options.tune_delay) # in complex samples

    def set_fft_size(self, size):
        """Set the fft size in bins (must be a multiple of 32)."""
        if size % 32:
            msg = "Unable to set fft size to {}, must be a multiple of 32"
            self.logger.warn(msg.format(size))
            if self.fft_size is None:
                # likely got passed a bad value via the command line
                # so just set a sane default
                self.fft_size = 256
        else:
            self.fft_size = size

        self.logger.debug("fft size is {} bins".format(self.fft_size))

    def set_window(self, fn_name):
        """Set the window string.

        The actual window is initialized by update_window.
        """
        if fn_name in self.windows.keys():
            self.window_str = fn_name

    def update_window(self):
        """Update the window function"""
        self.window = self.windows[self.window_str](self.fft_size)

    def update_frequencies(self):
        """Update various frequency-related variables and caches"""

        # Update the channel bandwidth
        self.channel_bandwidth = int(self.sample_rate/self.fft_size)

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.
        self.freq_step = self.adjust_sample_rate(
            self.sample_rate, self.channel_bandwidth
        )

        self.min_center_freq = self.min_freq + (self.freq_step/2)
        initial_nsteps = math.floor(
            (self.max_freq - self.min_freq) / self.freq_step
        )
        self.max_center_freq = (
            self.min_center_freq + (initial_nsteps * self.freq_step)
        )
        self.adjusted_max_freq = self.max_center_freq + (self.freq_step / 2)
        maxfreq_msg = "Max freq adjusted to {}MHz"
        self.logger.debug(maxfreq_msg.format(int(self.adjusted_max_freq/1e6)))

        # cache frequencies and related information for speed
        self.center_freqs = np.arange(
            self.min_center_freq, self.max_center_freq + 1, self.freq_step
        )
        self.nsteps = len(self.center_freqs)

        self.bin_freqs = np.arange(
            self.min_freq , self.adjusted_max_freq, self.channel_bandwidth,
            dtype=np.uint32 # uint32 restricts max freq up to 4294967295 Hz
        )
        self.bin_start = int(self.fft_size * ((1 - 0.75) / 2))
        self.bin_stop = int(self.fft_size - self.bin_start)
        self.bin_offset = int(self.fft_size * .75 / 2)

        # Start at the beginning
        self.next_freq = self.min_center_freq

    @staticmethod
    def adjust_sample_rate(samp_rate, chan_bw):
        """Given a sample rate, reduce its size by 75% and round it.

        The adjusted sample size is used to calculate a smaller frequency step.
        This allows us to overlap the outer 12.5% of bins, which are most
        affected by the windowing function.

        The adjusted sample size is then rounded so that a whole number of bins
        of size chan_bw go into it.
        """
        return int(round(samp_rate * 0.75 / chan_bw, 0) * chan_bw)


class top_block(gr.top_block):
    def __init__(self, cfg):
        gr.top_block.__init__(self)

        # Set logging levels
        self.logger = logging.getLogger('USRPAnalyzer')
        console_handler = logging.StreamHandler()
        logfmt = logging.Formatter("%(levelname)s:%(funcName)s: %(message)s")
        console_handler.setFormatter(logfmt)
        self.logger.addHandler(console_handler)
        if options.debug:
            loglvl = logging.DEBUG
        else:
            loglvl = logging.INFO
        self.logger.setLevel(loglvl)

        # Use 2 copies of the configuration:
        # cgf - settings that matches the current state of the flowgraph
        # pending_cfg - requested config changes that will be applied during
        #               the next run of configure_flowgraph
        self.cfg = cfg
        self.pending_cfg = copy(self.cfg)

        realtime = False
        if options.real_time:
            # Attempt to enable realtime scheduling
            r = gr.enable_realtime_scheduling()
            if r == gr.RT_OK:
                realtime = True
            else:
                self.logger.warning("failed to enable realtime scheduling")

        # USRP source
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
        cfg = self.cfg = copy(self.pending_cfg)

        if cfg.spec:
            self.u.set_subdev_spec(options.spec, 0)

        # Set the antenna
        if cfg.antenna:
            self.u.set_antenna(options.antenna, 0)

        self.set_sample_rate(cfg.sample_rate)

        # Skip "tune_delay" complex samples, customized to be resetable
        self.skip = skiphead_reset(gr.sizeof_gr_complex, cfg.tune_delay)

        s2v = gr_blocks.stream_to_vector(gr.sizeof_gr_complex, cfg.fft_size)

        # We run the flow graph once at each frequency. head counts the samples
        # and terminates the flow graph when we have what we need.
        self.head = gr_blocks.head(
            gr.sizeof_gr_complex * cfg.fft_size, cfg.dwell
        )

        forward = True
        shift = True
        ffter = fft.fft_vcc(cfg.fft_size, forward, cfg.window, shift)

        c2mag_sq = gr_blocks.complex_to_mag_squared(cfg.fft_size)

        # Create vector sinks to access data at various stages of processing:
        #
        # iq_vsink - holds complex i/q data from the most recent complete sweep
        # fft_vsink - holds complex fft data from the most recent complete sweep
        # final_vsink - holds sweep's fully processed real data
        self.iq_vsink = gr_blocks.vector_sink_c(cfg.fft_size)
        self.fft_vsink = gr_blocks.vector_sink_c(cfg.fft_size)
        self.final_vsink = gr_blocks.vector_sink_f(cfg.fft_size)

        stats = bin_statistics_ff(cfg.fft_size, cfg.dwell)

        power = sum(tap*tap for tap in cfg.window)

        # Divide magnitude-square by a constant to obtain power
        # in Watts. Assumes unit of USRP source is volts.
        impedance = 50.0 # ohms
        Vsq2W_dB = -10.0 * math.log10(cfg.fft_size * power * impedance)
        # Convert from Watts to dBm.
        W2dBm = gr_blocks.nlog10_ff(10.0, cfg.fft_size, 30 + Vsq2W_dB)

        self.reconfigure = False

        # Create the flowgraph:
        #
        # USRP  - hardware source output stream of 32bit complex float
        # skip  - for each run of flowgraph, drop N samples, then copy
        # s2v   - group 32-bit complex stream into vectors of length fft_size
        # head  - copies N vectors, then terminates flowgraph
        # fft   - compute forward FFT, complex in complex out
        # mag^2 - convert vectors from complex to real by taking mag squared
        # stats - linear average vectors if dwell > 1
        # W2dBm - convert volt to dBm
        # *sink - data containers monitored by main thread
        #
        #                            > raw i/q vector sink
        #                           /
        # USRP > skip > s2v > head > fft > mag^2 > stats > W2dBm > final sink
        #                                 \
        #                                  > fft sink
        #
        self.connect(self.u, self.skip, s2v, self.head)
        self.connect((self.head, 0), ffter)
        self.connect((self.head, 0), self.iq_vsink)
        self.connect((ffter, 0), c2mag_sq)
        self.connect((ffter, 0), self.fft_vsink)
        self.connect(c2mag_sq, stats, W2dBm, self.final_vsink)

    def set_sample_rate(self, rate):
        """Set the USRP sample rate"""
        self.u.set_samp_rate(rate)
        self.sample_rate = self.u.get_samp_rate()
        self.logger.debug("sample rate is {} S/s".format(int(rate)))

    def set_next_freq(self):
        """Retune the USRP and calculate our next center frequency."""
        target_freq = self.cfg.next_freq
        if not self.set_freq(target_freq):
            self.logger.error("Failed to set frequency to {}".format(target_freq))

        self.cfg.next_freq = self.cfg.next_freq + self.cfg.freq_step
        if self.cfg.next_freq > self.cfg.max_center_freq:
            self.cfg.next_freq = self.cfg.min_center_freq

        return target_freq

    def set_freq(self, target_freq):
        """Set the center frequency and LO offset of the USRP."""
        r = self.u.set_center_freq(uhd.tune_request(
            target_freq,
            rf_freq=(target_freq + self.cfg.lo_offset),
            rf_freq_policy=uhd.tune_request.POLICY_MANUAL
        ))

        #r = self.u.set_center_freq(uhd.tune_request(target_freq, self.cfg.lo_offset))
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
    def _chunks(l, n):
        """Yield successive n-sized chunks from l"""
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    @staticmethod
    def _verify_data_dir(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    def _to_savemat_format(self, data):
        """Build a numpy array of complex data suitable for scipy.io.savemat"""

        data_chunks = self._chunks(data, self.cfg.fft_size)

        # Construct a python dictionary holding a list of power measurements at
        # each frequency
        #
        # { 712499200: [
        #     (0.005035535432398319-0.002960284473374486j),
        #     (0.004394649062305689-0.003509615547955036j),
        #     ...
        #     ]
        #   ...
        # }
        native_format_data = {}
        for freq in self.cfg.center_freqs:
            x_points = calc_x_points(freq, self.cfg)

            dwell_count = 0
            while dwell_count < self.cfg.dwell:
                chunk = next(data_chunks)
                y_points = chunk[self.cfg.bin_start:self.cfg.bin_stop]

                for (x, y) in izip(x_points, y_points):
                    native_format_data.setdefault(x, []).append(y)

                dwell_count += 1

        # Translate the data to a numpy structed array that savemat understands
        #
        # [ (712499200L, [
        #     (0.005035535432398319-0.002960284473374486j),
        #     (0.004394649062305689-0.003509615547955036j),
        #     ...
        #   ])
        #   ...
        # ]
        matlab_format_data = np.array(native_format_data.items(), dtype=[
            ('frequency', np.uint32),
            ('data', np.complex64, (self.cfg.dwell,))
        ])

        return matlab_format_data

    def save_iq_data_to_file(self):
        """Save pre-FFT I/Q data to file"""

        if (tb.single_run.is_set() or tb.continuous_run.is_set()):
            msg = "Can't export data while the flowgraph is running."
            msg += " Use \"single\" run mode."
            self.logger.error(msg)
            return

        # creates path string 'data/iq_data_TIMESTAMP.mat'
        dirname = "data"
        self._verify_data_dir(dirname)
        fname = str.join('', ('iq_data_', str(int(time.time())), '.mat'))
        pathname = os.path.join(dirname, fname)

        data = self.iq_vsink.data()
        self.iq_vsink.reset() # empty the sink

        if data:
            formatted_data = self._to_savemat_format(data)

            # Export to a file in .mat format
            sio.savemat(pathname, {'iq_data': formatted_data}, appendmat=True)
            self.logger.info("Exported pre-FFT I/Q data to {}".format(pathname))
        else:
            self.logger.warn("No more data to export")

    def save_fft_data_to_file(self):
        """Save post_FFT I/Q data to file"""

        if (tb.single_run.is_set() or tb.continuous_run.is_set()):
            msg = "Can't export data while the flowgraph is running."
            msg += " Use \"single\" run mode."
            self.logger.error(msg)
            return

        # creates path string 'data/fft_data_TIMESTAMP.mat'
        dirname = "data"
        self._verify_data_dir(dirname)
        fname = str.join('', ('fft_data_', str(int(time.time())), '.mat'))
        pathname = os.path.join(dirname, fname)

        data = self.fft_vsink.data()
        self.fft_vsink.reset() # empty the sink

        if data:
            formatted_data = self._to_savemat_format(data)

            # Export to a file in .mat format
            sio.savemat(pathname, {'fft_data': formatted_data}, appendmat=True)
            self.logger.info("Exported post-FFT I/Q data to {}".format(pathname))
        else:
            self.logger.warn("No more data to export")


def calc_x_points(center_freq, cfg):
    """Find the index of a given freq in an array of bin center frequencies.

    Then use bin_offset to calculate the index range
    that will hold all of the appropriate x-values (frequencies) for the
    y-values (power measurements) that we just took at center_freq."""

    center_bin = np.where(cfg.bin_freqs == center_freq)[0][0]
    low_bin = center_bin - cfg.bin_offset
    high_bin = center_bin + cfg.bin_offset

    return cfg.bin_freqs[low_bin:high_bin]


def main(tb):
    """Run the main loop of the program"""

    app = wx.App()
    app.frame = wxpygui_frame(tb)
    app.frame.Show()
    gui = threading.Thread(target=app.MainLoop)
    gui.start()

    logger = logging.getLogger('USRPAnalyzer.pyplot_sink_f')

    freq = tb.set_next_freq() # initialize at min_center_freq

    reconfigure_plot = False

    while True:
        last_sweep = freq == tb.cfg.max_center_freq
        if last_sweep:
            tb.single_run.clear()

        # Execute flow graph and wait for it to stop
        tb.run()

        data = np.array(tb.final_vsink.data(), dtype=np.float32)
        y_points = data[tb.cfg.bin_start:tb.cfg.bin_stop]
        x_points = calc_x_points(freq, tb.cfg)
        # flush the final vector sink
        tb.final_vsink.reset()

        try:
            if app.frame.closed:
                break
            wx.CallAfter(app.frame.update_plot, (x_points, y_points), reconfigure_plot, False)
            tb.gui_idle.clear()
            reconfigure_plot = False
        except wx._core.PyDeadObjectError:
            break

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
                # keep certain gui elements alive
                try:
                    if app.frame.closed:
                        break
                    # Keep live elements updated
                    wx.CallAfter(app.frame.update_plot, None, reconfigure_plot, True)
                except wx._core.PyDeadObjectError:
                    break
                # check run mode again in 1/4 second
                time.sleep(.25)

            # flush iq data vectors for next sweep
            tb.iq_vsink.reset()
            tb.fft_vsink.reset()

        if last_sweep and tb.reconfigure:
            tb.logger.debug("Reconfiguring flowgraph")
            tb.lock()
            tb.configure_flowgraph()
            tb.unlock()
            reconfigure_plot = True

        # Tune to next freq, delay, and reset skip and head for next run
        freq = tb.set_next_freq()


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
                      help="time to delay (in complex samples) after changing frequency [default=%default]")
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

    cfg = configuration(options, args)
    tb = top_block(cfg)
    try:
        main(tb)
        logging.getLogger('USRPAnalyzer').info("Exiting.")
    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
