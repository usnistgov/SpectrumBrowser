function idxf0 = findPeaks(w, wT)
% Returns indices of peak of band of continguous frequency bins with
% measured radar signals that exceed threshold wT 
n = nXgtY(w, wT);
if n == 0
  idxf0 = [];
else 
  [~, idx1] = sort(w, 'descend');
  idx2 = sort(idx1(1:n));
  m = 0; % Number of blocks of contiguous frequency bins with w >= wT
  for k = 1:n
    if k == 1 || idx2(k) ~= idx2(k-1)+1
      cnt = 1; % Number of contiguous frequency bins with w >= wT
      m = m + 1;
      idxf0(m) = idx2(k);
    else
      cnt = cnt + 1;
      [~,idxMax] =  max(w(idx2(k - cnt + 1):idx2(k)));
      idxf0(m) = idxMax + idx2(k - cnt + 1) - 1;
    end
  end
end

