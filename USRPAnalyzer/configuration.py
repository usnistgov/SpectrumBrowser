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

from __future__ import division

import math
import itertools
import logging
import numpy as np

from gnuradio.filter import window


WIRE_FORMATS = {"sc8", "sc16"}
CPU_FORMATS = {"fc32", "sc16"}


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

        # Add command line argument values to config namespace
        self.__dict__.update(args.__dict__)
        self.overlap = self.overlap / 100.0 # percent to decimal
        self.requested_span = self.span
        self.cpu_format = "fc32"            # hard coded for now

        # configuration variables set by update_frequencies:
        self.span = None               # width in Hz of total area to sample
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
        self.window = None # Name of window, set by set_window
        self.window_coefficients = None # Set by set_window
        self.set_window("Blackman-Harris")

    def set_wire_format(self, fmt):
        """Set the ethernet wire format between the USRP and host."""
        if fmt in WIRE_FORMATS:
            self.wire_format = str(fmt) # ensure not unicode str

    def set_fft_size(self, size):
        """Set the fft size in bins (must be a multiple of 32)."""
        if size > 0 and not size % 32:
            self.fft_size = size
        else:
            msg = "Unable to set fft size to {}, must be a multiple of 32"
            self.logger.warn(msg.format(size))

        self.logger.debug("fft size is {} bins".format(self.fft_size))

    def set_window(self, fn_name):
        """Set the window"""
        if fn_name in self.windows.keys():
            self.window = fn_name

        self.window_coefficients = self.windows[self.window](self.fft_size)

    def update_frequencies(self):
        """Update various frequency-related variables and caches"""

        # Update the channel bandwidth
        self.channel_bandwidth = self.sample_rate / self.fft_size

        # Set the freq_step to a percentage of the actual data throughput.
        # This allows us to discard bins on both ends of the spectrum.
        self.freq_step = self.adjust_rate(
            self.sample_rate, self.channel_bandwidth, self.overlap
        )

        # If user did not request a certain span, ensure we do not retune USRP
        if self.requested_span:
            self.span = self.requested_span
        else:
            self.span = self.freq_step

        # calculate start and end of requested span
        self.min_freq = self.center_freq - (self.span / 2)
        self.max_freq = self.min_freq + self.span

        # calculate min and max center frequencies
        self.min_center_freq = self.min_freq + (self.freq_step / 2)
        if self.span <= self.freq_step:
            self.max_center_freq = self.min_center_freq
        else:
            initial_nsteps = math.floor(self.span / self.freq_step)
            self.max_center_freq = (
                self.min_center_freq + (initial_nsteps * self.freq_step)
            )

        # cache center (tuned) frequencies
        if self.span <= self.freq_step:
            self.center_freqs = np.array([self.min_center_freq])
        else:
            self.center_freqs = np.arange(
                self.min_center_freq,
                self.max_center_freq + 1,
                self.freq_step
            )
        self.center_freq_iter = itertools.cycle(self.center_freqs)
        self.nsteps = len(self.center_freqs)

        # cache all fft bin frequencies
        self.bin_freqs = np.arange(
            self.min_freq,
            self.max_center_freq + (self.freq_step / 2), # actual max bin freq
            self.channel_bandwidth
        )
        self.bin_start = int(self.fft_size * (self.overlap / 2))
        self.bin_stop = int(self.fft_size - self.bin_start)
        self.max_plotted_bin = self.find_nearest(self.bin_freqs, self.max_freq) + 1
        self.bin_offset = (self.bin_stop - self.bin_start) / 2


    @staticmethod
    def adjust_rate(samp_rate, chan_bw, overlap):
        """Reduce rate by a user-selected percentage and round it.

        The adjusted sample size is used to calculate a smaller frequency
        step.  This allows us to overlap a percentage of bins which are most
        affected by the windowing function.

        The adjusted sample size is then rounded so that a whole number of bins
        of size chan_bw go into it.

        """
        throughput = 1.0 - overlap
        return int(round((samp_rate * throughput) / chan_bw) * chan_bw)

    @staticmethod
    def find_nearest(array, value):
        """Find the index of the closest matching value in an bin_freqs."""
        #http://stackoverflow.com/a/2566508
        return np.abs(array - value).argmin()


def find_nearest(array, value):
    """Find the index of the closest matching value in a NumPyarray."""
    #http://stackoverflow.com/a/2566508
    return np.abs(array - value).argmin()
