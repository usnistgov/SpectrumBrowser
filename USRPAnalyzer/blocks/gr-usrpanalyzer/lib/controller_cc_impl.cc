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

#include <algorithm> /* copy, min */
#include <cassert>   /* assert */
#include <deque>
#include <vector>

#include <gnuradio/io_signature.h>
#include <gnuradio/uhd/usrp_source.h>
#include <pmt/pmt.h>
#include <uhd/types/tune_request.hpp>
#include "controller_cc_impl.h"

namespace gr {
  namespace usrpanalyzer {

    controller_cc::sptr
    controller_cc::make(gr::uhd::usrp_source *usrp,
                        std::vector<double> center_freqs,
                        double lo_offset,
                        size_t skip_initial,
                        size_t ncopy)
    {
      return gnuradio::get_initial_sptr
        (new controller_cc_impl(usrp, center_freqs, lo_offset, skip_initial, ncopy));
    }

    /*
     * The private constructor
     */
    controller_cc_impl::controller_cc_impl(gr::uhd::usrp_source *usrp,
                                           std::vector<double> center_freqs,
                                           double lo_offset,
                                           size_t skip_initial,
                                           size_t ncopy)
      : gr::block("controller_cc",
                  gr::io_signature::make(1, 1, sizeof(gr_complex)),
                  gr::io_signature::make(1, 1, sizeof(gr_complex))),
        usrp_ptr(usrp), d_lo_offset(lo_offset), d_skip_initial(skip_initial), d_ncopy(ncopy)
    {
      d_cfreqs_orig = center_freqs;
      d_cfreqs_iter = std::deque<double>(center_freqs.begin(), center_freqs.end());
      d_nsegments = center_freqs.size();
      d_current_segment = 1;
      d_nskipped = 0;
      d_ncopied = 0;

      d_got_rx_freq_tag = false;
      d_did_initial_tune = false;
      d_retune = d_nsegments > 1;
      d_exit_after_complete = false;
      d_exit_flowgraph = false;

      d_tag_key = pmt::intern("rx_freq");

      set_tag_propagation_policy(TPP_DONT);
    }

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
        tune_next_freq();
        d_did_initial_tune = true;
        consume_each(0);
        return 0;
      }

      // Drop samples until receiving a sample tagged with "rx_freq"
      if (!d_got_rx_freq_tag)
      {
        d_range_start = nitems_read(0);
        d_range_stop = d_range_start + ninput_items[0];

        assert(d_tags.empty()); // tags vector should have been left empty
        // populate tags vector with any tag on chan 0 matching tag_key
        get_tags_in_range(d_tags, 0, d_range_start, d_range_stop, d_tag_key);

        // Find first tag matching target freq
        bool got_target_freq = false;
        double trfreq;
        while (!d_tags.empty() && !got_target_freq)
        {
          // For some reason rx_freq's value is not part of tune_request_t
          trfreq = d_tune_result.actual_rf_freq - d_tune_result.actual_dsp_freq;
          if (pmt::to_double(d_tags[0].value) == trfreq)
          {
            d_rel_offset = d_tags[0].offset - d_range_start;
            got_target_freq = true;
          }

          // Potentially expensive, but d_tags.size() is rarely > 1
          d_tags.erase(d_tags.begin());
        }

        if (got_target_freq)
        {
          d_got_rx_freq_tag = true;
          if (d_rel_offset != 0)
          {
            consume_each(d_rel_offset-1); // consume up to tagged sample
            return 0;
          }
          // else tagged sample is first, so just continue
        }
        else
        {
          // didn't get correct tag in this batch
          consume_each(ninput_items[0]);
          return 0;
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
          tune_next_freq();
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
        d_cfreqs_iter = std::deque<double>(d_cfreqs_orig.begin(), d_cfreqs_orig.end());
        d_nskipped = 0;
        d_did_initial_tune = false;
        d_got_rx_freq_tag = false;
      }

      d_exit_flowgraph = false;
    }

    void
    controller_cc_impl::tune_next_freq()
    {
      rotate_cfreqs();
      ::uhd::tune_request_t tune_req(d_current_freq, d_lo_offset);
      d_tune_result = usrp_ptr->set_center_freq(tune_req);
    }

    void
    controller_cc_impl::rotate_cfreqs()
    {
      d_current_freq = d_cfreqs_iter.front();
      d_cfreqs_iter.pop_front();
      d_cfreqs_iter.push_back(d_current_freq);
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
