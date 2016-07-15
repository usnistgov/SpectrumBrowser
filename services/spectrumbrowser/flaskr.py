# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others.
#This software has been contributed to the public domain.
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain.
#As a result, a formal license is not needed to use this software.
#
#This software is provided "AS IS."
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.

import Bootstrap
Bootstrap.setPath()
from flask import Flask, request, abort, make_response, redirect
from flask import jsonify
from flask import render_template
import random
import json
import os
import matplotlib as mpl
mpl.use('Agg')
import urlparse
import sys
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
from flask_sockets import Sockets
import traceback
import GetLocationInfo
import GetDailyMaxMinMeanStats
import util
import GeneratePowerVsTime
import GenerateSpectrum
import GenerateSpectrogram
import GetDataSummary
import GetOneDayStats
import GetStreamingCaptureOccupancies
import msgutils
import SensorDb
import Config
import Bootstrap
import Log
import GetPeerSystemAndLocationInfo
import CaptureDb
from flask.ext.cors import CORS
from TestCaseDecorator import testcase
import DbCollections
from Defines import STATUS
from Defines import ERROR_MESSAGE
from Defines import FFT_POWER
from Defines import LAT
from Defines import LON
from Defines import ALT
from Defines import SENSOR_ID
from Defines import SWEPT_FREQUENCY
from Defines import TIME
from Defines import FREQ_RANGE
from Defines import PORT
from Defines import ENABLED
from Defines import OCCUPANCY_ALERT_PORT

from Defines import ONE_HOUR

from Defines import USER
import DebugFlags
import SessionLock

UNIT_TEST_DIR = "./unit-tests"

global launchedFromMain

Log.configureLogging("spectrumbrowser")

secureSessions = {}

launchedFromMain = False
app = Flask(__name__, static_url_path="")
app.static_folder = Bootstrap.getSpectrumBrowserHome() + "/flask/static"
app.template_folder = Bootstrap.getSpectrumBrowserHome() + "/flask/templates"
cors = CORS(app)
sockets = Sockets(app)
random.seed()

###############################################################################
# Note: This has to go here after the definition of some globals.
import AccountsCreateNewAccount
import AccountsChangePassword
import AccountsResetPassword
import authentication
import GenerateZipFileForDownload
import DataStreaming

DbCollections.initIndexes()
AccountsCreateNewAccount.startAccountScanner()
AccountsResetPassword.startAccountsResetPasswordScanner()
SessionLock.startSessionExpiredSessionScanner()
SensorDb.startSensorDbScanner()

Config.printConfig()

###############################################################################


def formatError(errorStr):
    return jsonify({"Error": errorStr})

###############################################################################


@app.route("/help/<path:path>", methods=["GET"])
@app.route("/api/<path:path>", methods=["GET"])
@app.route("/myicons/<path:path>", methods=["GET"])
@app.route("/spectrumbrowser/<path:path>", methods=["GET"])
def getFile(path):
    util.debugPrint("getFile()")
    p = urlparse.urlparse(request.url)
    urlpath = p.path
    util.debugPrint(urlpath)
    util.debugPrint(urlpath[1:])
    if DebugFlags.generateTestCase:
        pieces = urlpath.split("/")
        testFile = UNIT_TEST_DIR + "/unit-test.json"
        if pieces[1] == "generated":
            testMap = {}
            testMap["statusCode"] = 200
            testMap["httpRequestMethod"] = "GET"
            testMap["requestUrl"] = request.url
            toWrite = json.dumps(testMap, indent=4)
            if os.path.exists(testFile):
                f = open(testFile, "a+")
                f.write(",\n")
            else:
                f = open(testFile, "w+")
            f.write(toWrite)
            f.close()
    return app.send_static_file(urlpath[1:])


@app.route("/spectrumbrowser/isAuthenticationRequired", methods=['POST'])
def isAuthenticationRequired():
    @testcase
    def isAuthenticationRequiredWorker():
        """
        Return true if authentication is required.
        """
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if Config.isAuthenticationRequired():
                return jsonify({"AuthenticationRequired": True})
            else:
                return jsonify({"AuthenticationRequired": False,
                                "SessionToken":
                                authentication.generateGuestToken()})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return isAuthenticationRequiredWorker()


@app.route("/spectrumbrowser/checkSessionTimeout/<sessionId>",
           methods=['POST'])
def checkSessionTimeout(sessionId):
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)

        if not authentication.checkSessionId(
                sessionId, USER, updateSessionTimer=False):
            return jsonify({"status": "NOK"})
        else:
            return jsonify({"status": "OK"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


##################################################################################
# Return a customized help screen.
#
@app.route("/spectrumbrowser/getHelpPage", methods=["GET"])
def getHelpPage():
    return render_template('HelpTemplate.html',
                           adminName=Config.getAdminContactName(),
                           adminNumber=Config.getAdminContactNumber(),
                           adminEmail=Config.getSmtpEmail())


###################################################################################
# The admin clicks here (from link in an admin email address) when activating an account
# The email here is the users email, not the admin's email:
@app.route("/spectrumbrowser/authorizeAccount/<email>/<token>",
           methods=["GET"])
def authorizeAccount(email, token):
    """System admin can authorize an account (for accounts that do not end in
    .mil or .gov) which is currently stored in temp accounts.  After the admin
    authorizes the account, the user will have to click on a link in their
    email to activate their account which also ensures that their email is
    valid.

    URL Path:

    - email: user's email for denying the account.
    - token: token in temp accounts, one for each email.

    HTTP Returns:
        500 - System not configured.
        200 - Successful invocation.


    Example:

    """

    @testcase
    def authorizeAccountWorker(email, token):
        try:
            util.debugPrint("authorizeAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            if AccountsCreateNewAccount.authorizeAccount(
                    email.strip(), int(token), urlPrefix):
                return render_template(
                    'AccountTemplate.html',
                    string1="The user account was authorized and the user was sent an email message to active their account.",
                    string2="")
                # return app.send_static_file("account_authorized.html")
            else:
                return render_template(
                    'AccountTemplate.html',
                    string1="There was an error processing your request. Check the server logs.",
                    string2="")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return authorizeAccountWorker(email, token)


# The admin clicks here (from link in an admin email address) when denying an account
# The email here is the users email, not the admin's email:
@app.route("/spectrumbrowser/denyAccount/<email>/<token>", methods=["GET"])
def denyAccount(email, token):
    """
    System admin can deny an account (for accounts that do not end in .mil or .gov) which is currently stored in temp accounts.

    URL Path:

    - email: user's email for denying the account.
    - token: token in temp accounts, one for each email.

    """

    @testcase
    def denyAccountWorker(email, token):
        try:
            util.debugPrint("denyAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            if AccountsCreateNewAccount.denyAccount(email.strip(), int(token),
                                                    urlPrefix):
                return render_template(
                    'AccountTemplate.html',
                    string1="User account was denied and the user was sent an email message to inform them of the denial.",
                    string2="")
            else:
                return render_template(
                    'AccountTemplate.html',
                    string1="There was an error processing your request. Check the server logs.",
                    string2="")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return denyAccountWorker(email, token)


# The user clicks here (from link in an email address) when activating an account
# Look up the account to active based on email address and token - to make sure unique
@app.route("/spectrumbrowser/activateAccount/<email>/<token>", methods=["GET"])
def activateAccount(email, token):
    """
    Activate an account that is currently stored in temp accounts.

    URL Path:
    -email: user's email for activating account.
    - token: token in temp accounts, one for each email.
    """

    @testcase
    def activateAccountWorker(email, token):
        try:
            util.debugPrint("activateAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            if AccountsCreateNewAccount.activateAccount(email.strip(),
                                                        int(token)):
                return redirect(urlPrefix + "/spectrumbrowser")
            else:
                return render_template(
                    'AccountTemplate.html',
                    string1="Sorry, there was an issue creating your account.",
                    string2="Please contact your system administrator.")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return activateAccountWorker(email, token)


@app.route("/spectrumbrowser/requestNewAccount", methods=["POST"])
def requestNewAccount():
    """
    When a user requests a new account, if their email ends in .mil or .gov, we can create
    an account without an admin authorizing it and all we need to do is store the temp
    account and send the user an email to click on to activate the account.

    If their email does not end in .mil or .gov & no adminToken, we need to save the temp account,
    as "Waiting admin authorization" and send an email to the admin to authorize the account.
    If the admin authorizes the account creation, the temp account will change to
    "Waiting User Activation" and the
    user will need to click on a link in their email to activate their account.
    Otherwise, the system will send the user a "we regret to inform you..." email that their account
    was denied.

    URL Path:

    URL Args:
        JSON data structure of account info.

    """

    @testcase
    def requestNewAccountWorker():
        try:
            util.debugPrint("requestNewAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsCreateNewAccount.requestNewAccount(
                accountData, urlPrefix))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return requestNewAccountWorker()


@app.route("/spectrumbrowser/changePassword", methods=["POST"])
def changePassword():
    """
    Change to a new password and email user.

    URL Path:

    URL Args (required):
    - JSON structure of change password data

    Returns:
        200 OK if invocation OK.
        500 if server not configured.

    """

    @testcase
    def changePasswordWorker():
        try:
            util.debugPrint("changePassword")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsChangePassword.changePasswordEmailUser(
                accountData, urlPrefix))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace("Unexpected error:" + str(sys.exc_info()[0]))
            raise

    return changePasswordWorker()


# The user clicks here (from link in an email address) when resetting an account password
# Look up the password based on email address and token - to make sure unique
@app.route("/spectrumbrowser/resetPassword/<email>/<token>", methods=["GET"])
def resetPassword(email, token):
    """
    Store new password data and email user a url to click to reset their password.
    The email click ensures a valid user is resetting the password.

    URL Path:
    - email: user's email for resetting password.
    - token: token for resetting the password for the user

    """

    @testcase
    def resetPasswordWorker(email, token):
        try:
            util.debugPrint("resetPassword")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            if AccountsResetPassword.activatePassword(email.strip(),
                                                      int(token)):
                return render_template(
                    'AccountTemplate.html',
                    string1="Your password was successfully reset. You can log in here:",
                    string2=urlPrefix + "/spectrumbrowser")
            else:
                return render_template(
                    'AccountTemplate.html',
                    string1="Sorry, there was an issue resetting your account.",
                    string2="Please contact your system administrator.")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return resetPasswordWorker(email, token)


@app.route("/spectrumbrowser/requestNewPassword", methods=["POST"])
def requestNewPassword():
    """

    Send email to the user with a url link to reset their password to their newly specified value.

    URL Path:

    URL Args (required):
     - JSON structure of change password data
    """

    @testcase
    def requestNewPasswordWorker():
        try:
            util.debugPrint("request new Password")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            urlPrefix = Config.getDefaultPath()
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsResetPassword.storePasswordAndEmailUser(
                accountData, urlPrefix))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return requestNewPasswordWorker()


@app.route("/", methods=["GET"])
@app.route("/spectrumbrowser", methods=["GET"])
def userEntryPoint():
    util.debugPrint("root()")
    return app.send_static_file("app.html")


@app.route("/spectrumbrowser/authenticate", methods=['POST'])
def authenticate():
    """

    Authenticate the user given his username and password from the requested browser page or return
    an error if the user cannot be authenticated.

    URL Path:

    URL Args:

    - JSON data
    """

    @testcase
    def authenticateWorker():
        try:
            util.debugPrint("authenticate")
            p = urlparse.urlparse(request.url)
            urlpath = p.path
            if not Config.isConfigured() and urlpath[0] == "spectrumbrowser":
                util.debugPrint(
                    "attempt to access spectrumbrowser before configuration -- please configure")
                abort(500)
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(authentication.authenticateUser(accountData))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return authenticateWorker()


@app.route("/spectrumbrowser/logOut/<sessionId>", methods=['POST'])
# @testcase
def logOut(sessionId):
    """
    Log out of an existing session.

    URL Path:

        sessionId: The session ID to log out.

    """

    @testcase
    def logOutWorker(sessionId):
        try:
            authentication.logOut(sessionId)
            return jsonify({"status": "OK"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return logOutWorker(sessionId)


@app.route("/spectrumbrowser/getScreenConfig", methods=["POST"])
def getScreenConfig():
    """
    get screen configuration.

    URLPath:

        None

    Returns:

        JSON Document containing the screen configuration. This is used by the browser to
        configure the screen.

    """

    @testcase
    def getScreenConfigWorker():
        try:
            screenConfig = Config.getUserScreenConfig()
            if screenConfig is None:
                config = Config.getDefaultScreenConfig()
                return jsonify(config)
            else:
                return jsonify(screenConfig)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getScreenConfigWorker()


@app.route("/spectrumbrowser/getLocationInfo/<sessionId>", methods=["POST"])
def getLocationInfo(sessionId):
    """

    Get the location and system messages for all sensors.

    URL Path:

    - sessionid: The session ID for the login session.

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
                    ALT: 143.5,
                    LAT: 39.134374999999999,
                    LON: -77.215337000000005,
                    "Mobility": "Stationary",
                    "SensorID": "ECR16W4XS",
                    "TimeZone": "America/New_York",
                    "Type": "Loc"Type,
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
                Defines.CAL: "N/A",
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

    @testcase
    def getLocationInfoWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            peerSystemAndLocationInfo = GetPeerSystemAndLocationInfo.getPeerSystemAndLocationInfo(
            )
            retval = GetLocationInfo.getLocationInfo()
            retval["peers"] = peerSystemAndLocationInfo
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getLocationInfoWorker(sessionId)


@app.route(
    "/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<startTime>/<dayCount>/<sys2detect>/<fmin>/<fmax>/<sessionId>",
    methods=["POST"])
def getDailyMaxMinMeanStats(sensorId, startTime, dayCount, sys2detect, fmin,
                            fmax, sessionId):
    """

    Get the daily statistics for the given start time, frequency band and day count for a given sensor ID

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in the UTC time zone specified as a second offset from 1.1.1970:0:0:0 (UTC).
    - dayCount: The number days for which we want the statistics.
    - sessionId: The session ID of the login session.
    - fmin: min freq in MHz of the band of interest.
    - fmax: max freq in MHz of the band of interest.
    - sessionId: login session ID.

    URL args (optional):

    - subBandMinFreq: the min freq of the sub band of interest (contained within a band supported by the sensor).
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
        CHANNEL_COUNT: 56, # The number of channels
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

    @testcase
    def getDailyMaxMinMeanStatsWorker(sensorId, startTime, dayCount,
                                      sys2detect, fmin, fmax, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            util.debugPrint("getDailyMaxMinMeanStats: " + sensorId + " " +
                            startTime + " " + dayCount)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            subBandMinFreq = int(request.args.get("subBandMinFreq", fmin))
            subBandMaxFreq = int(request.args.get("subBandMaxFreq", fmax))
            return jsonify(GetDailyMaxMinMeanStats.getDailyMaxMinMeanStats(
                sensorId, startTime, dayCount, sys2detect, fmin, fmax,
                subBandMinFreq, subBandMaxFreq, sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise

    return getDailyMaxMinMeanStatsWorker(sensorId, startTime, dayCount,
                                         sys2detect, fmin, fmax, sessionId)


@app.route(
    "/spectrumbrowser/getAcquisitionCount/<sensorId>/<sys2detect>/<fstart>/<fstop>/<tstart>/<daycount>/<sessionId>",
    methods=["POST"])
def getAcquisitionCount(sensorId, sys2detect, fstart, fstop, tstart, daycount,
                        sessionId):
    """

    Get the acquistion count from a sensor given the start date and day count.

    URL Path:
        - sensorId: the sensor Id of interest
        - sys2detect: the system to detect
        - fstart: The start frequency
        - fstop: The end frequency
        - tstart: The acquistion start time
        - daycount: the number of days
    """

    @testcase
    def getAcquisitionCountWorker(sensorId, sys2detect, fstart, fstop, tstart,
                                  daycount, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)

            return jsonify(GetDataSummary.getAcquistionCount(sensorId, sys2detect,
                           int(fstart), int(fstop), int(tstart), int(daycount)))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getAcquisitionCountWorker(sensorId, sys2detect, fstart, fstop,
                                     tstart, daycount, sessionId)


@app.route(
    "/spectrumbrowser/getDataSummary/<sensorId>/<lat>/<lon>/<alt>/<sessionId>",
    methods=["POST"])
def getDataSummary(sensorId, lat, lon, alt, sessionId):
    """

    Get the sensor data summary  for the sensor given its ID, latitude and longitude.

    URL Path:

    - sensorId: Sensor ID of interest.
    - lat: Latitude
    - lon: Longitude
    - alt: Altitude
    - sessionId: Login session ID

    URL args (optional):

    - minFreq: Min band frequency of a band supported by the sensor.
            if this parameter is not specified then the min freq of the sensor is used.
    - maxFreq: Max band frequency of a band supported by the sensor.
            If this parameter is not specified, then the max freq of the sensor is used.
    - minTime: Universal start time (seconds) of the interval we are
            interested in. If this parameter is not specified, then the acquisition
            start time is used.
    - sys2detect: The system to detect
    - dayCount: The number of days for which we want the data. If this
            parameter is not specified, then the interval from minTime to the end of the
            available data is used.

    HTTP return codes:

    - 200 OK Success. Returns a JSON document with a summary of the available
    data in the time range and frequency band of interest.
    Here is an example Request using the unix curl command:

   ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDataSummary/Cotton1/40/-105.26/1676/guest-123

    Here is an example of the JSON document (annotated) returned in response:

   ::

        {
          "maxFreq": 2899500000, # max Freq the band of interest for the sensor (hz)
                                 #for period of interest
          "minFreq": 2700500000, # min freq of the band of interest for  sensor (hz)
                                 #for period of interest
          "maxOccupancy": 1.0, # max occupancy for the results of the query for period of interest
          "meanOccupancy": 0.074, # Mean Occupancy for the results of the query for period of interest
          "minOccupancy": 0.015, # Min occupancy for the results of the query for period of interest
          "measurementType": SWEPT_FREQUENCY,# Measurement type
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

    @testcase
    def getDataSummaryWorker(sensorId, lat, lon, alt, sessionId):
        util.debugPrint("getDataSummary")
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                util.debugPrint("SessionId not found")
                abort(403)
            longitude = float(lon)
            latitude = float(lat)
            alt = float(alt)
            locationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:sensorId,
                                                                            LON:longitude, LAT:latitude, ALT:alt})
            if locationMessage is None:
                util.debugPrint("Location Message not found")
                return jsonify({STATUS: "NOK",
                                ERROR_MESSAGE: "Location Message Not Found"})
            tmin = request.args.get('minTime', None)
            dayCount = request.args.get('dayCount', None)
            return jsonify(GetDataSummary.getDataSummary(sensorId,
                                                         locationMessage,
                                                         tmin=tmin,
                                                         dayCount=dayCount))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getDataSummaryWorker(sensorId, lat, lon, alt, sessionId)


@app.route(
    "/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>",
    methods=["POST"])
def getOneDayStats(sensorId, startTime, sys2detect, minFreq, maxFreq,
                   sessionId):
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

    @testcase
    def getOneDayStatsWorker(sensorId, startTime, sys2detect, minFreq, maxFreq,
                             sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                util.debugPrint("SessionId not found")
                abort(403)
            minFreq = int(minFreq)
            maxFreq = int(maxFreq)
            return jsonify(GetOneDayStats.getOneDayStats(
                sensorId, startTime, sys2detect, minFreq, maxFreq))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getOneDayStatsWorker(sensorId, startTime, sys2detect, minFreq,
                                maxFreq, sessionId)


@app.route(
    "/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>",
    methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId, startTime, sys2detect,
                                         minFreq, maxFreq, sessionId):
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
            - "noiseFloor": Noise floor.
            - "maxFreq": max frequency for the spectrogram.
            - "minFreq": minFrequency for the spectrogram.
            - "minTime": min time for the spectrogram.
            - "timeDelta": Time delta for the spectrogram window.
            - "prevAcquisition": Time of the previous acquistion (or -1 if no acquistion exists).
            - "nextAcquisition": Time of the next acquistion (or -1 if no acquistion exists).
            - "formattedDate": Formatted date for the aquisition.
            - "image_width": Image width of generated image (pixels).
            - "image_height": Image height of generated image (pixels).
            - "timeArray": Time array for occupancy returned as offsets from the start time of the acquistion.
            - "occpancy": Occupancy occupancy for each spectrum of the spectrogram. This is returned as a one dimensional array.
            Each occupancy point in the array corresponds to the time offset recorded in the time array.
       - 403 Forbidden if the session ID is not recognized.
       - 404 Not Found if the message for the given time is not found.

    """

    @testcase
    def generateSingleAcquisitionSpectrogramWorker(
            sensorId, startTime, sys2detect, minFreq, maxFreq, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            startTimeInt = int(startTime)
            minfreq = int(minFreq)
            maxfreq = int(maxFreq)
            query = {SENSOR_ID: sensorId}

            msg = DbCollections.getDataMessages(sensorId).find_one(query)
            cutoff = request.args.get("cutoff")
            leftBound = float(request.args.get("leftBound", 0))
            rightBound = float(request.args.get("rightBound", 0))
            if msg is None or msg["mType"] != FFT_POWER:
                util.debugPrint("Illegal request " + sensorId)
                abort(404)
            return jsonify(GenerateSpectrogram.generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(sensorId, sessionId, cutoff,
                                                                                                           startTimeInt, minfreq, maxfreq,
                                                                                                           leftBound, rightBound))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return generateSingleAcquisitionSpectrogramWorker(
        sensorId, startTime, sys2detect, minFreq, maxFreq, sessionId)


@app.route(
    "/spectrumbrowser/generateSingleDaySpectrogramAndOccupancy/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>",
    methods=["POST"])
def generateSingleDaySpectrogram(sensorId, startTime, sys2detect, minFreq,
                                 maxFreq, sessionId):
    """

    Generate a single day spectrogram for Swept Frequency measurements as an image on the server.

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in UTC as a second offset from 1.1.1970:0:0:0 in the UTC time zone.
    - sys2detect: The system to detect.
    - minFreq: the min freq of the band of interest.
    - maxFreq: the max freq of the band of interest.
    - sessionId: The login session ID.

    URL Args:

    - subBandMinFreq: Sub band minimum frequency (should be contained in a frequency band supported by the sensor).
    - subBandMaxFreq: Sub band maximum frequency (should be contained in a frequency band supported by the sensor).

    HTTP Return Codes:

    - 403 Forbidden if the session ID is not found.
    - 200 OK if success. Returns a JSON document with a path to the generated spectrogram (which can be later used to access the image).

    """

    @testcase
    def generateSingleDaySpectrogramWorker(sensorId, startTime, sys2detect,
                                           minFreq, maxFreq, sessionId):
        try:
            util.debugPrint("generateSingleDaySpectrogram")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            startTimeInt = int(startTime)
            minfreq = int(minFreq)
            maxfreq = int(maxFreq)
            subBandMinFreq = int(request.args.get("subBandMinFreq", minFreq))
            subBandMaxFreq = int(request.args.get("subBandMaxFreq", maxFreq))
            query = {SENSOR_ID: sensorId}
            msg = DbCollections.getDataMessages(sensorId).find_one(query)
            if msg is None:
                util.debugPrint("Sensor ID not found " + sensorId)
                abort(404)
                query = {SENSOR_ID: sensorId,
                         TIME: {"$gte": startTimeInt},
                         FREQ_RANGE:
                         msgutils.freqRange(sys2detect, minfreq, maxfreq)}
                util.debugPrint(query)
                msg = DbCollections.getDataMessages(sensorId).find_one(query)
                if msg is None:
                    errorStr = "Data message not found for " + startTime
                    util.debugPrint(errorStr)
                    return make_response(formatError(errorStr), 404)
            if msg["mType"] == SWEPT_FREQUENCY:
                cutoff = request.args.get("cutoff", None)
                return jsonify(GenerateSpectrogram.generateSingleDaySpectrogramAndOccupancyForSweptFrequency
                               (msg, sessionId, startTimeInt, sys2detect, minfreq, maxfreq, subBandMinFreq, subBandMaxFreq, cutoff))
            else:
                errorStr = "Illegal message type"
                util.debugPrint(errorStr)
                return make_response(formatError(errorStr), 400)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return generateSingleDaySpectrogramWorker(sensorId, startTime, sys2detect,
                                              minFreq, maxFreq, sessionId)


@app.route(
    "/spectrumbrowser/generateSpectrum/<sensorId>/<start>/<timeOffset>/<sessionId>",
    methods=["POST"])
# @testcase
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

    @testcase
    def generateSpectrumWorker(sensorId, start, timeOffset, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            startTime = int(start)
            # get the type of the measurement.
            msg = DbCollections.getDataMessages(sensorId).find_one(
                {SENSOR_ID: sensorId})
            if msg["mType"] == FFT_POWER:
                msg = DbCollections.getDataMessages(sensorId).find_one(
                    {SENSOR_ID: sensorId,
                     "t": startTime})
                if msg is None:
                    errorStr = "dataMessage not found "
                    util.debugPrint(errorStr)
                    abort(404)
                milisecOffset = int(timeOffset)
                return jsonify(GenerateSpectrum.generateSpectrumForFFTPower(
                    msg, milisecOffset, sessionId))
            else:
                secondOffset = int(timeOffset)
                time = secondOffset + startTime
                util.debugPrint("time " + str(time))
                msg = DbCollections.getDataMessages(sensorId).find_one(
                    {SENSOR_ID: sensorId,
                     TIME: {"$gte": time}})
                minFreq = int(request.args.get("subBandMinFrequency", msg[
                    "mPar"]["fStart"]))
                maxFreq = int(request.args.get("subBandMaxFrequency", msg[
                    "mPar"]["fStop"]))
                if msg is None:
                    errorStr = "dataMessage not found "
                    util.debugPrint(errorStr)
                    abort(404)
                return jsonify(
                    GenerateSpectrum.generateSpectrumForSweptFrequency(
                        msg, sessionId, minFreq, maxFreq))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return generateSpectrumWorker(sensorId, start, timeOffset, sessionId)


@app.route(
    "/spectrumbrowser/generateZipFileFileForDownload/<sensorId>/<startTime>/<days>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>",
    methods=["POST"])
# @testcase
def generateZipFileForDownload(sensorId, startTime, days, sys2detect, minFreq,
                               maxFreq, sessionId):
    """

    Generate a Zip file file for download.

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: Start time as a second offset from 1.1.1970:0:0:0 UTC in the UTC time Zone.
    - sys2detect: The system to detect.
    - minFreq: Min freq of the band of interest.
    - maxFreq: Max Freq of the band of interest.
    - sessionId: Login session ID.

    URL Args:

    - None.

    HTTP Return Codes:

    - 200 OK successful execution. A JSON document containing a path to the generated Zip file is returned.
    - 403 Forbidden if the sessionId is invalid.
    - 404 Not found if the requested data was not found.

    """

    @testcase
    def generateZipFileForDownloadWorker(sensorId, startTime, days, sys2detect,
                                         minFreq, maxFreq, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            return GenerateZipFileForDownload.generateZipFileForDownload(
                sensorId, startTime, days, sys2detect, minFreq, maxFreq,
                sessionId)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return jsonify(generateZipFileForDownloadWorker(
        sensorId, startTime, days, sys2detect, minFreq, maxFreq, sessionId))


@app.route("/spectrumbrowser/emailDumpUrlToUser/<emailAddress>/<sessionId>",
           methods=["POST"])
def emailDumpUrlToUser(emailAddress, sessionId):
    """

    Send email to the given user when his requested dump file becomes available.

    URL Path:

    - emailAddress: The email address of the user.
    - sessionId: the login session Id of the user.

    URL Args (required):

    - urlPrefix: The url prefix that the web browser uses to access the data later (after the zip has been generated).
    - uri: The path used to access the zip file (previously returned from GenerateZipFileForDownload).

    HTTP Return Codes:

    - 200 OK: if the request successfully completed.
    - 403 Forbidden: Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """

    @testcase
    def emailDumpUrlToUserWorker(emailAddress, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            uri = request.args.get("uri", None)
            util.debugPrint(uri)
            if uri is None:
                util.debugPrint("UrI not specified")
                abort(400)
            url = Config.getGeneratedDataPath() + "/" + uri
            return jsonify(GenerateZipFileForDownload.emailDumpUrlToUser(
                emailAddress, url, uri))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return emailDumpUrlToUserWorker(emailAddress, sessionId)


@app.route("/spectrumbrowser/checkForDumpAvailability/<sessionId>",
           methods=["POST"])
def checkForDumpAvailability(sessionId):
    """

    Check for availability of a previously generated dump file.

    URL Path:

    - sessionId: The session ID of the login session.

    URL Args (required):

    - uri: A URI pointing to the generated file to check for.

    HTTP Return Codes:

    - 200 OK if success
      Returns a json document {status: OK} file exists.
      Returns a json document {status:NOT_FOUND} if the file does not exist.
    - 400 Bad request. If the URL args are not present.
    - 403 Forbidden if the sessionId is invalid.

    """

    @testcase
    def checkForDumpAvailabilityWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            uri = request.args.get("uri", None)
            util.debugPrint(uri)
            if uri is None:
                util.debugPrint("URI not specified.")
                abort(400)
            if GenerateZipFileForDownload.checkForDumpAvailability(uri):
                return jsonify({"status": "OK"})
            else:
                return jsonify({"status": "NOT_FOUND"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return checkForDumpAvailabilityWorker(sessionId)


@app.route(
    "/spectrumbrowser/generatePowerVsTime/<sensorId>/<startTime>/<freq>/<sessionId>",
    methods=["POST"])
def generatePowerVsTime(sensorId, startTime, freq, sessionId):
    """

    URL Path:

    - sensorId: the sensor ID of interest.
    - startTime: The start time of the aquisition.
    - freq: The frequency of interest.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK. Returns a JSON document containing the path to the generated image.
    - 403 Forbidden if the session was not recognized.
    - 404 Not found. If the aquisition was not found.

    """

    @testcase
    def generatePowerVsTimeWorker(sensorId, startTime, freq, sessionId):

        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            msg = DbCollections.getDataMessages(sensorId).find_one(
                {SENSOR_ID: sensorId})
            if msg is None:
                util.debugPrint("Message not found")
                abort(404)
            leftBound = float(request.args.get("leftBound", 0))
            rightBound = float(request.args.get("rightBound", 0))
            if leftBound < 0 or rightBound < 0:
                util.debugPrint("Bounds to exlude must be >= 0")
                abort(400)
            if msg["mType"] == FFT_POWER:
                freqHz = int(freq)
                return jsonify(
                    GeneratePowerVsTime.generatePowerVsTimeForFFTPower(
                        sensorId, int(startTime), leftBound, rightBound,
                        freqHz, sessionId))
            else:
                freqHz = int(freq)
                return jsonify(
                    GeneratePowerVsTime.generatePowerVsTimeForSweptFrequency(
                        sensorId, int(startTime), freqHz, sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return generatePowerVsTimeWorker(sensorId, startTime, freq, sessionId)


@app.route(
    "/spectrumbrowser/getLastAcquisitionTime/<sensorId>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>",
    methods=["POST"])
def getLastAcquisitionTime(sensorId, sys2detect, minFreq, maxFreq, sessionId):
    @testcase
    def getAcquisitionTimeWorker(sensorId, sys2detect, minFreq, maxFreq,
                                 sessionId):
        """
        get the timestamp of the last acquisition

        URL Path:

        - sensorId: sensor ID.
        - sys2deect: system to detect (eg. LTE)
        - minFreq: mininum frequency of detected band.
        - maxFreq: maximun frequency of detected band.
        - sessionId: session ID.



        HTTP Return Codes:

        - 200 OK if success
                Returns a json document with last acquisition timestamp. Format of returned document is
                {"aquisitionTimeStamp": timeStamp}
        - 500 Bad request. If system is not configured.
        - 403 Forbidden if the sessionId is invalid.

        Example:

       ::

                curl -k -X POST https://129.6.142.157/spectrumbrowser/getLastAcquisitionTime/E6R16W5XS/LTE/703970000/714050000/user-144786761953592438983

       ::

        Returns

       ::

                { "aquisitionTimeStamp": 1446590404 }
       ::


        """
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            timeStamp = msgutils.getLastAcquisitonTimeStamp(
                sensorId, sys2detect, minFreq, maxFreq)
            return jsonify({"aquisitionTimeStamp": timeStamp})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getAcquisitionTimeWorker(sensorId, sys2detect, minFreq, maxFreq,
                                    sessionId)


@app.route(
    "/spectrumbrowser/getLastSensorAcquisitionTimeStamp/<sensorId>/<sessionId>",
    methods=["POST"])
def getLastSensorAcquisitionTime(sensorId, sessionId):
    """
    Get the last sensor acquisition timestamp.

    URL Path:

        - sensorId: sensor ID.
        - sessionId: session ID.



    HTTP Return Codes:

    - 200 OK if success
         Returns a json document with last acquisition timestamp. Format of returned document is
         {"aquisitionTimeStamp": timeStamp}
    - 500 Bad request. If system is not configured.
    - 403 Forbidden if the sessionId is invalid.

    Example:

   ::

        curl -X POST http://localhost:8000/spectrumbrowser/getLastSensorAcquisitionTimeStamp/ECR16W4XS/user-123

   ::

    Returns

   ::

        { "aquisitionTimeStamp": 1405359391 }

   ::

    """

    @testcase
    def getLastSensorAcquisitionTimeWorker(sensorId, sessionId):
        try:
            util.debugPrint("getLastSensorAcquisitionTimeWorker: sensorId " +
                            sensorId + " sessionId " + sessionId)
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            timeStamp = msgutils.getLastSensorAcquisitionTimeStamp(sensorId)
            return jsonify({"aquisitionTimeStamp": timeStamp})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getLastSensorAcquisitionTimeWorker(sensorId, sessionId)


@app.route(
    "/spectrumbrowser/getCaptureEvents/<sensorId>/<startDate>/<dayCount>/<sessionId>",
    methods=["POST"])
def getCaptureEventList(sensorId, startDate, dayCount, sessionId):
    """

    Return a list of all capture events associated with this sensor.

    URL Path:

        - sensorId: sensor ID.
        - sessionId:  session ID.

    HTTP Return Codes:

    - 200 OK if success
      Returns a json document with list of all capture event details.  List may be empty.
    - 500 Bad request. If system is not configured.
    - 403 Forbidden if the sessionId is invalid.

    """

    @testcase
    def getCaptureEventListWorker(sensorId, startDate, dayCount, sessionId):
        try:
            util.debugPrint("getCaptureEventListWorker: " + sensorId + "/" +
                            str(startDate) + "/" + str(dayCount))
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)

            if not authentication.checkSessionId(sessionId, USER):
                util.debugPrint("getCaptureEvents: failed authentication")
                abort(403)
            try:
                sdate = int(startDate)
                dcount = int(dayCount)
            except ValueError:
                abort(400)
            if sdate < 0 or dcount < 0:
                abort(400)
            return jsonify(CaptureDb.getEvents(sensorId, sdate, dcount))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getCaptureEventListWorker(sensorId, startDate, dayCount, sessionId)

##########################################################################################


@app.route(
    "/spectrumbrowser/getOccupancies/<sensorId>/<sys2detect>/<minFreq>/<maxFreq>/<startTime>/<seconds>/<sessionId>",
    methods=["POST"])
def getOccupancies(sensorId, sys2detect, minFreq, maxFreq, startTime, seconds,
                   sessionId):
    """
    get the occupancies for a given sensor and frequency band in a given range of time.

    URL Path:

        - sensorId: sensorId
        - sys2detect: system to detect (eg. LTE)
        - minFreq: start of frequency range.
        - maxFreq: stop of frequency range.
        - startTime: absolute start time.
        - seconds: Interval
        - sessionId: Browser session ID.

    URL Parameters:

        - None.

   HTTP Return Codes:

        200 - OK if successful.
                Returns a document containing a URLs to the generated occupancies and a time array
                indicating the time offset from the query start time.
        403 - authentication failure.


    """

    @testcase
    def getOccupanciesWorker(sensorId, sys2detect, minFreq, maxFreq, startTime,
                             seconds, sessionId):
        """
        get the captured streaming occupancies for a given sensor ID and system to detect, in a given frequency range
        for a given start time and interval.
        """
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            return jsonify(GetStreamingCaptureOccupancies.getOccupancies(
                sensorId, sys2detect, int(minFreq), int(maxFreq), int(
                    startTime), int(seconds), sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getOccupanciesWorker(sensorId, sys2detect, minFreq, maxFreq,
                                startTime, seconds, sessionId)


@app.route(
    "/spectrumbrowser/getSpectrums/<sensorId>/<sys2detect>/<minFreq>/<maxFreq>/<startTime>/<seconds>/<sessionId>",
    methods=["POST"])
def getSpectrums(sensorId, sys2detect, minFreq, maxFreq, startTime, seconds,
                 sessionId):
    """
    get the captured streaming occupancies for a given sensor ID and system to detect, in a given frequency range
    for a given start time and interval. This can be used for offline analysis of the captured spectrum.

    URL Parameters:

        - sensorId: Sensor ID
        - sys2detect: system to detect.
        - minFreq: min band band frequency
        - maxFreq: max band frequency
        - startTime: start time ( absolute UTC)
        - seconds: Duration
        - sessionId: login session Id


    Example:

   ::

        curl -X POST http://localhost:8000/spectrumdb/getSpectrums/E6R16W5XS/LTE/703970000/714050000/1433875348/100/user-123

   ::

    Returns:

   ::

        {
          "status": "OK",
          "power": "https://localhost:8443/spectrumbrowser/generated/user-123/E6R16W5XS:LTE:703970000:714050000.power.1433875348-100.txt",
          "time": "https://localhost:8443/spectrumbrowser/generated/user-123/E6R16W5XS:LTE:703970000:714050000.power.time.1433875348-100.txt"
        }

   ::

    You can fetch the power and time arrays using HTTP GET i.e.:

   ::

       curl -k -X GET "https://localhost:8443/spectrumbrowser/generated/user-123/E6R16W5XS:LTE:703970000:714050000.power.1433875348-100.txt"

   ::

    The power array is where you find the power values.
    The time array is where you find the corresponding time value offsets (seconds from startTime).
    Each row of the power array is a power sepctrum (dBm).

    """

    @testcase
    def getSpectrumsWorker(sensorId, sys2detect, minFreq, maxFreq, startTime,
                           seconds, sessionId):

        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            return jsonify(GetStreamingCaptureOccupancies.getPowers(
                sensorId, sys2detect, int(minFreq), int(maxFreq), int(
                    startTime), int(seconds), sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getSpectrumsWorker(sensorId, sys2detect, minFreq, maxFreq,
                              startTime, seconds, sessionId)


@app.route(
    "/spectrumdb/getOccupanciesByDate/<sensorId>/<sys2detect>/<minFreq>/<maxFreq>/<startDate>/<timeOfDay>/<seconds>/<sessionId>",
    methods=["POST"])
def getOccupanciesByDate(sensorId, sys2detect, minFreq, maxFreq, startDate,
                         timeOfDay, seconds, sessionId):
    """
    get the captured streaming occupancies for a given sensor ID and system to detect, in a given frequency range
    for a given start time and interval.

    URL Path:

        - sensorId: sensor ID
        - minFreq: minimum freq of band of interest (Hz).
        - maxFreq: maximum freq of band of interest.
        - startDate: start date.
        - timeOfDay: time offset in seconds since start date.
        - seconds: period for which data is needed.
        - sessionId: browser session ID.


    """

    @testcase
    def getOccupanciesByDateWorker(sensorId, sys2detect, minFreq, maxFreq,
                                   startDate, timeOfDay, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId, USER):
                abort(403)
            if seconds > ONE_HOUR * 24:
                util.debugPrint("Interval is too long")
                abort(400)
            return jsonify(GetStreamingCaptureOccupancies.getOccupanciesByDate(
                sensorId, sys2detect, minFreq, maxFreq, startDate, timeOfDay,
                seconds, sessionId))

        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getOccupanciesByDateWorker(sensorId, sys2detect, minFreq, maxFreq,
                                      startDate, timeOfDay, seconds, sessionId)

#==============================================================================================


@app.route("/sensordata/getStreamingPort/<sensorId>", methods=["POST"])
def getStreamingPort(sensorId):
    """
    Get a port that sensor can use to stream data using TCP. This API is not authenticated.

    URL Path:

        - sensorId: the sensor ID for which the streaming port is being queried.

    HTTP Return Codes:

        - 200 OK if invocation successful. A JSON Document containing the port is returned.
        - 500 if Server not configured.
        - 404 Not found if sensor is not found.

    Example:

   ::

        curl -k -X POST https://129.6.142.143/sensordata/getStreamingPort/E6R16W5XS

   ::

    Returns the following json document:

   ::

       {
         "port": 9000
       }

   ::

    """

    @testcase
    def getStreamingPortWorker(sensorId):
        try:
            util.debugPrint("getStreamingPort: " + sensorId)
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            sensor = SensorDb.getSensorObj(sensorId)
            if sensor is None:
                util.debugPrint("Sensor " + sensorId + " not found")
                abort(404)
            return jsonify(DataStreaming.getSocketServerPort(sensorId))
        except:
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getStreamingPortWorker(sensorId)


@app.route("/sensordata/getMonitoringPort/<sensorId>", methods=["POST"])
def getMonitoringPort(sensorId):
    """
    Get port to the spectrum monitor to register for alerts.

    URL Parameters:

        - sensorId: sensor ID.

    HTTP Return Codes:

        - 200 OK  - successful invocation. The returned JSON document contains
                the monitoring port for the sensor.
        - 404 - If sensor is not found.
        - 500 - if server is not configured.
    """

    @testcase
    def getMonitoringPortWorker(sensorId):
        try:
            util.debugPrint("getSpectrumMonitorPort")
            retval = {}
            sensor = SensorDb.getSensorObj(sensorId)

            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)

            if sensor is None:
                abort(404)
            if sensor.getSensorStatus() != ENABLED:
                retval[PORT] = -1
            else:
                retval[PORT] = OCCUPANCY_ALERT_PORT
            return jsonify(retval)
        except:
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getMonitoringPortWorker(sensorId)

#==========================================================================


@sockets.route("/sensordata", methods=["POST", "GET"])
def getSensorData(ws):
    """
    Web-browser websocket connection handler.
    """
    util.debugPrint("getSensorData")
    try:
        DataStreaming.getSensorData(ws)
    except:
        util.logStackTrace(sys.exc_info())
        traceback.print_exc()
        raise


#==========================================================================
# Configuration information query.
#==========================================================================
@app.route("/sensordb/getSensorConfig/<sensorId>", methods=["POST"])
def getSensorConfig(sensorId):
    """
    getSensorConfig - get the sensor configuration. The sensor issues this request
    to get the configuration information. No authentication is required for this request.

    URL Path:

        - sensorId: The sensor ID for which the configuration is desired.

   HTTP Return Codes:

        - 200 OK if successful. Configuration is returned as a json document.
        - 500 if server not configured.
        - 404 if sensor not found.

    """

    @testcase
    def getSensorConfigWorker(sensorId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            util.debugPrint("getSensorConfig: " + sensorId)
            sensor = SensorDb.getSensorObj(sensorId)
            if sensor is None:
                util.debugPrint("Sensor " + sensorId + " not found")
                abort(404)
            return jsonify(SensorDb.getSensorConfig(sensorId))
        except:
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise

    return getSensorConfigWorker(sensorId)


@app.route("/sensordb/postError/<sensorId>", methods=["POST"])
def reportConfigError(sensorId):
    """
    report a configuration error detected at the sensor.
    The error message has the following format:

   ::

        { "SensorKey": "SensorKey",
          "ErrorMessage": "Client detected error message"
        }

   ::

    """
    errorMsg = request.data
    return jsonify(SensorDb.postError(sensorId, errorMsg))


@app.route("/spectrumbrowser/log/<sessionId>", methods=["POST"])
def log(sessionId):
    if not authentication.checkSessionId(
            sessionId, USER, updateSessionTimer=False):
        abort(403)
    return Log.log()


#=====================================================================
# For debugging.
#=====================================================================
@app.route("/getDebugFlags", methods=["POST"])
def getDebugFlags():
    retval = {}
    # debug = True
    retval["debug"] = DebugFlags.getDebugFlag()
    retval["disableSessionIdCheck"] = DebugFlags.getDisableSessionIdCheckFlag()
    retval["generateTestCase"] = DebugFlags.getGenerateTestCaseFlag()
    retval["debugRelaxedPasswords"] = DebugFlags.getDebugRelaxedPasswordsFlag()
    retval["disableAuthentication"] = DebugFlags.getDisableAuthenticationFlag()
    return jsonify(retval)


if __name__ == '__main__':
    launchedFromMain = True
    Log.loadGwtSymbolMap()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['CORS_HEADERS'] = 'Content-Type'
    # app.run('0.0.0.0',port=8000,debug="True")
    app.debug = True
    server = pywsgi.WSGIServer(('localhost', 8000),
                               app,
                               handler_class=WebSocketHandler)
    server.serve_forever()
