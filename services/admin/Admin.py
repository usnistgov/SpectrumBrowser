#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
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
import SensorDb
import Config
import Log
import AccountsManagement
import GenerateZipFileForDownload
from Defines import STATUS
from Defines import ADMIN
import SessionLock
import argparse
import ResourceDataStreaming
import ServiceControlFunctions
import RecomputeOccupancies
import daemon
import daemon.pidfile
import lockfile
import logging
import pwd


UNIT_TEST_DIR = "./unit-tests"



global launchedFromMain

if not Config.isConfigured() :
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
            retval = {"userAccounts":userAccounts, STATUS:"OK", "statusMessage":""}
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
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none

        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
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
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none

        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
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

@app.route("/admin/togglePrivilegeAccount/<emailAddress>/<sessionId>", methods=["POST"])
def togglePrivilegeAccount(emailAddress, sessionId):
    """
    delete user accounts


    URL Path:
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none

        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def togglePrivilegeAccountWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("togglePrivilegeAccount")
            return jsonify(AccountsManagement.togglePrivilegeAccount(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return togglePrivilegeAccountWorker(emailAddress, sessionId)

@app.route("/admin/resetAccountExpiration/<emailAddress>/<sessionId>", methods=["POST"])
def resetAccountExpiration(emailAddress, sessionId):
    """
    delete user accounts


    URL Path:
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none

        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def resetAccountExpirationWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("resetAccountExpiration")
            return jsonify(AccountsManagement.resetAccountExpiration(emailAddress))
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
        sessionId : login session ID

     URL Args (required):
        - JSON string of account info

        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
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

@app.route("/admin/authenticate", methods=['POST'])
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
            if not Config.isConfigured() and urlpath[0] == "spectrumbrowser" :
                util.debugPrint("attempt to access spectrumbrowser before configuration -- please configure")
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

@app.route("/admin/logOut/<sessionId>", methods=['POST'])
# @testcase
def logOut(sessionId):
    """
    Log out of an existing session.

    URL Path:

        sessionId : The session ID to log out.

    """
    @testcase
    def logOutWorker(sessionId):
        try:
            authentication.logOut(sessionId)
            return jsonify({"status":"OK"})
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

        sessionId : Session ID of the login session.

    """
    @testcase
    def getSystemConfigWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            systemConfig = Config.getSystemConfig()
            if systemConfig == None:
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
            retval = {"peers":peers}
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
        sessionId : login session ID
    """
    @testcase
    def removePeerWorker(host, port, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            Config.removePeer(host, int(port))
            peers = Config.getPeers()
            retval = {"peers":peers}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return removePeerWorker(host, port, sessionId)

@app.route("/admin/addPeer/<host>/<port>/<protocol>/<sessionId>", methods=["POST"])
def addPeer(host, port, protocol, sessionId):
    """
    add an outbound peer

    URL Path:
        host : Host of peer to add.
        port : port of peer
        protocol : http or https
        sessionId : login session id.
    """
    @testcase
    def addPeerWorker(host, port, protocol, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            # TODO -- parameter checking.
            Config.addPeer(protocol, host, int(port))
            peers = Config.getPeers()
            retval = {"peers":peers}
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
    sessionID = session ID of the login

    URL Args: None

    Returns : JSON formatted string containing the inbound Peers accepted by this server.

    """
    @testcase
    def getInboundPeersWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            peerKeys = Config.getInboundPeers()
            retval = {"inboundPeers":peerKeys}
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
    """
    @testcase
    def deleteInboundPeerWorker(peerId, sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN) :
                abort(403)
            Config.deleteInboundPeer(peerId)
            peerKeys = Config.getInboundPeers()
            retval = {"inboundPeers":peerKeys}
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
            if not authentication.checkSessionId(sessionId, ADMIN) :
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
            util.debugPrint("setSystemConfig : " + sessionId)
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("passed authentication")
            requestStr = request.data
            systemConfig = json.loads(requestStr)
            (statusCode, message) = Config.verifySystemConfig(systemConfig)
            if not statusCode:
                util.debugPrint("did not verify sys config")
                return jsonify({"status":"NOK", "ErrorMessage":message})

            util.debugPrint("setSystemConfig " + json.dumps(systemConfig, indent=4,))
            if Config.setSystemConfig(systemConfig):
                return jsonify({"status":"OK"})
            else:
                return jsonify({"status":"NOK", "ErrorMessage":"Unknown"})
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

@app.route("/admin/toggleSensorStatus/<sensorId>/<sessionId>", methods=["POST"])
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
            return jsonify(SensorDb.purgeSensor(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return purgeSensorWorker(sensorId, sessionId)

@app.route("/admin/updateSensor/<sessionId>", methods=["POST"])
def updateSensor(sessionId):
    @testcase
    def updateSensorWorker(sessionId):
        try:
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
            return jsonify(GenerateZipFileForDownload.generateSysMessagesZipFileForDownload(sensorId, sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getSystemMessagesWorker(sensorId, sessionId)

@app.route("/admin/getSensorInfo/<sessionId>", methods=["POST"])
def getSensorInfo(sessionId):
    @testcase
    def getSensorInfoWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
                return make_response("Session not found", 403)
            response = SensorDb.getSensors()
            return jsonify(response)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getSensorInfoWorker(sessionId)

@app.route("/admin/recomputeOccupancies/<sensorId>/<sessionId>", methods=["POST"])
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

@app.route("/admin/getSessions/<sessionId>", methods=["POST"])
def getSessions(sessionId):
    @testcase
    def getSessionsWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId, ADMIN):
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

@app.route("/admin/log", methods=["POST"])
def log():
    return Log.log()

@app.route("/admin/getScreenConfig/<sessionId>", methods=["POST"])
def getScreenConfig(sessionId):
    """
    get screen configuration.

    """
    @testcase
    def getScreenConfigWorker(sessionId):
        try:
            screenConfig = Config.getScreenConfig()
            if screenConfig == None:
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
    """
    @testcase
    def setScreenConfigWorker(sessionId):
        try:
            util.debugPrint("setScreenConfig : " + sessionId)
            if not authentication.checkSessionId(sessionId, ADMIN):
                abort(403)
            util.debugPrint("passed authentication")
            requestStr = request.data
            screenConfig = json.loads(requestStr)

            util.debugPrint("setScreenConfig " + json.dumps(screenConfig, indent=4,))
            if Config.setScreenConfig(screenConfig):
                return jsonify({"status":"OK"})
            else:
                return jsonify({"status":"NOK", "ErrorMessage":"Unknown"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return setScreenConfigWorker(sessionId)

@app.route("/admin/getServiceStatus/<service>/<sessionId>", methods=["POST"])
def getServiceStatus(service, sessionId):
    """
    get screen configuration.

    """
    try:
        util.debugPrint("getServiceStatus: " + str(service))
        if not authentication.checkSessionId(sessionId, ADMIN):
            abort(403)
        util.debugPrint("passed authentication")
        return jsonify(ServiceControlFunctions.thisServiceStatus(service))


    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/admin/stopService/<service>/<sessionId>", methods=["POST"])
def stopService(service, sessionId):
    """
    Stop specified service
    URL Path:
        sessionId the session Id of the login in session.

    URL Args: None

    Request Body:
        A String of the name of the service
    """
    try:
        util.debugPrint("stopService " + str(service))
        if not authentication.checkSessionId(sessionId, ADMIN):
            abort(403)
        util.debugPrint("passed authentication")
        if ServiceControlFunctions.stopThisService(service):
            return jsonify({"status":"OK"})
        else:
            return jsonify({"status":"NOK", "ErrorMessage":"Unknown"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/admin/restartService/<service>/<sessionId>", methods=["POST"])
def restartService(service, sessionId):
    """
    Restart specified service
    URL Path:
        sessionId the session Id of the login in session.

    URL Args: None

    Request Body:
        A String of the name of the service
    """
    try:
        util.debugPrint("restartService " + str(service))
        if not authentication.checkSessionId(sessionId, ADMIN):
            abort(403)
        util.debugPrint("passed authentication")
        if ServiceControlFunctions.restartThisService(service):
            return jsonify({"status":"OK"})
        else:
            return jsonify({"status":"NOK", "ErrorMessage":"Unknown"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise



if __name__ == '__main__':
    launchedFromMain = True
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".admin.pid")
    parser.add_argument("--logfile", help="LOG file", default="/var/log/admin.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")

    args = parser.parse_args()
 
    context = daemon.DaemonContext()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)

    context.stdin = sys.stdin
    context.stderr = open(args.logfile,'a')
    context.stdout = open(args.logfile,'a')

    context.pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pidfile)
    context.files_preserve = [fh.stream]

    context.uid = pwd.getpwnam(args.username).pw_uid 
    context.gid = pwd.getpwnam(args.groupname).pw_gid

    with context:
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        app.config['CORS_HEADERS'] = 'Content-Type'
        Log.loadGwtSymbolMap()
        app.debug = True
        util.debugPrint("Admin service -- starting")
        if Config.isConfigured():
            server = pywsgi.WSGIServer(('0.0.0.0', 8001), app, handler_class=WebSocketHandler)
        else:
            server = pywsgi.WSGIServer(('0.0.0.0', 8001), app, handler_class=WebSocketHandler)
        server.serve_forever()
