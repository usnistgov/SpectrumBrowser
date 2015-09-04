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
import Config
from flask import Flask, request, abort
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
import daemon
import daemon.pidfile
import pwd
##########################################################################################

app = Flask(__name__, static_url_path="")

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
        util.debugPrint(msg)
        sensorId = msg[SENSOR_ID]
        key = msg[SENSOR_KEY]
        if not authentication.authenticateSensor(sensorId, key):
            abort(403)
        populate_db.put_message(msg)
        return "OK"
    except:
        util.logStackTrace(sys.exc_info())
        traceback.print_exc()
        raise

if __name__ == '__main__':
    global jobs
    jobs = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".spectrumdb.pid")
    parser.add_argument("--logfile", help="LOG file", default="/var/log/admin.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")
    args = parser.parse_args()
    context = daemon.DaemonContext()

    args = parser.parse_args()

    context.stdin = sys.stdin
    context.stderr = open(args.logfile,'a')
    context.stdout = open(args.logfile,'a')

    context.pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pidfile)

    context.uid = pwd.getpwnam(args.username).pw_uid
    context.gid = pwd.getpwnam(args.groupname).pw_gid


    print "Starting upload service"
    with context:
        Log.configureLogging("spectrumdb")
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        app.config['CORS_HEADERS'] = 'Content-Type'
        app.debug = True
        if Config.isConfigured():
            server = pywsgi.WSGIServer(('localhost', 8003), app)
        else:
            server = pywsgi.WSGIServer(('localhost', 8003), app)
        server.serve_forever()
