function varargout = RadarOccupancy(varargin)
% RADAROCCUPANCY MATLAB code for RadarOccupancy.fig
%      RADAROCCUPANCY, by itself, creates a new RADAROCCUPANCY or raises the existing
%      singleton*.
%
%      H = RADAROCCUPANCY returns the handle to a new RADAROCCUPANCY or the handle to
%      the existing singleton*.
%
%      RADAROCCUPANCY('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in RADAROCCUPANCY.M with the given input arguments.
%
%      RADAROCCUPANCY('Property','Value',...) creates a new RADAROCCUPANCY or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before RadarOccupancy_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to RadarOccupancy_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help RadarOccupancy

% Last Modified by GUIDE v2.5 20-Jul-2014 23:35:10

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @RadarOccupancy_OpeningFcn, ...
                   'gui_OutputFcn',  @RadarOccupancy_OutputFcn, ...
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


% --- Executes just before RadarOccupancy is made visible.
function RadarOccupancy_OpeningFcn(hObject, ~, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to RadarOccupancy (see VARARGIN)

addpath \SpectrumMonitoring\Software\MATLAB\CodeLibrary\CottonUtilities
addpath \SpectrumMonitoring\Software\MATLAB\CodeLibrary\jsonlab
addpath \SpectrumMonitoring\Software\MATLAB\CodeLibrary\TimeZoneConvert
addpath \SpectrumMonitoring\Software\MATLAB\CodeLibrary\RSMS5G\MiscFunctions
addpath \SpectrumMonitoring\Software\MATLAB\CodeLibrary\RSMS5G\Drivers

% Initialize IP addresses
IP.WR = '192.168.1.12';
IP.SA = '192.168.1.13';

% Initialize measurement parameters from init.mat
% load init.mat; % initializes band Sys Loc Out and Comment
[band, Sys, Loc, Out, Comment] = ReadInitFile('init.json');
set(handles.edtFileNum, 'String', ['#### (' int2str(Out.StartFileNum) ')']);
set(handles.edtComment, 'String', Comment);

% Hardware certain fields in the Sys and Loc structures
Sys.Type = 'Sys';
Loc.Type = 'Loc';

% Make it so constant parameters cannot be changed by init file or GUI. These
% parameters/functions will be used when the software supports them.
% Sys.Cal.DataType = 'Binary - float32';
Sys.Cal.ByteOrder = 'Network';
Sys.Cal.Compression = 'None';
Sys.COTSsensor.Model = 'Agilent E4440A';
Loc.Mobility = 'Stationary';
% set(handles.popupDataType, 'Enable', 'off')
set(handles.popupByteOrder, 'Enable', 'off');
set(handles.popupCompress, 'Enable', 'off');
set(handles.popupModelCOTSsensor, 'Enable', 'off');
set(handles.btnStationary, 'Enable', 'off');
set(handles.btnMobile, 'Enable', 'off');


% Set antenna and COTS sensor parameters according to model
Sys.Antenna = SetAntennaStruct(Sys.Antenna.Model, Sys.Antenna.AZ, Sys.Antenna.EL, Sys.Antenna.lCable);
Sys.COTSsensor = SetCOTSsensorStruct(Sys.COTSsensor.Model);

% Populate GUI measurement parameters default values
switch band
case 1
  set(handles.btgRadarBand, 'SelectedObject', handles.btn2800MHz)
case 2
  set(handles.btgRadarBand, 'SelectedObject', handles.btn3600MHz)
end
rPar = RadarParameters(band);
set(handles.edtRadarParameters, 'String', [rPar.Name ': T_A = ' num2str(rPar.TA) ' s/rot, PI = ' num2str(1000*rPar.PI) ' ms, PW = ' num2str(1e6*rPar.PW) ' us'])
set(handles.btnOutputJSON, 'Value', Out.JSON4MSOD);
set(handles.btnOutputDBG, 'Value', Out.MAT4DBG);
set(handles.edtPrefix, 'String', Out.Prefix)
set(handles.edtCalsPerHour, 'String', num2str(Sys.Cal.CalsPerHour))
set(handles.edtVerMSOD, 'String', Sys.Ver)
if strcmpi(Sys.Cal.DataType, 'Binary - float32')
  set(handles.popupDataType, 'Value', 1)
elseif strcmpi(Sys.Cal.DataType, 'Binary - int16')
  set(handles.popupDataType, 'Value', 2)
elseif strcmpi(Sys.Cal.DataType, 'Binary - int8')
  set(handles.popupDataType, 'Value', 3)
elseif strcmpi(Sys.Cal.DataType, 'ASCII')
  set(handles.popupDataType, 'Value', 4)
end
if strcmpi(Sys.Cal.ByteOrder, 'Network')
  set(handles.popupByteOrder, 'Value', 1)
elseif strcmpi(Sys.Cal.ByteOrder, 'Big Endian')
  set(handles.popupByteOrder, 'Value', 2)
elseif strcmpi(Sys.Cal.ByteOrder, 'Little Endian')
  set(handles.popupByteOrder, 'Value', 3)
end
if strcmpi(Sys.Cal.Compression, 'None')
  set(handles.popupCompress, 'Value', 1)
elseif strcmpi(Sys.Cal.Compression, 'Zip')
  set(handles.popupCompression, 'Value', 2)
elseif strcmpi(Sys.Cal.Compression, 'N/A')
  set(handles.popupCompression, 'Value', 3)
end

% Populate GUI measurement location default values 
if strcmpi(Loc.Mobility, 'Stationary')
  set(handles.btgMobility, 'SelectedObject', handles.btnStationary)
elseif strcmpi(Loc.Mobility, 'Mobile')
  set(handles.btgMobility, 'SelectedObject', handles.btnMobile)
end
set(handles.edtLat, 'String', num2str(Loc.Lat))
set(handles.edtLon, 'String', num2str(Loc.Lon))
set(handles.edtAlt, 'String', num2str(Loc.Alt))
if strcmpi(Loc.TimeZone, 'America/New_York')
  set(handles.popupTimeZone, 'Value', 1)
elseif strcmpi(Loc.TimeZone, 'America/Chicago')
  set(handles.popupTimeZone, 'Value', 2)
elseif strcmpi(Loc.TimeZone, 'America/Denver')
  set(handles.popupTimeZone, 'Value', 3)
elseif strcmpi(Loc.TimeZone, 'America/Phoenix')
  set(handles.popupTimeZone, 'Value', 4)
elseif strcmpi(Loc.TimeZone, 'America/Los_Angeles')
  set(handles.popupTimeZone, 'Value', 5)
end

% Populate GUI system hardware default values
set(handles.edtSensorID, 'String', Sys.SensorID)
set(handles.edtSensorKey, 'String', num2str(Sys.SensorKey))
if strcmpi(Sys.Antenna.Model, 'AAC SPBODA-1080/Omni/Slant')
  set(handles.popupAntennaModel, 'Value', 1)
elseif strcmpi(Sys.Antenna.Model, 'Alpha AW3232/Sector/Slant')
  set(handles.popupAntennaModel, 'Value', 2)
elseif strcmpi(Sys.Antenna.Model, 'Cobham OA2-0.3-10.0v/1505/Omni/VPOL')
  set(handles.popupAntennaModel, 'Value', 3)
end
set(handles.edtAntennaAZ, 'String', num2str(Sys.Antenna.AZ))
set(handles.edtAntennaEL, 'String', num2str(Sys.Antenna.EL))
set(handles.edtLossCable, 'String', num2str(Sys.Antenna.lCable))
set(handles.edtfLowPassBPF, 'String', num2str(Sys.Preselector.fLowPassBPF/1e6))
set(handles.edtfHighPassBPF, 'String', num2str(Sys.Preselector.fHighPassBPF/1e6))
set(handles.edtfLowStopBPF, 'String', num2str(Sys.Preselector.fLowStopBPF/1e6))
set(handles.edtfHighStopBPF, 'String', num2str(Sys.Preselector.fHighStopBPF/1e6))
set(handles.edtNoiseFigLNA, 'String', num2str(Sys.Preselector.fnLNA))
set(handles.edtGainLNA, 'String', num2str(Sys.Preselector.gLNA))
set(handles.edtPmaxLNA, 'String', num2str(Sys.Preselector.pMaxLNA))
set(handles.edtENR, 'String', num2str(Sys.Preselector.enrND))
if strcmpi(Sys.COTSsensor.Model, 'Agilent E4440A')
  set(handles.popupModelCOTSsensor, 'Value', 1)
elseif strcmpi(Sys.COTSsensor.Model, 'Agilent Sensor N6841A')
  set(handles.popupModelCOTSsensor, 'Value', 2)
elseif strcmpi(Sys.COTSsensor.Model, 'CRFS RFeye')
  set(handles.popupModelCOTSsensor, 'Value', 3)
elseif strcmpi(Sys.COTSsensor.Model, 'NI USRP N210')
  set(handles.popupModelCOTSsensor, 'Value', 4)
elseif strcmpi(Sys.COTSsensor.Model, 'Signal Hound BB60C')
  set(handles.popupModelCOTSsensor, 'Value', 5)
elseif strcmpi(Sys.COTSsensor.Model, 'ThinkRF WSA5000-108')
  set(handles.popupModelCOTSsensor, 'Value', 6)
end 

% Disable monitor text boxes
set(handles.edtDateTimeStart, 'Enable', 'off')
set(handles.edtFileNum, 'Enable', 'off')
set(handles.edtDateTimeLastCal, 'Enable', 'off')
set(handles.edtGainLastCal, 'Enable', 'off')
set(handles.edtNoiseFigLastCal, 'Enable', 'off')
set(handles.edtSysNoiseLastCal, 'Enable', 'off')
set(handles.edtTempLastCal, 'Enable', 'off')
set(handles.edtfStart, 'Enable', 'off')
set(handles.edtfStop, 'Enable', 'off')
set(handles.edtNfreqs, 'Enable', 'off')
set(handles.edtRBW, 'Enable', 'off')
set(handles.edtDet, 'Enable', 'off')
set(handles.edttd, 'Enable', 'off')
set(handles.edtRadarParameters, 'Enable', 'off')

% Set global application variables
SaveAllGlobalVariables(handles, band, Sys, Loc, Out, Comment, IP);
setappdata(handles.figure1, 'state', 0);

% Choose default command line output for RadarOccupancy
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes RadarOccupancy wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = RadarOccupancy_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --------------------------------------------------------------------
function tlbStart_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to tlbStart (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% disable some buttons for duraiton of measurement

% Clear plots
ClearPlots(handles)

% Adjust state variable/GUI 
setappdata(handles.figure1, 'state', 1)
adjustGUIcontrols(handles)

% Initialize variables
[band, Sys, Loc, Out, ~, IP] = LoadAllGlobalVariables(handles);
FileNum = Out.StartFileNum;
tVlastCal = [0, 0, 0, 0, 0, 0];

% Inititialize Sys.Cal.mPar according to chosen band
Sys.Cal.nM = 2;
Sys.Cal.mType = 'Y-factor: swept-frequency';
Sys.Cal.mPar = MeasParameters(band);
Sys.Cal.mPar.td = 0.1;
Sys.Cal.mPar.Det = 'RMS';

% Match Loc to Sys header info  
Loc.Ver = Sys.Ver;
Loc.SensorID = Sys.SensorID;
Loc.SensorKey = Sys.SensorKey;

% Initalize spectrum analyzer
[SAiObj, SAdObj] = SA_Init(IP.SA, MeasParameters(band));

% Initialize web relay
WRobj = WR_Init(IP.WR, 1024);

% Initialize web relay to occupancy measurement configuration
SetFrontEndInput(WRobj, 0, handles); % input = antenna
SetVDC2NoiseDiode(WRobj, 0, handles) % noise diode = off

% Loop through measurement cycle until user stops
a = 1; % Acquisition index
while getappdata(handles.figure1, 'state') == 1

  % Populate GUI monitor - start date/time and file number 
  set(handles.edtFileNum, 'String', [int2str(FileNum) ' (' int2str(FileNum - a + 1) ')'])
  drawnow

  % Clear variables
  clear Data tV t tVlocal teDay tStr w x OL wI fAdj fUnits idxf0 lStr

  % Initialize Data structures
  Data = InitDataStruct(band, Sys);
  
  % Record time stamp
  tV = clock;
  t = etime(tV, [1970, 1, 1, 0, 0, 0]); % This assumes that the computer clock is Coordinated Universal time
  tVlocal = datevec(TimezoneConvert(datenum(tV), 'UTC', Loc.TimeZone));
  if a == 1
    t1 = t;
    set(handles.edtDateTimeStart, 'String', datestr(datenum(tVlocal), 'mm/dd/yy HH:MM'))
  end

  % Write JSON Loc messages
  if Out.JSON4MSOD && (a==1 || strcmpi(Loc.Mobility, 'Mobile'))
    Loc.t = t;
    savejson('', Loc, [Out.Prefix zzz2str(FileNum,6) 'Loc.json']);
  end
  
  % Generate plotting variables and strings
  teDay = etime(tVlocal, [tVlocal(1), tVlocal(2), tVlocal(3), 0, 0, 0]);
  tStr = ['FileNum=' int2str(FileNum) ', ' datestr(tVlocal)];

  % Calibrate system
  % Perform noise diode calibration at specified interval
  if etime(tVlocal, tVlastCal) > 60*60/Sys.Cal.CalsPerHour

    % Clear cal variables
    clear AlignNeeded wOn wOff fn g w0r Mfn Mg wnPk wT V MwnPkI

    % Acquire temperature reading
    Sys.Cal.Temp = GetPreselectorTemp(WRobj);
    
    % Perform alignment if needed
    [~, AlignNeeded] = invoke(SAdObj, 'iGenGetOvrDrvAndAlignRqst');
    if AlignNeeded; invoke(SAdObj, 'iGenQuickCalNow', 1); end

    % Y-factor procedure
    SetFrontEndInput(WRobj, 1, handles); % input = noise diode
    SetVDC2NoiseDiode(WRobj, 1, handles) % noise diode = on
    [wOn, ~] = SA_FreqSweepMeas(SAdObj, Sys.Cal.mPar, handles);
    SetVDC2NoiseDiode(WRobj, 0, handles) % noise diode = off
    [wOff, ~] = SA_FreqSweepMeas(SAdObj, Sys.Cal.mPar, handles);
    SetFrontEndInput(WRobj, 0, handles); % input = antenna
      
    % Calculate system noise figure and gain
    [fn, g, w0r] = yFactCalcs(wOn, wOff, Sys.Preselector.enrND, Sys.Cal.mPar.RBW);
    Mfn = W2dBW(mean(dBW2W(fn)));
    Mg = W2dBW(mean(dBW2W(g)));
    
    % Calculate system noise parameters at COTS sensor
    wnPk = W2dBm(dBm2W(w0r)*SA_P2A(Data.mPar.td, Data.mPar.RBW)); % Peak-detected receiver noise level (dBm)
    wT = 3+max(wnPk); % Threshold that identifies signal in peak-detected measurement (dBm)
    V = transpose(floor(wT):10*ceil(Sys.COTSsensor.pMax/10)); % Color scale vector for contour plot

    % Calculate detected system noise power [dBm ref to terminal of isotropic antenna]
    MwnPkI = W2dBm(mean(dBm2W(wnPk + Sys.Antenna.lCable - g - Sys.Antenna.g)));
    
    % Write JSON Sys message
    if Out.JSON4MSOD
      Sys.t = t;  % Time stamp cal
      Sys.Cal.Processed = 'True';
      filename = [Out.Prefix zzz2str(FileNum,6) 'SysProc.json'];
      savejson('', Sys, filename);
      WriteDataBlock2File(filename, fn, Sys.Cal.DataType);
      WriteDataBlock2File(filename, g, Sys.Cal.DataType);
      clear filename
      if a == 1
        Sys.Cal.Processed = 'False';
        filename = [Out.Prefix zzz2str(FileNum,6) 'SysRaw.json'];
        savejson('', Sys, filename);
        WriteDataBlock2File(filename, wOn, Sys.Cal.DataType);
        WriteDataBlock2File(filename, wOff, Sys.Cal.DataType);
        clear filename
      end
    end

    % Plot today's cal data
    axes(handles.axsCal);
    if length(find(tVlastCal==0)) == 6 || tVlocal(3) ~= tVlastCal(3)
      yMin = -10; yMax = 40;
      hold off;
      if a==1; hA = area([0 teDay]/3600, [yMax yMax], yMin); else hA = area([0 0], [yMax yMax], yMin); end
      set(hA,'FaceColor',[.70 .70 .70],'LineStyle','none');
      hold on;
      plot(teDay/3600, Mfn, 'rx');
      plot(teDay/3600, Mg, 'k+');
      title(['Calibration Data: ' datestr(tVlocal, 1)]);
      xlabel('Hour');
      ylabel('dB');
      xlim([0 24]);
      ylim([yMin yMax]);
      set(handles.axsCal, 'Layer', 'top', 'XTick', 0:4:24);
      grid on;
      hL = legend('F_n', 'G');
      set(hL, 'FontSize', 8);
      clear yMin yMax hA hL;
    else
      plot(teDay/3600, Mfn, 'rx');
      plot(teDay/3600, Mg, 'k+');
    end
    
    % Populate GUI monitor with cal info 
    set(handles.edtDateTimeLastCal, 'String', datestr(datenum(tVlocal), 'mm/dd/yy HH:MM'));
    set(handles.edtGainLastCal, 'String', num2str(round(10*Mg)/10));
    set(handles.edtNoiseFigLastCal, 'String', num2str(round(10*Mfn)/10));
    set(handles.edtSysNoiseLastCal, 'String', num2str(round(10*MwnPkI)/10));
    set(handles.edtTempLastCal, 'String', num2str(Sys.Cal.Temp));
    drawnow
    
    tVlastCal = tVlocal;
  end
  
    % Measure peaks above threshold over entire band
  [w, x, OL] = SA_FreqSweepMeas(SAdObj, Data.mPar, handles);
  wI = w + Sys.Antenna.lCable - Sys.Antenna.g - g;
  [fAdj fUnits] = adjFreq(x);
  idxf0 = findPeaks(w, wT); % Find band centers

  % Plot frequency domain data
  lStr = ['RBW=' num2str(Data.mPar.RBW/1e6) ' MHz, t_d=' num2str(Data.mPar.td) ' s, Det=Peak'];
  plotPkFreqDomainData(handles.axsFreq, x, w, OL, wT, idxf0, wnPk, w0r, tStr, lStr)
  
  % Plot data in contour
  if a==1 || tVlocal(3)~=DayContour
    clear hr wPk
    aa = 1;
    DayContour = tVlocal(3);
  else
    aa = aa + 1;
  end
  hr(aa) = teDay/3600;
  wPk(:,aa) = w;
  if aa > 1
    yMin = fAdj(1); yMax = fAdj(length(fAdj));
    axes(handles.axsContour);
    if aa==a; hA = area([0 hr(2)], [yMax yMax]); else hA = area([0 0], [yMax yMax]); end
    set(hA,'FaceColor',[.70 .70 .70],'LineStyle','none');
    hold on;
    [~, hC] = contourf(hr, fAdj, wPk, V);
    set(hC, 'LineStyle', 'none');
    colorbar;
    caxis([min(V) max(V)]);
    title(['Measured Signal Powers, ' datestr(tVlocal, 1)])
    xlabel('Hour');
    ylabel(['f (' fUnits ')']);
    xlim([0 24]);
    ylim([yMin yMax]);
    set(handles.axsContour, 'Layer', 'top', 'XTick', 0:4:24);
    grid on;
    clear yMin yMax hA hC
    hold off;
  end
  
  % Write JSON Data message
  Comment = getappdata(handles.figure1, 'Comment');
  if Out.JSON4MSOD
    Data.t = t;  % Time stamp cal
    Data.Processed = 'True';
    Data.t1 = t1;
    Data.a = a;
    Data.OL = OL;
    Data.wnI = MwnPkI;
    Data.Comment = Comment;
    filename = [Out.Prefix zzz2str(FileNum,6) 'DataProc.json'];
    savejson('', Data, filename);
    WriteDataBlock2File(filename, wI, Data.DataType);
    clear filename
    if a == 1
      Data.Processed = 'False';
      filename = [Out.Prefix zzz2str(FileNum,6) 'DataRaw.json'];
      savejson('', Data, filename);
      WriteDataBlock2File(filename, w, Data.DataType);
      clear filename fid
    end
  end
  
  % Write MAT output file
  if Out.MAT4DBG; save([Out.Prefix zzz2str(FileNum,6) 'DBG.mat']); end

  % Update file number, init.mat, and acq counter
  FileNum = FileNum + 1;
  Out.StartFileNum = FileNum;
  SaveAllGlobalVariables(handles, band, Sys, Loc, Out, Comment, IP)
  WriteInitFile('init.json', band, Sys, Loc, Out, Comment);
  a = a + 1;
  
  if getappdata(handles.figure1, 'state') == 0
    adjustGUIcontrols(handles)
    SA_Close(SAiObj, SAdObj);
  end
end


% --- Executes during object creation, after setting all properties.
function pushbuttonCal_CreateFcn(hObject, eventdata, handles)
% hObject    handle to pushbuttonCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called


% --- Executes on button press in pushbuttonCal.
function pushbuttonCal_Callback(hObject, eventdata, handles)
% hObject    handle to pushbuttonCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Adjust state variable/GUI 
setappdata(handles.figure1, 'state', 1)
adjustGUIcontrols(handles);

% Global variables
[band, Sys, Loc, Out, Comment, IP] = LoadAllGlobalVariables(handles);

% Record time stamp
tV = clock;
Sys.t = etime(tV, [1970, 1, 1, 0, 0, 0]); % This assumes that the computer clock is Coordinated Universal time
tVlocal = datevec(TimezoneConvert(datenum(tV), 'UTC', Loc.TimeZone));

% Write starting file number, date, and time to GUI monitor
set(handles.edtFileNum, 'String', [int2str(Out.StartFileNum) ' (' int2str(Out.StartFileNum) ')'])
set(handles.edtDateTimeStart, 'String', datestr(datenum(tVlocal), 'mm/dd/yy HH:MM'));
drawnow

% Initalize spectrum analyzer
[SAiObj, SAdObj] = SA_Init(IP.SA, MeasParameters(band));

% Initialize web relay
WRobj = WR_Init(IP.WR, 1024);

% Inititialize Sys.Cal structure - this defines measurment parameters
Sys.Cal.Temp = GetPreselectorTemp(WRobj);
Sys.Cal.mType = 'Y-factor: swept-frequency';
Sys.Cal.nM = 2;
Sys.Cal.Processed = '';
Sys.Cal.mPar = MeasParameters(band);
Sys.Cal.mPar.td = 0.1;
Sys.Cal.mPar.Det = 'RMS';

% Y-factor procedure
SetFrontEndInput(WRobj, 1, handles); % input = noise diode
SetVDC2NoiseDiode(WRobj, 1, handles) % noise diode = on
[wOn, ~] = SA_FreqSweepMeas(SAdObj, Sys.Cal.mPar, handles);
SetVDC2NoiseDiode(WRobj, 0, handles) % noise diode = off
[wOff, ~] = SA_FreqSweepMeas(SAdObj, Sys.Cal.mPar, handles);
SetFrontEndInput(WRobj, 0, handles); % input = antenna

% Write JSON Sys message
[fn, g, w0r] = yFactCalcs(wOn, wOff, Sys.Preselector.enrND, Sys.Cal.mPar.RBW);
Sys.Cal.Processed = 'True';
filename = [Out.Prefix zzz2str(Out.StartFileNum,6) 'SysProc.json'];
savejson('', Sys, filename);
WriteDataBlock2File(filename, fn, Sys.Cal.DataType);
WriteDataBlock2File(filename, g, Sys.Cal.DataType);
clear filename

Sys.Cal.Processed = 'False';
filename = [Out.Prefix zzz2str(Out.StartFileNum,6) 'SysRaw.json'];
savejson('', Sys, filename);
WriteDataBlock2File(filename, wOn, Sys.Cal.DataType);
WriteDataBlock2File(filename, wOff, Sys.Cal.DataType);
clear filename

% Populate GUI monitor
Mfn = W2dBW(mean(dBW2W(fn)));
Mg = W2dBW(mean(dBW2W(g)));
set(handles.edtDateTimeLastCal, 'String', datestr(datenum(tVlocal), 'mm/dd/yy HH:MM'));
set(handles.edtGainLastCal, 'String', num2str(round(10*Mg)/10));
set(handles.edtNoiseFigLastCal, 'String', num2str(round(10*Mfn)/10));
set(handles.edtTempLastCal, 'String', num2str(Sys.Cal.Temp));
drawnow

% Increment Out.StartFileNum in global variables and init file
Out.StartFileNum = Out.StartFileNum + 1;
setappdata(handles.figure1, 'Out', Out);
WriteInitFile('init.json', band, Sys, Loc, Out, Comment);

% Disconnect SA and reset GUI
SA_Close(SAiObj, SAdObj);
setappdata(handles.figure1, 'state', 0);
adjustGUIcontrols(handles);


function [b, S, L, O, C, IP] = LoadAllGlobalVariables(h)
b = getappdata(h.figure1, 'band');
S = getappdata(h.figure1, 'Sys');
L = getappdata(h.figure1, 'Loc');
O = getappdata(h.figure1, 'Out');
C = getappdata(h.figure1, 'Comment');
IP = getappdata(h.figure1, 'IP');


function SaveAllGlobalVariables(h, b, S, L, O, C, IP)
setappdata(h.figure1, 'band', b);
setappdata(h.figure1, 'Sys', S);
setappdata(h.figure1, 'Loc', L);
setappdata(h.figure1, 'Out', O);
setappdata(h.figure1, 'Comment', C);
setappdata(h.figure1, 'IP', IP);


function rPar = RadarParameters(b)
switch b
case 1
  rPar.Name = 'Radar - ASR';
  rPar.TA = 4;
  rPar.PI = .001;
  rPar.PW = .000001;
case 2
  rPar.Name = 'Radar - SPN43';
  rPar.TA = 4;
  rPar.PI = .001;
  rPar.PW = .000001;
end


function mPar = MeasParameters(b)
% Defines the measurement parameters to measure a specific radar band.
% These parameters cannot be edited via the GUI.
rPar = RadarParameters(b);
switch b
case 1
  mPar.RBW = 1e6;
  mPar.fStart = 2.7e9 + mPar.RBW/2;
  mPar.fStop = 2.9e9 - mPar.RBW/2;
  mPar.n = floor(abs(mPar.fStop - mPar.fStart)/mPar.RBW) + 1;
  mPar.td = 1.25*rPar.TA;
  mPar.Det = 'Positive';
  mPar.Atten = 4;
  mPar.VBW = 50e6; % Maximum VBW for all measurements (hertz)
case 2
  mPar.RBW = 1e6;
  mPar.fStart = 3.45e9 + mPar.RBW/2;
  mPar.fStop = 3.65e9 - mPar.RBW/2;
  mPar.n = floor(abs(mPar.fStop - mPar.fStart)/mPar.RBW) + 1;
  mPar.td = 1.25*rPar.TA;
  mPar.Det = 'Positive';
  mPar.Atten = 4;
  mPar.VBW = 50e6; % Maximum VBW for all measurements (hertz)
end


function x = InitDataStruct(band, Sys)
rPar = RadarParameters(band);
x.Ver = Sys.Ver;
x.Type = 'Data';
x.SensorID = Sys.SensorID;
x.SensorKey = Sys.SensorKey;
x.t = -1;
x.Sys2Detect = rPar.Name;
x.Sensitivity = 'Medium';
x.mType = 'Swept-frequency';
x.t1 = -1;
x.a = -1;
x.nM = 1;
x.Ta = 0;
x.OL = -1;
x.wnI = -1;
x.Comment = '';
x.Processed = '';
x.DataType = Sys.Cal.DataType;
x.ByteOrder = Sys.Cal.ByteOrder;
x.Compression = Sys.Cal.Compression;
x.mPar = MeasParameters(band);


function y = SetAntennaStruct(Model, AZ, EL, lCable)
y.Model = Model;
if strcmpi(Model, 'AAC SPBODA-1080/Omni/Slant')
  y.fLow = 1e9;
  y.fHigh = 8e9;
  y.g = 0;
  y.bwH = 360;
  y.bwV = -1;
  y.AZ = AZ;
  y.EL = EL;
  y.Pol = 'Slant';
  y.XSD = -1;
  y.VSWR = 2.5;
elseif strcmpi(Model, 'Alpha AW3232/Sector/Slant')
  y.fLow = 3.3e9;
  y.fHigh = 3.8e9;
  y.g = 15;
  y.bwH = 120;
  y.bwV = 7;
  y.AZ = AZ;
  y.EL = EL;
  y.Pol = 'Slant';
  y.XSD = 13;
  y.VSWR = -1;
elseif strcmpi(Model, 'Cobham OA2-0.3-10.0v/1505/Omni/VPOL')
  y.fLow = 0.3e9;
  y.fHigh = 10e9;
  y.g = 1.5;
  y.bwH = 360;
  y.bwV = 93.2;
  y.AZ = AZ;
  y.EL = EL;
  y.Pol = 'Vertical';
  y.XSD = 19.9;
  y.VSWR = -1;
end
y.lCable = lCable;


function y = SetCOTSsensorStruct(Model)
y.Model = Model;
if strcmpi(Model, 'Agilent E4440A')
  y.fLow = 3;
  y.fHigh = 26.5e9;
  y.fn = 22;
  y.pMax = 0;
elseif strcmpi(Model, 'Agilent Sensor N6841A')
  y.fLow = 20e6;
  y.fHigh = 6e9;
  y.fn = -1;
  y.pMax = -1;
elseif strcmpi(Model, 'CRFS RFeye')
  y.fLow = 10e6;
  y.fHigh = 6e9;
  y.fn = 8;
  y.pMax = 10;
elseif strcmpi(Model, 'NI USRP N210')
  y.fLow = 400e6;
  y.fHigh = 4.4e9;
  y.fn = -1;
  y.pMax = -1;
elseif strcmpi(Model, 'Signal Hound BB60C')
  y.fLow = 9e3;
  y.fHigh = 6e9;
  y.fn = -1;
  y.pMax = -1;
elseif strcmpi(Model, 'ThinkRF WSA5000-108')
  y.fLow = 100e6;
  y.fHigh = 20e9;
  y.fn = 15;
  y.pMax = 10;
end 


function WriteDataBlock2File(filename, x, DataType)
if strcmpi(DataType, 'ASCII')
  fid = fopen(filename, 'a');
  fprintf(fid, '%s\r\n', savejson('', transpose(x)));
else
  fid = fopen(filename, 'a', 'ieee-be');
  fwrite(fid, transpose(x), Precision(DataType));
end
fclose(fid);


function p = Precision(DataType)
if strcmpi(DataType, 'Binary - float32')
  p = 'float32';
elseif strcmpi(DataType, 'Binary - int16')
  p = 'int16';
elseif strcmpi(DataType, 'Binary - int8')
  p = 'int8';
end


function obj = WR_Init(IP, BufferSize)
% Inititialize web relay
% Connect to web relay
obj = tcpip(IP, 80);
obj.Terminator = 'CR/LF';
obj.TransferDelay = 'off';
obj.InputBufferSize = BufferSize;


function SetFrontEndInput(obj, s, h)
% Set front-end input
% s: 0=antenna, 1=noise diode
WR_SetRelayState(obj, 2, s);
if nargin > 2
  if s == 0; str = 'green'; elseif s == 1; str = 'red'; end
  set(h.txtFrontEndInput, 'BackgroundColor', str);
  drawnow
end


function SetVDC2NoiseDiode(obj, s, h)
% Turn on/off noise diode - apply DC voltage to noise diode
% s: 0=off/0VDC, 1=on/28VDC
WR_SetRelayState(obj, 1, s);
if nargin > 2
  if s == 1; str = 'red'; elseif s == 0; str = 'green'; end
  set(h.txtNDon_off, 'BackgroundColor', str);
  drawnow
end


function WR_SetRelayState(obj, r, s)
fopen(obj);
fprintf(obj, '%s\n\n', ['GET /state.xml?relay' num2str(r) 'State=' num2str(s) ' HTTP/1.1']);
fclose(obj);


function s = WR_GetRelayState(obj, r)
fopen(obj);
fprintf(obj, '%s\n\n', 'GET /state.xml HTTP/1.1');
tic
while obj.BytesAvailable == 0
  t = toc;
  if t>5; break; end
end
if obj.BytesAvailable ~= 0
  reply = transpose(char(fread(obj, obj.BytesAvailable)));
  jj = findstr(reply, ['relay' num2str(r) 'state']);
  s = str2double(reply(jj(2)-3));
else
  s = NaN;
end
fclose(obj);


function T = GetPreselectorTemp(obj)
u = WR_GetTempUnits(obj);
if ~isempty(u)
  TT = WR_GetTemp(obj, 1);
  if ~isnan(TT)
    if strcmpi(u, 'F')
      T = TT;
    elseif strcmpi(u, 'C')
      T = 9*TT/5 + 32;
    elseif strcmpi(u, 'K')
      T = 9*(TT - 273)/5 + 32;
    end
  else
    T = -999;
  end
else
  T = -999;
end


function T = WR_GetTemp(obj, SensorNum)
% Turn on/off noise diode - apply DC voltage to noise diode
% arg: 0=off/0VDC, 1=on/28VDC
fopen(obj);
fprintf(obj, '%s\n\n', 'GET /state.xml HTTP/1.1');
tic
while obj.BytesAvailable == 0
  t = toc;
  if t>5; break; end
end
if obj.BytesAvailable ~= 0
  reply = transpose(char(fread(obj, obj.BytesAvailable)));
  jj = findstr(reply, ['sensor' num2str(SensorNum) 'temp']);
  idx1 = jj(1) + findstr(reply(jj(1):jj(2)), '>');
  idx2 = jj(1) + findstr(reply(jj(1):jj(2)), '<') - 2;
  T = str2double(reply(idx1:idx2));
else
  T = NaN;
end
fclose(obj);


function u = WR_GetTempUnits(obj)
fopen(obj);
fprintf(obj, '%s\n\n', 'GET /state.xml HTTP/1.1');
tic
while obj.BytesAvailable == 0
  t = toc;
  if t>5; break; end
end
if obj.BytesAvailable ~= 0
  reply = transpose(char(fread(obj, obj.BytesAvailable)));
  jj = findstr(reply, 'units');
  if length(jj)==2; u = reply(jj(2)-3); else u = ''; end 
else
  u = '';
end
fclose(obj);


function [iObj, dObj] = SA_Init(IP, mPar)
% Connect to spectrum analyzer
[iObj, dObj] = ConnectToInstrument('E4440SA', 'Visa', IP, 'NI');
% Inititialize spectrum analzer
invoke(dObj, 'iGenPreset');
set(dObj, 'iGenAutoCal', 'Off');
invoke(dObj, 'iGenSetOvrDrvAndAlignRqst');
invoke(dObj, 'iGenAutoCouple', 1, false, 1, 1);
set(dObj, 'iGenAtten', mPar.Atten);
set(dObj, 'iGenRefLevel', 0);
% if Sys.COTSsensor.yUnits==2; set(handles.SAdObj, 'iGenYUnits', 'W'); end
set(dObj, 'iGenSweepMode', 'Single');
% Perform alignment in specified frequency range
set(dObj, 'iGenStartFreq', mPar.fStart);
set(dObj, 'iGenStopFreq', mPar.fStop);
invoke(dObj, 'iGenCalNow', 1);


function SA_Close(SAiObj, SAdObj)
% Disconnect spectrum analyzer
disconnect(SAdObj);
delete(SAdObj);
delete(SAiObj)


function [w, f, OL] = SA_FreqSweepMeas(dObj, mPar, h)
% Input variable:
% mPar is a data structure w the following measurement parameters
%   fStart = start frequency (Hz)
%   fStop = stop frequency (Hz)
%   RBW = resolution bandwidth (Hz)
%   VBW = video bandwidth (Hz)
%   td = time per frequency bin (seconds)
%   Det = detector
StepSize = mPar.RBW;
nSteps = floor(abs(mPar.fStop - mPar.fStart)/StepSize) + 1;
f = mPar.fStart + transpose(0:(nSteps-1))*StepSize;
if nargin > 2
  % Update GUI 
  set(h.edtfStart, 'String', num2str(mPar.fStart/1e6));
  set(h.edtfStop, 'String', num2str(mPar.fStop/1e6));
  set(h.edtNfreqs, 'String', num2str(nSteps));
  set(h.edtRBW, 'String', num2str(mPar.RBW/1e6));
  set(h.edtDet, 'String', mPar.Det);
  set(h.edttd, 'String', num2str(mPar.td));
  drawnow
end
set(dObj, 'iGenStartFreq', mPar.fStart);
set(dObj, 'iGenStopFreq', mPar.fStop);
set(dObj, 'iGenSweepPoints', nSteps);
set(dObj, 'iGenRBW', mPar.RBW);
set(dObj, 'iGenVBW', mPar.VBW);
set(dObj, 'iGenDetector', mPar.Det);
set(dObj, 'iGenSweepTime', nSteps*mPar.td);
w = invoke(dObj, 'iGenTraceData', 1, 1, 0);
OL = invoke(dObj, 'iGenGetOvrDrvAndAlignRqst');


function [fn_dB, g_dB, w0r_dBm] = yFactCalcs(wNDon, wNDoff, enrND, RBW)
% Calculates noise figure (linear units), gain (linear units), and mean power (Watts)
% for a y-factor calibration measurement.
% input variables:
% wNDon = Measured power (dBm) w noise diode on
% wNDoff = Measured power (dBm) w noise diode off
% enrND = excess noise ratio (dB) of noise diode
% RBW = resolution bandwidth (Hz)
wOn = dBW2W(wNDon-30);
wOff = dBW2W(wNDoff-30);
enr = dBW2W(enrND);
y = wOn./wOff;
fn = enr./(y - 1); % noise figure
% 1.128 is factor for converting from RBW to noise equiv bandwidth
g = wOn./(1.38e-23*(25 + 273.15)*1.128*RBW*(enr + fn)); 
% Mean power of receiver noise (Watts)
w0r = 1.38e-23*(25 + 273.15)*1.128*RBW*fn.*g;
fn_dB = W2dBW(fn);
g_dB = W2dBW(g);
w0r_dBm = W2dBm(w0r);


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


function plotPkFreqDomainData(h, f, w, OL, wT, idxf0, wnPk, w0r, tStr, lStr)
% Input variables:
% h = handle to the axes
% f = frequency (Hz)
% w = Detected power (dBm)
% OL = Overload flag {0, 1}
% wT = threshold (dBm)
% idxf0 = indices at peaks of observed signals
% wnPk = peak of system noise (dBm)
% w0r = mean power of system noise (dBm)
% tStr = title string
% lStr = legend string
axes(h);
[fAdj fUnits] = adjFreq(f);
hA = area(fAdj, wnPk, W2dBm(mean(dBm2W(w0r))));
set(hA,'FaceColor',[.70 .70 .70],'LineStyle','none');
hold on;
grid on;
title(tStr);
xlabel(['f (' fUnits ')']);
ylabel('w (dBm)');
yMin = 10*floor(min([min(w0r) min(w)])/10);
yMax = 10;
ylim([yMin yMax]);
set(gca,'Layer','top');
plot(fAdj, w);
plot([fAdj(1) fAdj(length(fAdj))], wT*[1 1], 'g--')
if ~isempty(idxf0)
  for k = 1:length(idxf0)
    plot(fAdj(idxf0(k))*[1 1], [yMin yMax], 'r-')
  end
  hL = legend('< Peak & > Mean Rx Noise', lStr, 'w_T', 'f_{0,k}');
else
  hL = legend('< Peak & > Mean Rx Noise', lStr, 'w_T');
end
set(hL,'Visible','on','FontSize',8);
if OL; str = 'red'; else str = 'black'; end
set(h, 'XColor', str, 'YColor', str);
hold off;


function ClearPlots(h)
axes(h.axsCal);
hold off;
plot([], [])
axes(h.axsFreq);
hold off;
plot([], [])
axes(h.axsContour);
hold off
plot([], [])


% --- Sets enable on or off for GUI fields that allow user to control measurement parameters
function adjustGUIcontrols(handles)
if getappdata(handles.figure1, 'state') == 0
  str = 'on';
  set(handles.tlbStop, 'Enable', 'off');
  set(handles.txtStatus,'BackgroundColor','red');
  set(handles.txtStatus,'String','Measurement idle');
else
  str = 'off';
  set(handles.tlbStop, 'Enable', 'on');
  set(handles.txtStatus,'BackgroundColor','green');
  set(handles.txtStatus,'String','Measurement in progress');
end
set(handles.tlbStart, 'Enable', str);
set(handles.btn2800MHz, 'Enable', str);
set(handles.btn3600MHz, 'Enable', str);
set(handles.edtCalsPerHour, 'Enable', str);
set(handles.btnOutputJSON, 'Enable', str);
set(handles.btnOutputDBG, 'Enable', str);
set(handles.edtVerMSOD, 'Enable', str);
set(handles.edtPrefix, 'Enable', str);
set(handles.popupDataType, 'Enable', str);
% set(handles.popupByteOrder, 'Enable', str);
% set(handles.popupCompress, 'Enable', str);
% set(handles.btnStationary, 'Enable', str);
% set(handles.btnMobile, 'Enable', str);
set(handles.edtLat, 'Enable', str);
set(handles.edtLon, 'Enable', str);
set(handles.edtAlt, 'Enable', str);
set(handles.popupTimeZone, 'Enable', str);
set(handles.edtSensorID, 'Enable', str);
set(handles.edtSensorKey, 'Enable', str);
% set(handles.edtGainAntenna, 'Enable', str);
set(handles.popupAntennaModel, 'Enable', str);
set(handles.edtAntennaAZ, 'Enable', str);
set(handles.edtAntennaEL, 'Enable', str);
set(handles.edtLossCable, 'Enable', str);
set(handles.edtENR, 'Enable', str);
set(handles.edtfLowPassBPF, 'Enable', str);
set(handles.edtfHighPassBPF, 'Enable', str);
set(handles.edtfLowStopBPF, 'Enable', str);
set(handles.edtfHighStopBPF, 'Enable', str);
set(handles.edtGainLNA, 'Enable', str);
set(handles.edtNoiseFigLNA, 'Enable', str);
set(handles.edtPmaxLNA, 'Enable', str);
% set(handles.popupModelCOTSsensor, 'Enable', str);
% set(handles.edtfMinCOTSsensor, 'Enable', str);
% set(handles.edtfMaxCOTSsensor, 'Enable', str);
% set(handles.edtNoiseFigCOTSsensor, 'Enable', str);
% set(handles.edtPmaxCOTSsensor, 'Enable', str);
drawnow


% --------------------------------------------------------------------
function tlbStop_ClickedCallback(hObject, eventdata, handles)
% hObject    handle to tlbStop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

setappdata(handles.figure1, 'state', 0);
set(handles.tlbStart, 'Enable', 'off');
set(handles.tlbStop, 'Enable', 'off');
set(handles.txtStatus,'BackgroundColor','yellow');
set(handles.txtStatus,'String','System will shutdown after current measurement cycle');
drawnow


% --- Executes when selected object is changed in btgRadarBand.
function btgRadarBand_SelectionChangeFcn(hObject, eventdata, handles)
% hObject    handle to the selected object in btgRadarBand 
% eventdata  structure with the following fields (see UIBUTTONGROUP)
%	EventName: string 'SelectionChanged' (read only)
%	OldValue: handle of the previously selected object or empty if none was selected
%	NewValue: handle of the currently selected object
% handles    structure with handles and user data (see GUIDATA)
switch get(eventdata.NewValue,'Tag')
  case 'btn2800MHz'
    band = 1;
  case 'btn3600MHz'
    band = 2;
end
setappdata(handles.figure1, 'band', band);
rPar = RadarParameters(band);
set(handles.edtRadarParameters,'String',[rPar.Name ': T_A = ' num2str(rPar.TA) ' s/rot, PI = ' num2str(1000*rPar.PI) ' ms, PW = ' num2str(1e6*rPar.PW) ' us']);
mPar = MeasParameters(band);
set(handles.edtfStart,'String',num2str(mPar.fStart/1e6));
set(handles.edtfStop,'String',num2str(mPar.fStop/1e6));
set(handles.edtNfreqs,'String',num2str(mPar.n));
set(handles.edtRBW,'String',num2str(mPar.RBW/1e6));
set(handles.edtDet,'String',mPar.Det);
set(handles.edttd,'String',num2str(mPar.td));
drawnow


% --- Executes on button press in btn2800MHz.
function btn2800MHz_Callback(hObject, eventdata, handles)
% hObject    handle to btn2800MHz (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of btn2800MHz


% --- Executes on button press in btn3600MHz.
function btn3600MHz_Callback(hObject, eventdata, handles)
% hObject    handle to btn3600MHz (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of btn3600MHz


function edtCalsPerHour_Callback(hObject, eventdata, handles)
% hObject    handle to edtCalsPerHour (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtCalsPerHour as text
%        str2double(get(hObject,'String')) returns contents of edtCalsPerHour as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Cal.CalsPerHour = str2double(get(hObject,'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtCalsPerHour_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtCalsPerHour (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in btnOutputJSON.
function btnOutputJSON_Callback(hObject, eventdata, handles)
% hObject    handle to btnOutputJSON (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of btnOutputJSON
Out = getappdata(handles.figure1, 'Out');
Out.JSON4MSOD = get(hObject,'Value');
setappdata(handles.figure1, 'Out', Out);

% --- Executes on button press in btnOutputDBG.
function btnOutputDBG_Callback(hObject, eventdata, handles)
% hObject    handle to btnOutputDBG (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of btnOutputDBG
Out = getappdata(handles.figure1, 'Out');
Out.MAT4DBG = get(hObject,'Value');
setappdata(handles.figure1, 'Out', Out);


function edtVerMSOD_Callback(hObject, eventdata, handles)
% hObject    handle to edtVerMSOD (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtVerMSOD as text
%        str2double(get(hObject,'String')) returns contents of edtVerMSOD as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Ver = get(hObject,'String');
setappdata(handles.figure1, 'Sys', Sys);

% --- Executes during object creation, after setting all properties.
function edtVerMSOD_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtVerMSOD (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtPrefix_Callback(hObject, eventdata, handles)
% hObject    handle to edtPrefix (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtPrefix as text
%        str2double(get(hObject,'String')) returns contents of edtPrefix as a double
Out = getappdata(handles.figure1, 'Out');
Out.Prefix = get(hObject,'String');
setappdata(handles.figure1, 'Out', Out);


% --- Executes during object creation, after setting all properties.
function edtPrefix_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtPrefix (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupDataType.
function popupDataType_Callback(hObject, eventdata, handles)
% hObject    handle to popupDataType (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupDataType contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupDataType
Sys = getappdata(handles.figure1, 'Sys');
contents = cellstr(get(hObject, 'String'));
Sys.Cal.DataType = contents{get(hObject, 'Value')};
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function popupDataType_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupDataType (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupByteOrder.
function popupByteOrder_Callback(hObject, eventdata, handles)
% hObject    handle to popupByteOrder (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupByteOrder contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupByteOrder
Sys = getappdata(handles.figure1, 'Out');
contents = cellstr(get(hObject, 'String'));
Sys.Cal.ByteOrder = contents{get(hObject, 'Value')};
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function popupByteOrder_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupByteOrder (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupCompress.
function popupCompress_Callback(hObject, eventdata, handles)
% hObject    handle to popupCompress (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupCompress contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupCompress
Sys = getappdata(handles.figure1, 'Out');
contents = cellstr(get(hObject, 'String'));
Sys.Cal.Compression = contents{get(hObject, 'Value')};
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function popupCompress_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupCompress (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes when selected object is changed in btgMobility.
function btgMobility_SelectionChangeFcn(hObject, eventdata, handles)
% hObject    handle to the selected object in btgMobility 
% eventdata  structure with the following fields (see UIBUTTONGROUP)
%	EventName: string 'SelectionChanged' (read only)
%	OldValue: handle of the previously selected object or empty if none was selected
%	NewValue: handle of the currently selected object
% handles    structure with handles and user data (see GUIDATA)
Loc = getappdata(handles.figure1, 'Loc');
switch get(eventdata.NewValue,'Tag')
  case 'btnStationary'
    Loc.Mobility = 'Stationary';
  case 'btnMobile'
    Loc.Mobility = 'Mobile';
end
setappdata(handles.figure1, 'Loc', Loc);

function edtLat_Callback(hObject, eventdata, handles)
% hObject    handle to edtLat (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtLat as text
%        str2double(get(hObject,'String')) returns contents of edtLat as a double
Loc = getappdata(handles.figure1, 'Loc');
Loc.Lat = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Loc', Loc);


% --- Executes during object creation, after setting all properties.
function edtLat_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtLat (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtLon_Callback(hObject, eventdata, handles)
% hObject    handle to edtLon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtLon as text
%        str2double(get(hObject,'String')) returns contents of edtLon as a double
Loc = getappdata(handles.figure1, 'Loc');
Loc.Lon = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Loc', Loc);


% --- Executes during object creation, after setting all properties.
function edtLon_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtLon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtAlt_Callback(hObject, eventdata, handles)
% hObject    handle to edtAlt (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtAlt as text
%        str2double(get(hObject,'String')) returns contents of edtAlt as a double
Loc = getappdata(handles.figure1, 'Loc');
Loc.Alt = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Loc', Loc);


% --- Executes during object creation, after setting all properties.
function edtAlt_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtAlt (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupTimeZone.
function popupTimeZone_Callback(hObject, eventdata, handles)
% hObject    handle to popupTimeZone (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupTimeZone contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupTimeZone
Loc = getappdata(handles.figure1, 'Loc');
contents = cellstr(get(hObject, 'String'));
Loc.TimeZone = contents{get(hObject, 'Value')};
setappdata(handles.figure1, 'Loc', Loc);


% --- Executes during object creation, after setting all properties.
function popupTimeZone_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupTimeZone (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtSensorID_Callback(hObject, eventdata, handles)
% hObject    handle to edtSensorID (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtSensorID as text
%        str2double(get(hObject,'String')) returns contents of edtSensorID as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.SensorID = get(hObject, 'String');
setappdata(handles.figure1, 'Sys', Sys);

% --- Executes during object creation, after setting all properties.
function edtSensorID_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtSensorID (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtSensorKey_Callback(hObject, eventdata, handles)
% hObject    handle to edtSensorKey (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtSensorKey as text
%        str2double(get(hObject,'String')) returns contents of edtSensorKey as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.SensorKey = get(hObject, 'String');
setappdata(handles.figure1, 'Sys', Sys);

% --- Executes during object creation, after setting all properties.
function edtSensorKey_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtSensorKey (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupAntennaModel.
function popupAntennaModel_Callback(hObject, eventdata, handles)
% hObject    handle to popupAntennaModel (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupAntennaModel contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupAntennaModel
Sys = getappdata(handles.figure1, 'Sys');
contents = cellstr(get(hObject, 'String'));
Sys.Antenna.Model = contents{get(hObject, 'Value')};
Sys.Antenna = SetAntennaStruct(Sys.Antenna.Model, Sys.Antenna.AZ, Sys.Antenna.EL, Sys.Antenna.lCable);
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function popupAntennaModel_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupAntennaModel (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtAntennaAZ_Callback(hObject, eventdata, handles)
% hObject    handle to edtAntennaAZ (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtAntennaAZ as text
%        str2double(get(hObject,'String')) returns contents of edtAntennaAZ as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Antenna.AZ = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtAntennaAZ_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtAntennaAZ (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtAntennaEL_Callback(hObject, eventdata, handles)
% hObject    handle to edtAntennaEL (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtAntennaEL as text
%        str2double(get(hObject,'String')) returns contents of edtAntennaEL as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Antenna.EL = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtAntennaEL_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtAntennaEL (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtLossCable_Callback(hObject, eventdata, handles)
% hObject    handle to edtLossCable (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtLossCable as text
%        str2double(get(hObject,'String')) returns contents of edtLossCable as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Antenna.lCable = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtLossCable_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtLossCable (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtENR_Callback(hObject, eventdata, handles)
% hObject    handle to edtENR (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtENR as text
%        str2double(get(hObject,'String')) returns contents of edtENR as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.enrND = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtENR_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtENR (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtfLowPassBPF_Callback(hObject, eventdata, handles)
% hObject    handle to edtfLowPassBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtfLowPassBPF as text
%        str2double(get(hObject,'String')) returns contents of edtfLowPassBPF as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.fLowPassBPF = 1e6*str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtfLowPassBPF_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtfLowPassBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtfHighPassBPF_Callback(hObject, eventdata, handles)
% hObject    handle to edtfHighPassBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtfHighPassBPF as text
%        str2double(get(hObject,'String')) returns contents of edtfHighPassBPF as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.fHighPassBPF = 1e6*str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtfHighPassBPF_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtfHighPassBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtfLowStopBPF_Callback(hObject, eventdata, handles)
% hObject    handle to edtfLowStopBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtfLowStopBPF as text
%        str2double(get(hObject,'String')) returns contents of edtfLowStopBPF as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.fLowStopBPF = 1e6*str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtfLowStopBPF_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtfLowStopBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtfHighStopBPF_Callback(hObject, eventdata, handles)
% hObject    handle to edtfHighStopBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtfHighStopBPF as text
%        str2double(get(hObject,'String')) returns contents of edtfHighStopBPF as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.fHighStopBPF = 1e6*str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtfHighStopBPF_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtfHighStopBPF (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtGainLNA_Callback(hObject, eventdata, handles)
% hObject    handle to edtGainLNA (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtGainLNA as text
%        str2double(get(hObject,'String')) returns contents of edtGainLNA as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.gLNA = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtGainLNA_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtGainLNA (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtNoiseFigLNA_Callback(hObject, eventdata, handles)
% hObject    handle to edtNoiseFigLNA (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtNoiseFigLNA as text
%        str2double(get(hObject,'String')) returns contents of edtNoiseFigLNA as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.fnLNA = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtNoiseFigLNA_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtNoiseFigLNA (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtPmaxLNA_Callback(hObject, eventdata, handles)
% hObject    handle to edtPmaxLNA (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtPmaxLNA as text
%        str2double(get(hObject,'String')) returns contents of edtPmaxLNA as a double
Sys = getappdata(handles.figure1, 'Sys');
Sys.Preselector.pMaxLNA = str2double(get(hObject, 'String'));
setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function edtPmaxLNA_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtPmaxLNA (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in popupModelCOTSsensor.
% function popupModelCOTSsensor_Callback(hObject, eventdata, handles)
% hObject    handle to popupModelCOTSsensor (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns popupModelCOTSsensor contents as cell array
%        contents{get(hObject,'Value')} returns selected item from popupModelCOTSsensor
% Sys = getappdata(handles.figure1, 'Sys');
% contents = cellstr(get(hObject, 'String'));
% Sys.COTSsensor.Model = contents{get(hObject, 'Value')};
% Sys.COTSsensor = SetCOTSsensorStruct(Sys.COTSsensor.Model);
% setappdata(handles.figure1, 'Sys', Sys);


% --- Executes during object creation, after setting all properties.
function popupModelCOTSsensor_CreateFcn(hObject, eventdata, handles)
% hObject    handle to popupModelCOTSsensor (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edtComment_Callback(hObject, eventdata, handles)
% hObject    handle to edtComment (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edtComment as text
%        str2double(get(hObject,'String')) returns contents of edtComment as a double
setappdata(handles.figure1, 'Comment', get(handles.edtComment, 'String'));


% --- Executes during object creation, after setting all properties.
function edtComment_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtComment (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtRadarParameters_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtRadarParameters (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtDateTimeStart_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtDateTimeStart (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtFileNum_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtFileNum (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtDateTimeLastCal_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtDateTimeLastCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtGainLastCal_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtGainLastCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtNoiseFigLastCal_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtNoiseFigLastCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtfStart_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtfStart (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtfStop_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtfStop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtNfreqs_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtNfreqs (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtRBW_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtRBW (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtDet_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtDet (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edttd_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edttd (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtSysNoiseLastCal_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtSysNoiseLastCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function edtTempLastCal_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edtTempLastCal (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function txtFrontEndInput_CreateFcn(hObject, eventdata, handles)
% hObject    handle to txtFrontEndInput (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called


% --- Executes during object creation, after setting all properties.
function txtNDon_off_CreateFcn(hObject, eventdata, handles)
% hObject    handle to txtNDon_off (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called
