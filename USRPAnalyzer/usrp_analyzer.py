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


import os
import sys
import math
import time
import threading
import logging
import numpy as np
import scipy.io as sio # export to matlab file support
from copy import copy
from decimal import Decimal
from itertools import izip

from gnuradio import gr
from gnuradio import blocks
from gnuradio.filter import fractional_resampler_cc
from gnuradio import fft
from gnuradio import uhd

from usrpanalyzer import bin_statistics_ff, skiphead_reset
from configuration import configuration
from parser import init_parser
import gui


class top_block(gr.top_block):
    def __init__(self, cfg):
        gr.top_block.__init__(self)

        # Set logging levels
        self.logger = logging.getLogger('USRPAnalyzer')
        console_handler = logging.StreamHandler()
        logfmt = logging.Formatter("%(levelname)s:%(funcName)s: %(message)s")
        console_handler.setFormatter(logfmt)
        self.logger.addHandler(console_handler)
        if args.debug:
            loglvl = logging.DEBUG
        else:
            loglvl = logging.INFO
        self.logger.setLevel(loglvl)

        # Use 2 copies of the configuration:
        # cgf - settings that matches the current state of the flowgraph
        # pending_cfg - requested config changes that will be applied during
        #               the next run of configure_flowgraph
        self.cfg = cfg
        self.pending_cfg = copy(self.cfg)

        realtime = False
        if args.real_time:
            # Attempt to enable realtime scheduling
            r = gr.enable_realtime_scheduling()
            if r == gr.RT_OK:
                realtime = True
            else:
                self.logger.warning("failed to enable realtime scheduling")

        stream_args = {
            'cpu_format': 'fc32',
            'otw_format': cfg.wire_format,
            'args': cfg.stream_args
        }
        self.u = uhd.usrp_source(
            device_addr=args.device_addr,
            stream_args=uhd.stream_args(**stream_args)
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

        # FIXME:
        # Default to 0 gain, full attenuation
        if args.gain is None:
            g = self.u.get_gain_range()
            args.gain = g.start()

        self.set_gain(args.gain)
        self.gain = args.gain

        # Holds the most recent tune_result object returned by uhd.tune_request
        self.tune_result = None

        # The main loop clears this every time it makes a call to the gui and
        # the gui's EVT_IDLE event sets it when it done processing that
        # request.  After running the flowgraph, the main loop waits until
        # this is set before looping, allowing us to run the flowgraph as fast
        # as possible, but not faster!
        self.gui_idle = threading.Event()

        # The main loop blocks at the end of the loop until either continuous
        # or single run mode is set.
        self.continuous_run = threading.Event()
        self.single_run = threading.Event()
        if args.continuous_run:
            self.continuous_run.set()

        self.reconfigure = False
        self.reconfigure_usrp = False

        self.configure_flowgraph()

    def configure_flowgraph(self):
        """Configure or reconfigure the flowgraph"""

        self.disconnect_all()
        self.reconfigure = False

        # Apply any pending configuration changes
        cfg = self.cfg = copy(self.pending_cfg)

        stream_args = {
            'cpu_format': 'fc32',
            'otw_format': cfg.wire_format,
            'args': cfg.stream_args
        }
        if self.reconfigure_usrp:
            self.u.issue_stream_cmd(uhd.stream_args(**stream_args))
            self.reconfigure_usrp = False

        if cfg.spec:
            self.u.set_subdev_spec(cfg.spec, 0)

        # Set the antenna
        if cfg.antenna:
            self.u.set_antenna(cfg.antenna, 0)

        self.resampler = None
        self.set_sample_rate(cfg.sample_rate)

        # Skip "tune_delay" complex samples, customized to be resetable
        self.skip = skiphead_reset(gr.sizeof_gr_complex, cfg.tune_delay)

        s2v = blocks.stream_to_vector(gr.sizeof_gr_complex, cfg.fft_size)

        # We run the flow graph once at each frequency. head counts the samples
        # and terminates the flow graph when we have what we need.
        self.head = blocks.head(
            gr.sizeof_gr_complex * cfg.fft_size, cfg.dwell
        )

        forward = True
        shift = True
        ffter = fft.fft_vcc(cfg.fft_size, forward, cfg.window, shift)

        c2mag_sq = blocks.complex_to_mag_squared(cfg.fft_size)

        # Create vector sinks to access data at various stages of processing:
        #
        # iq_vsink - holds complex i/q data from the most recent complete sweep
        # fft_vsink - holds complex fft data from the most recent complete sweep
        # final_vsink - holds sweep's fully processed real data
        self.iq_vsink = blocks.vector_sink_c(cfg.fft_size)
        self.fft_vsink = blocks.vector_sink_c(cfg.fft_size)
        self.final_vsink = blocks.vector_sink_f(cfg.fft_size)

        stats = bin_statistics_ff(cfg.fft_size, cfg.dwell)

        power = sum(tap*tap for tap in cfg.window)

        # Divide magnitude-square by a constant to obtain power
        # in Watts. Assumes unit of USRP source is volts.
        impedance = 50.0 # ohms
        Vsq2W_dB = -10.0 * math.log10(cfg.fft_size * power * impedance)
        # Convert from Watts to dBm.
        W2dBm = blocks.nlog10_ff(10.0, cfg.fft_size, 30 + Vsq2W_dB)

        # Create the flowgraph:
        #
        # USRP   - hardware source output stream of 32bit complex float
        # resamp - rational resampler for LTE sample rates
        # skip   - for each run of flowgraph, drop N samples, then copy
        # s2v    - group 32-bit complex stream into vectors of length fft_size
        # head   - copies N vectors, then terminates flowgraph
        # fft    - compute forward FFT, complex in complex out
        # mag^2  - convert vectors from complex to real by taking mag squared
        # stats  - linear average vectors if dwell > 1
        # W2dBm  - convert volt to dBm
        # *sink  - data containers monitored by main thread
        #
        #                                     > raw i/q vector sink
        #                                    /
        # USRP > resamp > skip > s2v > head > fft > mag^2 > stats > W2dBm > sink
        #                                          \
        #                                           > fft sink
        #
        if self.resampler:
            self.connect(self.u, self.resampler, self.skip)
        else:
            self.connect(self.u, self.skip)
        self.connect(self.skip, s2v, self.head)
        self.connect((self.head, 0), ffter)
        self.connect((self.head, 0), self.iq_vsink)
        self.connect((ffter, 0), c2mag_sq)
        self.connect((ffter, 0), self.fft_vsink)
        self.connect(c2mag_sq, stats, W2dBm, self.final_vsink)

    def set_sample_rate(self, rate):
        """Set the USRP sample rate"""
        hwrate = rate

        if (rate not in self.sample_rates) and (rate in self.lte_rates):
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
        #self.sample_rate = self.u.get_samp_rate()
        self.sample_rate = rate
        self.logger.debug("sample rate is {} S/s".format(int(rate)))

    def set_next_freq(self):
        """Retune the USRP and calculate our next center frequency."""
        target_freq = self.cfg.next_freq
        if not self.set_freq(target_freq):
            self.logger.error("Failed to set frequency to {}".format(target_freq))

        self.cfg.next_freq = self.cfg.next_freq + self.cfg.freq_step
        if self.cfg.next_freq > self.cfg.max_center_freq:
            self.cfg.next_freq = self.cfg.min_center_freq

        return target_freq

    def set_freq(self, target_freq):
        """Set the center frequency and LO offset of the USRP."""
        r = self.u.set_center_freq(uhd.tune_request(
            target_freq,
            rf_freq=(target_freq + self.cfg.lo_offset),
            rf_freq_policy=uhd.tune_request.POLICY_MANUAL
        ))

        #r = self.u.set_center_freq(uhd.tune_request(target_freq, self.cfg.lo_offset))
        if r:
            self.tune_result = r
            return True
        return False

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

    @staticmethod
    def _chunks(l, n):
        """Yield successive n-sized chunks from l"""
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    @staticmethod
    def _verify_data_dir(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    def _to_savemat_format(self, data):
        """Build a numpy array of complex data suitable for scipy.io.savemat"""

        data_chunks = self._chunks(data, self.cfg.fft_size)

        # Construct a python dictionary holding a list of power measurements at
        # each frequency
        #
        # { 712499200: [
        #     (0.005035535432398319-0.002960284473374486j),
        #     (0.004394649062305689-0.003509615547955036j),
        #     ...
        #     ]
        #   ...
        # }
        native_format_data = {}
        for freq in self.cfg.center_freqs:
            x_points = calc_x_points(freq, self.cfg)

            dwell_count = 0
            while dwell_count < self.cfg.dwell:
                chunk = next(data_chunks)
                y_points = chunk[self.cfg.bin_start:self.cfg.bin_stop]

                for (x, y) in izip(x_points, y_points):
                    native_format_data.setdefault(x, []).append(y)

                dwell_count += 1

        # Translate the data to a numpy structed array that savemat understands
        #
        # [ (712499200L, [
        #     (0.005035535432398319-0.002960284473374486j),
        #     (0.004394649062305689-0.003509615547955036j),
        #     ...
        #   ])
        #   ...
        # ]
        matlab_format_data = np.array(native_format_data.items(), dtype=[
            ('frequency', np.uint32),
            ('data', np.complex64, (self.cfg.dwell,))
        ])

        return matlab_format_data

    def save_iq_data_to_file(self):
        """Save pre-FFT I/Q data to file"""

        if (self.single_run.is_set() or self.continuous_run.is_set()):
            msg = "Can't export data while the flowgraph is running."
            msg += " Use \"single\" run mode."
            self.logger.error(msg)
            return

        # creates path string 'data/iq_data_TIMESTAMP.mat'
        dirname = "data"
        self._verify_data_dir(dirname)
        fname = str.join('', ('iq_data_', str(int(time.time())), '.mat'))
        pathname = os.path.join(dirname, fname)

        data = self.iq_vsink.data()
        self.iq_vsink.reset() # empty the sink

        if data:
            formatted_data = self._to_savemat_format(data)

            # Export to a file in .mat format
            sio.savemat(pathname, {'iq_data': formatted_data}, appendmat=True)
            self.logger.info("Exported pre-FFT I/Q data to {}".format(pathname))
        else:
            self.logger.warn("No more data to export")

    def save_fft_data_to_file(self):
        """Save post_FFT I/Q data to file"""

        if (self.single_run.is_set() or self.continuous_run.is_set()):
            msg = "Can't export data while the flowgraph is running."
            msg += " Use \"single\" run mode."
            self.logger.error(msg)
            return

        # creates path string 'data/fft_data_TIMESTAMP.mat'
        dirname = "data"
        self._verify_data_dir(dirname)
        fname = str.join('', ('fft_data_', str(int(time.time())), '.mat'))
        pathname = os.path.join(dirname, fname)

        data = self.fft_vsink.data()
        self.fft_vsink.reset() # empty the sink

        if data:
            formatted_data = self._to_savemat_format(data)

            # Export to a file in .mat format
            sio.savemat(pathname, {'fft_data': formatted_data}, appendmat=True)
            self.logger.info("Exported post-FFT I/Q data to {}".format(pathname))
        else:
            self.logger.warn("No more data to export")


def calc_x_points(center_freq, cfg):
    """Find the index of a given freq in an array of bin center frequencies.

    Then use bin_offset to calculate the index range
    that will hold all of the appropriate x-values (frequencies) for the
    y-values (power measurements) that we just took at center_freq."""

    center_bin = np.where(cfg.bin_freqs == center_freq)[0][0]
    low_bin = center_bin - cfg.bin_offset
    high_bin = center_bin + cfg.bin_offset

    return cfg.bin_freqs[low_bin:high_bin]


def main(tb):
    """Run the main loop of the program"""

    plot = gui.plot_interface(tb)
    logger = logging.getLogger('USRPAnalyzer.main')
    freq = tb.set_next_freq() # initialize at min_center_freq
    reconfigure_plot = False # notify plot when major parameters change
    gui_alive = True # watch for gui close

    n_to_consume = tb.cfg.max_plotted_bin
    n_consumed = 0

    while True:
        if n_to_consume == 0:
            n_to_consume = tb.cfg.max_plotted_bin
            n_consumed = 0

        last_sweep = freq == tb.cfg.max_center_freq
        if last_sweep:
            tb.single_run.clear()

        # Execute flow graph and wait for it to stop
        tb.run()

        data = np.array(tb.final_vsink.data(), dtype=np.float32)
        y_points = data[tb.cfg.bin_start:tb.cfg.bin_stop][:n_to_consume]
        x_points = calc_x_points(freq, tb.cfg)[:n_to_consume]

        # flush the final vector sink
        tb.final_vsink.reset()

        gui_alive = plot.update((x_points, y_points), reconfigure_plot)
        if not gui_alive:
            break
        tb.gui_idle.clear()
        reconfigure_plot = False

        n_consumed = len(x_points)
        n_to_consume -= n_consumed

        # Sleep as long as necessary to keep a responsive gui
        sleep_count = 0
        while not tb.gui_idle.is_set():
            time.sleep(.01)
            sleep_count += 1
        #if sleep_count > 0:
        #    logger.debug("Slept {0}s waiting for gui".format(sleep_count / 100.0))

        # Block on run mode trigger
        if last_sweep:
            while not (tb.single_run.is_set() or tb.continuous_run.is_set()):
                # keep certain gui elements alive
                points = None
                gui_alive = plot.update(points, reconfigure_plot)
                if not gui_alive:
                    break
                # check run mode again in 1/4 second
                time.sleep(.25)

            # flush iq data vectors for next sweep
            tb.iq_vsink.reset()
            tb.fft_vsink.reset()

        if last_sweep and tb.reconfigure:
            tb.logger.debug("Reconfiguring flowgraph")
            tb.lock()
            tb.configure_flowgraph()
            tb.unlock()
            reconfigure_plot = True

        # Tune to next freq, and reset skip and head for next run
        freq = tb.set_next_freq()
        tb.skip.reset()
        tb.head.reset()


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()
    cfg = configuration(args)
    tb = top_block(cfg)
    try:
        main(tb)
        logging.getLogger('USRPAnalyzer').info("Exiting.")
    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
