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

#ifndef INCLUDED_USRPANALYZER_CONTROLLER_CC_IMPL_H
#define INCLUDED_USRPANALYZER_CONTROLLER_CC_IMPL_H

#include <vector>

#include <pmt/pmt.h>
#include <gnuradio/feval.h>
#include <usrpanalyzer/controller_cc.h>

namespace gr {
  namespace usrpanalyzer {

    class controller_cc_impl : public controller_cc
    {
    private:
      // used for finding tag streams
      bool d_got_rx_freq_tag;     // true after caught rx_freq tag after retune
      pmt::pmt_t d_tag_key;
      size_t d_range_start;
      size_t d_range_stop;
      size_t d_rel_offset;
      std::vector<gr::tag_t> d_tags;

      // used for skipping samples
      size_t d_skip_initial;        // samples to skip after rx_freq tag/before copy
      size_t d_nskipped;          // total samples skipped so far this segment
      size_t d_skips_left;        // d_skip_initial - d_skipped
      size_t d_nskip_this_time;   // samples to copy this call to general_work

      // used for copying
      size_t d_ncopy;             // samples to copy per segment
      size_t d_ncopied;           // total samples copied so far this segment
      size_t d_copies_left;       // d_ncopy - d_ncopied
      size_t d_ncopy_this_time;   // samples to copy this call to general_work

      // used for general flow control
      feval_dd* d_tune_callback;  // callback to retune USRP
      size_t d_nsegments;         // number of center frequencies in span
      size_t d_current_segment;   // incremented from 1 to nsegments
      double d_current_freq;      // holds return val of tune_callback
      bool d_did_initial_tune;    // true after initial call to tune_callback
      bool d_retune;              // convenience variable for "nsegments > 1"
      bool d_done_copying;
      bool d_last_segment;
      bool d_exit_after_complete; // if true, exit at end of span
      bool d_exit_flowgraph;      // if true, exit immediately

      void reset();               // helper function called at end of span
    public:
      controller_cc_impl(feval_dd *tune_callback,
                         size_t skip_initial,
                         size_t ncopy,
                         size_t nsegments
        );

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items);

      bool get_exit_after_complete();
      void set_exit_after_complete();
      void clear_exit_after_complete();
      void reset_nskipped();
    };

  } // namespace usrpanalyzer
} // namespace gr

#endif /* INCLUDED_USRPANALYZER_CONTROLLER_CC_IMPL_H */
