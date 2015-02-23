function n = nXgtY(X,y)
% nXgtY(x,y) returns number of elements in X that exceed y.
%
% input parameters:
% X = sample fct of random variable
% y = ordinate
%
% return variables:
% n = number of elements where X > y

if isreal(X)
  n = length(find(X > y));
else
  disp('nXgtY: Input values must be real.');
end
