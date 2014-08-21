#!/usr/bin/env python

import sys
import math
import logging
from optparse import OptionParser, SUPPRESS_HELP

from gnuradio import gr
from gnuradio import blocks as gr_blocks
from gnuradio import filter as gr_filters
from gnuradio import fft
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option

from myblocks import bin_statistics_ff

from blocks import pyplot_sink_f


class top_block(gr.top_block):
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
        parser.add_option("-s", "--samp-rate", type="eng_float", default=5e6,
                          help="set sample rate [default=%default]")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                          help="set gain in dB (default is midpoint)")
        parser.add_option("", "--tune-delay", type="eng_float",
                          default=0.1, metavar="SECS",
                          help="time to delay (in seconds) after changing frequency [default=%default]")
        parser.add_option("", "--dwell", type="eng_float",
                          default=2, metavar="fft frames",
                          help="number of passes (with averaging) at a given frequency [default=%default]")
        parser.add_option("-b", "--channel-bandwidth", type="eng_float",
                          default=None, metavar="Hz",
                          help="channel bandwidth of fft bins in Hz [default=sample-rate/fft-size]")
        parser.add_option("-l", "--lo-offset", type="eng_float",
                          default=None, metavar="Hz",
                          help="lo_offset in Hz [default=half the sample rate]")
        parser.add_option("-q", "--squelch-threshold", type="eng_float",
                          default=None, metavar="dB",
                          help="squelch threshold in dB [default=%default]")
        parser.add_option("-F", "--fft-size", type="int", default=128,
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

        self.logger = logging.getLogger('USRPAnalyzer')
        console_handler = logging.StreamHandler()
        logfmt = logging.Formatter("%(levelname)s:%(funcName)s: %(message)s")
        console_handler.setFormatter(logfmt)
        self.logger.addHandler(console_handler)
        if options.debug:
            loglvl = logging.DEBUG
        elif options.verbose:
            loglvl = logging.INFO
        else:
            loglvl = logging.WARNING
        self.logger.setLevel(loglvl)

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
                self.logger.warning("failed to enable realtime scheduling")

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

        s2v = gr_blocks.stream_to_vector(gr.sizeof_gr_complex, self.fft_size)

        forward = True
        window = gr_filters.window.blackmanharris(self.fft_size)
        shift = True

        ffter = fft.fft_vcc(self.fft_size, forward, window, shift)

        c2mag = gr_blocks.complex_to_mag_squared(self.fft_size)

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.

        self.freq_step = self.nearest_freq((0.75 * self.usrp_rate), self.channel_bandwidth)
        self.min_center_freq = self.min_freq + (self.freq_step/2) 
        self.nsteps = math.ceil((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (self.nsteps * self.freq_step)

        self.next_freq = self.min_center_freq

        self.tune_delay = int(round((options.tune_delay * usrp_rate)/float(self.fft_size))) # in fft_frames
        dwell = max(1, options.dwell) # in fft_frames

        stats = bin_statistics_ff(self.fft_size, dwell)

        power = sum(tap*tap for tap in window)

        # Divide magnitude-square by a constant to obtain power
        # in Watts. Assumes unit of USRP source is volts.
        impedance = 50.0 # ohms
        Vsq2W_dB = -10.0 * math.log10(self.fft_size * power * impedance)
        # Convert from Watts to dBm.
        W2dBm = gr_blocks.nlog10_ff(10.0, self.fft_size, 30.0 + Vsq2W_dB)

        plot = pyplot_sink_f(self, self.fft_size)

        self.connect(self.u, s2v, ffter, c2mag, stats, W2dBm, plot)

        if options.gain is None:
            # if no gain was specified, use the 0 gain
            g = self.u.get_gain_range()
            #options.gain = float(g.start()+g.stop())/2.0
            options.gain = g.start()

        self.set_gain(options.gain)
        self.gain = options.gain

        self.tune_result = None

    def set_next_freq(self):
        target_freq = self.next_freq
        if not self.set_freq(target_freq):
            self.logger.error("Failed to set frequency to {0}".format(target_freq))


        self.next_freq = self.next_freq + self.freq_step
        if self.next_freq >= self.max_center_freq:
            self.next_freq = self.min_center_freq

        return target_freq

    def set_freq(self, target_freq):
        r = self.u.set_center_freq(uhd.tune_request(target_freq, self.lo_offset))
        if r:
            self.tune_result = r
            return True
        return False

    def set_gain(self, gain):
        self.u.set_gain(gain)
    
    def nearest_freq(self, freq, channel_bandwidth):
        freq = round(freq / channel_bandwidth, 0) * channel_bandwidth
        return freq


if __name__ == '__main__':
    tb = top_block()
    try:
        tb.start()
        tb.wait()
        logging.getLogger('USRPAnalyzer').info("Exiting.")
    except KeyboardInterrupt:
        tb.stop()
        tb.wait()
