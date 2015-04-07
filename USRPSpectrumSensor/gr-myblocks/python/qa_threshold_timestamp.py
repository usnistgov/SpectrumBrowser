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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import myblocks_swig as myblocks

class qa_threshold_timestamp (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # set up fg
	src_data = (0, 0, 1, 0, 0, 1.0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1, 0, 0)
	src = blocks.vector_source_f(src_data)
	f2c = blocks.float_to_complex(1)
	s2v = blocks.stream_to_vector(gr.sizeof_gr_complex, 5)
	f = open('/raid/souryal/temp/threshold_timestamp_test001.out', 'w')
	tts = myblocks.threshold_timestamp(5, gr.sizeof_gr_complex, 0, 6.0, f.fileno())
	ns = blocks.null_sink(5 * gr.sizeof_float)
	self.tb.connect(src, f2c, s2v, tts, ns)
        self.tb.run ()
	f.close()
        # check data
	# look for 1 line of 'Current time' written to
        # file 'threshold_timestamp_test001.out'

    def test_002_t (self):
        # set up fg
	src_data = (0, 0, 1, 0, 0, 1.0, 1, 2, 1, 1, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1, 0, 0)
	src = blocks.vector_source_f(src_data)
	f2c = blocks.float_to_char()
	s2v = blocks.stream_to_vector(gr.sizeof_char, 5)
	f = open('/raid/souryal/temp/threshold_timestamp_test002.out', 'w')
	tts = myblocks.threshold_timestamp(5, gr.sizeof_char, 1, 1.5, f.fileno())
	ns = blocks.null_sink(5 * gr.sizeof_float)
	self.tb.connect(src, f2c, s2v, tts, ns)
        self.tb.run ()
	f.close()
        # check data
	# look for 1 line of 'Current time' written to
        # file 'threshold_timestamp_test002.out'


if __name__ == '__main__':
    gr_unittest.run(qa_threshold_timestamp, "qa_threshold_timestamp.xml")
