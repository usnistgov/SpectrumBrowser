function x = SA_P2A(tau, RBW)
% SA_P2A calculates the peak-to-average ratio for a spectrum analyzer
% positive-peak-detected measurement of Gaussian noise.
% Input variables:
% tau = dwell-time (seconds)
% RBW = resolution bandwidth
% written by Michael Cotton, mcotton@its.bldrdoc.gov, 303-497-7346
% x = log(2*pi*tau*1.68*RBW + exp(1));
x = log(2*pi*tau*1.499*RBW + exp(1));
