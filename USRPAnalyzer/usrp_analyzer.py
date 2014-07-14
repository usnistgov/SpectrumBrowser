#!/usr/bin/env python
#
# Copyright 2005,2007,2011 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import sys
import math
import time
import struct
import logging
import numpy as np
import matplotlib
# This must be set before import pylab
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt
from optparse import OptionParser, SUPPRESS_HELP

from gnuradio import gr
from gnuradio import blocks
from gnuradio import filter as gr_filters
from gnuradio import fft
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option


class Tune(gr.feval_dd):
    """ This class allows C++ code to callback into python. """
    def __init__(self, tb):
        gr.feval_dd.__init__(self)
        self.tb = tb

    def eval(self, ignore):
        """
        This method is called from blocks.bin_statistics_f when it wants
        to change the center frequency.  This method tunes the front
        end to the new center frequency, and returns the new frequency
        as its result.
        """

        try:
            # We use this try block so that if something goes wrong
            # from here down, at least we'll have a prayer of knowing
            # what went wrong.  Without this, you get a very
            # mysterious:
            #
            #   terminate called after throwing an instance of
            #   'Swig::DirectorMethodException' Aborted
            #
            # message on stderr.  Not exactly helpful ;)

            new_freq = self.tb.set_next_freq()

            # wait until msgq is empty before continuing
            while self.tb.msgq.full_p():
                time.sleep(0.1)

            return new_freq

        except TypeError:
            # Tune still alive after tb.stop()... exiting
            self.tb.wait()
        except Exception, e:
            print "tune: Exception: ", e


class Message(object):
    def __init__(self, msg):
        self.center_freq = msg.arg1()
        self.vlen = int(msg.arg2())
        assert(msg.length() == self.vlen * gr.sizeof_float)

        # FIXME consider using NumPy array
        t = msg.to_string()
        self.raw_data = t
        self.data = struct.unpack('%df' % (self.vlen,), t)


class TopBlock(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        usage = "usage: %prog [options] min_freq max_freq"
        parser = OptionParser(option_class=eng_option, usage=usage)
        parser.add_option("-a", "--args", type="string", default="",
                          help="UHD device device address args [default=%default]")
        parser.add_option("", "--spec", type="string", default=None,
	                  help="Subdevice of UHD device where appropriate")
        parser.add_option("-A", "--antenna", type="string", default=None,
                          help="select Rx Antenna where appropriate")
        parser.add_option("-s", "--samp-rate", type="eng_float", default=1e6,
                          help="set sample rate [default=%default]")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                          help="set gain in dB (default is midpoint)")
        parser.add_option("", "--tune-delay", type="eng_float",
                          default=0.1, metavar="SECS",
                          help="time to delay (in seconds) after changing frequency [default=%default]")
        parser.add_option("", "--dwell-delay", type="eng_float",
                          default=1, metavar="fft frames",
                          help="time to dwell (in seconds) at a given frequency [default=%default]")
        parser.add_option("-b", "--channel-bandwidth", type="eng_float",
                          default=None, metavar="Hz",
                          help="channel bandwidth of fft bins in Hz [default=sample-rate/fft-size]")
        parser.add_option("-l", "--lo-offset", type="eng_float",
                          default=None, metavar="Hz",
                          help="lo_offset in Hz [default=half the sample rate]")
        parser.add_option("-q", "--squelch-threshold", type="eng_float",
                          default=None, metavar="dB",
                          help="squelch threshold in dB [default=%default]")
        parser.add_option("-F", "--fft-size", type="int", default=4096,
                          help="specify number of FFT bins [default=%default]")
        parser.add_option("-v", "--verbose", action="store_true", default=False,
                          help="extra info printed to stdout"),
        parser.add_option("", "--debug", action="store_true", default=False,
                          help=SUPPRESS_HELP),
        parser.add_option("", "--real-time", action="store_true", default=False,
                          help="Attempt to enable real-time scheduling"),

        (options, args) = parser.parse_args()
        if len(args) != 2:
            parser.print_help()
            sys.exit(1)

        if options.debug:
            loglvl = logging.DEBUG
        elif options.verbose:
            loglvl = logging.INFO
        else:
            loglvl = logging.WARNING
        logfmt = "%(levelname)s:%(funcName)s: %(message)s"
        logging.basicConfig(level=loglvl, format=logfmt)


        self.channel_bandwidth = options.channel_bandwidth

        self.min_freq = eng_notation.str_to_num(args[0])
        self.max_freq = eng_notation.str_to_num(args[1])

        if self.min_freq > self.max_freq:
            # swap them
            self.min_freq, self.max_freq = self.max_freq, self.min_freq

        realtime = False
        if options.real_time:
            # Attempt to enable realtime scheduling
            r = gr.enable_realtime_scheduling()
            if r == gr.RT_OK:
                realtime = True
            else:
                logging.warning("failed to enable realtime scheduling")


        # build graph
        self.u = uhd.usrp_source(device_addr=options.args,
                                 stream_args=uhd.stream_args('fc32'))

        # Set the subdevice spec
        if options.spec:
            self.u.set_subdev_spec(options.spec, 0)

        # Set the antenna
        if options.antenna:
            self.u.set_antenna(options.antenna, 0)
        
        self.u.set_samp_rate(options.samp_rate)
        self.usrp_rate = usrp_rate = self.u.get_samp_rate()
        
        if options.lo_offset is None:
            self.lo_offset = usrp_rate / 2.0
        else:
            self.lo_offset = options.lo_offset


        if options.fft_size:
            self.fft_size = options.fft_size
        else:
            self.fft_size = int(self.usrp_rate/self.channel_bandwidth)

        if options.channel_bandwidth:
            self.channel_bandwidth = options.channel_bandwidth
        else:
            self.channel_bandwidth = int(self.usrp_rate/self.fft_size)

        self.squelch_threshold = options.squelch_threshold

        s2v = blocks.stream_to_vector(gr.sizeof_gr_complex, self.fft_size)

        forward = True
        self.window = gr_filters.window.blackmanharris(self.fft_size)
        shift = True
        ffter = fft.fft_vcc(self.fft_size, forward, self.window, shift)

        c2mag = blocks.complex_to_mag_squared(self.fft_size)

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.

        self.freq_step = self.nearest_freq((0.75 * self.usrp_rate), self.channel_bandwidth)
        self.min_center_freq = self.min_freq + (self.freq_step/2) 
        self.nsteps = math.ceil((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (self.nsteps * self.freq_step)

        self.next_freq = self.min_center_freq

        tune_delay  = max(0, int(round(options.tune_delay * usrp_rate / self.fft_size)))  # in fft_frames
        dwell_delay = max(1, options.dwell_delay) # in fft_frames

        #average = False
        #if dwell_delay > 1:
        #   average = True

        self.msgq = gr.msg_queue(1)
        self._tune_callback = Tune(self)        # hang on to this to keep it from being GC'd
        stats = blocks.bin_statistics_f(self.fft_size, self.msgq,
                                        self._tune_callback, tune_delay,
                                        dwell_delay)

        self.connect(self.u, s2v, ffter, c2mag, stats)

        if options.gain is None:
            # if no gain was specified, use the 0 gain
            g = self.u.get_gain_range()
            #options.gain = float(g.start()+g.stop())/2.0
            options.gain = g.start()

        self.set_gain(options.gain)
        self.gain = options.gain

        self.plot = View(self)

        self.tune_result = None

        self.exit_requested = False

    def set_next_freq(self):
        target_freq = self.next_freq
        self.next_freq = self.next_freq + self.freq_step

        if not self.set_freq(target_freq):
            logging.error("Failed to set frequency to {0}".format(target_freq))
            self.clean_exit()

        if self.next_freq >= self.max_center_freq:
            self.next_freq = self.min_center_freq

        return target_freq


    def set_freq(self, target_freq):
        """
        Set the center frequency we're interested in.

        Args:
            target_freq: frequency in Hz
        @rypte: bool
        """
        
        r = self.u.set_center_freq(
            uhd.tune_request(
                target_freq,
                rf_freq=(target_freq + self.lo_offset),
                rf_freq_policy=uhd.tune_request.POLICY_MANUAL
            )
        )

        if r:
            self.tune_result = r
            return True
        return False

    def set_gain(self, gain):
        self.u.set_gain(gain)
    
    def nearest_freq(self, freq, channel_bandwidth):
        freq = round(freq / channel_bandwidth, 0) * channel_bandwidth
        return freq

    def clean_exit(self):
        self.exit_requested = True
        # Put an kill msg in the queue so we don't hang on blocking call
        logging.debug("queueing msg type=1")
        self.msgq.insert_tail(gr.message(type=1))


class View(object):
    def __init__(self, tb):
        self.tb = tb

        # exit when window closed
        fig = plt.figure()
        fig.canvas.mpl_connect('close_event', self.close)

        plt.ion()
        plt.xlabel('Frequency(GHz)')
        plt.ylabel('Power')
        plt.xlim(self.tb.min_freq-1e7, self.tb.max_freq+1e7)
        plt.ylim(-120,0)
        plt.yticks(np.arange(-130,0,10))
        plt.xticks(np.arange(self.tb.min_freq, self.tb.max_freq+1,1e8))
        plt.grid(color='.90', linestyle='-', linewidth=1)
        plt.title('Power Spectrum Density')

        self.line, = plt.plot([])
        self.__x = 0
        self.__y = 0

    def close(self, event):
        logging.debug("GUI window caught close event")
        self.tb.clean_exit()

    def update_line(self, xypair):
        x, y = xypair
        if x > self.__x:
            self.line.set_xdata(np.append(self.line.get_xdata(), x))
            self.line.set_ydata(np.append(self.line.get_ydata(), y))
        else:
            # restarted sweep, clear line
            self.line.set_xdata([x])
            self.line.set_ydata([y])
        plt.pause(0.01)
        self.__x = x
        self.__y = y


def bin_freq(i_bin, center_freq):
    #hz_per_bin = tb.usrp_rate / tb.fft_size
    freq = center_freq - (tb.usrp_rate / 2) + (tb.channel_bandwidth * i_bin)
    #print "freq original:",freq
    #freq = nearest_freq(freq, tb.channel_bandwidth)
    #print "freq rounded:",freq
    return freq


def Vsq2dBm(volts, k):
    """Volts mag^2 to dBm plus adjustment k"""
    return 10*math.log10(volts) + k


def main_loop(tb):
    power = sum(tap*tap for tap in tb.window)
    power_adjustment = -20.0*math.log10(tb.fft_size) - 10*math.log10(power/tb.fft_size)

    bin_start = int(tb.fft_size * ((1 - 0.75) / 2))
    bin_stop = int(tb.fft_size - bin_start)

    while True:

        # Get the next message sent from the C++ code (blocking call).
        # It contains the center frequency and the mag squared of the fft
        msg = tb.msgq.delete_head()
        if msg.type() == 1:
            logging.debug("main_loop: got msg type=1")
            return
        m = Message(tb.msgq.delete_head())

        # m.center_freq is the center frequency at the time of capture
        # m.data are the mag_squared of the fft output
        # m.raw_data is a string that contains the binary floats.
        # You could write this as binary to a file.

        x = []
        y = []
        noise_floor_db = Vsq2dBm(min(m.data), power_adjustment)
        for i_bin in range(bin_start, bin_stop):

            center_freq = m.center_freq
            freq = bin_freq(i_bin, center_freq)

            dBm = Vsq2dBm(m.data[i_bin], power_adjustment)

            if (dBm > tb.squelch_threshold) and (freq >= tb.min_freq) and (freq <= tb.max_freq):
                #print datetime.now(), "center_freq", center_freq, "freq", freq, "power_db", power_db, "noise_floor_db", noise_floor_db

                x.append(freq)
                y.append(dBm)

        logging.info("PLOTTING CENTER FREQ: {0} GHz WITH NOISE FLOOR: {1} dB AND MAX: {2} dB".format(
            round(m.center_freq/1e9, 5), int(noise_floor_db), int(max(y))
        ))

        x_point = x[y.index(max(y))]
        y_point = max(y)
        tb.plot.update_line([x_point, y_point])




if __name__ == '__main__':
    tb = TopBlock()
    try:
        tb.start()
        main_loop(tb)
        logging.debug("calling stop() on topblock")
        tb.stop()
        logging.debug("wait() for topblock")
        tb.wait()
        logging.debug("topblock.wait() returned")
        logging.info("Exiting.")
    except KeyboardInterrupt:
        pass
