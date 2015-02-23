function [s, nC, nl] = ReadJsonPacket(fid)
% ReadJsonPacket reads the next JSON packet starting from the file pointer
% (fid). A JSON packet begins and ends with curly brackets. 
n = 0;
s = '';
nC = 0;
nl = 0;
% Find the first open bracket
while n == 0 && ~feof(fid)
  l = fgetl(fid);
  n = length(strfind(l, '{'));
end
% If open bracket was found read until close bracket
if n > 0
  s = strcat(s, l);
  nl = 1;
  while n>0
    clear l
    l = fgetl(fid);
    n = n + length(strfind(l, '{')) - length(strfind(l, '}'));
    s = strcat(s, l);
    nl = nl + 1;
  end
  nC = length(s);
end
