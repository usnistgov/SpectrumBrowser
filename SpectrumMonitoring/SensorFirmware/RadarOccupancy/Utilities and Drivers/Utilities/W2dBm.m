function x_dBm = W2dBm(x_W)
%
% W2dBm(x_W) converts Watts into dBm.
%
% written by Mike Cotton (303-497-7346, mcotton@its.bldrdoc.gov)

x_dBm = 10*log10(x_W) + 30;