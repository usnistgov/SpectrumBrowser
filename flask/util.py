from flask import jsonify
import os
import DebugFlags
import DbCollections
from Defines import SENSOR_ID
import logging
from logging import DEBUG
from logging import ERROR
import traceback
import StringIO

FORMAT = "%(levelname)s %(asctime)-15s %(message)s"
if DebugFlags.debug:
    logging.basicConfig(format=FORMAT,level= logging.DEBUG, filename="logs/spectrumbrowser.log")
else:
    logging.basicConfig(format=FORMAT,level=logging.ERROR,filename="logs/spectrumbrowser.log")



global launchedFromMain


def getPath(x):
    if "launchedFromMain" in globals() and launchedFromMain:
        return x
    else:
        flaskRoot = os.environ['SPECTRUM_BROWSER_HOME'] + "/flask/"
        return flaskRoot + x


def debugPrint(string):
    logger = logging.getLogger("spectrumbrowser")
    logger.debug(string)
    

def logStackTrace(tb):
    tb_output = StringIO.StringIO()
    traceback.print_tb(tb, None, tb_output)
    logger = logging.getLogger('spectrumbrowser')
    logger.error(tb_output.getvalue())
    tb_output.close()
    
def errorPrint(string):
    logger = logging.getLogger("spectrumbrowser")
    logger.error(string)

def roundTo1DecimalPlaces(value):
    newVal = int((value+0.05)*10)
    return float(newVal)/float(10)

def roundTo2DecimalPlaces(value):
    newVal = int((value+0.005)*100)
    return float(newVal)/float(100)

def roundTo3DecimalPlaces(value):
    newVal = int((value+.0005)*1000)
    return float(newVal)/float(1000)


def formatError(errorStr):
    return jsonify({"Error": errorStr})


            
def getMySensorIds():
    """
    get a collection of sensor IDs that we manage.
    """
    sensorIds = set()
    systemMessages = DbCollections.getSystemMessages().find()
    for systemMessage in systemMessages:
        sid = systemMessage[SENSOR_ID]
        sensorIds.add(sid)
    return sensorIds

def generateUrl(protocol,host,port):
    return protocol+ "://" + host + ":" + str(port)
