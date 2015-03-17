/* -*- c++ -*- */

#define USRPANALYZER_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "usrpanalyzer_swig_doc.i"

%{
#include "usrpanalyzer/bin_statistics_ff.h"
#include "usrpanalyzer/stitch_fft_segments_ff.h"
#include "usrpanalyzer/controller_cc.h"
%}

%include "usrpanalyzer/bin_statistics_ff.h"
GR_SWIG_BLOCK_MAGIC2(usrpanalyzer, bin_statistics_ff);
%include "usrpanalyzer/stitch_fft_segments_ff.h"
GR_SWIG_BLOCK_MAGIC2(usrpanalyzer, stitch_fft_segments_ff);
%include "usrpanalyzer/controller_cc.h"
GR_SWIG_BLOCK_MAGIC2(usrpanalyzer, controller_cc);
