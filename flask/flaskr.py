from flask import Flask, request, abort, make_response
from flask import jsonify
import random
import json
import os
import matplotlib as mpl
mpl.use('Agg')
from pymongo import MongoClient
import urlparse
import populate_db
import sys
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
from flask_sockets import Sockets
import traceback
import GenerateZipFileForDownload
import GetLocationInfo
import GetDailyMaxMinMeanStats
import util
import authentication
import GeneratePowerVsTime
import GenerateSpectrum
import GenerateSpectrogram
import GetDataSummary
import DataStreaming
import GetOneDayStats
import msgutils
import GetAdminInfo
import AdminChangePassword
import Config
import PeerConnectionManager
import time
from flask.ext.cors import CORS 


global sessions
global client
global db
global admindb


if not Config.isConfigured() :
    print "Please configure system using admin interface"

sessions = {}
secureSessions = {}
gwtSymbolMap = {}

# move these to another module



launchedFromMain = False
app = Flask(__name__, static_url_path="")
cors = CORS(app)
sockets = Sockets(app)
random.seed()
mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.spectrumdb
admindb = client.admindb
accounts = client.accounts

#Note: This has to go here after the definition of some globals.
import AdminCreateNewAccount


debug = True
# Note : In production we will set this to True
isSecure = False

HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY * 60
SECONDS_PER_DAY = MINUTES_PER_DAY * 60
MILISECONDS_PER_DAY = SECONDS_PER_DAY * 1000
UNDER_CUTOFF_COLOR = '#D6D6DB'
OVER_CUTOFF_COLOR = '#000000'
SENSOR_ID = "SensorID"
TIME_ZONE_KEY = "TimeZone"
flaskRoot = os.environ['SPECTRUM_BROWSER_HOME'] + "/flask/"
PeerConnectionManager.start()
Config.printConfig()


######################################################################################

@app.route("/api/<path:path>",methods=["GET"])
@app.route("/generated/<path:path>", methods=["GET"])
@app.route("/myicons/<path:path>", methods=["GET"])
@app.route("/spectrumbrowser/<path:path>", methods=["GET"])
def getFile(path):
    util.debugPrint("getFile()")
    p = urlparse.urlparse(request.url)
    urlpath = p.path
    util.debugPrint(urlpath)
    util.debugPrint(urlpath[1:])
    return app.send_static_file(urlpath[1:])

@app.route("/admin", methods=["GET"])
def adminEntryPoint():
    util.debugPrint("admin")
    return app.send_static_file("admin.html")

# The user clicks here when activating an account
@app.route("/admin/activate/<token>",methods=["GET"])
def activate(token):
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if AdminCreateNewAccount.activate(int(token)):
            return app.send_static_file("account_created.html")
        else:
            return app.send_static_file("account_denied.html")
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/admin/createNewAccount/<emailAddress>/<password>", methods=["POST"])
@app.route("/spectrumbrowser/createNewAccount/<emailAddress>/<password>", methods=["POST"])
def createNewAccount(emailAddress,password):
    """
    Create a place holder for a new account and mail the requester that a new account has been created.

    URL Path:

        - emailAddress : the email address of the requester.
        - password : the clear text password of the requester.

    URL Args:

        - firstName: First name of requester
        - lastName: Last name of requester
        - urlPrefix : server url prefix (required)


    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        firstName = request.args.get("firstName","UNKNOWN")
        lastName = request.args.get("lastName","UNKNOWN")
        serverUrlPrefix = request.args.get("urlPrefix",None)
        if serverUrlPrefix == None:
            return util.formatError("urlPrefix missing"),400
        else:
            return AdminCreateNewAccount.adminCreateNewAccount(emailAddress,firstName,lastName,password,serverUrlPrefix)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@app.route("/federated/peerSignIn/<peerServerId>/<peerKey>",methods=["POST"])
def peerSignIn(peerServerId, peerKey):
    """
    Handle authentication request from federated peer and send our location information.
    """
    try :
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        util.debugPrint("peerSignIn " + peerServerId + "/" + peerKey)
        rc =  authentication.authenticatePeer(peerServerId,peerKey)
        # successfully authenticated? if so, return the location info for ALL
        # sensors.
        util.debugPrint("Status : " + str(rc))
        retval = {}
        if rc:
            requestStr = request.data
            if requestStr != None:
                remoteAddr = request.remote_addr
                jsonData = json.loads(requestStr)
                Config.getPeers()
                if isSecure:
                    protocol = "https:"
                else:
                    protocol = "http:"
                PeerConnectionManager.setPeerSystemAndLocationInfo(protocol + "//" + remoteAddr,jsonData)
            retval["status"] = "OK"
            if not Config.isAuthenticationRequired():
                locationInfo = GetLocationInfo.getLocationInfo()
                retval["locationInfo"] = locationInfo
            return jsonify(retval)
        else:
            retval["status"] = "NOK"
            return jsonify(retval)
    except :
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/", methods=["GET"])
@app.route("/spectrumbrowser", methods=["GET"])
def userEntryPoint():
    util.debugPrint("root()")
    return app.send_static_file("app.html")

@app.route("/admin/changePassword/<emailAddress>/<sessionId>", methods=["GET"])
def changePassword(emailAddress, sessionId):
    util.debugPrint("changePassword()")
    return app.send_static_file("app2.html")

@app.route("/spectrumbrowser/emailChangePasswordUrlToUser/<emailAddress>/<sessionId>", methods=["POST"])
def emailChangePasswordUrlToUser(emailAddress, sessionId):
    """

    Send email to the given user when his requested dump file becomes available.

    URL Path:

    - emailAddress : The email address of the user.
    - sessionId : the login session Id of the user.

    URL Args (required):

    - urlPrefix : The url prefix that the web browser uses to access the website later when clicks on change password link in email message.
    HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        urlPrefix = request.args.get("urlPrefix", None)
        util.debugPrint(urlPrefix)
        if urlPrefix == None :
            abort(400)
        url = urlPrefix + "/admin/changePassword/"+emailAddress+ "/guest-123"
        util.debugPrint(url)
        return AdminChangePassword.emailUrlToUser(emailAddress, url)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise
    return 200


@app.route("/spectrumbrowser/isAuthenticationRequired",methods=['POST'])
def isAuthenticationRequired():
    """
    Return true if authentication is required.
    """
    if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
    if Config.isAuthenticationRequired():
        return jsonify({"AuthenticationRequired": True})
    else:
        return jsonify({"AuthenticationRequired": False, "SessionToken":authentication.generateGuestToken()})



@app.route("/admin/logOut/<sessionId>", methods=['POST'])
@app.route("/spectrumbrowser/logOut/<sessionId>", methods=['POST'])
def logOut(sessionId):
    """
    Log out of an existing session.

    URL Path:

        sessionId : The session ID to log out.

    """
    authentication.logOut(sessionId)
    return jsonify({"status":"OK"})


@app.route("/admin/getSystemConfig/<sessionId>", methods=["POST"])
def getSystemConfig(sessionId):
    """
    get system configuration.
    
    URL Path:
    
        sessionId : Session ID of the login session.
        
    """
    if not authentication.checkSessionId(sessionId):
        abort(403)
    systemConfig = Config.getSystemConfig()
    if systemConfig == None:
        config = { "ADMIN_EMAIL_ADDRESS": "UNKNOWN", "ADMIN_PASSWORD": "UNKNOWN", "API_KEY": "UNKNOWN", \
                    "HOST_NAME": "UNKNOWN", "IS_AUTHENTICATION_REQUIRED": False, \
                    "MY_SERVER_ID": "UNKNOWN", "MY_SERVER_KEY": "UNKNOWN",  "SMTP_PORT": 0, "SMTP_SERVER": "UNKNOWN", \
                    "STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS": -1, "STREAMING_FILTER": "PEAK", \
                    "STREAMING_SAMPLING_INTERVAL_SECONDS": -1, "STREAMING_SECONDS_PER_FRAME": -1, "STREAMING_SERVER_PORT": 9000}
        return jsonify(config)
    else:
        return jsonify(systemConfig)
    
@app.route("/admin/getPeers/<sessionId>",methods=["POST"])
def getPeers(sessionId):
    """
    get outbound peers.
    
    URL Path:
    
        sessionId: session ID of the login session.
        
    """
    if not authentication.checkSessionId(sessionId):
        abort(403)
    peers = Config.getPeers()
    retval = {"peers":peers}
    return jsonify(retval)

@app.route("/admin/removePeer/<host>/<port>/<sessionId>", methods=["POST"])
def removePeer(host,port,sessionId):
    """
    remove outbound peer.
    
    URL Path:
        host: Host of peer to remove
        port: port or peer to remove
        sessionId : login session ID
    """
    if not authentication.checkSessionId(sessionId):
        abort(403)
    Config.removePeer(host,int(port))
    peers = Config.getPeers()
    retval = {"peers":peers}
    return jsonify(retval)

@app.route("/admin/addPeer/<host>/<port>/<protocol>/<sessionId>", methods=["POST"])
def addPeer(host,port,protocol,sessionId):
    """
    add an outbound peer
    
    URL Path:
        host : Host of peer to add.
        port : port of peer
        protocol : http or https
        sessionId : login session id.
    """
    if not authentication.checkSessionId(sessionId):
        abort(403)
    # TODO -- parameter checking.
    Config.addPeer(protocol,host,int(port))
    peers = Config.getPeers()
    retval = {"peers":peers}
    return jsonify(retval)

@app.route("/admin/getInboundPeers/<sessionId>",methods=["POST"])
def getInboundPeers(sessionId):
    """
    get a list of inbound peers.
    
    URL path:
    sessionID = session ID of the login
    
    URL Args: None
    
    Returns : JSON formatted string containing the inbound Peers accepted by this server.
    
    """
    if not authentication.checkSessionId(sessionId):
        abort(403)
    peerKeys = Config.getInboundPeers()
    retval = {"inboundPeers":peerKeys}
    return jsonify(retval)

@app.route("/admin/deleteInboundPeer/<peerId>/<sessionId>", methods=["POST"])
def deleteInboundPeer(peerId, sessionId):
    """
    Delete an inbound peer record.
    """
    if not authentication.checkSessionId(sessionId) :
        abort(403)
    Config.deleteInboundPeer(peerId)
    peerKeys = Config.getInboundPeers()
    retval = {"inboundPeers":peerKeys}
    return jsonify(retval)

@app.route("/admin/addInboundPeer/<sessionId>", methods=["POST"])
def addInboundPeer(sessionId):
    """
    Add an inbound peer.
    """
    try:
        if not authentication.checkSessionId(sessionId) :
            abort(403)
        requestStr = request.data
        peerConfig = json.loads(requestStr)
        util.debugPrint("peerConfig " + json.dumps(peerConfig, indent=4))
        Config.addInboundPeer(peerConfig)
        peers = Config.getInboundPeers()
        retval = {"inboundPeers":peers}
        return jsonify(retval)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise
    
@app.route("/admin/setSystemConfig/<sessionId>",methods=["POST"])
def setSystemConfig(sessionId):
    """
    set system configuration
    URL Path:
        sessionId the session Id of the login in session.
        
    URL Args: None
        
    Request Body:
        A JSON formatted string containing the system configuration.
    """
    if not authentication.checkSessionId(sessionId):
        abort(403)
    requestStr = request.data
    systemConfig = json.loads(requestStr)
    if not Config.verifySystemConfig(systemConfig):
        return jsonify({"Status":"NOK"})

    util.debugPrint("setSystemConfig " + json.dumps(systemConfig,indent=4,))
    if Config.setSystemConfig(systemConfig):
        return jsonify({"Status":"OK"})
    else:
        return jsonify({"Status":"NOK"})



@app.route("/admin/authenticate/<privilege>/<userName>", methods=['POST'])
@app.route("/spectrumbrowser/authenticate/<privilege>/<userName>", methods=['POST'])
def authenticate(privilege, userName):
    """

    Authenticate the user given his username and password at the requested privilege or return
    error if the user cannot be authenticated.

    URL Path:

    - privilege : Desired privilege (user or admin).
    - userName : user login name.
    URL Args:

    - None

    Return codes:

    - 200 OK if authentication is OK
            On success, a JSON document with the following information is returned.
        - sessionId : The login session ID to be used for subsequent interactions
            with this service.
    - 403 Forbidden if authentication fails.

    """
    password = request.args.get("password", None)
    util.debugPrint( "authenticate " + userName + " " + str(password) + " " + privilege)
    return authentication.authenticateUser(privilege,userName,password)

@app.route("/spectrumbrowser/getAdminBand/<sessionId>/<bandName>", methods=["POST"])
def getAdminBand(sessionId, bandName):
    """
    get an admin frequency band from the mongoDB database
    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            util.debugPrint("SessionId not found")
            abort(403)
        print "bandName ", bandName
        return GetAdminInfo.getAdminBandInfo(bandName)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise
    




@app.route("/spectrumbrowser/getLocationInfo/<sessionId>", methods=["POST"])
def getLocationInfo(sessionId):
    """

    Get the location and system messages for all sensors.

    URL Path:

    - sessionid : The session ID for the login session.

    URL Args:

    - None

    HTTP return codes:

        - 200 OK if the call completed successfully.
        On success this returns a JSON formatted document
        containing a list of all the System and Location messages
        in the database. Additional information is added to the
        location messages (i.e.  the supported frequency bands of
        the sensor). Sensitive information such as sensor Keys are
        removed from the returned document.  Please see the MSOD
        specification for documentation on the format of these JSON
        messages. This API is used to populate the top level view (the map)
        that summarizes the data. Shown below is an example interaction
        (consult the MSOD specification for details):

        Request:

        ::

           curl -X POST http://localhost:8000/spectrumbrowser/getLocationInfo/guest-123

        Returns the following jSON document:

        ::

            {
                "locationMessages": [
                    {
                    "Alt": 143.5,
                    "Lat": 39.134374999999999,
                    "Lon": -77.215337000000005,
                    "Mobility": "Stationary",
                    "SensorID": "ECR16W4XS",
                    "TimeZone": "America/New_York",
                    "Type": "Loc",
                    "Ver": "1.0.9",
                    "sensorFreq": [ # An array of frequency bands supported (inferred
                                    # from the posted data messages)
                        "703967500:714047500",
                        "733960000:744040000",
                        "776967500:787047500",
                        "745960000:756040000"
                    ],
                    "t": 1404964924,
                    "tStartLocalTime": 1404950524,
                    }, ....
                ],
                "systemMessages": [
                {
                    "Antenna": {
                    "Model": "Unknown (whip)",
                    "Pol": "VL",
                    "VSWR": "NaN",
                    "XSD": "NaN",
                    "bwH": 360.0,
                    "bwV": "NaN",
                    "fHigh": "NaN",
                    "fLow": "NaN",
                    "gAnt": 2.0,
                    "lCable": 0.5,
                    "phi": 0.0,
                    "theta": "N/A"
                    }
                "COTSsensor": {
                    "Model": "Ettus USRP N210 SBX",
                    "fMax": 4400000000.0,
                    "fMin": 400000000.0,
                    "fn": 5.0,
                    "pMax": -10.0
                },
                "Cal": "N/A",
                "Preselector": {
                    "enrND": "NaN",
                    "fHighPassBPF": "NaN",
                    "fHighStopBPF": "NaN",
                    "fLowPassBPF": "NaN",
                    "fLowStopBPF": "NaN",
                    "fnLNA": "NaN",
                    "gLNA": "NaN",
                    "pMaxLNA": "NaN"
                },
                "SensorID": "ECR16W4XS",
                "Type": "Sys",
                "Ver": "1.0.9",
                "t": 1404964924
                },....
            ]
            }

        - 403 Forbidden if the session ID is not found.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        peerSystemAndLocationInfo = PeerConnectionManager.getPeerSystemAndLocationInfo()
        retval=GetLocationInfo.getLocationInfo()
        retval["peers"] = peerSystemAndLocationInfo
        return jsonify(retval)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<startTime>/<dayCount>/<sys2detect>/<fmin>/<fmax>/<sessionId>", methods=["POST"])
def getDailyStatistics(sensorId, startTime, dayCount, sys2detect, fmin, fmax, sessionId):
    """

    Get the daily statistics for the given start time, frequency band and day count for a given sensor ID

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in the UTC time zone specified as a second offset from 1.1.1970:0:0:0 (UTC).
    - dayCount : The number days for which we want the statistics.
    - sessionId : The session ID of the login session.
    - fmin : min freq in MHz of the band of interest.
    - fmax : max freq in MHz of the band of interest.
    - sessionId: login session ID.

    URL args (optional):

    - subBandMinFreq : the min freq of the sub band of interest (contained within a band supported by the sensor).
    - subBandMaxFreq: the max freq of the sub band of interest (contained within a band supported by the sensor).

    If the URL args are not specified, the entire frequency band is used for computation.

    HTTP return codes:

    - 200 OK if the call returned without errors.
        Returns a JSON document containing the daily statistics for the queried sensor returned as an array of JSON
        records. Here is an example interaction (using UNIX curl to send the request):

    Request:

    ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDailyMaxMinMeanStats/ECR16W4XS/1404907200/5/745960000/756040000/guest-123

    Which returns the following response (annotated and abbreviated):

    ::

        {
        "channelCount": 56, # The number of channels
        "cutoff": -75.0,    # The cutoff for occupancy computations.
        "maxFreq": 756040000.0, # Max band freq. in Hz.
        "minFreq": 745960000.0, # Min band freq in Hz.
        "startDate": "2014-07-09 00:00:00 EDT", # The formatted time stamp.
        "tmin": 1404892800, # The universal time stamp.
        "values": {
            "0": {          # The hour offset from start time.
                "maxOccupancy": 0.05, # Max occupancy
                "meanOccupancy": 0.01,# Mean occupancy
                "minOccupancy": 0.01  # Min occupancy.
            }, ... # There is an array of such structures

        }
        }


    - 403 Forbidden if the session ID was not found.
    - 404 Not Found if the sensor data was not found.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        util.debugPrint("getDailyMaxMinMeanStats : " + sensorId + " " + startTime + " " + dayCount)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        subBandMinFreq = int(request.args.get("subBandMinFreq", fmin))
        subBandMaxFreq = int(request.args.get("subBandMaxFreq", fmax))
        return GetDailyMaxMinMeanStats.getDailyMaxMinMeanStats(sensorId, startTime, dayCount,sys2detect, fmin, fmax,subBandMinFreq,subBandMaxFreq, sessionId)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@app.route("/spectrumbrowser/getAcquisitionCount/<sensorId>/<sys2detect>/<fstart>/<fstop>/<tstart>/<daycount>/<sessionId>", methods=["POST"])
def getAcquisitionCount(sensorId, sys2detect, fstart, fstop, tstart, daycount, sessionId):

    """

    Get the acquistion count from a sensor given the start date and day count.

    URL Path:
        - sensorId : the sensor Id of interest
        - sys2detect : the system to detect
        - fstart : The start frequency
        - fstop : The end frequency
        - tstart : The acquistion start time
        - daycount : the number of days
    """

    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)

        return GetDataSummary.getAcquistionCount(sensorId,sys2detect,\
                int(fstart),int(fstop),int(tstart),int(daycount))
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/getDataSummary/<sensorId>/<lat>/<lon>/<alt>/<sessionId>", methods=["POST"])
def getDataSummary(sensorId, lat, lon, alt, sessionId):
    """

    Get the sensor data summary  for the sensor given its ID, latitude and longitude.

    URL Path:

    - sensorId: Sensor ID of interest.
    - lat : Latitude
    - lon: Longitude
    - alt: Altitude
    - sessionId : Login session ID

    URL args (optional):

    - minFreq : Min band frequency of a band supported by the sensor.
            if this parameter is not specified then the min freq of the sensor is used.
    - maxFreq : Max band frequency of a band supported by the sensor.
            If this parameter is not specified, then the max freq of the sensor is used.
    - minTime : Universal start time (seconds) of the interval we are
            interested in. If this parameter is not specified, then the acquisition
            start time is used.
    - sys2detect: The system to detect
    - dayCount : The number of days for which we want the data. If this
            parameter is not specified, then the interval from minTime to the end of the
            available data is used.

    HTTP return codes:

    - 200 OK Success. Returns a JSON document with a summary of the available
    data in the time range and frequency band of interest.
    Here is an example Request using the unix curl command:

    ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDataSummary/Cotton1/40/-105.26/1676/guest-123

    Here is an example of the JSON document (annotated) returned in response :

    ::

        {
          "maxFreq": 2899500000, # max Freq the band of interest for the sensor (hz)
                                 #for period of interest
          "minFreq": 2700500000, # min freq of the band of interest for  sensor (hz)
                                 #for period of interest
          "maxOccupancy": 1.0, # max occupancy for the results of the query for period of interest
          "meanOccupancy": 0.074, # Mean Occupancy for the results of the query for period of interest
          "minOccupancy": 0.015, # Min occupancy for the results of the query for period of interest
          "measurementType": "Swept-frequency",# Measurement type
          "readingsCount": 882, # acquistion count in interval of interest.
          "tAquisitionEnd": 1403899158, # Timestamp (universal time) for end acquisition
                                        # in interval of interest.
          "tAquisitionEndFormattedTimeStamp": "2014-06-27 09:59:18 MDT", #Formatted timestamp
                                                                         #for end acquistion
          "tAquistionStart": 1402948665, # universal timestamp for start of acquisition
          "tAquisitionStartFormattedTimeStamp": "2014-06-16 09:57:45 MDT",# Formatted TS for start of acq.
          "tEndReadings": 1403899158, # universal Timestamp for end of available readings.
          "tEndDayBoundary": 1403863200, # Day boundary of the end of available data (i.e 0:0:0 next day)
          "tEndReadingsLocalTime": 1403877558.0, # Local timestamp for end of readings.
          "tEndLocalTimeFormattedTimeStamp": "2014-06-27 09:59:18 MDT", # formatted TS for end of interval.
          "tStartReadings": 1402948665  # universal timestamp for start of available readings.
          "tStartDayBoundary": 1402912800.0, # Day boundary (0:0:0 next day) timestamp
                                             # for start of available readings.
          "tStartLocalTime": 1402927065, # Local timestamp for start of available readings
          "tStartLocalTimeFormattedTimeStamp": "2014-06-16 09:57:45 MDT", # formatted timestamp for the
                                                                          # start of interval of interest.
          "acquistionCount": 5103, # Available number of acquisitions for sensor
          "acquistionMaxOccupancy": 1.0, # Max occupancy over all the aquisitions
                                         #for sensor in band of interest.
          "acquistionMinOccupancy": 0.0, # Min occupancy over all aquisitions
                                         #for sensor in band of interest.
          "aquistionMeanOccupancy": 0.133 # Mean occupancy over all aquisitions
                                         #for sensor in band of interest.
          }

    - 403 Forbidden if the session ID is not recognized.
    - 404 Not Found if the location message for the sensor ID is not found.

    """

    util.debugPrint("getDataSummary")
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            util.debugPrint("SessionId not found")
            abort(403)
        longitude = float(lon)
        latitude = float(lat)
        alt = float(alt)
        locationMessage = db.locationMessages.find_one({SENSOR_ID:sensorId, "Lon":longitude, "Lat":latitude, "Alt":alt})
        if locationMessage == None:
            util.debugPrint("Location Message not found")
            abort(404)
        return GetDataSummary.getDataSummary(sensorId,locationMessage)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def getOneDayStats(sensorId, startTime,sys2detect, minFreq, maxFreq, sessionId):
    """

    Get the statistics for a given sensor given a start time for a single day of data.
    The time is rounded to the start of the day boundary.
    Times for this API are specified as the time in the UTC time domain as a second offset from 1.1.1970:0:0:0
    (i.e. universal time; not local time)

    URL Path:

    - sensorId: Sensor ID for the sensor of interest.
    - startTime: start time within the day boundary of the acquisitions of interest.
    - minFreq: Minimum Frequency in MHz of the band of interest.
    - maxFreq: Maximum Frequency in MHz of the band of interest.
    - sys2detect: the system to detect.
    - sessionId: login Session ID.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK on success. Returns a JSON document with the path to the generated image of the spectrogram.
    - 403 Forbidden if the session ID was not found.
    - 404 Not found if the data was not found.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            util.debugPrint("SessionId not found")
            abort(403)
        minFreq = int(minFreq)
        maxFreq = int(maxFreq)
        return GetOneDayStats.getOneDayStats(sensorId,startTime,sys2detect,minFreq,maxFreq)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId, startTime, sys2detect,minFreq, maxFreq, sessionId):
    """

    Generate the single acquisiton spectrogram image for FFT-Power readings. The
    spectrogram is used by the GUI to put up an image of the spectrogram.
    This API also returns the occupancy array for the generated image.
    An image for the spectrogram is generated by the server and a path
    to that image is returned.  Times for this API are specified as the
    time in the UTC time domain (universal time not local time) as a second offset from
    1.1.1970:0:0:0 UTC time.

    URL Path:

        - sensorId is the sensor ID of interest.
        - startTime - the acquisition  time stamp  for the data message for FFT power.
        - sys2detect - the system to detect
        - minFreq - The minimum frequency of the frequency band of interest.
        - maxFreq - The maximum frequency of the frequency band of interest.
        - sessionId - Login session Id.

    HTTP Return codes:

       - 200 OK On Success this returns a JSON document containing the following information.
            - "spectrogram": File resource containing the generated spectrogram.
            - "cbar": path to the colorbar for the spectrogram.
            - "maxPower": Max power for the spectrogram
            - "minPower": Min power for the spectrogram.
            - "cutoff": Power cutoff for occupancy.
            - "noiseFloor" : Noise floor.
            - "maxFreq": max frequency for the spectrogram.
            - "minFreq": minFrequency for the spectrogram.
            - "minTime": min time for the spectrogram.
            - "timeDelta": Time delta for the spectrogram window.
            - "prevAcquisition" : Time of the previous acquistion (or -1 if no acquistion exists).
            - "nextAcquisition" : Time of the next acquistion (or -1 if no acquistion exists).
            - "formattedDate" : Formatted date for the aquisition.
            - "image_width": Image width of generated image (pixels).
            - "image_height": Image height of generated image (pixels).
            - "timeArray" : Time array for occupancy returned as offsets from the start time of the acquistion.
            - "occpancy" : Occupancy occupancy for each spectrum of the spectrogram. This is returned as a one dimensional array.
            Each occupancy point in the array corresponds to the time offset recorded in the time array.
       - 403 Forbidden if the session ID is not recognized.
       - 404 Not Found if the message for the given time is not found.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        startTimeInt = int(startTime)
        minfreq = int(minFreq)
        maxfreq = int(maxFreq)
        query = { SENSOR_ID: sensorId}
        msg = db.dataMessages.find_one(query)
        if msg == None:
            util.debugPrint("Sensor ID not found " + sensorId)
            abort(404)
        if msg["mType"] == "FFT-Power":
            query = { SENSOR_ID: sensorId, "t": startTimeInt, "freqRange": populate_db.freqRange(sys2detect,minfreq, maxfreq)}
            util.debugPrint(query)
            msg = db.dataMessages.find_one(query)
            if msg == None:
                errorStr = "Data message not found for " + startTime
                util.debugPrint(errorStr)
                response = make_response(util.formatError(errorStr), 404)
                return response
            result = GenerateSpectrogram.generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg, sessionId)
            if result == None:
                errorStr = "Illegal Request"
                response = make_response(util.formatError(errorStr), 400)
                return response
            else:
                return result
        else :
            util.debugPrint("Only FFT-Power type messages supported")
            errorStr = "Illegal Request"
            response = make_response(util.formatError(errorStr), 400)
            return response
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/generateSingleDaySpectrogramAndOccupancy/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleDaySpectrogram(sensorId, startTime, sys2detect, minFreq, maxFreq, sessionId):
    """

    Generate a single day spectrogram for Swept Frequency measurements as an image on the server.

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in UTC as a second offset from 1.1.1970:0:0:0 in the UTC time zone.
    - sys2detect : The system to detect.
    - minFreq: the min freq of the band of interest.
    - maxFreq: the max freq of the band of interest.
    - sessionId: The login session ID.

    URL Args:

    - subBandMinFreq : Sub band minimum frequency (should be contained in a frequency band supported by the sensor).
    - subBandMaxFreq : Sub band maximum frequency (should be contained in a frequency band supported by the sensor).

    HTTP Return Codes:

    - 403 Forbidden if the session ID is not found.
    - 200 OK if success. Returns a JSON document with a path to the generated spectrogram (which can be later used to access the image).

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        startTimeInt = int(startTime)
        minfreq = int(minFreq)
        maxfreq = int(maxFreq)
        print request
        subBandMinFreq = int(request.args.get("subBandMinFreq", minFreq))
        subBandMaxFreq = int(request.args.get("subBandMaxFreq", maxFreq))
        query = { SENSOR_ID: sensorId}
        msg = db.dataMessages.find_one(query)
        if msg == None:
            util.debugPrint("Sensor ID not found " + sensorId)
            abort(404)
            query = { SENSOR_ID: sensorId, "t":{"$gte" : startTimeInt}, "freqRange":populate_db.freqRange(sys2detect,minfreq, maxfreq)}
            util.debugPrint(query)
            msg = db.dataMessages.find_one(query)
            if msg == None:
                errorStr = "Data message not found for " + startTime
                util.debugPrint(errorStr)
                return make_response(util.formatError(errorStr), 404)
        if msg["mType"] == "Swept-frequency" :
            return GenerateSpectrogram.generateSingleDaySpectrogramAndOccupancyForSweptFrequency\
                    (msg, sessionId, startTimeInt,sys2detect,minfreq, maxfreq, subBandMinFreq, subBandMaxFreq)
        else:
            errorStr = "Illegal message type"
            util.debugPrint(errorStr)
            return make_response(util.formatError(errorStr), 400)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/spectrumbrowser/generateSpectrum/<sensorId>/<start>/<timeOffset>/<sessionId>", methods=["POST"])
def generateSpectrum(sensorId, start, timeOffset, sessionId):
    """

    Generate the spectrum image for a given start time and time offset from that start time.

    URL Path:

    - sensorId: Sensor ID of interest.
    - start: start time in the UTC time zone as an offset from 1.1.1970:0:0:0 UTC.
    - timeOffset: time offset from the start time in seconds.
    - sessionId: The session ID of the login session.

    URL Args: None

    HTTP return codes:
    - 403 Forbidden if the session ID is not recognized.
    - 200 OK if the request was successfully processed.
      Returns a JSON document with a URI to the generated image.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        startTime = int(start)
        # get the type of the measurement.
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId})
        if msg["mType"] == "FFT-Power":
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t":startTime})
            if msg == None:
                errorStr = "dataMessage not found "
                util.debugPrint(errorStr)
                abort(404)
            milisecOffset = int(timeOffset)
            return GenerateSpectrum.generateSpectrumForFFTPower(msg, milisecOffset, sessionId)
        else :
            secondOffset = int(timeOffset)
            time = secondOffset + startTime
            util.debugPrint("time " + str(time))
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t":{"$gte": time}})
            minFreq = int(request.args.get("subBandMinFrequency", msg["mPar"]["fStart"]))
            maxFreq = int(request.args.get("subBandMaxFrequency", msg["mPar"]["fStop"]))
            if msg == None:
                errorStr = "dataMessage not found "
                util.debugPrint(errorStr)
                abort(404)
            return GenerateSpectrum.generateSpectrumForSweptFrequency(msg, sessionId, minFreq, maxFreq)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/generateZipFileFileForDownload/<sensorId>/<startTime>/<days>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateZipFileForDownload(sensorId, startTime, days,sys2detect, minFreq, maxFreq, sessionId):
    """

    Generate a Zip file file for download.

    URL Path:

    - sensorId : The sensor ID of interest.
    - startTime : Start time as a second offset from 1.1.1970:0:0:0 UTC in the UTC time Zone.
    - sys2detect : The system to detect.
    - minFreq : Min freq of the band of interest.
    - maxFreq : Max Freq of the band of interest.
    - sessionId : Login session ID.

    URL Args:

    - None.

    HTTP Return Codes:

    - 200 OK successful execution. A JSON document containing a path to the generated Zip file is returned.
    - 403 Forbidden if the sessionId is invalid.
    - 404 Not found if the requested data was not found.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        return GenerateZipFileForDownload.generateZipFileForDownload(sensorId, startTime, days,sys2detect, minFreq, maxFreq, sessionId)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/emailDumpUrlToUser/<emailAddress>/<sessionId>", methods=["POST"])
def emailDumpUrlToUser(emailAddress, sessionId):
    """

    Send email to the given user when his requested dump file becomes available.

    URL Path:

    - emailAddress : The email address of the user.
    - sessionId : the login session Id of the user.

    URL Args (required):

    - urlPrefix : The url prefix that the web browser uses to access the data later (after the zip has been generated).
    - uri : The path used to access the zip file (previously returned from GenerateZipFileForDownload).

    HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        urlPrefix = request.args.get("urlPrefix", None)
        util.debugPrint(urlPrefix)
        uri = request.args.get("uri", None)
        util.debugPrint(uri)
        if urlPrefix == None or uri == None :
            abort(400)
        url = urlPrefix + uri
        return GenerateZipFileForDownload.emailDumpUrlToUser(emailAddress, url, uri)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/checkForDumpAvailability/<sessionId>", methods=["POST"])
def checkForDumpAvailability(sessionId):
    """

    Check for availability of a previously generated dump file.

    URL Path:

    - sessionId: The session ID of the login session.

    URL Args (required):

    - uri : A URI pointing to the generated file to check for.

    HTTP Return Codes:

    - 200 OK if success
      Returns a json document {status: OK} file exists.
      Returns a json document {status:NOT_FOUND} if the file does not exist.
    - 400 Bad request. If the URL args are not present.
    - 403 Forbidden if the sessionId is invalid.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        uri = request.args.get("uri", None)
        util.debugPrint(uri)
        if  uri == None :
            util.debugPrint("URI not specified.")
            abort(400)
        if  GenerateZipFileForDownload.checkForDumpAvailability(uri):
            return jsonify({"status":"OK"})
        else:
            return jsonify({"status":"NOT_FOUND"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@app.route("/spectrumbrowser/generatePowerVsTime/<sensorId>/<startTime>/<freq>/<sessionId>", methods=["POST"])
def generatePowerVsTime(sensorId, startTime, freq, sessionId):
    """

    URL Path:

    - sensorId : the sensor ID of interest.
    - startTime: The start time of the aquisition.
    - freq : The frequency of interest.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK. Returns a JSON document containing the path to the generated image.
    - 404 Not found. If the aquisition was not found.

    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId})
        if msg == None:
            util.debugPrint("Message not found")
            abort(404)
        if msg["mType"] == "FFT-Power":
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t":int(startTime)})
            if msg == None:
                errorMessage = "Message not found"
                util.debugPrint(errorMessage)
                abort(404)
            freqHz = int(freq)
            return GeneratePowerVsTime.generatePowerVsTimeForFFTPower(msg, freqHz, sessionId)
        else:
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t": {"$gt":int(startTime)}})
            if msg == None:
                errorMessage = "Message not found"
                util.debugPrint(errorMessage)
                abort(404)
            freqHz = int(freq)
            return GeneratePowerVsTime.generatePowerVsTimeForSweptFrequency(msg, freqHz, sessionId)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/getLastAcquisitionTime/<sensorId>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def getLastAcquisitionTime(sensorId,sys2detect,minFreq,maxFreq,sessionId):
    """
    get the timestamp of the last acquisition


    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        timeStamp = msgutils.getLastAcquisitonTimeStamp(sensorId,sys2detect,minFreq,maxFreq)
        return jsonify({"aquisitionTimeStamp": timeStamp})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@app.route("/spectrumbrowser/getLastSensorAcquisitionTimeStamp/<sensorId>/<sessionId>", methods=["POST"])
def getLastSensorAcquisitionTime(sensorId,sessionId):
    try: 
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        if not authentication.checkSessionId(sessionId):
            abort(403)
        timeStamp = msgutils.getLastSensorAcquisitionTimeStamp(sensorId)
        return jsonify({"aquisitionTimeStamp": timeStamp})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@app.route("/sensordata/getStreamingPort", methods=["POST"])
def getStreamingPorts():
    """
    Get a list of ports that sensors can use to stream data using TCP.
    """
    try:
        util.debugPrint("getStreamingPort")
        return DataStreaming.getSocketServerPort()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumdb/upload", methods=["POST"])
def upload() :
    """

    Upload sensor data to the database. The format is as follows:

        lengthOfDataMessageHeader<CRLF>DataMessageHeader Data

    Note that the data should immediately follow the DataMessage header (no space or CRLF).

    URL Path:

    - None

    URL Parameters:

    - None.

    Return Codes:

    - 200 OK if the data was successfully put into the MSOD database.
    - 403 Forbidden if the sensor key is not recognized.

    """
    try:
        msg = request.data
        sensorId = msg[SENSOR_ID]
        key = msg["SensorKey"]
        if not authentication.authenticateSensor(sensorId,key):
            abort(403)
        populate_db.put_message(msg)
        return "OK"
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@sockets.route("/sensordata", methods=["POST", "GET"])
def getSensorData(ws):
    try:
        DataStreaming.getSensorData(ws)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


@sockets.route("/spectrumdb/stream", methods=["POST"])
def datastream(ws):
    DataStreaming.dataStream(ws)


@app.route("/log", methods=["POST"])
def log():
    if debug:
        data = request.data
        jsonValue = json.loads(data)
        message = jsonValue["message"]
        print "Log Message : " + message
        exceptionInfo = jsonValue["ExceptionInfo"]
        if len(exceptionInfo) != 0 :
            print "Exception Info:"
            for i in range(0, len(exceptionInfo)):
                print "Exception Message:"
                exceptionMessage = exceptionInfo[i]["ExceptionMessage"]
                print "Stack Trace :"
                stackTrace = exceptionInfo[i]["StackTrace"]
                print exceptionMessage
                util.decodeStackTrace(stackTrace)
    return "OK"

# @app.route("/spectrumbrowser/login", methods=["POST"])
# def login() :
#    sessionId = random.randint(0,1000)
#    returnVal = {}
#    returnVal["status"] = "OK"
#    returnVal["sessionId"] = sessionId
#    secureSessions[request.remote_addr] = sessionId
#    return JSONEncoder().encode(returnVal)


if __name__ == '__main__':
    launchedFromMain = True
    util.loadGwtSymbolMap()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['CORS_HEADERS'] = 'Content-Type'
    # app.run('0.0.0.0',port=8000,debug="True")
    app.debug = True
    if Config.isConfigured():
        server = pywsgi.WSGIServer(('0.0.0.0', 8000), app, handler_class=WebSocketHandler)
    else:
        server = pywsgi.WSGIServer(('localhost', 8000), app, handler_class=WebSocketHandler)
    server.serve_forever()
