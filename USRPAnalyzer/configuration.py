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


import math
import logging
import numpy as np

from gnuradio.filter import window


WIRE_FORMATS = {"sc8", "sc16"}


class configuration(object):
    """Container for configurable settings."""
    def __init__(self, args):

        # Set logging levels
        self.logger = logging.getLogger('USRPAnalyzer')
        console_handler = logging.StreamHandler()
        logfmt = logging.Formatter("%(levelname)s:%(funcName)s: %(message)s")
        console_handler.setFormatter(logfmt)
        self.logger.addHandler(console_handler)
        if args.debug:
            loglvl = logging.DEBUG
        else:
            loglvl = logging.INFO
        self.logger.setLevel(loglvl)

        self.realtime = args.realtime
        self.device_addr = args.device_addr
        self.center_freq = args.center_freq
        self.requested_bandwidth = args.bandwidth
        self.spec = args.spec
        self.antenna = args.antenna
        self.squelch_threshold = args.squelch_threshold
        self.lo_offset = args.lo_offset
        self.gain = args.gain
        self.continuous_run = args.continuous_run

        self.fft_size = None
        self.set_fft_size(args.fft_size)

        self.sample_rate = args.samp_rate

        # configuration variables set by update_frequencies:
        self.bandwidth = None          # width in Hz of total area to sample
        self.channel_bandwidth = None  # width in Hz of one fft bin
        self.freq_step = None          # step in Hz between center frequencies
        self.min_freq = None           # lowest sampled frequency
        self.min_center_freq = None    # lowest tuned frequency
        self.max_freq = None           # highest sampled frequency
        self.max_center_freq = None    # highest tuned frequency
        self.center_freqs = None       # cached nparray of center (tuned) freqs
        self.nsteps = None             # number of rf frontend retunes required
        self.bin_freqs = None          # cached nparray of all sampled freqs
        self.bin_start = None          # array index of first usable bin
        self.bin_stop = None           # array index of last usable bin
        self.bin_offset = None         # offset of start/stop index from center
        self.max_plotted_bin = None    # absolute max bin in bin_freqs to plot
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

        self.wire_format = None
        self.set_wire_format(args.wire_format)

        self.stream_args = args.stream_args

        # capture at least 1 fft frame
        self.dwell = int(max(1, args.dwell)) # in fft_frames
        self.tune_delay = int(args.tune_delay) # in complex samples

    def set_wire_format(self, fmt):
        """Set the ethern wire format between the USRP and host."""
        if fmt in WIRE_FORMATS:
            self.wire_format = fmt

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
        self.freq_step = self.adjust_bandwidth(
            self.sample_rate, self.channel_bandwidth
        )

        # If user did not request a certain scan bandwidth, do not retune
        if self.requested_bandwidth:
            self.bandwidth = self.requested_bandwidth
        else:
            self.bandwidth = self.freq_step

        self.min_freq = self.center_freq - (self.bandwidth / 2)
        self.min_center_freq = self.min_freq + (self.freq_step/2)
        initial_nsteps = math.floor(self.bandwidth / self.freq_step)
        self.max_center_freq = (
            self.min_center_freq + (initial_nsteps * self.freq_step)
        )
        self.max_freq = self.min_freq + self.bandwidth
        actual_max_freq = self.max_center_freq + (self.freq_step / 2)

        # cache frequencies and related information for speed
        self.center_freqs = np.arange(
            self.min_center_freq, self.max_center_freq, self.freq_step
        )
        self.nsteps = len(self.center_freqs)

        self.bin_freqs = np.arange(
            self.min_freq, actual_max_freq, self.channel_bandwidth,
            dtype=np.uint32 # uint32 restricts max freq up to 4294967295 Hz
        )
        self.bin_start = int(self.fft_size * ((1 - 0.75) / 2))
        self.bin_stop = int(self.fft_size - self.bin_start)
        self.min_plotted_bin = self.find_nearest(self.bin_freqs, self.min_freq)
        self.max_plotted_bin = self.find_nearest(self.bin_freqs, self.max_freq) + 1
        self.bin_offset = int(self.fft_size * .75 / 2)

        # Start at the beginning
        self.next_freq = self.min_center_freq

    @staticmethod
    def find_nearest(array, value):
        """Find the index of the closest matching value in an bin_freqs."""
        #http://stackoverflow.com/a/2566508
        return np.abs(array - value).argmin()

    @staticmethod
    def adjust_bandwidth(samp_rate, chan_bw):
        """Reduce bandwidth size by 75% and round it.

        The adjusted sample size is used to calculate a smaller frequency step.
        This allows us to overlap the outer 12.5% of bins, which are most
        affected by the windowing function.

        The adjusted sample size is then rounded so that a whole number of bins
        of size chan_bw go into it.
        """
        return int(round(samp_rate * 0.75 / chan_bw, 0) * chan_bw)


def find_nearest(array, value):
    """Find the index of the closest matching value in a NumPyarray."""
    #http://stackoverflow.com/a/2566508
    return np.abs(array - value).argmin()
