/* -*- c++ -*- */
/* 
 * Copyright 2015 <+YOU OR YOUR COMPANY+>.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "threshold_timestamp_impl.h"
#include <volk/volk.h>
#include <unistd.h>
#include <stdio.h>
#include <time.h>
#include <string.h>

namespace gr {
  namespace myblocks {

    threshold_timestamp::sptr
    threshold_timestamp::make(unsigned int vlen, size_t itemsize, int type, float threshold, int fd)
    {
      return gnuradio::get_initial_sptr
        (new threshold_timestamp_impl(vlen, itemsize, type, threshold, fd));
    }

    /*
     * The private constructor
     */
    threshold_timestamp_impl::threshold_timestamp_impl(unsigned int vlen, size_t itemsize, int type, float threshold, int fd)
      : gr::sync_block("threshold_timestamp",
              gr::io_signature::make(1, 1, vlen * itemsize),
              gr::io_signature::make(1, 1, vlen * sizeof(float))),
	d_vlen(vlen), d_itemsize(itemsize), d_type(type),
	d_threshold(threshold), d_fd(fd)
    {
	d_prior = 0.0;
	const int alignment_multiple = volk_get_alignment() / sizeof(float);
	set_alignment(std::max(1,alignment_multiple));
    }

    /*
     * Our virtual destructor.
     */
    threshold_timestamp_impl::~threshold_timestamp_impl()
    {
    }

    int
    threshold_timestamp_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
	clock_t t;
	char s[100];
	float value[noutput_items * d_vlen];

	if (d_type == 0) {
          const gr_complex *in = (const gr_complex *) input_items[0];
	  volk_32fc_magnitude_squared_32f(value, in, noutput_items * d_vlen);
	} else {
	  const int8_t *in = (const int8_t *) input_items[0];
	  for (int i = 0; i < noutput_items * d_vlen; i++)
	    value[i] = (float)(in[i]);
	}

        // Do timestamping of detected threshold crossings
	for (int n = 0; n < noutput_items; n++) {
	  float current;
	  if (d_type == 0) {
	    // compute the sum of the value vector
	    current = 0.0;
	    for (int i = 0; i < d_vlen; i++) {
	      current += value[n * d_vlen + i];
	    }
	  } else {
	    // find the maximum of the value vector
	    current = value[n * d_vlen];
	    for (int i = 1; i < d_vlen; i++)
	      current = (value[n * d_vlen + i] > current) ? value[n * d_vlen + i] : current;
	  }
	  float metric = (d_type == 0) ? (d_prior / current) : (d_prior - current);
	  if (metric > d_threshold) {
	    // write current time to file descriptor d_fd
	    t = clock();
	    sprintf(s, "%d clicks; %f s\n", t, ((float)t)/CLOCKS_PER_SEC);
	    write(d_fd, s, strlen(s));
	  }
	  d_prior = current;
	}

        // Tell runtime system how many output items we produced.
        return noutput_items;
    }

  } /* namespace myblocks */
} /* namespace gr */

