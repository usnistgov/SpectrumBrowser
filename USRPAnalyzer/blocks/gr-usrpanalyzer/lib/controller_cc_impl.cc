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

#include <iostream> // DELETE ME
#include <algorithm> /* copy, min */
#include <cassert>   /* assert */

#include <pmt/pmt.h>
#include <gnuradio/io_signature.h>
#include "controller_cc_impl.h"

namespace gr {
  namespace usrpanalyzer {

    controller_cc::sptr
    controller_cc::make(
      feval_dd *tune_callback, size_t skip_initial, size_t ncopy, size_t nsegments
      )
    {
      return gnuradio::get_initial_sptr
        (new controller_cc_impl(tune_callback, skip_initial, ncopy, nsegments));
    }

    /*
     * The private constructor
     */
    controller_cc_impl::controller_cc_impl(feval_dd *tune_callback,
                                           size_t skip_initial,
                                           size_t ncopy,
                                           size_t nsegments)
      : gr::block("controller_cc",
                  gr::io_signature::make(1, 1, sizeof(gr_complex)),
                  gr::io_signature::make(1, 1, sizeof(gr_complex))),
        d_tune_callback(tune_callback),
        d_skip_initial(skip_initial),
        d_ncopy(ncopy),
        d_nsegments(nsegments)
    {
      d_current_segment = 1;
      d_nskipped = 0;
      d_ncopied = 0;

      d_got_rx_freq_tag = false;
      d_did_initial_tune = false;
      d_retune = nsegments > 1;
      d_exit_after_complete = false;
      d_exit_flowgraph = false;

      d_tag_key = pmt::intern("rx_freq");
    }

    ///*
    // * Our virtual destructor.
    // */
    //controller_cc_impl::~controller_cc_impl()
    //{
    //}

    void
    controller_cc_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = noutput_items;
    }

    int
    controller_cc_impl::general_work (int noutput_items,
                                      gr_vector_int &ninput_items,
                                      gr_vector_const_void_star &input_items,
                                      gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *)input_items[0];
      gr_complex *out = (gr_complex *)output_items[0];

      // If last run completed copying and d_exit_after_complete was set,
      // then WORK_DONE
      if (d_exit_flowgraph)
      {
        reset();  // leave the block in a sane state
        consume_each(0);
        return WORK_DONE;
      }

      // Tune to the first frequency in the span
      if (!d_did_initial_tune)
      {
        d_current_freq = d_tune_callback->calleval(0.0);
        d_did_initial_tune = true;
        consume_each(0);
        return 0;
      }

      // Drop samples until receiving a sample tagged with "rx_freq"
      if (!d_got_rx_freq_tag)
      {
        d_range_start = nitems_read(0);
        d_range_stop = d_range_start + ninput_items[0];

        assert(d_tags.empty()); // tags vector should have been left in an empty
        // populate tags vector with any tag on chan 0 matching tag_key
        get_tags_in_range(d_tags, 0, d_range_start, d_range_stop, d_tag_key);
        if (d_tags.empty())
        {
          // no tags in this batch
          consume_each(ninput_items[0]);
          return 0;
        }
        else
        {
          // drop all samples up to the first tagged sample
          d_got_rx_freq_tag = true;
          d_rel_offset = d_tags[0].offset - d_range_start;
          d_tags.clear();               // leave tags vector in a clean state
          if (d_rel_offset != 0)
          {
            consume_each(d_rel_offset-1); // consume up to tagged sample
            return 0;
          }
          // else tagged sample is first, so just continue
        }
      }

      // Optionally skip additional samples after initial tune
      d_skips_left = d_skip_initial - d_nskipped;
      if (d_skips_left > 0)
      {
        d_nskip_this_time = std::min((size_t)noutput_items, d_skips_left);
        consume_each(d_nskip_this_time);
        d_nskipped += d_nskip_this_time;
        return 0;
      }

      // copy samples
      d_copies_left = d_ncopy - d_ncopied;
      d_ncopy_this_time = std::min((size_t)noutput_items, d_copies_left);

      std::copy(&in[0], &in[d_ncopy_this_time], &out[0]);
      d_ncopied += d_ncopy_this_time;

      d_done_copying = d_ncopied == d_ncopy;
      d_last_segment = d_current_segment == d_nsegments;

      // retune and advance to next segment or set exit_flowgraph
      if (d_done_copying)
      {
        d_ncopied = 0;

        if (d_last_segment)
        {
          d_current_segment = 1;
        }

        if (d_last_segment && d_exit_after_complete)
        {
          d_exit_flowgraph = true;
        }
        else if (d_retune)
        {
          d_current_freq = d_tune_callback->calleval(0.0);
          ++d_current_segment;
          d_got_rx_freq_tag = false;
        }
      }

      consume_each(d_ncopy_this_time);
      return d_ncopy_this_time;
    }

    void
    controller_cc_impl::reset()
    {
      d_current_segment = 1;
      d_ncopied = 0;
      if (d_retune)
      {
        d_nskipped = 0;
        d_did_initial_tune = false;
        d_got_rx_freq_tag = false;
      }

      d_exit_flowgraph = false;
    }

    bool
    controller_cc_impl::get_exit_after_complete()
    {
      return d_exit_after_complete;
    }

    void
    controller_cc_impl::set_exit_after_complete()
    {
      d_exit_after_complete = true;
    }

    void
    controller_cc_impl::clear_exit_after_complete()
    {
      d_exit_after_complete = false;
    }

    void
    controller_cc_impl::reset_nskipped()
    {
      d_nskipped = 0;
    }

  } /* namespace usrpanalyzer */
} /* namespace gr */
