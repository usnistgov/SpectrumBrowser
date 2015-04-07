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

import numpy
from gnuradio import gr

class sslsocket_sink(gr.sync_block):
    """
    docstring for block sslsocket_sink
    """
    def __init__(self, dtype, nitems_per_block, sock):
        gr.sync_block.__init__(self,
            name="sslsocket_sink",
            in_sig=[(dtype, nitems_per_block)],
            out_sig=None)

    def set_sock(self, sock):
	self.sock = sock

    def work(self, input_items, output_items):
        in0 = input_items[0]
        num_input_items = len(in0)
	for i in range(num_input_items):
            self.sock.send(in0[i])
        return num_input_items

