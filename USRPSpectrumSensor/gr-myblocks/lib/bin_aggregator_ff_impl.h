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

#ifndef INCLUDED_MYBLOCKS_BIN_AGGREGATOR_FF_IMPL_H
#define INCLUDED_MYBLOCKS_BIN_AGGREGATOR_FF_IMPL_H

#include <myblocks/bin_aggregator_ff.h>

namespace gr {
  namespace myblocks {

    class bin_aggregator_ff_impl : public bin_aggregator_ff
    {
     private:
      unsigned int d_input_vlen;
      unsigned int d_output_vlen;
      std::vector<unsigned int> d_output_bin_index;

     public:
      void set_bin_index(const std::vector<unsigned int> &output_bin_index);

      bin_aggregator_ff_impl(unsigned int input_vlen, unsigned int output_vlen, const std::vector<unsigned int> &output_bin_index);
      ~bin_aggregator_ff_impl();

      // Where all the action really happens
      int work(int noutput_items,
	       gr_vector_const_void_star &input_items,
	       gr_vector_void_star &output_items);
    };

  } // namespace myblocks
} // namespace gr

#endif /* INCLUDED_MYBLOCKS_BIN_AGGREGATOR_FF_IMPL_H */

