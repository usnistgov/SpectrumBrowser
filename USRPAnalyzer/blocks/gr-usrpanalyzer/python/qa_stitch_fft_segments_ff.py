#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 <+YOU OR YOUR COMPANY+>.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import numpy as np

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import usrpanalyzer_swig as usrpanalyzer

class qa_stitch_fft_segments_ff(gr_unittest.TestCase):
    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_000(self):
        overlap = 0.25
        fft_size = 32
        n_segments = 1
        n_valid_bins = 24 #int(fft_size - (fft_size * overlap))
        src_data = np.arange(32)
        expected_result = np.arange(4, 28)
        src = blocks.vector_source_f(src_data)
        s2v = blocks.stream_to_vector(gr.sizeof_float, fft_size * n_segments)
        stitch = usrpanalyzer.stitch_fft_segments_ff(fft_size, n_segments, overlap)
        dst = blocks.vector_sink_f(n_valid_bins * n_segments)
        dst = blocks.vector_sink_f(n_valid_bins * n_segments)
        self.tb.connect(src, s2v, stitch, dst)
        self.tb.run()
        result_data = dst.data()
        self.assertEqual(len(src_data), fft_size*n_segments)
        self.assertFloatTuplesAlmostEqual(expected_result, result_data, 6)
        self.assertEqual(len(result_data), n_valid_bins*n_segments)

    def test_001(self):
        overlap = 0.25
        fft_size = 512
        n_segments = 4
        n_valid_bins = 384 #int(fft_size - (fft_size * overlap))
        src_data = np.concatenate((
            np.array([1] * fft_size),
            np.array([2] * fft_size),
            np.array([3] * fft_size),
            np.array([4] * fft_size),
        ))
        expected_result = np.concatenate((
            np.array([1] * n_valid_bins),
            np.array([2] * n_valid_bins),
            np.array([3] * n_valid_bins),
            np.array([4] * n_valid_bins),
        ))
        src = blocks.vector_source_f(src_data)
        s2v = blocks.stream_to_vector(gr.sizeof_float, fft_size * n_segments)
        stitch = usrpanalyzer.stitch_fft_segments_ff(fft_size, n_segments, overlap)
        dst = blocks.vector_sink_f(n_valid_bins * n_segments)
        self.tb.connect(src, s2v, stitch, dst)
        self.tb.run()
        result_data = dst.data()
        self.assertEqual(len(src_data), fft_size*n_segments)
        self.assertFloatTuplesAlmostEqual(expected_result, result_data, 6)
        self.assertEqual(len(result_data), n_valid_bins*n_segments)

        # Test edges
        self.assertEqual(result_data[0], 1)
        self.assertEqual(result_data[n_valid_bins-1], 1)
        self.assertEqual(result_data[n_valid_bins], 2)
        self.assertEqual(result_data[n_valid_bins*2-1], 2)
        self.assertEqual(result_data[n_valid_bins*2], 3)
        self.assertEqual(result_data[n_valid_bins*3-1], 3)
        self.assertEqual(result_data[n_valid_bins*3], 4)
        self.assertEqual(result_data[n_valid_bins*4-1], 4)

    def test_002(self):
        overlap = 0.25
        fft_size = 8
        n_segments = 2
        n_valid_bins = 6 #int(fft_size - (fft_size * overlap))
        #src_data = np.concatenate((np.arange(0,8), np.arange(6,14)))
        src_data = np.array([ 0,  1,  2,  3,  4,  5,  6,  7,  6,  7,  8,  9, 10, 11, 12, 13])
        #expected_result = np.arange(1, 13)
        expected_result = np.array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12])
        src = blocks.vector_source_f(src_data)
        s2v = blocks.stream_to_vector(gr.sizeof_float, fft_size * n_segments)
        stitch = usrpanalyzer.stitch_fft_segments_ff(fft_size, n_segments, overlap)
        dst = blocks.vector_sink_f(n_valid_bins * n_segments)
        dst = blocks.vector_sink_f(n_valid_bins * n_segments)
        self.tb.connect(src, s2v, stitch, dst)
        self.tb.run()
        result_data = dst.data()
        self.assertEqual(len(src_data), fft_size*n_segments)
        self.assertFloatTuplesAlmostEqual(expected_result, result_data, 6)
        self.assertEqual(len(result_data), n_valid_bins*n_segments)



if __name__ == '__main__':
    #import os
    #print("Blocked waiting for GDB attach (pid = {})".format(os.getpid()))
    #raw_input("Press Enter to continue...")
    gr_unittest.run(qa_stitch_fft_segments_ff, "qa_stitch_fft_segments_ff.xml")
