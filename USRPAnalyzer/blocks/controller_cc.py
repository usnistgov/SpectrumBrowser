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

import pmt
from gnuradio import gr


class controller_cc(gr.basic_block):
    def __init__(self, tune_callback, tune_delay, n_copy, n_segments):
        gr.basic_block.__init__(
            self,
            name="controller_cc",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.tune_callback = tune_callback
        self.tune_delay = tune_delay # n samps to skip after tune/before copy
        self.n_segments = n_segments
        self.retune = n_segments > 1
        self.current_segment = 1
        self.n_skipped = 0
        self.n_copy = n_copy
        self.n_copied = 0
        self.got_rx_freq_tag = False
        self.current_freq = None

        self.tag_key = pmt.intern("rx_freq")

        self.exit_after_complete = False
        self.exit_flowgraph = False

    def general_work(self, input_items, output_items):
        ninput_items = len(input_items[0])
        noutput_items = len(output_items[0])
        in0 = input_items[0]
        out = output_items[0]

        if self.current_freq is None:
            self.current_freq = self.tune_callback.calleval(0.0)
            self.consume_each(0)
            return 0

        if self.exit_flowgraph:
            self.consume_each(0)
            return -1

        if not self.got_rx_freq_tag:
            #get_tags_in_range(which_input, range_start, range_stop, tag_key)
            range_start = self.nitems_read(0)
            range_stop = range_start + ninput_items
            tags = self.get_tags_in_range(
                0, range_start, range_stop, self.tag_key
            )
            if tags:
                rel_offset = tags[0].offset - range_start
                self.got_rx_freq_tag = True
                self.consume_each(rel_offset-1)
                return 0
            else:
                self.consume_each(ninput_items)
                return 0

        skips_left = self.tune_delay - self.n_skipped
        if skips_left:
            nskip = min(noutput_items, ninput_items, skips_left)
            self.consume_each(nskip)
            self.n_skipped += nskip
            return 0

        copies_left = self.n_copy - self.n_copied
        ncopy = min(noutput_items, ninput_items, copies_left)
        out[:ncopy] = in0[:ncopy]
        self.n_copied += ncopy
        self.consume_each(ncopy)

        done_copying = self.n_copied == self.n_copy
        last_segment = self.current_segment == self.n_segments

        if done_copying:
            if last_segment and self.exit_after_complete:
                self.exit_flowgraph = True
            elif self.retune:
                self.current_freq = self.tune_callback.calleval(0.0)
                self.current_segment += 1
                self.got_rx_freq_tag = False
                self.n_copied = 0

        return ncopy

    def set_exit_after_complete(self):
        self.exit_after_complete = True


if __name__ == "__main__":
    # Run block test

    import itertools
    import unittest

    from gnuradio import blocks, analog

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
        def __init__(self, tune_delay, n_copy, center_freqs):
            gr.top_block.__init__(self)
            self.tune_callback = tune_callback(self)
            self.configure(tune_delay, n_copy, center_freqs)

        def configure(self, tune_delay, n_copy, center_freqs):
            self.center_freqs = center_freqs
            n_segments = len(center_freqs)
            self.center_freq_iter = itertools.cycle(self.center_freqs)

            self.source = analog.noise_source_c(analog.GR_GAUSSIAN, 0.1)
            self.throttle = blocks.throttle(gr.sizeof_gr_complex, 1e6)
            self.tag_emitter = rx_freq_tag_emitter_cc()
            self.ctrl_block = controller_cc(
                self.tune_callback,
                tune_delay,
                n_copy,
                n_segments
            )
            self.tag_debug = blocks.tag_debug(gr.sizeof_gr_complex, "tag_debug", "rx_freq")
            self.tag_debug.set_display(False)
            self.msg_debug = blocks.message_debug()
            self.sink = blocks.null_sink(gr.sizeof_gr_complex)

            self.connect(self.source, self.throttle, self.tag_emitter)
            self.connect((self.tag_emitter, 0), self.tag_debug)
            self.connect((self.tag_emitter, 0), self.ctrl_block, self.sink)

        def reconfigure(self, tune_delay, n_copy, center_freqs):
            self.disconnect_all()
            self.configure(tune_delay, n_copy, center_freqs)

        def set_next_freq(self):
            next_freq = next(self.center_freq_iter)
            msg = pmt.cons(pmt.intern("rx_freq"), pmt.to_pmt(next_freq))
            self.tag_emitter.to_basic_block()._post(pmt.intern("command"), msg)

            return next_freq

        def set_exit_after_complete(self):
            self.ctrl_block.set_exit_after_complete()


    class test_controller_cc(unittest.TestCase):
        def setUp(self):
            tune_delay = 100
            n_copy = 100
            center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
            self.tb = top_block(tune_delay, n_copy, center_freqs)

        def test_multi_cfreqs_delay_single_run(self):
            tune_delay = 100
            n_copy = 100
            center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
            self.tb.lock()
            self.tb.reconfigure(tune_delay, n_copy, center_freqs)
            self.tb.unlock()
            n_cfreqs = len(center_freqs)  # 5

            self.assertFalse(self.tb.ctrl_block.exit_after_complete)
            self.tb.set_exit_after_complete()
            self.assertTrue(self.tb.ctrl_block.exit_after_complete)

            self.tb.run()

            self.assertEqual(self.tb.ctrl_block.nitems_written(0), n_copy * n_cfreqs)

        def test_multi_cfreqs_no_delay_single_run(self):
            tune_delay = 0
            n_copy = 100
            center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
            self.tb.lock()
            self.tb.reconfigure(tune_delay, n_copy, center_freqs)
            self.tb.unlock()
            n_cfreqs = len(center_freqs)  # 5

            self.assertFalse(self.tb.ctrl_block.exit_after_complete)
            self.tb.set_exit_after_complete()
            self.assertTrue(self.tb.ctrl_block.exit_after_complete)

            self.tb.run()

            self.assertEqual(self.tb.ctrl_block.nitems_written(0), n_copy * n_cfreqs)

        def test_single_cfreq_no_delay_single_run(self):
            tune_delay = 0
            n_copy = 100
            center_freqs = np.arange(1.0) # array([ 0.])
            self.tb.lock()
            self.tb.reconfigure(tune_delay, n_copy, center_freqs)
            self.tb.unlock()
            n_cfreqs = len(center_freqs)  # 1

            self.assertFalse(self.tb.ctrl_block.exit_after_complete)
            self.tb.set_exit_after_complete()
            self.assertTrue(self.tb.ctrl_block.exit_after_complete)

            self.tb.run()

            self.assertEqual(self.tb.ctrl_block.nitems_written(0), n_copy * n_cfreqs)

        def test_single_cfreq_delay_single_run(self):
            tune_delay = 100
            n_copy = 100
            center_freqs = np.arange(1.0) # array([ 0.])
            self.tb.lock()
            self.tb.reconfigure(tune_delay, n_copy, center_freqs)
            self.tb.unlock()
            n_cfreqs = len(center_freqs)  # 1

            self.assertFalse(self.tb.ctrl_block.exit_after_complete)
            self.tb.set_exit_after_complete()
            self.assertTrue(self.tb.ctrl_block.exit_after_complete)

            self.tb.run()

            self.assertEqual(self.tb.ctrl_block.nitems_written(0), n_copy * n_cfreqs)

        def test_multi_cfreqs_no_delay_two_single_runs(self):
            tune_delay = 0
            n_copy = 100
            center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
            self.tb.lock()
            self.tb.reconfigure(tune_delay, n_copy, center_freqs)
            self.tb.unlock()
            n_cfreqs = len(center_freqs)  # 5

            self.assertFalse(self.tb.ctrl_block.exit_after_complete)
            self.tb.set_exit_after_complete()
            self.assertTrue(self.tb.ctrl_block.exit_after_complete)

            self.tb.run()

            self.assertEqual(self.tb.ctrl_block.nitems_written(0), n_copy * n_cfreqs)

            # Note: insufficient connected input ports (1 needed, 0 connected)
            #       error can be caused by calling self.disconnect but not
            #       self.msg_disconnect while reconfiguring flowgraph.

            tune_delay = 0
            n_copy = 100
            center_freqs = np.arange(5.0) # array([ 0.,  1.,  2.,  3.,  4.])
            self.tb.lock()
            self.tb.reconfigure(tune_delay, n_copy, center_freqs)
            self.tb.unlock()
            n_cfreqs = len(center_freqs)  # 5

            self.assertFalse(self.tb.ctrl_block.exit_after_complete)
            self.tb.set_exit_after_complete()
            self.assertTrue(self.tb.ctrl_block.exit_after_complete)

            self.tb.run()

            self.assertEqual(self.tb.ctrl_block.nitems_written(0), n_copy * n_cfreqs)


    unittest.main()
