/* -*- c++ -*- */
/* 
 * Copyright 2014 <+YOU OR YOUR COMPANY+>.
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
#include "bin_statistics_ff_impl.h"

namespace gr {
  namespace usrpanalyzer {

    bin_statistics_ff::sptr
    bin_statistics_ff::make(unsigned int vlen, unsigned int meas_interval)
    {
      return gnuradio::get_initial_sptr
        (new bin_statistics_ff_impl(vlen, meas_interval));
    }

    /*
     * The private constructor
     */
    bin_statistics_ff_impl::bin_statistics_ff_impl(unsigned int vlen, unsigned int meas_interval)
      : gr::sync_decimator("bin_statistics_ff",
              gr::io_signature::make(1, 1, vlen * sizeof(float)),
              gr::io_signature::make(1, 1, vlen * sizeof(float)), meas_interval),
	d_vlen(vlen), d_meas_interval(meas_interval)
    {}

    /*
     * Our virtual destructor.
     */
    bin_statistics_ff_impl::~bin_statistics_ff_impl()
    {
    }

    int
    bin_statistics_ff_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
        const float *in = (const float *) input_items[0];
        float *out = (float *) output_items[0];

	for (int n = 0; n < noutput_items; n++) {
	  // Output the average of the input vectors in the measurement interval.
	  for (int i = 0; i < d_vlen; i++)
	    out[n * d_vlen + i] = in[n * d_meas_interval * d_vlen + i];
	  for (int i = 1; i < d_meas_interval; i++)
	    for (int j = 0; j < d_vlen; j++)
	      out[n * d_vlen + j] += in[(n * d_meas_interval + i) * d_vlen + j];
	  for (int i = 0; i < d_vlen; i++)
	    out[n * d_vlen + i] /= d_meas_interval;
	}

        // Tell runtime system how many output items we produced.
        return noutput_items;
    }

  } /* namespace usrpanalyzer */
} /* namespace gr */

