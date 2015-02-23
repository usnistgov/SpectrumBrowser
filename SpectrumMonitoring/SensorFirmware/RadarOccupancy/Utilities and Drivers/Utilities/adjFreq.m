function [f, units] = adjFreq(Hz);
%
% [f, units] = adjFreq(Hz) adjusts the frequency units.
%
% written by Mike Cotton (303-497-7346, mcotton@its.bldrdoc.gov)

if log10(min(Hz)) >= 9
  f = Hz*10^-9;
  units = 'GHz';
elseif log10(min(Hz)) >= 6
  f = Hz*10^-6;
  units = 'MHz';
elseif log10(min(Hz)) >= 3
  f = Hz*10^-3;
  units = 'kHz';
else
  f = Hz;
  units = 'Hz';
end

