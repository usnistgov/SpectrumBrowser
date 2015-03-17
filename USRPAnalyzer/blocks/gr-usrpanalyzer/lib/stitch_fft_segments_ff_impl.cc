/* -*- c++ -*- */
/*
 * Copyright 2015 Douglas Anderson
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

#include <algorithm> /* copy */

#include <gnuradio/io_signature.h>
#include "stitch_fft_segments_ff_impl.h"

namespace gr {
  namespace usrpanalyzer {

    stitch_fft_segments_ff::sptr
    stitch_fft_segments_ff::make(size_t fft_size, size_t nsegments, float overlap)
    {
      return gnuradio::get_initial_sptr
        (new stitch_fft_segments_ff_impl(fft_size, nsegments, overlap));
    }

    /*
     * The private constructor
     */
    stitch_fft_segments_ff_impl::stitch_fft_segments_ff_impl(
      size_t fft_size,
      size_t nsegments,
      float overlap
      )
      : gr::sync_block("stitch_fft_segments_ff",
                       gr::io_signature::make(1, 1, fft_size * nsegments * sizeof(float)),
                       gr::io_signature::make(1, 1, nsegments*(fft_size*(1-overlap))*sizeof(float))),
        d_fft_size(fft_size), d_nsegments(nsegments), d_overlap(overlap)
    {
      d_nin = fft_size * nsegments;
      d_nvalid_bins = fft_size * (1 - overlap);
      d_nout = nsegments * d_nvalid_bins;
      d_bin_start = fft_size * (overlap / 2); // d_overlap is float
      d_bin_stop = fft_size - d_bin_start;
    }

    /*
     * Our virtual destructor.
     */
    stitch_fft_segments_ff_impl::~stitch_fft_segments_ff_impl()
    {
    }

    int
    stitch_fft_segments_ff_impl::work(int noutput_items,
                                      gr_vector_const_void_star &input_items,
                                      gr_vector_void_star &output_items)
    {
      const float *in = (const float *) input_items[0];
      float *out = (float *) output_items[0];

      size_t in_idx = d_bin_start;
      size_t out_idx = 0;
      size_t bytes_to_copy = d_nvalid_bins * sizeof(float);
      for (in_idx, out_idx; out_idx < d_nout; in_idx += d_fft_size, out_idx += d_nvalid_bins)
      {
        std::copy(&in[in_idx], &in[in_idx + d_nvalid_bins], &out[out_idx]);
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace usrpanalyzer */
} /* namespace gr */
