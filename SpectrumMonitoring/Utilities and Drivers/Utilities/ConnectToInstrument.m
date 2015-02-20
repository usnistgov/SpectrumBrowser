function [InterfaceObject, DeviceObject] = ConnectToInstrument(DriverName, ConnType, Address, VisaProvider)
% This function connects to an instrument applies the designated driver and
% returns the interface and device objects that go along with. If it is not
% possible to connect then an error is raised. If bad inputs are entered
% then the empty set [] is returned for both the interface and device
% objects.
%
% Inputs:
% DriverName = string conatining the name of the driver without the .mdd
% ConnType = the type of connection the instrument requires
%   Visa = Visa type instruments (E4440, PXA)
%   Modbus = modbus instruments such as the 4G preselectors
%   GPIB = GPIB instruments (if it needs ENET/100)
%   YIGTracker = YIG tracker
% Address = the address of the instrument. For the most part this is the IP
%   address except for GPIB instruments where it is the default ENET/100
%   number and the instrument GPIB address, and the YIG tracker where the
%   IP address of the glitch detector I/O module is also included.
% VisaProvider = optional input indicating which manufacturer's visa is
%   being used. If nothing is input then NI is the default.
%
% Outputs:
% InterfaceObject = interface object
% DeviceObject = device object
%

% Created by Geoff Sanders 3/23/2010
try
  switch ConnType
    case 'Visa'
      if ~exist('VisaProvider', 'var')
        VisaProvider = 'NI';
      end
      InterfaceObject = instrfind('Type', 'visa-tcpip', 'RsrcName', ['TCPIP0::',Address,'::inst0::INSTR'], 'Tag', '');
      
      % Create the VISA-TCPIP object if it does not exist
      % otherwise use the object that was found.
      if isempty(InterfaceObject)
        InterfaceObject = visa(VisaProvider, ['TCPIP0::',Address,'::inst0::INSTR']);
      else
        fclose(InterfaceObject);
        InterfaceObject = InterfaceObject(1);
      end
      
      % Create a device object.
      DeviceObject = icdevice(DriverName, InterfaceObject);
      
      % Connect device object to hardware
      connect(DeviceObject);
      
    case 'VisaSocket'
      if ~exist('VisaProvider', 'var')
        VisaProvider = 'NI';
      end
      InterfaceObject = instrfind('Type', 'generic', 'RsrcName', ['TCPIP0::',Address,'::5025::SOCKET'], 'Tag', '');
      
      % Create the VISA-TCPIP object if it does not exist
      % otherwise use the object that was found.
      if isempty(InterfaceObject)
        InterfaceObject = visa(VisaProvider, ['TCPIP0::',Address,'::5025::SOCKET']);
      else
        fclose(InterfaceObject);
        InterfaceObject = InterfaceObject(1);
      end
      
      % Create a device object.
      DeviceObject = icdevice(DriverName, InterfaceObject);
      
      % Connect device object to hardware
      connect(DeviceObject);
    case 'Modbus'
      % If an IP is selected create the TCPIP object.
      InterfaceObject = instrfind('Type', 'tcpip', 'RemoteHost', Address, 'RemotePort', 502, 'Tag', '');
      
      % Create the TCPIP object if it does not exist
      % otherwise use the object that was found.
      if isempty(InterfaceObject)
        InterfaceObject = tcpip(Address, 502);
      else
        fclose(InterfaceObject);
        InterfaceObject = InterfaceObject(1);
      end
      
      % Create a device object. Apply the driver to the interface (TCPIP)
      % object.
      DeviceObject = icdevice(DriverName, InterfaceObject);
      
      % Connect device object to hardware.
      connect(DeviceObject);
    case 'GPIB'
      if ~exist('VisaProvider', 'var')
        VisaProvider = 'NI';
      end
      defaultInput = {num2str(Address(1)), num2str(Address(2))};
      [GPIBInfo] = inputdlg({'GPIB (ENET100) #'; 'Instrument Address?'},'Input GPIB and Instrument Info',1,defaultInput);
      
      % if user cancels return empty set for interfaceobj and deviceobj and let measurement handle the problem
      if ~isempty(GPIBInfo)
        GPIBNum = str2double(GPIBInfo{1});
        InstAddress = str2double(GPIBInfo{2});
        % Find a GPIB object.
        InterfaceObject = instrfind('Type', 'gpib', 'BoardIndex', GPIBNum, 'PrimaryAddress', InstAddress, 'Tag', '');
        
        % Create the GPIB object if it does not exist
        % otherwise use the object that was found.
        if isempty(InterfaceObject)
          InterfaceObject = gpib(VisaProvider, GPIBNum, InstAddress);
        else
          fclose(InterfaceObject);
          InterfaceObject = InterfaceObject(1);
        end
        
        % Create device object
        DeviceObject = icdevice(DriverName, InterfaceObject);
        
        % Connect to instrument
        connect(DeviceObject);
      else
        InterfaceObject = [];
        DeviceObject = [];
      end
    case 'YIGTracker'
      if ~exist('VisaProvider', 'var')
        VisaProvider = 'NI';
      end
      temp = Address;
      Address = temp{1};
      IOModIPAdd = temp{2};
      defaultInput = {num2str(Address(1)), num2str(Address(2))};
      [GPIBInfo] = inputdlg({'GPIB (ENET100) #'; 'Instrument Address?'},'Input GPIB and Instrument Info',1,defaultInput);
      
      % if user cancels return empty set for interfaceobj and deviceobj and let measurement handle the problem
      if ~isempty(GPIBInfo)
        GPIBNum = str2double(GPIBInfo{1});
        InstAddress = str2double(GPIBInfo{2});
        % Find a GPIB object.
        InterfaceObject = instrfind('Type', 'gpib', 'BoardIndex', GPIBNum, 'PrimaryAddress', InstAddress, 'Tag', '');
        
        % Create the GPIB object if it does not exist
        % otherwise use the object that was found.
        if isempty(InterfaceObject)
          InterfaceObject = gpib(VisaProvider, GPIBNum, InstAddress);
        else
          fclose(InterfaceObject);
          InterfaceObject = InterfaceObject(1);
        end
        
        % Create device object
        DeviceObject = icdevice(DriverName, InterfaceObject, 'IOModuleIP', IOModIPAdd);
        
        % Connect to instrument
        connect(DeviceObject);
      else
        InterfaceObject = [];
        DeviceObject = [];
      end
    case 'ENET232'
      if ~exist('VisaProvider', 'var')
        VisaProvider = 'NI';
      end
      ENET232PortNum = inputdlg('Please enter the ENET-232 serial port number','Input ENET-232 Port Number',1,Address(2));
      
      % if user cancels return empty set for interfaceobj and deviceobj and let measurement handle the problem
      if ~isempty(ENET232PortNum)
       InterfaceObject = visa(VisaProvider, ['ASRL::',Address{1},'::',ENET232PortNum{1},'::INSTR']);
  
        
        % Create device object
        DeviceObject = icdevice(DriverName, InterfaceObject);
        
        % Connect to instrument
        connect(DeviceObject);
      else
        InterfaceObject = [];
        DeviceObject = [];
      end
    case 'Serial'
      % Needs to be added
  end
catch oops
  error([ConnType,':Connection:Failure'],oops.message)
end