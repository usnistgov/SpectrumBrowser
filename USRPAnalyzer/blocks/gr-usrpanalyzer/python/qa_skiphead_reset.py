#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Douglas Anderson
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

class qa_skiphead_reset (gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()
        self.src_data = np.arange(65536)

    def tearDown(self):
        self.tb = None

    def test_skip_0(self):
        skip_cnt = 0
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_1(self):
        skip_cnt = 1
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_1023(self):
        skip_cnt = 1023
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_6339(self):
        skip_cnt = 6339
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_12678(self):
        skip_cnt = 12678
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_all(self):
        skip_cnt = len(self.src_data)
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_reset(self):
        skip_cnt = 2
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)
        op.reset()
        src1.rewind()
        self.tb.run()
        self.assertAlmostEqual(expected_result, dst_data, 6)

    def test_skip_reset_then_copy(self):
        skip_cnt = 2
        expected_result = tuple(self.src_data[skip_cnt:])
        src1 = blocks.vector_source_f(self.src_data)
        op = usrpanalyzer.skiphead_reset(gr.sizeof_float, skip_cnt)
        dst1 = blocks.vector_sink_f()
        self.tb.connect(src1, op, dst1)
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(expected_result, dst_data, 6)
        op.reset()
        src1.rewind()
        self.tb.run()
        self.assertAlmostEqual(expected_result, dst_data, 6)

        # run again without resetting skiphead
        dst1.reset() # empty data vsink
        src1.rewind()
        self.tb.run()
        dst_data = dst1.data()
        self.assertAlmostEqual(tuple(self.src_data), dst_data, 6)


if __name__ == '__main__':
    gr_unittest.run(qa_skiphead_reset, "qa_skiphead_reset.xml")
