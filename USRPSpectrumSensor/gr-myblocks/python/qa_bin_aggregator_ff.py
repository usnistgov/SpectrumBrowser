#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2014 <+YOU OR YOUR COMPANY+>.
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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import myblocks_swig as myblocks

class qa_bin_aggregator_ff (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # set up fg
	src_data = (1, 2.1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
	output_bin_index = (0, 1, 1, 2, 2, 2, 3, 3, 4, 4, 0, 5, 5, 6, 6, 6, 7, 7, 8, 8)
	expected_result = (5.1, 15, 15, 19, 25, 45, 35, 39)
	src = blocks.vector_source_f(src_data)
	s2v = blocks.stream_to_vector(gr.sizeof_float, 20)
	aggr = myblocks.bin_aggregator_ff(20, 8, output_bin_index)
	dst = blocks.vector_sink_f(8)
	self.tb.connect(src, s2v, aggr, dst)
        self.tb.run ()
        # check data
	result_data = dst.data()
	self.assertFloatTuplesAlmostEqual(expected_result, result_data, 6)

    def test_002_t (self):
        # set up fg
	src_data = (1, 2.1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
	output_bin_index = (1, 1, 1, 2, 2, 0, 3, 3, 4, 4)
	expected_result = (6.1, 9, 15, 19, 36, 29, 35, 39)
	src = blocks.vector_source_f(src_data)
	s2v = blocks.stream_to_vector(gr.sizeof_float, 10)
	aggr = myblocks.bin_aggregator_ff(10, 4, output_bin_index)
	dst = blocks.vector_sink_f(4)
	self.tb.connect(src, s2v, aggr, dst)
        self.tb.run ()
        # check data
	result_data = dst.data()
	self.assertFloatTuplesAlmostEqual(expected_result, result_data, 6)

if __name__ == '__main__':
    gr_unittest.run(qa_bin_aggregator_ff, "qa_bin_aggregator_ff.xml")
