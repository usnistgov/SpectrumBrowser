function x_W = dBW2W(x_dBW)
%
% dBW2W(x_dBW) converts dBW into Watts.
%
% written by Mike Cotton (303-497-7346, mcotton@its.bldrdoc.gov)

x_W = 10.^(x_dBW/10);