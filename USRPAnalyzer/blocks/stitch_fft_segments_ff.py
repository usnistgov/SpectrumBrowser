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

import numpy as np

from gnuradio import gr


class stitch_fft_segments_ff(gr.sync_block):
    def __init__(self, fft_size, n_segments, overlap):
        # Formula for scaling from num of total bins to num of valid bins
        self.n_out = int(n_segments * (fft_size - (fft_size * (overlap / 2) * 2)))

        gr.sync_block.__init__(
            self,
            name="fft_stitch_ff",
            in_sig=[(np.float32, fft_size*n_segments)],
            out_sig=[(np.float32, self.n_out)]
        )
        self.fft_size = fft_size # 2^n between 32-8192
        self.n_segments = n_segments  # int
        self.overlap = overlap   # percent {0..50}
        self.bin_start = int(self.fft_size * (self.overlap / 2))
        self.bin_stop = int(self.fft_size - self.bin_start)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        ninput_items = len(in0)

        assert(len(in0[0]) == self.fft_size*self.n_segments)
        assert(len(out[0]) == self.n_out)

        # Split array of values back into separate arrays of length fft_size
        segments = np.split(in0[0], self.n_segments)

        stitched_segments = np.concatenate(
            [x[self.bin_start:self.bin_stop] for x in segments]
        )

        # Check formula for scaling from num of total bins to num of valid bins
        assert(len(stitched_segments) == self.n_out)

        out[0][:] = stitched_segments

        return ninput_items
