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

#ifndef INCLUDED_USRPANALYZER_SKIPHEAD_RESET_IMPL_H
#define INCLUDED_USRPANALYZER_SKIPHEAD_RESET_IMPL_H

#include <usrpanalyzer/skiphead_reset.h>

namespace gr {
  namespace usrpanalyzer {

    class skiphead_reset_impl : public skiphead_reset
    {
    private:
      uint64_t d_nitems_to_skip;
      uint64_t d_nitems;           // total items seen
      uint64_t d_nitems_skipped;   // total items skipped
      
    public:
      skiphead_reset_impl(size_t itemsize, uint64_t nitems_to_skip);
      ~skiphead_reset_impl();

      void set_nitems_to_skip(uint64_t nitems_to_skip);

      uint64_t nitems_to_skip() const;

      uint64_t nitems_skipped() const;

      void reset();
      
      int general_work(int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items);
    };

  } // namespace usrpanalyzer
} // namespace gr

#endif /* INCLUDED_USRPANALYZER_SKIPHEAD_RESET_IMPL_H */
