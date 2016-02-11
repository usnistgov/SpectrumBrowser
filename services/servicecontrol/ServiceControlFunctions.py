#! /usr/local/bin/python2.7
'''
Created on Jul 28, 2015

@author: mranga, mdb4
'''
import Bootstrap
sbHome = Bootstrap.getSpectrumBrowserHome()
import sys
sys.path.append(sbHome + "/services/common")
sys.path.append(sbHome + "/services/svc")
import traceback
import util
from Defines import SERVICE_NAMES
import subprocess
from Defines import STATUS
from Defines import OK,NOK,ERROR_MESSAGE,SERVICE_STATUS,ADMIN,STATIC_GENERATED_FILE_LOCATION
from flask import Flask,  abort, request
from flask import jsonify
import pwd
import logging
import argparse
import Log
from gevent import pywsgi
import os
import authentication
import zipfile
import memcache
import Config
import DebugFlags
import json
import threading

launchedFromMain = False
app = Flask(__name__, static_url_path="")





def thisServiceStatus(service):
    try:
        if service in SERVICE_NAMES:
            output = subprocess.Popen(["service",service,"status"],stdout=subprocess.PIPE)
            statusRawInit, errorStr = output.communicate()
            if not errorStr == None:
                util.debugPrint("Error String detected (status): " + str(errorStr))
                return {STATUS:NOK,ERROR_MESSAGE:errorStr}
            statusRaw = statusRawInit.split()
            util.debugPrint("statusRaw: " + str(statusRaw))
            if "running" in statusRaw:
                return {STATUS:OK,SERVICE_STATUS:"Running"}
            elif "stopped" in statusRaw:
                return {STATUS:OK,SERVICE_STATUS:"Stopped"}
            else:
                return {STATUS:OK,SERVICE_STATUS:"UNKNOWN"}
        else:
            util.errorPrint(service + " does not match a service")
            return {STATUS:NOK,ERROR_MESSAGE:service + " does not match a service"}

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise



def stopThisService(service):
    try:
        if service in SERVICE_NAMES:
            if service == SERVICE_NAMES[0]:
                return False
            else:
                output = subprocess.Popen(["/sbin/service",service,"stop"],stdout=subprocess.PIPE)
                stopRawInit, errorStr = output.communicate()
                if not errorStr == None:
                    util.debugPrint("Error String detected (stop): " + str(errorStr))
                    return False
                util.debugPrint("output.communicate() (stop): " + str(stopRawInit))
                return True
        else:
            util.debugPrint(service + " does not match a service")
            return False
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/svc/getServicesStatus/<sessionId>", methods=["POST"])
def getServicesStatus(sessionId):
    """
    get screen configuration.

    """
    try:
        util.debugPrint("getServicesStatus")
        if not authentication.checkSessionId(sessionId, ADMIN,updateSessionTimer=False):
            abort(403)
        util.debugPrint("passed authentication")
        retval = {}
        retval[STATUS] = OK
        serviceStatus = {}
        for service in SERVICE_NAMES:
            output = subprocess.Popen(["service",service,"status"],stdout=subprocess.PIPE)
            statusRawInit, errorStr = output.communicate()
            if not errorStr == None:
                util.debugPrint("Error String detected (status): " + str(errorStr))
            statusRaw = statusRawInit.split()
            util.debugPrint("statusRaw: " + str(statusRaw))
            if "running" in statusRaw:
                serviceStatus[service]="Running"
            elif "stopped" in statusRaw:
                serviceStatus[service] = "Stopped"
            else:
                serviceStatus[service] = "UNKNOWN"

        retval[SERVICE_STATUS] = serviceStatus
        return jsonify(retval)


    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/svc/getServiceStatus/<service>/<sessionId>", methods=["POST"])
def getServiceStatus(service, sessionId):
    """
    get screen configuration.

    """
    try:
        util.debugPrint("getServiceStatus: " + str(service))
        if not authentication.checkSessionId(sessionId, ADMIN,updateSessionTimer=False):
            abort(403)
        util.debugPrint("passed authentication")
        return jsonify(thisServiceStatus(service))


    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/svc/stopService/<service>/<sessionId>", methods=["POST"])
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
        if stopThisService(service):
            return jsonify({"status":"OK"})
        else:
            return jsonify({"status":"NOK", "ErrorMessage":"Unknown"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/svc/restartService/<service>/<sessionId>", methods=["POST"])
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
        if restartThisService(service):
            return jsonify({"status":"OK"})
        else:
            return jsonify({"status":"NOK", "ErrorMessage":"Unknown service"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


@app.route("/svc/getDebugFlags/<sessionId>", methods=["POST"])
def getDebugFlags(sessionId):
    """

    Get the debug flags for this server instance. Note - debug flag settings
    are not persistent.


    """
    try:
        if not authentication.checkSessionId(sessionId, ADMIN):
            abort(403)
    	debugFlags = DebugFlags.getDebugFlags()
        return jsonify({"status":"OK","debugFlags":debugFlags})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/svc/setDebugFlags/<sessionId>", methods=["POST"])
def setDebugFLags(sessionId):
    """

    Set the debug flags for this server instance. Note - debug flag settings
    are not persistent.


    """
    try:
        if not authentication.checkSessionId(sessionId, ADMIN):
            abort(403)
	if request.data == None:
	    abort(400)
        debugFlags = json.loads(request.data)
	DebugFlags.setDebugFlags(debugFlags)
        return jsonify({"status":"OK"})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

@app.route("/svc/getLogs/<sessionId>", methods=["POST"])
def getLogs(sessionId):
    """

    Bunlde the logs on the server and return a URL to it.

    URL Path:
        sessionId the session Id of the login in session.

    """
    try:
       zipFileName = sessionId + "/logs.zip"
       dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION + sessionId)
       if not os.path.exists(dirname):
           os.makedirs(dirname)
       zipFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + zipFileName
       if os.path.exists(zipFilePath):
          os.remove(zipFilePath)
       zipFile = zipfile.ZipFile(zipFilePath, mode="w")
       for f in ["/var/log/admin.log", "/var/log/monitoring.log", "/var/log/federation.log", \
		"/var/log/streaming.log", "/var/log/occupancy.log", "/var/log/flask/federation.log", "/var/log/servicecontrol.log",\
		"/var/log/flask/spectrumbrowser.log", "/var/log/flask/spectrumdb.log"]:
          if os.path.exists(f):
		zipFile.write(f,compress_type=zipfile.ZIP_DEFLATED)
       zipFile.close()
       url = Config.getGeneratedDataPath() + "/" + zipFileName
       return jsonify({"status":"OK","url":url})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/svc/clearLogs/<sessionId>", methods=["POST"])
def clearlogs(sessionId):
    if not authentication.checkSessionId(sessionId, ADMIN):
       abort(403)
    try:
       for f in ["/var/log/admin.log", "/var/log/monitoring.log", "/var/log/federation.log", \
		"/var/log/streaming.log", "/var/log/occupancy.log", "/var/log/flask/federation.log", \
		"/var/log/flask/spectrumbrowser.log", "/var/log/flask/spectrumdb.log"]:
          if os.path.exists(f):
		os.remove(f)
       serviceNames = ["admin", "spectrumbrowser", "streaming", "occupancy", "monitoring","federation","spectrumdb"]
       for service in serviceNames:
	  restartThisService(service)
       return jsonify({"status":"OK"})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

def restartThisService(service):
    try:
        if service in SERVICE_NAMES :
            if service == "servicecontrol":
                return False
            else:
                output = subprocess.Popen(["/sbin/service",service,"restart"],stdout=subprocess.PIPE)
                restartRawInit, errorStr = output.communicate()
                if not errorStr == None:
                    util.debugPrint("Error String detected (restart): " + str(errorStr))
                    return False
                util.debugPrint("output.communicate() (restart): " + str(restartRawInit))
                return True
        else:
            util.debugPrint(service + " does not match a service")
            return False
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


if __name__ == '__main__':
    launchedFromMain = True
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".svc.pid")
    parser.add_argument("--logfile", help="LOG file", default="/tmp/svc.log")
    parser.add_argument("--username", help="USER name", default="root")
    parser.add_argument("--groupname", help="GROUP name", default="root")
    parser.add_argument("--daemon", help="daemon flag", default="True")

    args = parser.parse_args()
    isDaemon = args.daemon == "True"
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)
    DebugFlags.setDefaults()


    if isDaemon:
	import daemon
	import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile,'a')
        context.stdout = open(args.logfile,'a')
        context.files_preserve = [fh.stream]
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
 	# There is a race condition here but it will do for us.
        if os.path.exists(args.pidfile):
            pid = open(args.pidfile).read()
            try :
                os.kill(int(pid), 0)
                print "svc is running -- not starting"
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
            util.debugPrint("Svc service -- starting")
    	    util.debugPrint("Debug flags : " + str(DebugFlags.getDebugFlags()))
    	    util.debugPrint("Debug flags : " + str(DebugFlags.getDebugFlags()))
            server = pywsgi.WSGIServer(('0.0.0.0', 8005), app)
            server.serve_forever()
    else:
        with util.pidfile(args.pidfile):
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            app.config['CORS_HEADERS'] = 'Content-Type'
            Log.loadGwtSymbolMap()
            app.debug = True
            util.debugPrint("Svc service -- starting")
    	    util.debugPrint("Debug flags : " + str(DebugFlags.getDebugFlags()))
            server = pywsgi.WSGIServer(('0.0.0.0', 8005), app)
            server.serve_forever()

