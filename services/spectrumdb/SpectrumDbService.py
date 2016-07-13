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

#! /usr/local/bin/python2.7
import Bootstrap
sbHome = Bootstrap.getSpectrumBrowserHome()

import sys
sys.path.append(sbHome + "/services/common")

import util
import traceback
import populate_db
import authentication
import argparse
from gevent import pywsgi
import Log
from flask import Flask, request, abort, jsonify
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
import pwd
import os
import json
import logging
##########################################################################################

app = Flask(__name__, static_url_path="")


@app.route("/spectrumdb/upload", methods=["POST"])
def upload():
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
        populate_db.put_message(request.data)
        return jsonify({"status": "OK"})
    except:
        util.logStackTrace(sys.exc_info())
        traceback.print_exc()
        raise


if __name__ == '__main__':
    global jobs
    jobs = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".spectrumdb.pid")
    parser.add_argument("--logfile",
                        help="LOG file",
                        default="/var/log/admin.log")
    parser.add_argument("--username",
                        help="USER name",
                        default="spectrumbrowser")
    parser.add_argument("--groupname",
                        help="GROUP name",
                        default="spectrumbrowser")
    parser.add_argument("--daemon", help="daemon flag", default="True")
    args = parser.parse_args()

    daemonFlag = args.daemon == "True"

    if daemonFlag:
        import daemon
        import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile, 'a')
        context.stdout = open(args.logfile, 'a')
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
        print "Starting upload service"
        fh = logging.FileHandler(args.logfile)
        logger = logging.getLogger()
        logger.addHandler(fh)
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
            Log.configureLogging("spectrumdb")
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            server = pywsgi.WSGIServer(('localhost', 8003), app)
            server.serve_forever()
    else:
        with util.pidfile(args.pidfile):
            Log.configureLogging("spectrumdb")
            app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
            server = pywsgi.WSGIServer(('localhost', 8003), app)
            server.serve_forever()
