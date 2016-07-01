#! /usr/local/bin/python2.7
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
sbHome = Bootstrap.getSpectrumBrowserHome()
from flask import Flask, request, abort
from flask import jsonify
import PeerConnectionManager
import util
import argparse
import signal
import Log
import os
import Config
import authentication
import json
import sys
import traceback
import GetLocationInfo
from gevent import pywsgi
from multiprocessing import Process
import time
import pwd

app = Flask(__name__, static_url_path="")
app.static_folder = sbHome + "/flask/static"


@app.route("/federated/peerSignIn/<peerServerId>/<peerKey>", methods=["POST"])
def peerSignIn(peerServerId, peerKey):
    """
    Handle authentication request from federated peer and send our location information.
    """
    try:
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        util.debugPrint("peerSignIn " + peerServerId + "/" + peerKey)
        rc = authentication.authenticatePeer(peerServerId, peerKey)
        # successfully authenticated? if so, return the location info for ALL
        # sensors.
        util.debugPrint("Status : " + str(rc))
        retval = {}
        if rc:
            requestStr = request.data
            if requestStr != None:
                jsonData = json.loads(requestStr)
                Config.getPeers()
                protocol = Config.getAccessProtocol()
                peerUrl = protocol + "//" + jsonData["HostName"] + ":" + str(
                    jsonData["PublicPort"])
                PeerConnectionManager.setPeerUrl(peerServerId, peerUrl)
                PeerConnectionManager.setPeerSystemAndLocationInfo(
                    peerUrl, jsonData["locationInfo"])
            retval["status"] = "OK"
            retval["HostName"] = Config.getHostName()
            retval["Port"] = Config.getPublicPort()
            if not Config.isAuthenticationRequired():
                locationInfo = GetLocationInfo.getLocationInfo()
                retval["locationInfo"] = locationInfo
            return jsonify(retval)
        else:
            retval["status"] = "NOK"
            return jsonify(retval)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


def signal_handler(signo, frame):
    global jobs
    print('Federation Server : Caught signal! Exiting.')
    for job in jobs:
        os.kill(job, signal.SIGINT)
        time.sleep(1)
        os.kill(job, signal.SIGKILL)
    sys.exit(0)
    os._exit(0)


if __name__ == '__main__':
    global jobs
    jobs = []
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".federation.pid")
    parser.add_argument("--logfile", default="/var/log/federation.log")
    parser.add_argument("--username", default="spectrumbrowser")
    parser.add_argument("--groupname", default="spectrumbrowser")
    parser.add_argument("--daemon", default="True")
    args = parser.parse_args()

    isDaemon = args.daemon == "True"
    global pidfile
    pidfile = args.pidfile
    if isDaemon:
        import daemon
        import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile, 'a')
        context.stdout = open(args.logfile, 'a')
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
        print "Starting federation service"
        Log.configureLogging("federation")
        # There is a race condition here but it will do for us.
        if os.path.exists(args.pidfile):
            pid = open(args.pidfile).read()
            try:
                os.kill(int(pid), 0)
                print "svc is running -- not starting"
                sys.exit(-1)
                os._exit(-1)
            except:
                print "removing pidfile and starting"
                os.remove(args.pidfile)
        context.pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pidfile)
        with context:
            proc = Process(target=PeerConnectionManager.start)
            proc.start()
            jobs.append(proc.pid)
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            app.config['CORS_HEADERS'] = 'Content-Type'
            Log.loadGwtSymbolMap()
            app.debug = True
            server = pywsgi.WSGIServer(('localhost', 8002), app)
            server.serve_forever()
    else:
        print "Starting federation service"
        with util.pidfile(pidfile):
            Log.configureLogging("federation")
            proc = Process(target=PeerConnectionManager.start)
            proc.start()
            jobs.append(proc.pid)
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            app.config['CORS_HEADERS'] = 'Content-Type'
            Log.loadGwtSymbolMap()
            app.debug = True
            server = pywsgi.WSGIServer(('localhost', 8002), app)
            server.serve_forever()
