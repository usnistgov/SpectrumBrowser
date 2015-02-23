function str = zzz2str(x,N)
% Returns a string equivalent to x, but N characters long with leading zeros.
%
% written by Mike Cotton (303-497-7346)

Nx = length(num2str(x));
if N>Nx
  for k = 1:N-Nx
    zzz(k) = '0';
  end
else
  zzz = '';
end
str = [zzz num2str(x)];
