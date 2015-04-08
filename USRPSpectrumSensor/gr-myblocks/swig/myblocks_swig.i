/* -*- c++ -*- */

#define MYBLOCKS_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "myblocks_swig_doc.i"

%{
#include "myblocks/bin_aggregator_ff.h"
#include "myblocks/bin_statistics_ff.h"
#include "myblocks/file_descriptor_sink.h"
#include "myblocks/file_descriptor_source.h"
#include "myblocks/threshold_timestamp.h"
%}

%include "myblocks/bin_aggregator_ff.h"
GR_SWIG_BLOCK_MAGIC2(myblocks, bin_aggregator_ff);

%include "myblocks/bin_statistics_ff.h"
GR_SWIG_BLOCK_MAGIC2(myblocks, bin_statistics_ff);
%include "myblocks/file_descriptor_sink.h"
GR_SWIG_BLOCK_MAGIC2(myblocks, file_descriptor_sink);
%include "myblocks/file_descriptor_source.h"
GR_SWIG_BLOCK_MAGIC2(myblocks, file_descriptor_source);
%include "myblocks/threshold_timestamp.h"
GR_SWIG_BLOCK_MAGIC2(myblocks, threshold_timestamp);
