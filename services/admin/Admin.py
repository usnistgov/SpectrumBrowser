#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 Untied States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.
'''
Created on Jun 3, 2015

All the admin methods go in here.

@author: local
'''

import Bootstrap
sbHome = Bootstrap.getSpectrumBrowserHome()

import sys
sys.path.append(sbHome + "/services/common")
sys.path.append(sbHome + "/services/admin")

from flask import Flask, request, abort, make_response
from flask import jsonify
from TestCaseDecorator import testcase
import random
import json
import authentication
import urlparse
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
from flask_sockets import Sockets
import traceback
import util
import GarbageCollect
from GarbageCollect import RepeatingTimer
import SensorDb
from Sensor import Sensor
import Config
import Log
import AccountsManagement
import AccountsChangePassword
import GenerateZipFileForDownload
from Defines import STATUS
from Defines import ADMIN
from Defines import OK
import SessionLock
import argparse
import ResourceDataStreaming
import DataStreamSharedState
import CaptureDb
import RecomputeOccupancies
import logging
import pwd
import os
import DbCollections
from multiprocessing import Process

UNIT_TEST_DIR = "./unit-tests"

global launchedFromMain

if not Config.isConfigured():
    print "Please configure system using admin interface"

# sessions = {}
secureSessions = {}
gwtSymbolMap = {}

launchedFromMain = False
app = Flask(__name__, static_url_path="")
app.static_folder = sbHome + "/flask/static"
app.template_folder = sbHome + "/flask/templates"
sockets = Sockets(app)
random.seed()


@sockets.route("/admin/sysmonitor", methods=["GET"])
def getResourceData(ws):
    """
    Web-browser websocket connection handler.
    """
    util.debugPrint("getResourceData")
    try:
        ResourceDataStreaming.getResourceData(ws)
    except:
        util.logStackTrace(sys.exc_info())
        traceback.print_exc()
        raise


@app.route("/admin", methods=["GET"])
def adminEntryPoint():
    util.debugPrint("admin")
    return app.send_static_file("admin.html")


@app.route("/admin/getUserAccounts/<sessionId>", methods=["POST"])
def getUserAccounts(sessionId):
    """
    get user accounts.

    URL Path:

        sessionId: session ID of the admin login session.

    """

    @testcase
    def getUserAccountsWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("getUserAccounts")
            userAccounts = AccountsManagement.getUserAccounts()
            retval = {"userAccounts": userAccounts,
                      STATUS: "OK",
                      "statusMessage": ""}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getUserAccountsWorker(sessionId)


@app.route("/admin/deleteAccount/<emailAddress>/<sessionId>", methods=["POST"])
def deleteAccount(emailAddress, sessionId):
    """
    delete user account


    URL Path:
    - emailAddress: The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none

        HTTP Return Codes:

    - 200 OK: if the request successfully completed.
    - 403 Forbidden: Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """

    def deleteAccountWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("deleteAccount")
            return jsonify(AccountsManagement.deleteAccount(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return deleteAccountWorker(emailAddress, sessionId)


@app.route("/admin/unlockAccount/<emailAddress>/<sessionId>", methods=["POST"])
def unlockAccount(emailAddress, sessionId):
    """
    unlock user account


    URL Path:
    - emailAddress: The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
      none

    HTTP Return Codes:

    - 200 OK: if the request successfully completed.
    - 403 Forbidden: Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """

    @testcase
    def unlockAccountWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("unlockAccount")
            return jsonify(AccountsManagement.unlockAccount(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return unlockAccountWorker(emailAddress, sessionId)


@app.route("/admin/togglePrivilegeAccount/<emailAddress>/<sessionId>",
           methods=["POST"])
def togglePrivilegeAccount(emailAddress, sessionId):
    """
    delete user accounts


    URL Path:
    - emailAddress: The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none

    HTTP Return Codes:

    - 200 OK: if the request successfully completed.
    - 403 Forbidden: Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """

    @testcase
    def togglePrivilegeAccountWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("togglePrivilegeAccount")
            return jsonify(AccountsManagement.togglePrivilegeAccount(
                emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return togglePrivilegeAccountWorker(emailAddress, sessionId)


@app.route("/admin/resetAccountExpiration/<emailAddress>/<sessionId>",
           methods=["POST"])
def resetAccountExpiration(emailAddress, sessionId):
    """
    delete user accounts


    URL Path:
    - emailAddress: The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args:
    none

    HTTP Return Codes:

    - 200 OK: if the request successfully completed.
    - 403 Forbidden: Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """

    @testcase
    def resetAccountExpirationWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("resetAccountExpiration")
            return jsonify(AccountsManagement.resetAccountExpiration(
                emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return resetAccountExpirationWorker(emailAddress, sessionId)


@app.route("/admin/createAccount/<sessionId>", methods=["POST"])
def createAccount(sessionId):
    """
    create user account

    URL Path:
        sessionId: login session ID

    Body (required):
        - JSON string of account info

    HTTP Return Codes:

    - 200 OK: if the request successfully completed.
    - 403 Forbidden: Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """

    @testcase
    def createAccountWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("createAccount")
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsManagement.createAccount(accountData))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return createAccountWorker(sessionId)


@app.route("/admin/resetPassword", methods=['POST'])
def resetPassword():
    @testcase
    def resetPasswordWorker():
        try:
            requestStr = request.data
            accountData = json.loads(requestStr)
            return authentication.resetPassword(accountData)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return resetPasswordWorker()


@app.route("/admin/authenticate", methods=['POST'])
def authenticate():
    """
    Authenticate the user given his username and password from the requested
    browser page or return an error if the user cannot be authenticated.

    URL Path:

    URL Args:
        None

    Body:
    - JSON data

    """

    @testcase
    def authenticateWorker():
        try:
            util.debugPrint("authenticate")
            p = urlparse.urlparse(request.url)
            urlpath = p.path
            if not Config.isConfigured() and urlpath[0] == "spectrumbrowser":
                msg = "attempt to access spectrumbrowser before configuration"
                msg += " -- please configure"
                util.debugPrint(msg)
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


@app.route("/admin/verifySessionToken/<sessionId>", methods=['POST'])
def verifySessionToken(sessionId):
    """
    Check the session token. Return TRUE if session Token is good and false
    otherwise.

    URL Path:

        - sessionId: the session ID to check.


    HTTP Return code:

       - 200 OK
         returns a document {status:OK} or {status: NOK} depending upon
         whether the session token verified or not.

    """
    try:
        if authentication.checkSessionId(sessionId, ADMIN):
            return jsonify({"status": "OK"})
        else:
            return jsonify({"status": "NOK"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/admin/logOut/<sessionId>", methods=['POST'])
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


@app.route("/admin/getSystemConfig/<sessionId>", methods=["POST"])
def getSystemConfig(sessionId):
    """
    get system configuration.

    URL Path:

        sessionId: Session ID of the login session.

    """

    @testcase
    def getSystemConfigWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            systemConfig = Config.getSystemConfig()
            if systemConfig is None:
                config = Config.getDefaultConfig()
                return jsonify(config)
            else:
                return jsonify(systemConfig)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getSystemConfigWorker(sessionId)


@app.route("/admin/getESAgents/<sessionId>", methods=["POST"])
def getESAgents(sessionId):
    """
    get Sensor Control agents (typically the ESC) .

    URL Path:

        sessionId: session ID of the login session.

    """

    @testcase
    def getESAgentsWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            agents = Config.getESAgents()
            retval = {"esAgents": agents}
            retval[STATUS] = 'OK'
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getESAgentsWorker(sessionId)


@app.route("/admin/armSensor/<sensorId>/<sessionId>", methods=["POST"])
def testArmSensor(sensorId, sessionId):
    """
    URL Path:
        sessionId -- the session ID of the login session.
        sensorId -- the sensorId

    URL Args: None

    Request Body:

        - agentName: Name of the agent to arm/disarm sensor.
        - key      : Key (password) of the agent to arm/disarm the sensor.

    HTTP Return Codes:

        - 200 OK: invocation was successful.
        - 403 Forbidden: authentication failure
        - 400 Bad request: Sensor is not a streaming sensor.

    Example Invocation:

   ::

       params = {}
       params["agentName"] = "NIST_ESC"
       params["key"] = "ESC_PASS"
       url = "https://{host}:8443/admin/armSensor/{self.sensorId}"
       r = requests.post(url, data=json.dumps(params), verify=False)

    """
    try:
        if not authentication.checkSessionId(sessionId, ADMIN):
            abort(403)
        sensorConfig = SensorDb.getSensorObj(sensorId)
        if sensorConfig is None:
            abort(404)
        if not sensorConfig.isStreamingEnabled():
            abort(400)
        persistent = request.args.get("persistent")
        if persistent is None:
            persistent = "false"
        DataStreamSharedState.sendCommandToSensor(sensorId, json.dumps(
            {"sensorId": sensorId,
             "command": "arm",
             "persistent": persistent}))
        return jsonify({STATUS: OK})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/admin/addESAgent/<sessionId>", methods=["POST"])
def addESAgent(sessionId):
    invalid_chars = {'&', '$', '+', '/', ':', ';', '=', '?', '@', '#'}

    @testcase
    def addESAgentWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            requestStr = request.data
            agentConfig = json.loads(requestStr)
            agentName = agentConfig["agentName"]

            bad_chars = invalid_chars.intersection(agentName)
            if bad_chars:
                msg = "Invalid character in agentName: {}"
                util.debugPrint(msg.format(bad_chars))
                abort(400)

            key = agentConfig["key"]
            bad_chars = invalid_chars.intersection(key)
            if bad_chars:
                msg = "Invalid character in key: {}"
                util.debugPrint(msg.format(bad_chars))
                abort(400)

            Config.addESAgent(agentName, key)
            agents = Config.getESAgents()
            retval = {"esAgents": agents}
            retval[STATUS] = 'OK'
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return addESAgentWorker(sessionId)


@app.route("/admin/deleteESAgent/<agentName>/<sessionId>", methods=["POST"])
def deleteESAgent(agentName, sessionId):
    """
    remove ES Agent.

    URL Path:

        agentName: Agent name to remove.
        sessionId: session ID of the login session.

    """

    @testcase
    def deleteESAgentWorker(agentName, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            Config.removeESAgent(agentName)
            agents = Config.getESAgents()
            retval = {"esAgents": agents}
            retval[STATUS] = 'OK'
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return deleteESAgentWorker(agentName, sessionId)


@app.route("/admin/getPeers/<sessionId>", methods=["POST"])
def getPeers(sessionId):
    """
    get outbound peers.

    URL Path:

        sessionId: session ID of the login session.

    """

    @testcase
    def getPeersWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            peers = Config.getPeers()
            retval = {"peers": peers}
            retval[STATUS] = 'OK'
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getPeersWorker(sessionId)


@app.route("/admin/removePeer/<host>/<port>/<sessionId>", methods=["POST"])
def removePeer(host, port, sessionId):
    """
    remove outbound peer.

    URL Path:
        host: Host of peer to remove
        port: port or peer to remove
        sessionId: login session ID
    """

    @testcase
    def removePeerWorker(host, port, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            Config.removePeer(host, int(port))
            peers = Config.getPeers()
            retval = {"peers": peers}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return removePeerWorker(host, port, sessionId)


@app.route("/admin/addPeer/<host>/<port>/<protocol>/<sessionId>",
           methods=["POST"])
def addPeer(host, port, protocol, sessionId):
    """
    add an outbound peer

    URL Path:
        host: Host of peer to add.
        port: port of peer
        protocol: http or https
        sessionId: login session id.
    """

    @testcase
    def addPeerWorker(host, port, protocol, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            # TODO -- parameter checking.
            Config.addPeer(protocol, host, int(port))
            peers = Config.getPeers()
            retval = {"peers": peers}
            retval[STATUS] = OK
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return addPeerWorker(host, port, protocol, sessionId)


@app.route("/admin/getInboundPeers/<sessionId>", methods=["POST"])
def getInboundPeers(sessionId):
    """
    get a list of inbound peers.

    URL path:
        - sessionID = session ID of the login

    URL Args:
        None

    Returns:
        - JSON string containing the inbound Peers accepted by this server.

    HTTP Return Codes:
        - 403 if authentication failed.
        - 200 successful return.

    """

    @testcase
    def getInboundPeersWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            peerKeys = Config.getInboundPeers()
            retval = {"inboundPeers": peerKeys}
            retval[STATUS] = OK
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getInboundPeersWorker(sessionId)


@app.route("/admin/deleteInboundPeer/<peerId>/<sessionId>", methods=["POST"])
def deleteInboundPeer(peerId, sessionId):
    """
    Delete an inbound peer record.

    URL Path:
        - peerId: Peer ID of peer to delete.
        - sessionId: session ID of authenticated session.

    Returns:
        - JSON formatted list of peers.

    HTTP Return Codes:
        - 403 if authentication not successful.

    """

    @testcase
    def deleteInboundPeerWorker(peerId, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            Config.deleteInboundPeer(peerId)
            peerKeys = Config.getInboundPeers()
            retval = {"inboundPeers": peerKeys}
            retval[STATUS] = OK
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return deleteInboundPeerWorker(peerId, sessionId)


@app.route("/admin/addInboundPeer/<sessionId>", methods=["POST"])
def addInboundPeer(sessionId):
    """
    Add an inbound peer.
    """

    @testcase
    def addInboundPeerWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            requestStr = request.data
            peerConfig = json.loads(requestStr)
            util.debugPrint("peerConfig " + json.dumps(peerConfig, indent=4))
            Config.addInboundPeer(peerConfig)
            peers = Config.getInboundPeers()
            retval = {"inboundPeers": peers}
            retval[STATUS] = "OK"
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return addInboundPeerWorker(sessionId)


@app.route("/admin/setSystemConfig/<sessionId>", methods=["POST"])
def setSystemConfig(sessionId):
    """
    set system configuration
    URL Path:
        sessionId the session Id of the login in session.

    URL Args: None

    Request Body:
        A JSON formatted string containing the system configuration.
    """

    @testcase
    def setSystemConfigWorker(sessionId):
        try:
            util.debugPrint("setSystemConfig: " + sessionId)
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("passed authentication")
            requestStr = request.data
            systemConfig = json.loads(requestStr)
            (statusCode, message) = Config.verifySystemConfig(systemConfig)
            if not statusCode:
                util.debugPrint("did not verify sys config")
                return jsonify({"status": "NOK", "ErrorMessage": message})

            util.debugPrint("setSystemConfig " + json.dumps(systemConfig,
                                                            indent=4, ))
            if Config.setSystemConfig(systemConfig):
                return jsonify({"status": "OK"})
            else:
                return jsonify({"status": "NOK", "ErrorMessage": "Unknown"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return setSystemConfigWorker(sessionId)


@app.route("/admin/addSensor/<sessionId>", methods=["POST"])
def addSensor(sessionId):
    """
    Add a sensor to the system or return error if the sensor does not exist.
    URL Path:
        sessionId the session Id of the login in session.

    URL Args: None

    Request Body:
        A JSON formatted string containing the sensor configuration.

    """

    @testcase
    def addSensorWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system", 500)
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found.", 403)
            requestStr = request.data
            sensorConfig = json.loads(requestStr)
            return jsonify(SensorDb.addSensor(sensorConfig))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return addSensorWorker(sessionId)


@app.route("/admin/toggleSensorStatus/<sensorId>/<sessionId>",
           methods=["POST"])
def toggleSensorStatus(sensorId, sessionId):
    @testcase
    def toggleSensorStatusWorker(sensorId, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system", 500)
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found.", 403)
            return jsonify(SensorDb.toggleSensorStatus(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return toggleSensorStatusWorker(sensorId, sessionId)


@app.route("/admin/purgeSensor/<sensorId>/<sessionId>", methods=["POST"])
def purgeSensor(sensorId, sessionId):
    @testcase
    def purgeSensorWorker(sensorId, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system", 500)
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found.", 403)
            return jsonify(SensorDb.markSensorForPurge(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return purgeSensorWorker(sensorId, sessionId)


@app.route("/admin/deleteSensor/<sensorId>/<sessionId>", methods=["POST"])
def deleteSensor(sensorId, sessionId):
    @testcase
    def deleteSensorWorker(sensorId, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system", 500)
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found.", 403)
            return jsonify(SensorDb.deleteSensor(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return deleteSensorWorker(sensorId, sessionId)


@app.route("/admin/updateSensor/<sessionId>", methods=["POST"])
def updateSensor(sessionId):
    @testcase
    def updateSensorWorker(sessionId):
        try:
            util.debugPrint("updateSensor")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system", 500)
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found.", 403)
            requestStr = request.data
            sensorConfig = json.loads(requestStr)
            return jsonify(SensorDb.updateSensor(sensorConfig))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return updateSensorWorker(sessionId)


@app.route("/admin/getSystemMessages/<sensorId>/<sessionId>", methods=["POST"])
def getSystemMessages(sensorId, sessionId):
    @testcase
    def getSystemMessagesWorker(sensorId, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system", 500)
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found.", 403)
            genzip = GenerateZipFileForDownload
            zipfile = genzip.generateSysMessagesZipFileForDownload(sensorId,
                                                                   sessionId)
            return jsonify(zipfile)

        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getSystemMessagesWorker(sensorId, sessionId)


@app.route("/admin/getSensorInfo/<sessionId>", methods=["POST"])
def getSensorInfo(sessionId):
    '''

    Get the sensor configuration information of all sensors from the
    sensor database.  Note that sensitive information such as sensor
    key is not returned.

    URL Path:
        sessionId the session Id of the login in session.

    URL Args:
        - getFirstLastMessages: return the first and last message metadata


    Request Body:
        A JSON formatted string containing the sensor information.

    HTTP Return codes:
        200 OK if the invocation successful.

    '''

    @testcase
    def getSensorInfoWorker(sessionId):
        try:

            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found", 403)
            lastMessageFlagStr = request.args.get("getFirstLastMessages")
            if lastMessageFlagStr is not None and lastMessageFlagStr == "true":
                lastMessageFlag = True
            else:
                lastMessageFlag = False
            response = SensorDb.getSensors(getMessageDates=lastMessageFlag)
            return jsonify(response)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getSensorInfoWorker(sessionId)


@app.route("/admin/recomputeOccupancies/<sensorId>/<sessionId>",
           methods=["POST"])
def recomputeOccupancies(sensorId, sessionId):
    @testcase
    def recomputeOccupanciesWorker(sensorId, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found", 403)
            return jsonify(RecomputeOccupancies.recomputeOccupancies(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return recomputeOccupanciesWorker(sensorId, sessionId)


@app.route("/admin/resetNoiseFloor/<sensorId>/<noiseFloor>/<sessionId>",
           methods=["POST"])
def resetNoiseFloor(sensorId, noiseFloor, sessionId):
    try:
        if not authentication.checkSessionId(sessionId, ADMIN):
            return make_response("Session not found", 403)
        return jsonify(RecomputeOccupancies.resetNoiseFloor(sensorId,
                                                            noiseFloor))
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/admin/garbageCollect/<sensorId>/<sessionId>", methods=["POST"])
def garbageCollect(sensorId, sessionId):
    @testcase
    def garbageCollectWorker(sensorId, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found", 403)
            return jsonify(GarbageCollect.runGarbageCollector(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return garbageCollectWorker(sensorId, sessionId)


@app.route("/admin/deleteCaptureEvents/<sensorId>/<startDate>/<sessionId>",
           methods=["POST"])
def deleteCaptureEvents(sensorId, startDate, sessionId):
    """
    Delete the events from the capture db.
    Send a message to the sensor to do the same.
    """
    try:
        if not authentication.checkSessionId(sessionId, ADMIN):
            util.debugPrint("deleteCaptureEvents: failed authentication")
            abort(403)
        sdate = int(startDate)
        if sdate < 0:
            util.debugPrint("deleteCaptureEvents: illegal param")
            abort(400)
        else:
            CaptureDb.deleteCaptureDb(sensorId, sdate)
            command = json.dumps({"sensorId": sensorId,
                                  "timestamp": sdate,
                                  "command": "garbage_collect"})
            DataStreamSharedState.sendCommandToSensor(sensorId, command)
            return jsonify({STATUS: "OK"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/admin/deleteAllCaptureEvents/<sensorId>/<sessionId>",
           methods=["POST"])
def deleteAllCaptureEvents(sensorId, sessionId):
    """
    Delete all the the capture events from the capture db.
    Send a message to the sensor to do the same.
    """
    try:
        if not authentication.checkSessionId(sessionId, ADMIN):
            util.debugPrint("deleteCaptureEvents: failed authentication")
            abort(403)
        else:
            CaptureDb.deleteCaptureDb(sensorId)
            return jsonify({STATUS: "OK"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/admin/getSessions/<sessionId>", methods=["POST"])
def getSessions(sessionId):
    @testcase
    def getSessionsWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,
                                                 ADMIN,
                                                 updateSessionTimer=False):
                return make_response("Session not found", 403)
            return jsonify(SessionLock.getSessions())
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return getSessionsWorker(sessionId)


@app.route("/admin/freezeRequest/<sessionId>", methods=["POST"])
def freezeRequest(sessionId):
    @testcase
    def freezeRequestWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found", 403)
            return jsonify(SessionLock.freezeRequest(sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return freezeRequestWorker(sessionId)


@app.route("/admin/unfreezeRequest/<sessionId>", methods=["POST"])
def unfreezeRequest(sessionId):
    @testcase
    def unfreezeRequestWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found", 403)
            return jsonify(SessionLock.freezeRelease(sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return unfreezeRequestWorker(sessionId)


@app.route("/admin/log/<sessionId>", methods=["POST"])
def log(sessionId):
    return Log.log()


@app.route("/admin/getScreenConfig/<sessionId>", methods=["POST"])
def getScreenConfig(sessionId):
    """
    get screen configuration.

    URL Path:

        sessionId -- the session ID for the login session.

    Returns:
        200 OK on successful completion. A JSON Document

    """

    @testcase
    def getScreenConfigWorker(sessionId):
        try:
            screenConfig = Config.getScreenConfig()
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

    return getScreenConfigWorker(sessionId)


@app.route("/admin/setScreenConfig/<sessionId>", methods=["POST"])
def setScreenConfig(sessionId):
    """
    set system configuration

    URL Path:
        sessionId the session Id of the login in session.

    URL Args: None

    Request Body:
        A JSON formatted string containing the system configuration.

    HTTP Return codes:
        200 OK if the invocation successful.
        {status:OK} returned JSON document.

    """

    @testcase
    def setScreenConfigWorker(sessionId):
        try:
            util.debugPrint("setScreenConfig: " + sessionId)
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            requestStr = request.data
            screenConfig = json.loads(requestStr)
            if Config.setScreenConfig(screenConfig):
                return jsonify({"status": "OK"})
            else:
                return jsonify({"status": "NOK", "ErrorMessage": "Unknown"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return setScreenConfigWorker(sessionId)


@app.route("/admin/changePassword", methods=["POST"])
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
                accountData, urlPrefix, sendEmail=False))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace("Unexpected error:" + str(sys.exc_info()[0]))
            raise

    return changePasswordWorker()


def purgeSensors():
    """
    Run in an infinite loop purging all the sensors that are marked for purging.
    This is invoked as a process from main.
    """
    from Defines import PURGING
    import time
    while True:
        for sensor in DbCollections.getSensors().find():
            sensorObj = Sensor(sensor)
            if sensorObj.getSensorStatus() == PURGING:
                SensorDb.purgeSensor(sensorObj)
        time.sleep(30)


if __name__ == '__main__':
    launchedFromMain = True
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".admin.pid")
    parser.add_argument("--logfile", help="LOG file", default="/tmp/admin.log")
    parser.add_argument("--username",
                        help="USER name",
                        default="spectrumbrowser")
    parser.add_argument("--groupname",
                        help="GROUP name",
                        default="spectrumbrowser")
    parser.add_argument("--daemon", help="GROUP name", default="True")

    args = parser.parse_args()
    isDaemon = args.daemon == "True"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)
    timer = RepeatingTimer(3600, GarbageCollect.scanGeneratedDirs)
    timer.start()
    t = Process(target=purgeSensors)
    t.start()

    if isDaemon:
        import daemon
        import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile, 'a')
        context.stdout = open(args.logfile, 'a')
        context.files_preserve = [fh.stream]
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
        if os.path.exists(args.pidfile):
            pid = open(args.pidfile).read()
            try:
                os.kill(int(pid), 0)
                print "service is running -- not starting"
                sys.exit(-1)
                os._exit(-1)
            except:
                print "removing pidfile and starting"
                os.remove(args.pidfile)
        context.pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pidfile)
        with context:
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            app.config['CORS_HEADERS'] = 'Content-Type'
            Log.loadGwtSymbolMap()
            app.debug = True
            util.debugPrint("Admin service -- starting")
            if Config.isConfigured():
                authentication.removeAdminSessions()
                server = pywsgi.WSGIServer(('0.0.0.0', 8001),
                                           app,
                                           handler_class=WebSocketHandler)
            else:
                server = pywsgi.WSGIServer(('0.0.0.0', 8001), app)
            server.serve_forever()
    else:
        # for debugging.
        with util.pidfile(args.pidfile):
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            app.config['CORS_HEADERS'] = 'Content-Type'
            Log.loadGwtSymbolMap()
            app.debug = True
            util.debugPrint("Admin service -- starting")
            if Config.isConfigured():
                authentication.removeAdminSessions()
                server = pywsgi.WSGIServer(('0.0.0.0', 8001),
                                           app,
                                           handler_class=WebSocketHandler)
            else:
                server = pywsgi.WSGIServer(('0.0.0.0', 8001), app)
            server.serve_forever()
