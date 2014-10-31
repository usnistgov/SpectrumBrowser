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


#ifndef INCLUDED_USRPANALYZER_SKIPHEAD_RESET_H
#define INCLUDED_USRPANALYZER_SKIPHEAD_RESET_H

#include <usrpanalyzer/api.h>
#include <gnuradio/sync_block.h>
#include <stddef.h>  /* size_ t */

namespace gr {
  namespace usrpanalyzer {

    /*!
     * \brief adds a reset member function to skiphead
     * \ingroup usrpanalyzer
     *
     */
    class USRPANALYZER_API skiphead_reset : virtual public gr::block
    {
     public:
      typedef boost::shared_ptr<skiphead_reset> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of usrpanalyzer::skiphead_reset.
       *
       * To avoid accidental use of raw pointers, usrpanalyzer::skiphead_reset's
       * constructor is in a private implementation
       * class. usrpanalyzer::skiphead_reset::make is the public interface for
       * creating new instances.
       */
      static sptr make(size_t itemsize, uint64_t nitems_to_skip);

      /*!
       * \brief Set number of items to skip
       */
      virtual void set_nitems_to_skip(uint64_t nitems_to_skip) = 0;

      /*!
       * \brief Return number of items to skip
       */
      virtual uint64_t nitems_to_skip() const = 0;

      /*!
       * \brief Return number of items skipped
       */
      virtual uint64_t nitems_skipped() const = 0;

      /*!
       * \brief Reset d_nitems (the number of items skipped) to 0.
       */
      virtual void reset() = 0;
    };

  } // namespace usrpanalyzer
} // namespace gr

#endif /* INCLUDED_USRPANALYZER_SKIPHEAD_RESET_H */

