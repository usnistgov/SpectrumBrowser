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


import argparse

from gnuradio import eng_notation

import consts


def eng_float(value):
    """Covert an argument string in engineering notation to float"""
    try:
        return eng_notation.str_to_num(value)
    except:
        msg = "invalid engineering notation value: {0!r}".format(value)
        raise argparse.ArgumentTypeError(msg)


def percent(value):
    """Ensure argument is a valid percentage and return in decimal format"""
    try:
        value = int(value)
        assert(0 <= value < 100)

        return value
    except (ValueError, AssertionError):
        msg = "invalid percent value: {0!r}, use int > 0 and <= 100"
        raise argparse.ArgumentTypeError(msg.format(value))


def pos_int(value):
    """Ensure argument is a positive integer"""
    try:
        value = int(value)
        assert(value > 0)

        return value
    except (ValueError, AssertionError):
        msg = "invalid value: {0!r}, use int > 0"
        raise argparse.ArgumentTypeError(msg.format(value))


def fft_size(value):
    """Sane fft size should be a multiple of 32"""
    try:
        value = int(value)
        assert(not value % 32)

        return value
    except (ValueError, AssertionError):
        msg = "invalid fft size: {0!r}, use multiple of 32"
        raise argparse.ArgumentTypeError(msg.format(value))


def init_parser():
    """Initialize an OptionParser instance, populate it, and return it."""

    usage =  "%(prog)s [options] center_freq"
    usage += "\n\n"
    usage += "Examples:\n"
    usage += "  %(prog)s 700M --continuous\n"
    usage += "  %(prog)s 700M --span 100M\n"
    usage += "  %(prog)s 700M --wire-format=sc8 --args='peak=0.1' --samp-rate 30.72M\n\n"

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument("center_freq", type=eng_float)
    parser.add_argument("-S", "--span", type=eng_float, default=None,
                        help="width to scan around center_freq [default=samp-rate]")
    parser.add_argument("-d", "--device-addr", type=str, default="",
                        help="UHD device address [default=%(default)s]")
    parser.add_argument("--wire-format", type=str, default="sc16",
                        choices=consts.WIRE_FORMATS,
                        help="Set wire format from USRP [default=%(default)s]")
    parser.add_argument("--stream-args", type=str, default="peak=1.0",
                        help="Set additional stream args [default=%(default)s]")
    parser.add_argument("--spec", type=str, default=None, dest="subdev_spec",
                        help="Subdevice of UHD device where appropriate")
    parser.add_argument("-A", "--antenna", type=str, default=None,
                        help="select Rx Antenna where appropriate")
    parser.add_argument("-s", "--sample-rate", type=eng_float, default=10e6,
                        help="set sample rate [default=%(default)s]")
    parser.add_argument("-g", "--gain", type=eng_float, default=None,
                        help="set gain in dB")
    parser.add_argument("--skip-initial", type=int,
                        default=1000000, metavar="samples",
                        help="samples to skip after initiating flowgraph [default=%(default)s]")
    parser.add_argument("--averages", type=pos_int, dest="n_averages",
                        default=30, metavar="fft frames",
                        help="number of DFTs to average at a given frequency [default=%(default)s]")
    parser.add_argument("-l", "--lo-offset", type=eng_float,
                        default=0, metavar="Hz",
                        help="lo_offset in Hz [default=%(default)s]")
    parser.add_argument('-o', "--overlap", type=percent, metavar='%', default=25,
                        help="Overlap the outer n%% of the fft [default=%(default)s]")
    parser.add_argument("-F", "--fft-size", type=fft_size, default=1024,
                        help="specify number of FFT bins [default=%(default)s]")
    parser.add_argument("--debug", action="store_true", default=False,
                        help=argparse.SUPPRESS)
    parser.add_argument("-c", "--continuous", action="store_true", default=False,
                        dest="continuous_run",
                        help="Start in continuous run mode [default=%(default)s]")
    parser.add_argument("--realtime", action="store_true", default=False,
                        help="Attempt to enable realtime scheduling")

    return parser
