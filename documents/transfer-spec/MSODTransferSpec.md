**Data Transfer Specification for the ITS/ITL Measured Spectrum Occupancy Database**

*Version 1.0.12 (29 October, 2014)*

# 1.  Description

This data transfer specification defines the format and required information for data to be ingested into the Measured Spectrum Occupancy Database (MSOD). MSOD is being developed in a collaborative effort between NTIA’s Institute for Telecommunication Sciences (ITS) and NIST’s Information Technology Laboratory (ITL).

# 2.  Format

The messages between sensor and MSOD will be in JavaScript Object Notation (JSON). The following is an example of a JSON Loc (Location) message (to be defined below):

```json
{
    "Ver": "1.0.12",
    "Type": "Loc",
    "SensorID": "101010101",
    "SensorKey": 846859034,
    "t": 987654321,
    "Mobility": "Stationary",
    "Lat": 40.0,
    "Lon": -105.26,
    "Alt": 1655,
    "TimeZone": "America\Denver"
}
```

JSON is a language-independent data-interchange format that is easy for humans to read and write. There are code and functions readily available in C, C++, C\#, Java, JavaScript, MATLAB, Perl, and Python for parsing and generating JSON. It is a lightweight alternative to XML, commonly used to transmit data between server and browser applications.

# 3.  JSON Message Descriptions

The data fields in the JSON message descriptions below are required fields. If an attribute is not relevant to the sensor implementation, then the value is set to NaN or "NaN". Each message (in general) will begin with a header comprised of attribute-value pairs in ASCII characters. The first five fields are the same for all messages; they are:

1.  Ver = Schema/data transfer version with the major.minor.revision syntax `string`
2.  Type = Type of JSON message {“Sys”, ”Loc”, or “Data”} `string of URL unreserved characters`
3.  SensorID = Unique identifier of sensor `string`
4.  SensorKey = Authentication key given out by MSOD `integer`
5.  t = Time [seconds since Jan 1, 1970 UTC] `long integer`

The following are specific formatting rules to be followed to avoid problems when messages are ingested into MSOD: (1) All timestamps, i.e., t (defined above) and t1 (to be defined in Data message description) will be reported as seconds since 1/1/1970 midnight UTC in the UTC time zone; (2) String values for SensorID and Sys2Detect (to be defined in Data message description) must only contain URL unreserved characters (i.e., uppercase and lowercase letters, decimal digits, hyphen, period, underscore, and tilde); and (3) Field names cannot start with an underscore because that convention is reserved for MSOD internal use.

We define three types of JSON messages for our purposes: (1) Sys, (2) Loc, or (3) Data. The Sys and Data messages can contain data in addition to the header information. Required fields for each message type are defined in the following subsections.

### 3.1.  Sys Messages

The Sys (System) message lists the critical hardware components of the sensor along with relevant RF specifications. It can also contain calibration data. Sys messages are sent when the sensor “registers” with the database, at the start of a sequence of measurements, and/or at a specified calibration frequency (e.g., hourly, daily). If the Sys message does not contain calibration data, the Cal data structure (9 below) and data block are excluded. The Sys message is comprised of header information and an optional data block. The Sys header contains the following fields:

1.  Ver = Schema/data transfer version with the major.minor.revision syntax `string`
2.  Type = Type of JSON message {”Sys”} `string`
3.  SensorID = Unique identifier of sensor `string of URL unreserved characters`
4.  SensorKey = Authentication key given out by MSOD `integer`
5.  t = Time [seconds since Jan 1, 1970 UTC] `long integer`
6.  Antenna = data that describes the antenna (see Antenna object below)
7.  Preselector = data that describes RF hardware components in preselector (see Preselector object below)
8.  COTSsensor = data that describes the COTS sensor (see COTSsensor object below)
9.  Cal = data structure that describes the calibration measurement (optional, see Cal object below)

The Sys data block is comprised of two streams of numbers of the specified data type and byte order. If Processed = “False”, then the data streams are

10a. wOn(n) = Raw measured data vector [dBm ref to input of COTS sensor] when known source is on.

11a. wOff(n) = Raw measured data vector [dBm ref to input of COTS sensor] when known source is off.

where n = mPar.n is specified in the Sys message header. Raw cal data is straight from the COTS sensor and is provided for the first calibration in a sequence. The Sys raw stream is ordered as follows: {wOn(1), wOn(2), … wOn(n), wOff(1), wOff(2), …, wOff(n)}, where the argument denotes a frequency index.

If Processed = “True”, then the data streams are,

10b. fn(n) = Noise figure [dB] referenced to input of preselector.

11b. g(n) = System gain [dB] referenced to input of preselector

The Sys processed stream is ordered as follows: {fn(1), fn(2), … fn(n), g(1), g(2), …, g(n)}.

### 3.2.  Loc Messages

The Loc message specifies the geolocation of the sensor. Loc messages are sent when the location information changes, e.g., if the sensor is mobile it will be sent with each data file. It is also sent when a sequence of continuous acquisitions is initiated. It is comprised only of header information with the following fields:

1.  Ver = Schema/data transfer version with the major.minor.revision syntax `string`
2.  Type = Type of JSON message {“Loc”} `string`
3.  SensorID = Unique identifier of sensor `string of URL unreserved characters`
4.  SensorKey = Authentication key given out by MSOD `integer`
5.  t = Time [seconds since Jan 1, 1970 UTC] `long integer`
6.  Mobility = Mobility of sensor {“Stationary”, “Mobile”} `string`
7.  Lat = angle [degrees N] from equatorial plane {0 – 360} `float`
8.  Lon = angle [degrees E] from Greenwich median {-180 – 180} `(float`
9.  Alt = height above sea level [m] {0 - 10<sup>6</sup>} `float`
10. TimeZone = Local time zone identifier {“America/New\_York”, “America/Chicago”, “America/Denver”, “America/Phoenix”, or “America/Los\_Angeles”} `string`

### 3.3.  Data Messages

The Data message contains acquired data from measurements of the environment using an antenna. The Data message is sent after each acquisition, i.e., after a burst of nM measurements are acquired. Some measurement schemes will involve an imposed pause after each acquisition. Each Data message is comprised of a header and a data block. The header information contains the following information:

1.  Ver = Schema/data transfer version with the major.minor.revision syntax `string`
2.  Type = Type of JSON message {“Data”} `string`
3.  SensorID = Unique identifier of sensor `string of URL unreserved characters`
4.  SensorKey = Authentication key given out by MSOD `integer`
5.  t = Time [seconds since Jan 1, 1970 UTC] `long integer`
6.  Sys2Detect = System that measurement is designed to detect {“Radar–SPN43”, “LTE”, “None”} `string of URL unreserved characters`
7.  Sensitivity = Sensitivity of the data {“Low”, “Medium”, “High”} `string`
8.  mType = Type of measurement {“Swept-frequency”, “FFT-power”} `string`
9.  t1 = Time of 1<sup>st</sup> acquisition in a sequence [seconds since Jan 1, 1970 UTC] `long integer`
10. a = Index of current acquisition in a sequence `integer`
11. nM = Number of measurements per acquisition `integer`
12. Ta = Imposed time between acquisition starts `float`
13. OL = Overload flag(s) {0 or 1} `integer`
14. wnI = Detected system noise power [dBm ref to output of isotropic antenna] `float`
15. Comment `string`
16. Processed = Indicator on processing of data {"True", "False"} `string`
17. DataType = Data type {"Binary–float32", "Binary–int16", "Binary–int8", "ASCII"} `string`
18. ByteOrder = Order of bytes for binary data {"Network", "Big Endian", "Little Endian", "N/A"} `string`
19. Compression = Indicator on compression of data {"Zip", "None", "N/A"} `string`
20. mPar = Measurement parameters (elements listed in Objects section below)

The data block is comprised of one stream of numbers of the specified data type and byte order. If Processed = “False”, then the data stream is

21a. w(n, nM) = Raw measured data vector [dBm ref to input of COTS sensor]

where n = mPar.n is specified in the Data message header. Raw data is straight from the COTS sensor and is provided for the first acquisition in a sequence. Raw data allows for a quality assurance check on the system specifications. The Data raw stream is ordered as follows: {w(1, 1), w(2, 1), … w(n, 1), w(1, 2), w(2, 2), …, w(n, 2), …, w(1, nM), w(2, nM), …, w(n, nM)}, where the first argument denotes a frequency index and the second argument denotes measurement index.

If Processed = “True”, then the data stream is

21b. wI(n, nM) = Measured power vector [dBm ref to output of isotropic antenna]

Processed data is adjusted to remove system gains and losses and provide signal amplitude that is sensor-independent. Processed data is intended for ingest straight into MSOD. The Data processed stream is ordered as follows: {wI(1, 1), wI(2, 1), … wI(n, 1), w(1, 2), wI(2, 2), …, wI(n, 2), …, wI(1, nM), wI(2, nM), …, wI(n, nM)}.

# 4.  Objects

The following are object definitions that exist in the JSON data messages above.

Antenna = antennas parameters with elements

1.  Model = Make/model {“AAC SPBODA-1080\_NFi”, “Alpha AW3232”} `string`
2.  fLow = Low frequency [Hz] of operational range `float`
3.  fHigh = High frequency [Hz] of operational range `float`
4.  g = Antenna gain [dBi] `float`
5.  bwH = Horizontal 3-dB beamwidth [degrees] `float`
6.  bwV = Vertical 3-dB beamwidth [degrees] `float`
7.  AZ = direction of main beam in azimuthal plane [degrees from N] `float`
8.  EL = direction of main beam in elevation plane [degrees from horizontal] `float`
9.  Pol = Polarization {“VL”, “HL”, “LHC”, “RHC”, “Slant”} `string`
10. XSD = Cross-polarization discrimination [dB] `float`
11. VSWR = Voltage standing wave ratio `float`
12. lCable = Cable loss (dB) for cable connecting antenna and preselector `float`

Preselector = preselector parameters with elements

1.  fLowPassBPF = Low frequency [Hz] of filter 1-dB passband `float`
2.  fHighPassBPF= High frequency [Hz] of filter 1-dB passband `float`
3.  fLowStopBPF = Low frequency [Hz] of filter 60-dB stopband `float`
4.  fHighStopBPF = High frequency [Hz] of filter 60-dB stopband `float`
5.  fnLNA = Noise figure [dB] of LNA `float`
6.  gLNA = Gain [dB] of LNA `float`
7.  pMaxLNA = Max power [dBm] at output of LNA, e.g., 1-dB compression point `float`
8.  enrND = Excess noise ratio of noise [dB] diode for y-factor calibrations

COTSsensor = COTS sensor parameters with elements

1.  Model = Make and model {"Agilent N6841A", "Agilent E4440A", "CRFS RFeye", "NI USRP N210", "ThinkRF WSA5000-108", "Spectrum Hound BB60C"} `string`
2.  fLow = LowMinimum frequency [Hz] of operational range `float`
3.  fHigh = HighMaximum frequency [Hz] of operational range `float`
4.  fn = Noise figure [dB] of COTS sensor in contrast to overall system `float`
5.  pMax = Maximum power [dBm at input] of COTS sensor `float`

Cal = Calibration parameters with elements

1.  CalsPerHour = Number of cals per hour `float`
2.  Temp = Measured temperature inside preselctor [F] `float`
3.  mType: Type of measurement {“Y-factor:Swept-frequency”, “Y-factor:FFT-power”, “None”} `string`
4.  nM = Number of measurements per calibration `integer`
5.  Processed = Indicator on processing of data {"True", "False"} `string`
6.  DataType = Data type {"Binary–float32", "Binary–int16", "Binary–int8", "ASCII"} `string`
7.  ByteOrder = Order of bytes for binary data {"Network", "Big Endian", "Little Endian", "N/A"} `string`
8.  Compression = Compression of data {"Zip", "None", "N/A"} `string`
9.  mPar = Measurement parameters (elements listed in Objects section below)

mPar = Measurement parameters

1.  fStart = Start frequency [Hz] of sweep \<Required for swept-freq\> `float`
2.  fStop = Stop frequency [Hz] of sweep \<Required for swept-freq\> `float`
3.  n = Number of frequencies in sweep \<Required for swept-freq\> `float`
4.  td = Dwell time [s] at each frequency in a sweep \<Required for swept-freq\> `float`
5.  Det = Detector: {"RMS", "Positive”} \<Required for swept-freq\> `string`
6.  RBW = Resolution bandwidth [Hz] \<Required for swept-freq\> `float`
7.  VBW = Video bandwidth [Hz] \<Required for swept-freq\> `float`
8.  Atten = COTS sensor attenuation [dB] \<Required for swept-freq\> `float`

# 5.  Transfer Mechanism

TCP sockets or HTTPS posts will be used to transfer data from sensor (client) to staging server either real time or post-acquisition.

### 5.1.  Socket Setup

A socket is a standard API for networking that is uniquely identified by internet address, end-to-end protocol, and port number. We will use a stream socket that uses transmission control protocol (TCP) to establish a reliable and bidirectional byte-stream channel (where all transmissions arrive in order with no duplicates). In the client-server communication, the client is active and initiates communication. The server is passive; it waits and responds to client communications.

The following setup is performed when a socket is used for communications between client and server: (1) Both server and client create a socket. This creates the interface; it does not specify where data will be coming from or going to. (2) Server instructs TCP protocol implementation to listen for connections. (3) To allow for perpetual client connections the server repeatedly (a) accepts new connections, (b) communicates, and (c) closes the connection. (4) To transfer data, the client establishes a connection, communicates, and closes the connection.

If a socket is using during a sequence of acquisitions, the socket is kept open for the entire sequence. For each message, the client sends a preceding integer (and /CR) that indicates the number of ASCII characters in the header of the message that follows.

### 5.2.  HTTPS post

### 5.3.  MSOD Ingest Process

A database schema applies a set of integrity constraints during the data ingest process. Each field is constrained by (data type) and {range of value}. As new types of sensors and measurements are developed, data requirements will change (e.g., existing message syntax will likely evolve, new message types will likely be added).
