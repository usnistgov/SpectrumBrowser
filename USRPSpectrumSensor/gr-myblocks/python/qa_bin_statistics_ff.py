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

class qa_bin_statistics_ff (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # set up fg
	src_data = (1, 2.1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
	# for average statistic
	expected_result = (8.5, 9.525, 10.5, 11.5, 12.5)
	# for total statistic
	# expected_result = (34, 38.1, 42, 46, 50)
	src = blocks.vector_source_f(src_data)
	s2v = blocks.stream_to_vector(gr.sizeof_float, 5)
	stats = myblocks.bin_statistics_ff(5, 4)
	dst = blocks.vector_sink_f(5)
	self.tb.connect(src, s2v, stats, dst)
        self.tb.run ()
        # check data
	result_data = dst.data()
	self.assertFloatTuplesAlmostEqual(expected_result, result_data, 5)

    def test_002_t (self):
        # set up fg
	src_data = (1, 2.1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
	# for average statistic
	expected_result = (3.5, 4.55, 5.5, 6.5, 7.5, 13.5, 14.5, 15.5, 16.5, 17.5)
	# for total statistic
	# expected_result = (7, 9.1, 11, 13, 15, 27, 29, 31, 33, 35)
	src = blocks.vector_source_f(src_data)
	s2v = blocks.stream_to_vector(gr.sizeof_float, 5)
	stats = myblocks.bin_statistics_ff(5, 2)
	dst = blocks.vector_sink_f(5)
	self.tb.connect(src, s2v, stats, dst)
        self.tb.run ()
        # check data
	result_data = dst.data()
	self.assertFloatTuplesAlmostEqual(expected_result, result_data, 6)


if __name__ == '__main__':
    gr_unittest.run(qa_bin_statistics_ff, "qa_bin_statistics_ff.xml")
