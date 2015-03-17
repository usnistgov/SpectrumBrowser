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


import sys
import math
import time
import threading
import logging
import numpy as np
import itertools
from copy import copy
from decimal import Decimal

from gnuradio import gr
from gnuradio import blocks
from gnuradio.filter import fractional_resampler_cc
from gnuradio import fft
from gnuradio import uhd

from usrpanalyzer import (
    skiphead_reset, controller_cc, bin_statistics_ff, stitch_fft_segments_ff
)
from blocks.plotter_f import plotter_f
from configuration import configuration
from parser import init_parser
import gui


class tune_callback(gr.feval_dd):
    def __init__(self, u, cfg):
        gr.feval_dd.__init__(self)
        self.u = u
        self.cfg = cfg

        self.logger = logging.getLogger("USRPAnalyzer.tune_callback")
        self.cfreq_iter = itertools.cycle(cfg.center_freqs)
        self.tune_result = None

    def eval(self, *args):
        try:
            next_freq = self.get_next_freq()
            success = self.set_freq(next_freq)
            return self.tune_result.actual_rf_freq
        except Exception, e:
            self.logger.error(e)

    def get_next_freq(self):
        """Step to the next center frequency."""
        return next(self.cfreq_iter) # step cyclical iterator

    def set_freq(self, target_freq):
        """Set the center frequency and LO offset of the USRP."""
        r = self.u.set_center_freq(uhd.tune_request(
            target_freq,
            rf_freq=(target_freq + self.cfg.lo_offset),
            rf_freq_policy=uhd.tune_request.POLICY_MANUAL
        ))

        if r:
            self.tune_result = r
            return True
        return False


class top_block(gr.top_block):
    def __init__(self, cfg):
        gr.top_block.__init__(self)

        self.logger = logging.getLogger("USRPAnalyzer.top_block")

        # Use 2 copies of the configuration:
        # cgf - settings that matches the current state of the flowgraph
        # pending_cfg - requested config changes that will be applied during
        #               the next run of configure
        self.cfg = cfg
        self.pending_cfg = copy(self.cfg)

        if cfg.realtime:
            # Attempt to enable realtime scheduling
            r = gr.enable_realtime_scheduling()
            if r != gr.RT_OK:
                self.logger.warning("failed to enable realtime scheduling")

        self.stream_args = uhd.stream_args(
            cpu_format=cfg.cpu_format,
            otw_format=cfg.wire_format,
            args=cfg.stream_args
        )

        self.u = uhd.usrp_source(
            device_addr=cfg.device_addr,
            stream_args=self.stream_args
        )

        self.sample_rates = np.array(
            [r.start() for r in self.u.get_samp_rates().iterator()],
            dtype=np.float
        )

        self.lte_rates = np.array([
            # rate (Hz) | Ch BW (MHz) | blocks | occupied | DFT size | samps/slot
            1.92e6,    #|     1.4     |  6     |   72     |  128     |   960
            3.83e6,    #|     3       |  15    |   180    |  256     |   1920
            7.68e6,    #|     5       |  25    |   300    |  512     |   3840
            15.36e6,   #|     10      |  50    |   600    |  1024    |   7680
            23.04e6,   #|     15      |  75    |   900    |  1536    |   11520
            30.72e6    #|     20      |  100   |   1200   |  2048    |   15360
        ], dtype=np.float)

        # Default to 0 gain, full attenuation
        if cfg.gain is None:
            g = self.u.get_gain_range()
            cfg.gain = g.start()

        self.set_gain(cfg.gain)
        self.gain = cfg.gain

        # Holds the most recent tune_result object returned by uhd.tune_request
        self.tune_result = None

        # The main loop blocks at the end of the loop until either continuous
        # or single run mode is set.
        self.continuous_run = threading.Event()
        self.single_run = threading.Event()

        self.current_freq = None

        self.reset_stream_args = False

        self.plot_iface = gui.plot_interface(self)

        self.rebuild_flowgraph = False
        self.configure(initial=True)

    def set_single_run(self):
        self.clear_continuous_run()
        self.single_run.set()

    def clear_single_run(self):
        self.single_run.clear()

    def set_continuous_run(self):
        self.clear_single_run()
        self.clear_exit_after_complete()
        self.continuous_run.set()

    def clear_continuous_run(self):
        self.set_exit_after_complete()
        self.continuous_run.clear()

    def set_exit_after_complete(self):
        self.ctrl.set_exit_after_complete()

    def clear_exit_after_complete(self):
        self.ctrl.clear_exit_after_complete()

    def reconfigure(self, redraw_plot=False, reset_stream_args=False):
        msg = "tb.reconfigure called - redraw_plot: {}, reset_stream_args: {}"
        self.logger.debug(msg.format(redraw_plot, reset_stream_args))
        self.rebuild_flowgraph = True
        self.set_exit_after_complete()
        self.reset_stream_args = reset_stream_args
        if redraw_plot:
            self.plot_iface.redraw_plot.set()

    def configure(self, initial=False):
        """Configure or reconfigure the flowgraph"""

        self.lock()
        if not initial:
            self.disconnect_all()
            self.msg_disconnect(self.plot, "gui_busy_notifier", self.copy_if_gui_idle, "en")

        # Apply any pending configuration changes
        cfg = self.cfg = copy(self.pending_cfg)

        self.stream_args = uhd.stream_args(
            cpu_format=cfg.cpu_format,
            otw_format=cfg.wire_format,
            args=cfg.stream_args
        )

        if self.reset_stream_args:
            self.u.set_stream_args(self.stream_args)
            self.reset_stream_args = False

        if cfg.subdev_spec:
            self.u.set_subdev_spec(cfg.subdev_spec, 0)

        # Set the antenna
        if cfg.antenna:
            self.u.set_antenna(cfg.antenna, 0)

        self.resampler = None
        self.set_sample_rate(cfg.sample_rate)

        #TODO: consider relying on rx_freq tag for single acquisition as well
        # Skip first 30 ms of samples to allow USRP to wake up
        n_skip = int(cfg.sample_rate * 0.1)
        self.skip = skiphead_reset(gr.sizeof_gr_complex, n_skip)
        self.tune_callback = tune_callback(self.u, cfg)
        self.ctrl = controller_cc(
            self.tune_callback,
            cfg.tune_delay,
            cfg.fft_size * cfg.n_averages,
            cfg.n_segments
        )

        stream_to_fft_vec = blocks.stream_to_vector(
            gr.sizeof_gr_complex, cfg.fft_size
        )

        forward = True
        shift = True
        self.fft = fft.fft_vcc(
            cfg.fft_size,
            forward,
            cfg.window_coefficients,
            shift
        )

        c2mag_sq = blocks.complex_to_mag_squared(cfg.fft_size)

        stats = bin_statistics_ff(cfg.fft_size, cfg.n_averages)

        power = sum(tap*tap for tap in cfg.window_coefficients)

        # Divide magnitude-square by a constant to obtain power
        # in Watts. Assumes unit of USRP source is volts.
        impedance = 50.0 # ohms
        Vsq2W_dB = -10.0 * math.log10(cfg.fft_size * power * impedance)
        # Convert from Watts to dBm.
        W2dBm = blocks.nlog10_ff(10.0, cfg.fft_size, 30 + Vsq2W_dB)

        stitch = stitch_fft_segments_ff(
            cfg.fft_size,
            cfg.n_segments,
            cfg.overlap
        )

        fft_vec_to_stream = blocks.vector_to_stream(gr.sizeof_float, cfg.fft_size)
        n_valid_bins = cfg.fft_size - (cfg.fft_size * (cfg.overlap / 2) * 2)
        #FIXME: think about whether to cast to int vs round vs...
        stitch_vec_len = int(cfg.n_segments * cfg.fft_size)
        stream_to_stitch_vec = blocks.stream_to_vector(gr.sizeof_float, stitch_vec_len)

        plot_vec_len = int(cfg.n_segments * n_valid_bins)

        # Only copy sample to plot if enabled to keep from overwhelming gui thread
        self.copy_if_gui_idle = blocks.copy(gr.sizeof_float * plot_vec_len)

        self.plot = plotter_f(self, plot_vec_len)

        # Create the flowgraph:
        #
        # USRP   - hardware source output stream of 32bit complex floats
        # resamp - rational resampler for LTE sample rates
        # skip   - for each run of flowgraph, drop N samples, then copy
        # ctrl   - copy N samples then call retune callback and loop
        # fft    - compute forward FFT, complex in complex out
        # mag^2  - convert vectors from complex to real by taking mag squared
        # stats  - linear average vectors if n_averages > 1
        # W2dBm  - convert volt to dBm
        # stitch - overlap FFT segments by a certain number of bins
        # plot   - plot resulting data without overwhelming gui thread
        #
        # USRP > (resamp) > skip > ctrl > fft > mag^2 > stats > W2dBm > stitch > plot

        if self.resampler:
            self.connect(self.u, self.resampler, self.skip)
        else:
            self.connect(self.u, self.skip)
        self.connect(self.skip, self.ctrl, stream_to_fft_vec, self.fft)
        self.connect(self.fft, c2mag_sq, stats, W2dBm, fft_vec_to_stream)
        self.connect(fft_vec_to_stream, stream_to_stitch_vec, stitch)
        self.connect(stitch, self.copy_if_gui_idle, self.plot)

        self.msg_connect(self.plot, "gui_busy_notifier", self.copy_if_gui_idle, "en")

        if cfg.continuous_run:
            self.set_continuous_run()
        else:
            self.set_exit_after_complete()

        self.unlock()

    def set_sample_rate(self, rate):
        """Set the USRP sample rate"""
        hwrate = rate

        if rate in self.lte_rates:
            # Select closest USRP sample rate higher than LTE rate
            hwrate = self.sample_rates[
                np.abs(self.sample_rates - rate).argmin() + 1
            ]
            phase_shift = 0.0
            resamp_ratio = hwrate / rate
            self.resampler = fractional_resampler_cc(phase_shift, resamp_ratio)
        else:
            self.resampler = None

        self.u.set_samp_rate(hwrate)
        if self.resampler:
            self.sample_rate = rate
        else:
            self.sample_rate = self.u.get_samp_rate()

        # Pass the actual samp rate back to cfgs so they have it before
        # calling cfg.update()
        requested_rate = self.cfg.sample_rate
        self.pending_cfg.sample_rate = self.cfg.sample_rate = self.sample_rate

        # If the rate was adjusted, recalculate freqs and reconfigure flowgraph
        if requested_rate != self.sample_rate:
            self.pending_cfg.update()
            self.reconfigure(redraw_plot=True)

        resample = " using fractional resampler" if self.resampler else ""
        msg = "sample rate is {} S/s {}".format(int(self.sample_rate), resample)
        self.logger.debug(msg)

    def set_gain(self, gain):
        """Let UHD decide how to distribute gain."""
        self.u.set_gain(gain)

    def set_ADC_gain(self, gain):
        """Via uhd_usrp_probe:
        Name: ads62p44 (TI Dual 14-bit 105MSPS ADC)
        Gain range digital: 0.0 to 6.0 step 0.5 dB
        Gain range fine: 0.0 to 0.5 step 0.1 dB
        """
        max_digi = self.u.get_gain_range('ADC-digital').stop()
        max_fine = self.u.get_gain_range('ADC-fine').stop()
        # crop to 0.0 - 6.0
        cropped = Decimal(str(max(0.0, min(max_digi, float(gain)))))
        mod = cropped % Decimal(max_fine)  # ex: 5.7 -> 0.2
        fine = round(mod, 1)               # get fine in terms steps of 0.1
        digi = float(cropped - mod)        # ex: 5.7 - 0.2 -> 5.5
        self.u.set_gain(digi, 'ADC-digital')
        self.u.set_gain(fine, 'ADC-fine')

        return (digi, fine) # return vals for testing

    def get_gain(self):
        """Return total ADC gain as float."""
        return self.u.get_gain('ADC-digital') + self.u.get_gain('ADC-fine')

    def get_gain_range(self, name=None):
        """Return a UHD meta range object for whole range or specific gain.

        Available gains: ADC-digital ADC-fine PGA0
        """
        return self.u.get_gain_range(name if name else "")

    def get_ADC_digital_gain(self):
        return self.u.get_gain('ADC-digital')

    def get_ADC_fine_gain(self):
        return self.u.get_gain('ADC-fine')

    def get_attenuation(self):
        max_atten = self.u.get_gain_range('PGA0').stop()
        return max_atten - self.u.get_gain('PGA0')

    def set_attenuation(self, atten):
        """Adjust level on Hittite HMC624LP4E Digital Attenuator.

        UHD driver increases gain by removing attenuation, so to:
        - add 10dB attenuation, we need to remove 10dB gain from PGA0
        - remove 10dB attenuation, we need to add 10dB gain to PGA0

        Specs: Range 0 - 31.5 dB, 0.5 dB step
        NOTE: uhd driver handles range input for the attenuator
        """
        max_atten = self.u.get_gain_range('PGA0').stop()
        self.u.set_gain(max_atten - atten, 'PGA0')

#   @staticmethod
#   def _chunks(l, n):
#       """Yield successive n-sized chunks from l"""
#       for i in xrange(0, len(l), n):
#           yield l[i:i+n]

def main(tb):
    """Run the main loop of the program"""

    logger = logging.getLogger('USRPAnalyzer.main')
    gui_alive = True

    while True:
        # Execute flow graph and wait for it to stop
        tb.run()
        tb.clear_single_run()

        #FIXME: import pdb; pdb.set_trace() shows plot.update not handling first plot
        if tb.continuous_run.is_set() and not tb.plot_iface.is_alive():
            # FIXME: this isn't fool-proof
            # GUI was destroyed while in continuous mode
            return

        while not (tb.single_run.is_set() or tb.continuous_run.is_set()):
            # keep certain gui elements alive
            gui_alive = tb.plot_iface.keep_alive()
            if not gui_alive:
                # GUI was destroyed while in single mode
                return
            # check run mode again in 1/4 second
            time.sleep(.25)

        if tb.rebuild_flowgraph:
            tb.configure()
            tb.rebuild_flowgraph = False

        tb.skip.reset()


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()
    cfg = configuration(args)

    if cfg.debug:
        import os
        print("Blocked waiting for GDB attach (pid = {})".format(os.getpid()))
        raw_input("Press Enter to continue...")

    tb = top_block(cfg)
    try:
        main(tb)
        logging.getLogger('USRPAnalyzer').info("Exiting.")
    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
