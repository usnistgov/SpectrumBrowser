function [band, Sys, Loc, Out, Comment] = ReadInitFile(filename)

if isequal(exist(filename, 'file'), 2)
  fid = fopen(filename, 'r');
  % band = loadjson(fgetl(fid));
  band = str2num(fgetl(fid));
  Sys = loadjson(ReadJsonPacket(fid));
  Loc = loadjson(ReadJsonPacket(fid));
  Out = loadjson(ReadJsonPacket(fid));
  % x = loadjson(fgetl(fid));
  % Comment = x{1};
  Comment = fgetl(fid);
  fclose(fid);
end
