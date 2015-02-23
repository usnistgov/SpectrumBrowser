function NewInit()

addpath \SpectrumMonitoring\Software\MATLAB\CodeLibrary\jsonlab

filename = 'init.json';

Ver = '1.0.11';
SensorID = 'Norfolk';
SensorKey = 123456789;
t = -1;

band = 2;

Comment = 'Dry run before shipping equipment to Norfolk.';

Out.JSON4MSOD = 1;
Out.MAT4DBG = 0;
Out.StartFileNum = 225;
Out.Prefix = 'DN0714_';

Sys.Ver = Ver;
Sys.Type = 'Sys';
Sys.SensorID = SensorID;
Sys.SensorKey = SensorKey;
Sys.t = t;
Sys.Antenna.Model = 'Alpha AW3232/Sector/Slant';
Sys.Antenna.fLow = 3.3e9;
Sys.Antenna.fHigh = 3.8e9;
Sys.Antenna.g = 2;
Sys.Antenna.bwH = 120;
Sys.Antenna.bwH = 7;
Sys.Antenna.AZ = 0;
Sys.Antenna.EL = 0;
Sys.Antenna.Pol = 'Slant';
Sys.Antenna.XSD = 13;
Sys.Antenna.VSWR = -1;
Sys.Antenna.lCable = 5.4;
Sys.Preselector.fLowPassBPF = 3.45e9;
Sys.Preselector.fHighPassBPF = 3.65e9;
Sys.Preselector.fLowStopBPF = 3.44e9;
Sys.Preselector.fHighStopBPF = 3.66e9;
Sys.Preselector.fnLNA = 4;
Sys.Preselector.gLNA = 32;
Sys.Preselector.pMaxLNA = 20;
Sys.Preselector.enrND = 14.34;
Sys.COTSsensor.Model = 'Agilent E4440A';
Sys.COTSsensor.fLow = 3;
Sys.COTSsensor.fHigh = 26.5e9;
Sys.COTSsensor.fn = 22;
Sys.COTSsensor.pMax = 0;
Sys.Cal.CalsPerHour = 1;
Sys.Cal.Temp = -999;
Sys.Cal.mType = 'Y-factor:Swept-frequency';
Sys.Cal.nM = -1;
Sys.Cal.Processed = '';
Sys.Cal.DataType = 'ASCII';
Sys.Cal.ByteOrder = 'N/A';
Sys.Cal.Compression = 'N/A';
Sys.Cal.mPar.RBW = 1000000;
Sys.Cal.mPar.VBW = 50000000;
Sys.Cal.mPar.td = 0.1;
Sys.Cal.mPar.Det = 'RMS';
Sys.Cal.mPar.fStart = 3450500000;
Sys.Cal.mPar.fStop = 3649500000;
Sys.Cal.mPar.n = 200;
Sys.Cal.mPar.Atten = 6;

Loc.Ver = Ver;
Loc.Type = 'Loc';
Loc.SensorID = SensorID;
Loc.SensorKey = SensorKey;
Loc.t = t;
Loc.Mobility = 'Stationary';
Loc.Lat = 36.78;
Loc.Lon = -75.96;
Loc.Alt = 20;
Loc.TimeZone = 'America/New_York';

% Save init info to file
WriteInitFile(filename, band, Sys, Loc, Out, Comment)
