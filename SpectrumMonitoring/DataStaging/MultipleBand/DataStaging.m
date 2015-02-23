function varargout = DataStaging(varargin)
% DataStaging MATLAB code for DataStaging.fig
%      DataStaging, by itself, creates a new DataStaging or raises the existing
%      singleton*.
%
%      H = DataStaging returns the handle to a new DataStaging or the handle to
%      the existing singleton*.
%
%      DataStaging('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in DataStaging.M with the given input arguments.
%
%      DataStaging('Property','Value',...) creates a new DataStaging or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before DataStaging_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to DataStaging_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help DataStaging

% Last Modified by GUIDE v2.5 17-Feb-2015 15:18:25

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
    'gui_Singleton',  gui_Singleton, ...
    'gui_OpeningFcn', @DataStaging_OpeningFcn, ...
    'gui_OutputFcn',  @DataStaging_OutputFcn, ...
    'gui_LayoutFcn',  [] , ...
    'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before DataStaging is made visible.
function DataStaging_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to DataStaging (see VARARGIN)

% Choose default command line output for DataStagingServer
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% Start Initialization
iniData(hObject, eventdata, handles);

% --- Outputs from this function are returned to the command line.
function varargout = DataStaging_OutputFcn(hObject, eventdata, handles)
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
try
    varargout{1} = handles.output;
catch
    
end

% Determine whether or not the GUI needs to be closed
if (isfield(handles,'closeFigure') && handles.closeFigure)
    figure1_CloseRequestFcn(hObject, eventdata, handles)
end

% --- Executes on selection change in senBand.
function senBand_Callback(hObject, eventdata, handles)
% hObject    handle to senBand (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

contents = cellstr(get(handles.senBand,'String'));

if ~isempty(contents) && isfield(handles,'sensor')
    pCStructure = handles.sensor;
    changegui(pCStructure, handles); changeplot(pCStructure, handles);
else
    return;
end

% --- Executes during object creation, after setting all properties.
function senBand_CreateFcn(hObject, eventdata, handles)
% hObject    handle to senBand (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit1_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit2_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit3_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit4_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit5_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit6_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit7_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit8_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit9_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit10_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit11_CreateFcn(hObject, eventdata, handles)
% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit13_CreateFcn(hObject, eventdata, handles)

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit12_CreateFcn(hObject, eventdata, handles)

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit14_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit14 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit15_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit15 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit16_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit16 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit17_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit17 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in pushbutton3.
function pushbutton3_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

selection = questdlg(['Close ' get(handles.figure1,'Name') '?'],...
    ['Close ' get(handles.figure1,'Name') '...'],...
    'Yes','No','Yes');
if strcmp(selection,'No')
    return;
end

try
    stop(timerfindall);
    delete(timerfindall);
    delete(handles.figure1);
catch
    delete(handles.figure1);
end

% --- Executes during object creation, after setting all properties.
function edit18_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit18 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit19_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit18 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function edit20_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit20 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edit21_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit19 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes when user attempts to close figure1.
function figure1_CloseRequestFcn(hObject, eventdata, handles)
% hObject    handle to figure1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: delete(hObject) closes the figure
% stop(getappdata(hObject, 'timer_objF')); % stops the timer
% delete(getappdata(hObject, 'timer_objF'));  % delete the timer object
try
    stop(timerfindall);
    delete(timerfindall);
    delete(hObject);
catch
    delete(hObject);
end


% --- Executes during object creation, after setting all properties.
function edit25_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit21 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function ClearPlots(h)
axes(h.axCal);
hold off;
plot([], [])
axes(h.axFreq);
hold off;
plot([], [])
axes(h.axContour);
hold off
plot([], [])


function iniData(hObject, eventdata, handles)

persistent localDirectory sensorStructure

%Clears ALL PLots
ClearPlots(handles)

%Win vs Lin Environment
if ispc == 1
    localDirectory = 'G:\Created\'; handles.local = localDirectory;
else
    localDirectory = '~/home/Radar/'; handles.local = localDirectory;
end

%Searches Current Folder Directory
[ cDstructure, popup, handles ] = chkDir(localDirectory, sensorStructure, handles); %Parses Directories and Validates Files

%If Error vs Updating GUI
if (isfield(handles,'closeFigure') && handles.closeFigure) % Determine whether or not the GUI needs to be closed
    figure1_CloseRequestFcn(hObject, eventdata, handles);
else
    [ pDStructure ] = parLoad(cDstructure); %Load Files From Directory and Validate
    
    if ~isempty(popup)
        set(handles.senBand,'String',popup);
        set(handles.senBand,'Value', 1);
        set(handles.radBand,'Visible','on');
    else
        set(handles.senBand,'String','No Available Sensors');
        set(handles.senBand,'Enable','off');
        set(handles.radBand,'String','No Available Bands');
        set(handles.radBand,'Enable','off');
    end
    
    [ tDStructure ] = tempcalculations(pDStructure,handles);
    
    changegui(tDStructure, handles); changeplot(tDStructure, handles);
    
    %Saves Values to Figure Structure
    handles.pop = popup; handles.sensor = tDStructure;
    guidata(handles.figure1, handles); %timedChecks(hObject,handles);
    
end


function [ workingStructure, popupArray, shandles ] = chkDir( localDirectory, sensorArray, handles )

persistent nameArray

%Check if local directory is VALID, if not CLOSE the Entire GUI%
if ~isequal(exist(localDirectory,'dir'),7)
    uiwait(msgbox({'There is an ERROR with the Directory Path!'; 'The GUI will now close'}));
    workingStructure = ''; popupArray = '';
    handles.closeFigure = true; guidata(handles.figure1, handles);    
    shandles = handles;
else
    
    %If Directory is VALID, Continue with read and create Sensor%
    dir_list = dir(localDirectory); nameArray = {};
    
    sub = regexp( {dir_list.name}, 'Sensor.*', 'match' ); subs = ~cellfun( 'isempty', sub );
    sub_list = dir_list( subs ); 
    
    %Check if Folders in Directory are Unique Names
    [us, ~, n] = unique({sub_list.name}); resultArray = us(histc(n, 1:length(us))>1);
    
    if isempty(resultArray) == 1
        currentLength = length( nameArray ); subLength = length ( sub_list );
        
        if subLength > currentLength
            dirNames = {sub_list.name}; cur_list = setdiff( dirNames, nameArray );
            cur_length = length( cur_list );
            
            for i=1 : cur_length
                nameArray = horzcat(nameArray, cur_list(i).name);
                sensorArray(currentLength+i).sensor = cur_list(i).name;
                sensorArray(currentLength+i).directory = sprintf('%s\\%s',localDirectory, cur_list(i).name);
            end
            
        end
    else
        uiwait(msgbox({'There is a NAMING issue in the Directory!'; 'The GUI will be closed until further notice'}));
        clear nameArray
    end
    
    shandles = handles; workingStructure = sensorArray; popupArray = nameArray;
end


function [ resultArray ] = chkUnq( suspiciousArray )

[u, ~, n]  = unique(suspiciousArray);
compare = histc(n, 1:length(u));
resultArray = u(compare>1);


function [ workingStructure ] = parLoad( passedStructure )

if ~exist('len','var')
    len = length(passedStructure);
end

clearvars d_count e_count s_count d_list oet cet
%  fid = fopen( strcat(passedStructure(iD).directory,'\Error\error.txt'), 'w+' ); %Create and Open SensorLogErrorFile

for iD=1: len
    d_list = dir( strcat( passedStructure(iD).directory, '*.json' ) ); %Collects Current Directory List
    passedStructure(iD).directory_list = d_list; %Saves Directory List
    passedStructure(iD).directory_count = length(d_list); %Saves Current Directory Length
    direct_count = length(d_list);
    
    if direct_count ~= 0
        for dL=1: direct_count %Validation Loop
            filename = strcat( passedStructure(iD).directory, '\', d_list(dL).name);
            
            try
                vFile = loadjson(filename);
            catch
                % return;  %fprintf(fid, '%s: %s: %s \r', 'The File is Corrupted, Check the Formatting:', d_list(dL).name, datestr(clock , 'HH:MM PM')) ;
            end
            [~, qc] = parValidate(filename, vFile, d_list(dL).name); %Validate Files
            
            if strcmp(num2str(qc),'0') == 0 %If Not Validated, ,Move & Write to File
                %movefile(filename,'PF\')
            end
        end
        
        %Update Sensor List If Any Invalidated Files Existed
        d_list = dir( strcat( passedStructure(iD).directory, '*.json' ) ); %Collects Current Directory List
        passedStructure(iD).directory_list = d_list; %Saves Directory List
        passedStructure(iD).directory_count = length(d_list); %Saves Current Directory Length
        
    end
    
end


workingStructure = passedStructure;


function [ eText, output ] = parValidate( toss, name, standard )

persistent version type mobility errorText errorCount time_test sensor_unique model polar ...
    make stype datatype border process det comp s2d sen dtype timezone ol

if isempty(version)
    version = {'1.0.11'}; type = {'LocA', 'Sys', 'Data'}; mobility = {'Stationary', 'Mobile'};
    errorText = {}; errorCount = 0; timezone = {'America/New_York', 'America/Chicago', 'America/Denver', 'America/Phoenix', 'America/Los_Angeles'};
    
    
    if length(name) == 1
        time_test = name.t;
    else
        time_test = name{1}.t;
    end %Time Value Should Increase With Every New File%
    
    %Sensor ID is a Unique Key that will be Used to Validate Sensors Before
    %Data is Processed and Displayed%
    sensor_unique = {};
    
    model = {'AAC SPBODA-1080_NFi', 'Alpha AW3232', 'Cobham OA2-0.3-10.0v/1505/Omni/VPOL'};
    polar = {'VL', 'HL', 'LHC', 'RHC', 'Slant', 'Vertical'}; process = {'True', 'False'};
    make = {'Agilent N6841A', 'Agilent E4440A', 'CRFS RFeye', 'NI USRP N210', 'ThinkRF WSA5000-108', 'Spectrum Hound BB60C'};
    stype = {'Y-factor: swept-frequency', 'Y-factor: FFT-power', 'None'};  det = {'RMS', 'Positive'};
    datatype = {'Binary - float32', 'Binary - int16', 'Binary - int8', 'ASCII'}; ol = {'0', '1'};
    border = {'Network', 'Big Endian', 'Little Endian', 'N/A'}; comp = {'Zip', 'None', 'N/A'};
    
    s2d = {'Radar - SPN43', 'LTE', 'None'}; sen = {'Low', 'Medium', 'High'}; dtype = {'Swept-frequency', 'FFT-power'};
    
end

switch length(name)
    case 1
        if strcmp(name.Type,'Loc') == 1 %Determine if File is Location
            
            if time_test <= name.t;
                
                loc = name; lscompare = [strcmp(loc.Ver,version), isempty(setdiff(loc.Type,type)), isempty(setdiff(loc.Mobility,mobility)), ...
                    isempty(setdiff(loc.TimeZone,timezone))];
                
                lfcompare = [isfloat(loc.Lat), isfloat(loc.Lon), isfloat(loc.Alt)];
                
                lrcompare = [loc.Lat> 360 || loc.Lat < 0, loc.Lon > 180 || loc.Lon < -180, loc.Alt > 10^6 || loc.Alt < 0];
                
                if any(lscompare == 0) == 1 || any(lfcompare == 0) == 1 || any(lrcompare == 1) == 1
                    errorText = [errorText, sprintf('The Error Occured in File %s at %s\n',standard,datestr(clock , 'HH:MM PM'))];
                    
                    if any(lscompare == 0) == 1 %Loc File was Not Compatible with Current Settings
                        errorText = [errorText, sprintf('Please Check the Version Number, Document Type, and/or the set Mobility Preference.\n')];
                    end
                    
                    if any(lfcompare == 0) == 1
                        errorText = [errorText, sprintf('Error with Latitude, Longitude, and/or Altitude Ranges. Data Type Error.\n')];
                    end
                    
                    lat = loc.Lat> 360 || loc.Lat < 0; lon = loc.Lon > 180 || loc.Lon < -180; alt = loc.Alt > 10^6 || loc.Alt < 0;
                    
                    
                    if lat == 1
                        errorText = [errorText, sprintf('Latitude Angle is not within Range. Out of Bounds.\n')];
                    end
                    
                    if lon == 1
                        errorCount = errorCount + 1;    errorText = [errorText, sprintf('Longitude Angle is not within Range. Out of Bounds.\n')];
                    end
                    
                    if alt == 1
                        errorText = [errorText, sprintf('Altitude Angle is not within Range. Out of Bounds.\n')];
                    end
                    
                    output = 1;
                    
                else
                    output = 0;
                end
                
                time_test = name.t;
            else
                output = 1;
            end
            
        else
            
            errorText = [errorText, sprintf('The File Contains No Data Blocks but it is NOT a Location Message. File Type Error.\n')];
            errorText = [errorText, sprintf('The Error Occured in File %s at %s\n',standard,datestr(clock , 'HH:MM PM'))];
            movefile(toss,'Error'); %If It Does Push Error Files to It
            output = 1;
        end
        
    case 2
        if strcmp(name{1}.Type,'Data') == 1 %Determine if File is a Data File with One Data Block
            
            if time_test <= name{1}.t;
                
                data = name{1}; dscompare = [strcmp(data.Ver,version), isempty(setdiff(data.Type,type)), isempty(setdiff(data.Sys2Detect,s2d)), ...
                    isempty(setdiff(data.Sensitivity, sen)), isempty(setdiff(data.mType,dtype)), isempty(setdiff(data.Processed,process)), ...
                    isempty(setdiff(data.DataType,datatype)), isempty(setdiff(data.ByteOrder,border)), isempty(setdiff(data.Compression,comp)), ...
                    isempty(setdiff(data.mPar.Det,det)), isempty(setdiff(num2str(data.OL),ol))];
                
                dfcompare = [isfloat(data.Ta), isfloat(data.wnI), isfloat(data.mPar.fStart), isfloat(data.mPar.fStop), isfloat(data.mPar.n), ...
                    isfloat(data.mPar.td), isfloat(data.mPar.RBW), isfloat(data.mPar.VBW), isfloat(data.mPar.Atten)];
                
                dicompare = [isfloat(data.t), isfloat(data.t1), isfloat(data.a), isfloat(data.nM)];
                
                
                if any(dscompare == 0) == 1 || any(dfcompare == 0) == 1 || any(dicompare == 0) == 1
                    errorText = [errorText, sprintf('The Error Occured in File %s at %s\n',standard,datestr(clock , 'HH:MM PM'))];
                    
                    if any(dscompare == 0) == 1
                        errorText = [errorText, sprintf('Please Check all String Types. Data Type Error.\n')];
                    end
                    
                    if any(dfcompare == 0) == 1
                        errorText = [errorText, sprintf('Please Check all Float Types including the mPar Block. Data Type Error\n')];
                    end
                    
                    if any(dicompare == 0) == 1
                        errorText = [errorText, sprintf('Please Check the t, t1, a, nM, and/or OL fields. Data Type Error\n')];
                    end
                    
                    output = 1;
                    
                else
                    
                    output = 0;
                    
                end
                
                time_test = name{1}.t;
                
            else
                
                output = 1;
                
            end
            
        else %If Not There is an Error Within the File, Move to a Different Directory
            
            errorText = [errorText, sprintf('The File Contains One Data Block but it is NOT a Data Message. File Type Error.\n')];
            errorText = [errorText, sprintf('The Error Occured in File %s at %s\n',standard,datestr(clock , 'HH:MM PM'))];
            movefile(toss,'Error'); %If It Does Push Error Files to It
            output = 1;
        end
        
    case 3
        if strcmp(name{1}.Type,'Sys') %Determine if FIle is a Sys File with Two Data Blocks
            
            if time_test <= name{1}.t;
                
                sys = name{1}; sscompare = [strcmp(sys.Ver,version), isempty(setdiff(sys.Type,type)), isempty(setdiff(sys.Antenna.Model,model)), ...
                    isempty(setdiff(sys.Antenna.Pol,polar)), isempty(setdiff(sys.COTSsensor.Model,make)), isempty(setdiff(sys.Cal.mType,stype)), ...
                    isempty(setdiff(sys.Cal.Processed,process)), isempty(setdiff(sys.Cal.DataType,datatype)), isempty(setdiff(sys.Cal.ByteOrder,border)), ...
                    isempty(setdiff(sys.Cal.Compression,comp)), isempty(setdiff(sys.Cal.mPar.Det,det))];
                
                sfcompare = [isfloat(sys.Antenna.fLow), isfloat(sys.Antenna.fHigh), isfloat(sys.Antenna.g), isfloat(sys.Antenna.bwH), isfloat(sys.Antenna.bwV), ...
                    isfloat(sys.Antenna.AZ), isfloat(sys.Antenna.EL), isfloat(sys.Antenna.XSD), isfloat(sys.Antenna.VSWR), isfloat(sys.Antenna.lCable), ...
                    isfloat(sys.Preselector.fLowPassBPF), isfloat(sys.Preselector.fHighPassBPF), isfloat(sys.Preselector.fLowStopBPF), ...
                    isfloat(sys.Preselector.fHighStopBPF), isfloat(sys.Preselector.fnLNA), isfloat(sys.Preselector.gLNA), ...
                    isfloat(sys.Preselector.pMaxLNA), isfloat(sys.COTSsensor.fLow), isfloat(sys.COTSsensor.fHigh), isfloat(sys.COTSsensor.fn), ...
                    isfloat(sys.COTSsensor.pMax), isfloat(sys.Cal.CalsPerHour),  isfloat(sys.Cal.Temp), isfloat(sys.Cal.mPar.fStart), ...
                    isfloat(sys.Cal.mPar.fStop), isfloat(sys.Cal.mPar.n), isfloat(sys.Cal.mPar.td), isfloat(sys.Cal.mPar.RBW), ...
                    isfloat(sys.Cal.mPar.VBW), isfloat(sys.Cal.mPar.Atten)];
                
                sicompare = [isfloat(sys.t), isfloat(sys.Cal.nM)];
                
                if any(sscompare == 0) == 1 || any(sfcompare == 0) == 1 || any(sicompare == 0) == 1
                    errorText = [errorText, sprintf('The Error Occured in File %s at %s\n',standard,datestr(clock , 'HH:MM PM'))];
                    
                    if any(sscompare == 0) == 1
                        errorText = [errorText, sprintf('Please Check all String Types. Data Type Error.\n')];
                    end
                    
                    if any(sfcompare == 0) == 1
                        errorText = [errorText, sprintf('Please Check all Float Types including the mPar Block. Data Type Error\n')];
                    end
                    
                    if any(sicompare == 0) == 1
                        errorText = [errorText, sprintf('Please Check the t and/or nM . Data Type Error\n')];
                    end
                    
                    output = 1;
                    
                else
                    
                    output = 0;
                    
                end
                
                time_test = name{1}.t;
                
            else
                
                output = 1;
                
            end
            
        else %If Not There is an Error Within the File, Move to a Different Directory
            
            errorText = [errorText, sprintf('The File Contains Two Data Blocks but it is NOT a System Message. File Type Error \n')];
            errorText = [errorText, sprintf('The Error Occured in File %s at %s \n',standard,datestr(clock , 'HH:MM PM'))];
            movefile(toss,'Error'); %If It Does Push Error Files to It
            output = 1;
        end
end

eText = errorText;


function [ output_args ] = timedChecks( hObject, handles )
%UNTITLED12 Summary of this function goes here
%   Detailed explanation goes here

files_obj = timer(...
    'StartFcn',         @fileTimer, ...              % start function
    'TimerFcn',         {@files_timer_update, handles}, ...  % timer function, has to specific the handle to the GUI,
    'StopFcn',          @files_timer_stop, ...               % stop function
    'ErrorFcn',         @files_timer_err, ...                % error function
    'ExecutionMode',    'fixedRate', ...                    %
    'Period',           30.0, ...                           % updates every xx seconds
    'TasksToExecute',   inf, ...
    'BusyMode',         'drop');


start(files_obj);        % start the timer object

setappdata(hObject, 'timer_objF', files_obj');  % save the timer object as app data


function [ output_args ] = fileTimer( src, evt )

disp('Checking for New Files!');


function files_timer_update( src,evt, handles )

try
    fileStructure = handles.sensor; %Current Structure
    sensorDirectory = handles.local; %Current Directory
    
    %Parses Directories and Validates Files
    [ cDstructure, popup, handles ] = chkDir(sensorDirectory, fileStructure, handles);
    
    % Determine whether or not the GUI needs to be closed
    if (isfield(handles,'closeFigure') && handles.closeFigure)
        figure1_CloseRequestFcn(hObject, eventdata, handles);
    else
        [ pDStructure ] = parLoad(cDstructure); %Load Files From Directory and Validate
        
        
        if ~isempty(popup)
            set(handles.senBand,'String',popup);
        end
        
        
        [ tDStructure ] = tempcalculations(pDStructure,handles);
        changegui(tDStructure, handles); changeplot(tDStructure, handles);
        set(handles.edit18, 'string', datestr(clock + [0 0 0 0 0 30] , 'HH:MM PM'));
        
        %Saves Values to Figure Structure
        handles.pop = popup; handles.sensor = tDStructure;
        guidata(handles.figure1, handles);
    end
    
    
catch
   set(handles.edit18, 'string', datestr(clock + [0 0 0 0 0 30] , 'HH:MM PM'));
end


function files_timer_stop( src, evt )

disp('File Check Done');
stop(timerfindall);
delete(timerfindall);


function files_timer_err( src, evt )

disp('File error');


function tempStructure = tempcalculations(data, control)
%datestr(now)
strlen = length(data); d = datestr(clock,'dd-mmm-yyyy');
localD = control.local; vf = 1; 
persistent sF sMF sMG a cal couple cmf cmg NZ NZb NZs
persistent dF dFA dD lF w0r aa con wPk fox sw0r swnPk swT ol
persistent dFB sa cons wPks foxs sw0rs swnPks swTs ols
persistent dFS ba conb wPkb foxb sw0rb swnPkb swTb olb

for dC=1: strlen
    directory_list = data(dC).directory_list;
    dub = regexp( {directory_list.date}, d, 'match' );
    dub = ~cellfun( 'isempty', dub ); dub_list = directory_list( dub );
    dub_length = length ( dub_list );
    
    if isfield(data,'files')
        data(dC).files = ''; data(dC).syscal = '';
    end
    while vf <= dub_length
        filename = strcat( data(dC).directory, dub_list(vf).name);
        vFile = loadjson(filename); vFLen = length(vFile);
        
        switch vFLen
            case 1
                lF = vFile;
            case 2
                dF = vFile{1}; dD = vFile{2};
                
                switch dF.Sys2Detect
                    case 'Radar - ASR'
                        dFA = dF;
                    case 'Radar - BoatNav'
                        dFB = dF;
                    case 'Radar - SPN43'
                        dFS = dF;
                        if ~isempty(w0r)
                            wnPk = W2dBm(dBm2W(w0r)*SA_P2A(dF.mPar.td, dF.mPar.RBW)); % Peak-detected receiver noise level (dBm)
                            wT = 3+max(wnPk); % Threshold that identifies signal in peak-detected measurement (dBm)
                            StepSize = dF.mPar.RBW;
                            nSteps = floor(abs(dF.mPar.fStop - dF.mPar.fStart)/StepSize) + 1;
                            x = dF.mPar.fStart + transpose(0:(nSteps-1))*StepSize;
                            w = dD - sF.Antenna.lCable + sF.Antenna.g + sMG;
                            
                            if isempty(sa)
                                sa = 1;
                            else
                                sa = sa + 1;
                            end
                            
                            dt = datenum([1970, 1, 1, 0, 0, dF.t]); d = str2num(datestr(dt,'HH'));
                            cons(sa) = d; wPks(:,sa) = w; foxs(sa,:) = x'; sw0rs(sa,:) = w0r';
                            swnPks(sa,:) = wnPk'; swTs(sa,:) = wT'; ols(sa) = dF.OL;
                        end
                end
                
            case 3
                sF = vFile{1}; sMF = vFile{2}; sMG = vFile{3};
                
                if isempty(a)
                    a = 1;
                else
                    a = a + 1;
                end
                
                Mfn = W2dBW(mean(dBW2W(sMF))); Mg = W2dBW(mean(dBW2W(sMG)));
                w0r = W2dBm(1.38e-23*(25+273.15)*1.128*sF.Cal.mPar.RBW*dBW2W(sMF).*dBW2W(sMG));
                dt = datenum([1970, 1, 1, 0, 0, sF.t]); s = str2num(datestr(dt,'HH'));
                
                cal(a) = s; cmf(a) = Mfn; cmg(a) = Mg;
        end
        
        vf = vf + 1;
    end
    
    couple = {sF, dFA, dFB, dFS, lF};
    
    NZ = nnz(ol) + NZ; NZb = nnz(olb) + NZb; NZs = nnz(ols) + NZs;
    data(dC).files = couple; data(dC).syscal = {cal, cmf, cmg}; 
    data(dC).dataA = '';%{con wPk fox sw0r swnPk swT NZ};
    data(dC).dataB = '';%{conb wPkb foxb sw0rb swnPkb swTb NZb};
    data(dC).dataS = {cons wPks foxs sw0rs swnPks swTs NZs};
    a = ''; aa = ''; w0r = ''; NZ = 0; ol = ''; con = ''; wPk = ''; fox = ''; sw0r = ''; swnPk = ''; swT = ''; 
    ba = ''; NZb = 0; olb = ''; conb = ''; wPkb = ''; foxb = ''; sw0rb = ''; swnPkb = ''; swTb = '';
    sa = ''; NZs = 0; ols = ''; cons = ''; wPks = ''; foxs = ''; sw0rs = ''; swnPks = ''; swTs = '';
    couple = ''; cal = ''; cmf = ''; cmg = '';
    
end

tempStructure = data;


function changegui(data, control)

index1 = get(control.senBand,'Value'); index2 = get(control.radBand,'Value');

try
   filesystem = data(index1).files;
catch
    filesystem = '';
end
   
if ~isempty(filesystem)
    
    sysfile = filesystem{1}; locfile = filesystem{5}; syscalval = data(index1).syscal;
    
    switch index2
        case 1
            datafile = filesystem{2};
            dataconval = data(index1).dataA;
        case 2
            datafile = filesystem{3};
            dataconval = data(index1).dataB;
        case 3
            datafile = filesystem{4};
            dataconval = data(index1).dataS;
    end
        
        %System Message GUI Output%
        if ~isempty(sysfile)
            set(control.edit1, 'String', sysfile.COTSsensor.Model);
            set(control.edit2, 'String', sysfile.Antenna.Model);
            
            if ~isempty(syscalval)
                syscalt = syscalval{1}; syslen = length(syscalt);
                sysf = syscalval{2}; sysg = syscalval{3};
                
                if syslen >= 1  && ~isempty(datafile)
                    set(control.edit10, 'String', datestr(datenum([1970, 1, 1, 0, 0, sysfile.t])));
                    set(control.edit11, 'String', sysf(syslen));
                    set(control.edit12, 'String', sysg(syslen));
                    set(control.edit13, 'String', sysfile.Cal.Temp);
                else
                    set(control.edit10, 'String', 'Insufficient Information');
                    set(control.edit11, 'String', 'Insufficient Information');
                    set(control.edit12, 'String', 'Insufficient Information');
                    set(control.edit13, 'String', 'Insufficient Information');
                end
            end
            
        else
            set(control.edit1, 'String', 'System File Not Available');
            set(control.edit2, 'String', 'System File Not Available');
            set(control.edit10, 'String', 'Calibration Information Not Available');
            set(control.edit11, 'String', 'Calibration Information Not Available');
            set(control.edit12, 'String', 'Calibration Information Not Available');
            set(control.edit13, 'String', 'Calibration Information Not Available');
        end
        
        %Data Message GUI Output%
        if ~isempty(datafile)
            set(control.edit8, 'String', datafile.Sys2Detect);
            
            fSta = str2double(sprintf('%.3s',num2str(datafile.mPar.fStart)))/100;
            fSto = str2double(sprintf('%.3s',num2str(datafile.mPar.fStop)))/100;
            set(control.edit9, 'String', sprintf('%0.2f-%0.2f',fSta,fSto));
            
            if ~isempty(dataconval)
                datacont = dataconval{1}; datalen = length(datacont); ol = dataconval{7};
                if datalen >= 1
                    set(control.edit14, 'String', datalen);
                    set(control.edit15, 'String', (ol/datalen)*100);
                    ac= datenum(clock) - datenum([1970, 1, 1, 0, 0, datacont(datalen)]); A = datevec(ac);
                    set(control.edit16, 'String', sprintf('%d Years %d Month %d Days',A(1),A(2),A(3)));
                    set(control.edit17, 'String', datacont(datalen));
                else
                    set(control.edit14, 'String', 'Insufficient Information');
                    set(control.edit15, 'String', 'Insufficient Information');
                    set(control.edit16, 'String', 'Insufficient Information');
                    set(control.edit17, 'String', 'Insufficient Information');
                end
            end
            
        else
            set(control.edit8, 'String', 'Data Not Available')
            set(control.edit9, 'String', 'Data Not Available')
            set(control.edit14, 'String', 'Acquisition Information Not Available');
            set(control.edit15, 'String', 'Acquisition Information Not Available');
            set(control.edit16, 'String', 'Acquisition Information Not Available');
            set(control.edit17, 'String', 'Acquisition Information Not Available');
        end
        
        %Location Message GUI Output%
        if ~isempty(locfile)
            set(control.edit3, 'String', locfile.Mobility);
            set(control.edit4, 'String', locfile.Lat);
            set(control.edit5, 'String', locfile.Lon);
            set(control.edit6, 'String', locfile.Alt);
        else
            set(control.edit3, 'String', 'Location Not Available')
            set(control.edit4, 'String', 'N/A')
            set(control.edit5, 'String', 'N/A')
            set(control.edit6, 'String', 'N/A')
        end
        
        %Miscellaneous Messages GUI Output%
        set(control.edit7, 'String', data(index1).directory_count);
    
else
    set(control.edit1, 'String', 'System File Not Available');
    set(control.edit2, 'String', 'System File Not Available');
    set(control.edit10, 'String', 'Calibration Information Not Available');
    set(control.edit11, 'String', 'Calibration Information Not Available');
    set(control.edit12, 'String', 'Calibration Information Not Available');
    set(control.edit13, 'String', 'Calibration Information Not Available');
    set(control.edit8, 'String', 'Data Not Available')
    set(control.edit9, 'String', 'Data Not Available')
    set(control.edit14, 'String', 'Acquisition Information Not Available');
    set(control.edit15, 'String', 'Acquisition Information Not Available');
    set(control.edit16, 'String', 'Acquisition Information Not Available');
    set(control.edit17, 'String', 'Acquisition Information Not Available');
    set(control.edit3, 'String', 'Location Not Available')
    set(control.edit4, 'Enable', 'off')
    set(control.edit5, 'Enable', 'off')
    set(control.edit6, 'Enable', 'off')
    set(control.edit7,'String', 'Data Not Available');
end


function changeplot(data, control)

index = get(control.senBand,'Value');

% try
%     syscalval = data(index).syscal;
%     syscalt = syscalval{1}; syscalmfn = syscalval{2}; syscalmg = syscalval{3};
%     axes(control.axCal)
%     yCMin = -10; yMax = 40;
%     hold off;
%     hAC = area([0 syscalt(1)], [yMax yMax], yCMin); %else hAC = area([0 0], [yMax yMax], yCMin); end
%     set(hAC,'FaceColor',[.70 .70 .70],'LineStyle','none');
%     hold on;
%     xlabel('Hour');
%     ylabel('dB');
%     xlim([0 24]);
%     set(control.axCal, 'Layer', 'top', 'XTick', 0:4:24);
%     ylim([yCMin yMax]);
%     grid on;
%     cal(1) = plot(syscalt(1,:),syscalmfn(1,:),'rx');
%     cal(2) = plot(syscalt(1,:),syscalmg(1,:),'k+');
%     hL = legend(cal, 'F_n', 'G');
%     set(hL, 'FontSize', 8);
%     hold off; clear yCMin yMax hAC syscalval syscalt syscalmfn syscalmg
% catch
% 
% end
% 
% try
%     filesystem = data(index).files; dataconval = data(index).datacon; datafile = filesystem{2};
%     
%     datacont = dataconval{1}; dataconwPk = dataconval{2}; dataconfox = dataconval{3};
%     dataconw0r = dataconval{4}; dataconwnPk = dataconval{5}; dataconwT = dataconval{6};
%     dataconlength = length(datacont); dataconol = dataconval{7};
%     
%     axes(control.axFreq)
%     lStr = ['RBW=' num2str(datafile.mPar.RBW/1e6) ' MHz, t_d=' num2str(datafile.mPar.td) ' s, Det=Peak'];
%     x = dataconfox(dataconlength,:); wnPk = dataconwnPk(dataconlength,:);
%     w0r = dataconw0r(dataconlength,:); wI = dataconwPk(:,dataconlength);
%     wT = dataconwT(dataconlength,1);
%     
%     [fAdj, fUnits] = adjFreq(x);
%     idxf0 = findPeaks(wI, wT); % Find band centers
%     hA = area(fAdj, wnPk, W2dBm(mean(dBm2W(w0r))));
%     set(hA,'FaceColor',[.70 .70 .70],'LineStyle','none');
%     hold on;
%     grid on;
%     %title(tStr);
%     xlabel(['f (' fUnits ')']);
%     ylabel('w (dBm)');
%     yMin = 10*floor(min([min(w0r) min(dataconwPk)])/10);
%     yMax = 10;
%     ylim([yMin yMax]);
%     xlim([fAdj(1) fAdj(length(fAdj))]);
%     set(gca,'Layer','top');
%     plot(fAdj, wI);
%     plot([fAdj(1) fAdj(length(fAdj))], wT*[1 1], 'g--')
%     if ~isempty(idxf0)
%         for k = 1:length(idxf0)
%             plot(fAdj(idxf0(k))*[1 1], [yMin yMax], 'r-')
%         end
%         hL = legend('< Peak & > Mean Rx Noise', lStr, 'w_T', 'f_{0,k}');
%     else
%         hL = legend('< Peak & > Mean Rx Noise', lStr, 'w_T');
%     end
%     set(hL,'Visible','on','FontSize',8);
%     if dataconol; str = 'red'; else str = 'black'; end
%     set(control.axFreq, 'XColor', str, 'YColor', str);
%     clear yMin yMax hA hL 
% catch
% 
% end
% 
% try
%     filesystem = data(index).files; sysfile = filesystem{1};
%     axes(control.axContour)
%     yMin = fAdj(1); yMax = fAdj(length(fAdj));
%     V = transpose(floor(wT):10*ceil(sysfile.COTSsensor.pMax/10)); % Color scale vector for contour plot
%     hA = area([0 datacont(1)], [yMax yMax]); %else hA = area([0 0], [yMax yMax]); end
%     set(hA,'FaceColor',[.70 .70 .70],'LineStyle','none');
%     hold on;
%     [~, hC] = contourf(datacont, fAdj, dataconwPk, V);
%     set(hC, 'LineStyle', 'none');
%     colorbar;
%     caxis([min(V) max(V)]);
%     %title(['Measured Signal Powers, ' datestr(tVlocal, 1)])
%     xlabel('Hour');
%     ylabel(['f (' fUnits ')']);
%     xlim([0 24]);
%     ylim([yMin yMax]);
%     set(control.axContour, 'Layer', 'top', 'XTick', 0:4:24);
%     grid on;
%     hold off; clear yMax yMin hA V hC
% catch
% 
% end
% 
% hold all


% --- Executes on selection change in radBand.
function radBand_Callback(hObject, eventdata, handles)
% hObject    handle to radBand (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns radBand contents as cell array
%        contents{get(hObject,'Value')} returns selected item from radBand

value = handles.sensor;
changegui(value, handles); guidata(handles.figure1, handles);



% --- Executes during object creation, after setting all properties.
function radBand_CreateFcn(hObject, eventdata, handles)
% hObject    handle to radBand (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
