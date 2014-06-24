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


#ifndef INCLUDED_MYBLOCKS_FILE_DESCRIPTOR_SOURCE_H
#define INCLUDED_MYBLOCKS_FILE_DESCRIPTOR_SOURCE_H

#include <myblocks/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace myblocks {

    /*!
     * \brief <+description of block+>
     * \ingroup myblocks
     *
     */
    class MYBLOCKS_API file_descriptor_source : virtual public gr::sync_block
    {
     public:
      typedef boost::shared_ptr<file_descriptor_source> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of myblocks::file_descriptor_source.
       *
       * To avoid accidental use of raw pointers, myblocks::file_descriptor_source's
       * constructor is in a private implementation
       * class. myblocks::file_descriptor_source::make is the public interface for
       * creating new instances.
       */
      static sptr make(size_t itemsize, int fd, bool repeat=false);

      /*!
       * \brief Set file descriptor
       */
      virtual void set_fd(int fd) = 0;
    };

  } // namespace myblocks
} // namespace gr

#endif /* INCLUDED_MYBLOCKS_FILE_DESCRIPTOR_SOURCE_H */

