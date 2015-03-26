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

import time
import numpy as np
import itertools

from gnuradio import gr, gr_unittest, uhd
from gnuradio import blocks, analog
import pmt
import usrpanalyzer_swig as usrpanalyzer


class top_block(gr.top_block):
    def __init__(self, skip_initial, ncopy, center_freqs):
        gr.top_block.__init__(self)
        self.configure(skip_initial, ncopy, center_freqs)

    def configure(self, skip_initial, ncopy, center_freqs):
        self.center_freqs = center_freqs
        nsegments = len(center_freqs)
        self.center_freq_iter = itertools.cycle(self.center_freqs)

        self.u = uhd.usrp_source(device_addr="", stream_args=uhd.stream_args("fc32"))

        self.source = analog.noise_source_c(analog.GR_GAUSSIAN, 0.1)
        self.throttle = blocks.throttle(gr.sizeof_gr_complex, 1e6)
        self.ctrl_block = usrpanalyzer.controller_cc(
            self.u,
            skip_initial,
            ncopy,
            nsegments
        )
        self.tag_debug = blocks.tag_debug(gr.sizeof_gr_complex, "tag_debug", "rx_freq")
        self.tag_debug.set_display(False)
        self.msg_debug = blocks.message_debug()
        self.sink = blocks.null_sink(gr.sizeof_gr_complex)

        self.connect(self.source, self.throttle, self.tag_emitter)
        self.connect((self.tag_emitter, 0), self.tag_debug)
        self.connect((self.tag_emitter, 0), self.ctrl_block, self.sink)

    def reconfigure(self, skip_initial, ncopy, center_freqs):
        self.lock()
        self.disconnect_all()
        self.configure(skip_initial, ncopy, center_freqs)
        self.unlock()

    def set_next_freq(self):
        next_freq = next(self.center_freq_iter)
        msg = pmt.cons(pmt.intern("rx_freq"), pmt.to_pmt(next_freq))
        self.tag_emitter.to_basic_block()._post(pmt.intern("command"), msg)

        return next_freq

    def get_exit_after_complete(self):
        return self.ctrl_block.get_exit_after_complete()

    def set_exit_after_complete(self):
        self.ctrl_block.set_exit_after_complete()

    def clear_exit_after_complete(self):
        self.ctrl_block.clear_exit_after_complete()


class qa_controller_cc(gr_unittest.TestCase):
    def setUp(self):
        skip_initial = 100
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb = top_block(skip_initial, ncopy, center_freqs)

    def tearDown(self):
        self.tb = None

    def test_get_set_clear_exit_after_complete(self):
        self.assertFalse(self.tb.get_exit_after_complete())
        self.tb.set_exit_after_complete()
        self.assertTrue(self.tb.get_exit_after_complete())
        self.tb.clear_exit_after_complete()
        self.assertFalse(self.tb.get_exit_after_complete())

    def test_multi_cfreqs_delay_single_run(self):
        skip_initial = 100
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_multi_cfreqs_no_delay_single_run(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_no_delay_single_run(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_delay_single_run(self):
        skip_initial = 100
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_multi_cfreqs_no_delay_two_single_runs_with_recfg(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        # Note: insufficient connected input ports (1 needed, 0 connected)
        #       error can be caused by calling self.disconnect but not
        #       self.msg_disconnect while reconfiguring flowgraph.

        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_no_delay_two_single_runs_without_recfg(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_multi_cfreqs_no_delay_two_single_runs_without_recfg(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        self.assertTrue(self.tb.get_exit_after_complete())

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_no_delay_continuous_run(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.assertFalse(self.tb.get_exit_after_complete())

        self.tb.start()
        while True:
            if self.tb.ctrl_block.nitems_written(0) > (ncopy * n_cfreqs * 10):
                self.tb.set_exit_after_complete()
                break
                time.sleep(0.1)

        self.tb.wait()
        self.assertGreater(self.tb.ctrl_block.nitems_written(0), (ncopy *n_cfreqs * 10))

    def test_multiple_cfreqs_no_delay_continuous_run(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.assertFalse(self.tb.ctrl_block.get_exit_after_complete())

        self.tb.start()
        while True:
            if self.tb.ctrl_block.nitems_written(0) > (ncopy * n_cfreqs * 2):
                self.tb.set_exit_after_complete()
                break
                time.sleep(0.1)

        self.tb.wait()
        self.assertGreater(self.tb.ctrl_block.nitems_written(0), (ncopy * n_cfreqs * 2))

    def test_start_single_to_continuous_run(self):
        skip_initial = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.start()
        self.tb.clear_exit_after_complete()
        self.assertFalse(self.tb.get_exit_after_complete())
        while True:
            if self.tb.ctrl_block.nitems_written(0) > (ncopy * n_cfreqs * 2):
                self.tb.set_exit_after_complete()
                break
                time.sleep(0.1)

        self.tb.wait()
        self.assertGreater(self.tb.ctrl_block.nitems_written(0), (ncopy * n_cfreqs * 2))

    def test_multi_cfreqs_no_delay_single_run_with_large_ncopy(self):
        """Large ncopy exposes errors of needing to copying more than one
        buffer full of samples per segment"""
        skip_initial = 0
        n_averages = 30
        ncopy = 1024*n_averages
        center_freqs = np.arange(3.0) # array([ 0.,  1.,  2.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 3

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_large_delay_single_runs_with_large_ncopy(self):
        skip_initial = 10000
        n_averages = 30
        ncopy = 1024*n_averages
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(skip_initial, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

if __name__ == '__main__':
    #import os
    #print("Blocked waiting for GDB attach (pid = {})".format(os.getpid()))
    #raw_input("Press Enter to continue...")

    gr_unittest.run(qa_controller_cc, "qa_controller_cc.xml")
