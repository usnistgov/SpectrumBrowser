# Copyright 2011,2012 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

########################################################################
# Setup library
########################################################################
include(GrPlatform) #define LIB_SUFFIX

include_directories(${Boost_INCLUDE_DIR})
link_directories(${Boost_LIBRARY_DIRS})
list(APPEND myblocks_sources
    bin_aggregator_ff_impl.cc
    bin_statistics_ff_impl.cc
    file_descriptor_sink_impl.cc
    file_descriptor_source_impl.cc )

add_library(gnuradio-myblocks SHARED ${myblocks_sources})
#target_link_libraries(gnuradio-myblocks ${Boost_LIBRARIES} ${GNURADIO_RUNTIME_LIBRARIES})
target_link_libraries(gnuradio-myblocks ${Boost_LIBRARIES} ${GNURADIO_ALL_LIBRARIES})
set_target_properties(gnuradio-myblocks PROPERTIES DEFINE_SYMBOL "gnuradio_myblocks_EXPORTS")

########################################################################
# Install built library files
########################################################################
install(TARGETS gnuradio-myblocks
    LIBRARY DESTINATION lib${LIB_SUFFIX} # .so/.dylib file
    ARCHIVE DESTINATION lib${LIB_SUFFIX} # .lib file
    RUNTIME DESTINATION bin              # .dll file
)

########################################################################
# Build and register unit test
########################################################################
include(GrTest)

include_directories(${CPPUNIT_INCLUDE_DIRS})

list(APPEND test_myblocks_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/test_myblocks.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/qa_myblocks.cc
)

add_executable(test-myblocks ${test_myblocks_sources})

target_link_libraries(
  test-myblocks
  ${GNURADIO_RUNTIME_LIBRARIES}
  ${Boost_LIBRARIES}
  ${CPPUNIT_LIBRARIES}
  gnuradio-myblocks
)

GR_ADD_TEST(test_myblocks test-myblocks)
