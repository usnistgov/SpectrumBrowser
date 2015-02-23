function WriteInitFile(filename, band, Sys, Loc, Out, Comment)
fid = fopen(filename, 'w');
% str = strrep(savejson('', band), sprintf('\n'), sprintf('\r\n'));
% fprintf(fid, '%s', str);
fprintf(fid, '%i\r\n', band);
str = strrep(savejson('', Sys), sprintf('\n'), sprintf('\r\n'));
fprintf(fid, '%s', str);
str = strrep(savejson('', Loc), sprintf('\n'), sprintf('\r\n'));
fprintf(fid, '%s', str);
str = strrep(savejson('', Out), sprintf('\n'), sprintf('\r\n'));
fprintf(fid, '%s', str);
% str = strcat(['[' strrep(savejson('', Comment), sprintf('\n'), sprintf(''))], sprintf(']\r\n'));
% fprintf(fid, '%s', str);
fprintf(fid, '%s\r\n', Comment);
fclose(fid);
