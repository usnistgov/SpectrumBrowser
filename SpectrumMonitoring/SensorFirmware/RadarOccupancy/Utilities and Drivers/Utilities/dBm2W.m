function x_W = dBm2W(x_dBm)
%
% dBW2W(x_dBW) converts dBW into Watts.
%
% written by Mike Cotton (303-497-7346, mcotton@its.bldrdoc.gov)

x_W = 10.^((x_dBm-30)/10);