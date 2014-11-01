/* -*- c++ -*- */

#define USRPANALYZER_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "usrpanalyzer_swig_doc.i"

%{
#include "usrpanalyzer/skiphead_reset.h"
%}


%include "usrpanalyzer/skiphead_reset.h"
GR_SWIG_BLOCK_MAGIC2(usrpanalyzer, skiphead_reset);
