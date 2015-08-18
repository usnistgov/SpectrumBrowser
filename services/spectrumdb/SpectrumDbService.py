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
    args = parser.parse_args()

    print "Starting upload service"
    with util.PidFile(args.pidfile):
        Log.configureLogging("spectrumdb")
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        app.config['CORS_HEADERS'] = 'Content-Type'
        app.debug = True
        if Config.isConfigured():
            server = pywsgi.WSGIServer(('localhost', 8003), app)
        else:
            server = pywsgi.WSGIServer(('localhost', 8003), app)
        server.serve_forever()
