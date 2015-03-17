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

from gnuradio import gr, gr_unittest
from gnuradio import blocks, analog
import pmt
import usrpanalyzer_swig as usrpanalyzer


class tune_callback(gr.feval_dd):
    def __init__(self, tb):
        gr.feval_dd.__init__(self)
        self.tb = tb

    def eval(self, ignore):
        try:
            next_freq = self.tb.set_next_freq()
            # Make sure next_freq is float-compatible
            float(next_freq)
            return next_freq
        except Exception, e:
            print("TUNE_EXCEPTION: {}".format(e))


class rx_freq_tag_emitter_cc(gr.sync_block):
    """Fake a USRP by emitting 'rx_freq' stream tags."""
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="rx_freq_emitter",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )

        self.stream_tag_key = pmt.intern("rx_freq")
        self.stream_tag_value = None
        self.stream_tag_srcid = pmt.intern(self.name())
        self.tag_stream = False

        self.port_id = pmt.intern("command")
        self.message_port_register_in(self.port_id)
        self.set_msg_handler(self.port_id, self.set_tag_stream)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        ninput_items = len(in0)
        noutput_items = min(ninput_items, len(out))
        out[:noutput_items] = in0[:noutput_items]

        if self.tag_stream:
            tag = gr.python_to_tag({
                "offset": self.nitems_read(0)+ninput_items,
                "key": self.stream_tag_key,
                "value": self.stream_tag_value,
                "srcid": self.stream_tag_srcid,
            })
            self.add_item_tag(0, tag)
            self.tag_stream = False

        return noutput_items

    def set_tag_stream(self, msg):
        self.tag_stream = True
        self.stream_tag_value = pmt.to_pmt(pmt.to_python(msg)[1])


class top_block(gr.top_block):
    def __init__(self, tune_delay, ncopy, center_freqs):
        gr.top_block.__init__(self)
        self.tune_callback = tune_callback(self)
        self.configure(tune_delay, ncopy, center_freqs)

    def configure(self, tune_delay, ncopy, center_freqs):
        self.center_freqs = center_freqs
        nsegments = len(center_freqs)
        self.center_freq_iter = itertools.cycle(self.center_freqs)

        self.source = analog.noise_source_c(analog.GR_GAUSSIAN, 0.1)
        self.throttle = blocks.throttle(gr.sizeof_gr_complex, 1e6)
        self.tag_emitter = rx_freq_tag_emitter_cc()
        self.ctrl_block = usrpanalyzer.controller_cc(
            self.tune_callback,
            tune_delay,
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

    def reconfigure(self, tune_delay, ncopy, center_freqs):
        self.lock()
        self.disconnect_all()
        self.configure(tune_delay, ncopy, center_freqs)
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
        tune_delay = 100
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb = top_block(tune_delay, ncopy, center_freqs)

    def tearDown(self):
        self.tb = None

    def test_get_set_clear_exit_after_complete(self):
        self.assertFalse(self.tb.get_exit_after_complete())
        self.tb.set_exit_after_complete()
        self.assertTrue(self.tb.get_exit_after_complete())
        self.tb.clear_exit_after_complete()
        self.assertFalse(self.tb.get_exit_after_complete())

    def test_multi_cfreqs_delay_single_run(self):
        tune_delay = 100
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_multi_cfreqs_no_delay_single_run(self):
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_no_delay_single_run(self):
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_delay_single_run(self):
        tune_delay = 100
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_multi_cfreqs_no_delay_two_single_runs_with_recfg(self):
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        # Note: insufficient connected input ports (1 needed, 0 connected)
        #       error can be caused by calling self.disconnect but not
        #       self.msg_disconnect while reconfiguring flowgraph.

        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_no_delay_two_single_runs_without_recfg(self):
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 1

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_multi_cfreqs_no_delay_two_single_runs_without_recfg(self):
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 5

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

        self.assertTrue(self.tb.get_exit_after_complete())

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)

    def test_single_cfreq_no_delay_continuous_run(self):
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(1.0) # array([ 0.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
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
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
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
        tune_delay = 0
        ncopy = 100
        center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
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

    def test_multi_cfreqs_no_delay_single_runs_with_large_ncopy(self):
        """Large ncopy exposes errors of needing to copying more than one
        buffer full of samples per segment"""
        tune_delay = 0
        n_averages = 30
        ncopy = 1024*n_averages
        center_freqs = np.arange(3.0) # array([ 0.,  1.,  2.])
        self.tb.reconfigure(tune_delay, ncopy, center_freqs)
        n_cfreqs = len(center_freqs)  # 3

        self.tb.set_exit_after_complete()
        self.tb.run()

        self.assertEqual(self.tb.ctrl_block.nitems_written(0), ncopy * n_cfreqs)


if __name__ == '__main__':
    import os
    print("Blocked waiting for GDB attach (pid = {})".format(os.getpid()))
    raw_input("Press Enter to continue...")

    gr_unittest.run(qa_controller_cc, "qa_controller_cc.xml")
