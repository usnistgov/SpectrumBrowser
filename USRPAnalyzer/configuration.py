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
import tempfile
import numpy as np

from gnuradio.filter import window

import consts
import utils


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

        # If set to True, raw data from next run of flowgraph will be exported
        self.export_raw_time_data = False
        self.export_raw_fft_data = False

        # Add command line argument values to config namespace
        self.__dict__.update(args.__dict__)
        self.overlap = self.overlap / 100.0 # percent to decimal
        self.requested_span = self.span
        self.cpu_format = "fc32"            # hard coded for now

        # configuration variables set by update():
        self.span = None               # width in Hz of total area to sample
        self.RBW = None                # width in Hz of one fft bin (delta f)
        self.freq_step = None          # step in Hz between center frequencies
        self.min_freq = None           # lowest sampled frequency
        self.max_freq = None           # highest sampled frequency
        self.center_freqs = None       # cached nparray of center (tuned) freqs
        self.n_segments = None         # number of rf frontend retunes required
        self.bin_freqs = None          # cached nparray of all sampled freqs
        self.bin_start = None          # array index of first usable bin
        self.bin_stop = None           # array index of last usable bin
        self.bin_offset = None         # offset of start/stop index from center
        self.max_plotted_bin = None    # absolute max bin in bin_freqs to plot
        self.update()

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
        if fmt in consts.WIRE_FORMATS:
            self.wire_format = str(fmt) # ensure not unicode str

    def set_fft_size(self, size):
        """Set the fft size in bins (must be 2^n between 32 and 8192)."""
        if size in consts.FFT_SIZES:
            self.fft_size = size
        else:
            msg = "Unable to set fft size to {}, must be one of {!r}"
            self.logger.warn(msg.format(size, sorted(list(consts.FFT_SIZES))))

        self.logger.debug("fft size is {} bins".format(self.fft_size))

    def set_window(self, fn_name):
        """Set the window"""
        if fn_name in self.windows.keys():
            self.window = fn_name

        self.window_coefficients = self.windows[self.window](self.fft_size)

    def update(self):
        """Convencience function to update various variables and caches"""
        self.update_RBW()
        self.update_freq_step()
        self.update_span()
        self.update_min_max_freq()
        self.update_tuned_freq_cache()
        self.update_bin_freq_cache()
        self.update_bin_indices()

    def update_RBW(self):
        """Update the channel bandwidth"""
        self.RBW = self.sample_rate / self.fft_size

    def update_freq_step(self):
        """Set the freq_step to a percentage of the actual data throughput.

        This allows us to discard bins on both ends of the spectrum.
        """
        self.freq_step = self.adjust_rate(
            self.sample_rate, self.RBW, self.overlap
        )

    def update_span(self):
        """If no requested span, set max span using only one center frequency"""
        if self.requested_span:
            self.span = self.requested_span
        else:
            self.span = self.freq_step

    def update_min_max_freq(self):
        """Calculate actual start and end of requested span"""
        self.min_freq = self.center_freq - (self.span / 2) + (self.RBW / 2)
        self.max_freq = self.min_freq + self.span - self.RBW

    def update_tuned_freq_cache(self):
        """Cache center (tuned) frequencies.

        Sets:
          self.center_freqs     - array of all frequencies to be tuned
          self.n_segments       - length of self.center_freqs
        """
        # calculate min and max center frequencies
        min_center_freq = self.min_freq + (self.freq_step / 2)
        if self.span <= self.freq_step:
            self.center_freqs = np.array([min_center_freq])
        else:
            initial_n_segments = math.floor(self.span / self.freq_step)
            max_center_freq = (
                min_center_freq + (initial_n_segments * self.freq_step)
            )
            self.center_freqs = np.arange(
                min_center_freq,
                max_center_freq + 1,
                self.freq_step
            )

        self.n_segments = len(self.center_freqs)

    def update_bin_freq_cache(self):
        """Cache frequencies at the center of each FFT bin"""
        # cache all fft bin frequencies
        max_center_freq = self.center_freqs[-1]
        self.bin_freqs = np.arange(
            self.min_freq,
            max_center_freq + (self.freq_step / 2), # actual max bin freq
            self.RBW
        )

    def update_bin_indices(self):
        """Update common indices used in cropping and overlaying DFTs"""
        self.bin_start = int(self.fft_size * (self.overlap / 2))
        self.bin_stop = int(self.fft_size - self.bin_start)
        self.max_plotted_bin = utils.find_nearest(self.bin_freqs, self.max_freq) + 1
        self.bin_offset = (self.bin_stop - self.bin_start) / 2

    @staticmethod
    def adjust_rate(samp_rate, rbw, overlap):
        """Reduce rate by a user-selected percentage and round it.

        The adjusted sample size is used to calculate a smaller frequency
        step.  This allows us to overlap a percentage of bins which are most
        affected by the windowing function.

        The adjusted sample size is then rounded so that a whole number of bins
        of size RBW go into it.

        """
        ratio_valid_bins = 1.0 - overlap
        return int(round((samp_rate * ratio_valid_bins) / rbw) * rbw)
