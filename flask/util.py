import os
import DebugFlags
import DbCollections
from Defines import SENSOR_ID
import logging
import traceback
import StringIO
import Bootstrap
import fcntl

FORMAT = "%(levelname)s %(asctime)-15s %(message)s"
if not logging.getLogger("spectrumbrowser").disabled:
    loglvl = DebugFlags.getLogLevel()
    logging.basicConfig(
       format=FORMAT,
       level=loglvl,
       filename=os.path.join(Bootstrap.getFlaskLogDir(), "spectrumbrowser.log")
    )

global launchedFromMain


class PidFile(object):
    """Context manager that locks a pid file.
    http://code.activestate.com/recipes/577911-context-manager-for-a-daemon-pid-file/

    Example usage:
    >>> with PidFile('running.pid'):
    ...     f = open('running.pid', 'r')
    ...     print("This context has lockfile containing pid {}".format(f.read()))
    ...     f.close()
    ...
    This context has lockfile containing pid 31445
    >>> os.path.exists('running.pid')
    False

    """
    def __init__(self, path):
        self.path = path
        self.pidfile = None

    def __enter__(self):
        self.pidfile = open(self.path, "a+")
        try:
            fcntl.flock(self.pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise SystemExit("Already running according to " + self.path)
        self.pidfile.seek(0)
        self.pidfile.truncate()
        self.pidfile.write(str(os.getpid()) + '\n')
        self.pidfile.flush()
        self.pidfile.seek(0)
        return self.pidfile

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        try:
            self.pidfile.close()
        except IOError as err:
            # ok if file was just closed elsewhere
            if err.errno != 9:
                raise
        os.remove(self.path)


def getPath(x):
    flaskRoot = Bootstrap.getSpectrumBrowserHome() + "/flask/"
    return flaskRoot + x

def debugPrint(string):
    logger = logging.getLogger("spectrumbrowser")
    logger.debug(string)

def logStackTrace(tb):
    tb_output = StringIO.StringIO()
    traceback.print_stack(limit=None, file=tb_output)
    logger = logging.getLogger('spectrumbrowser')
    logging.exception("Exception occured")
    logger.error(tb_output.getvalue())
    tb_output.close()

def errorPrint(string):
    print "ERROR: ", string
    logger = logging.getLogger("spectrumbrowser")
    logger.error(string)

def roundTo1DecimalPlaces(value):
    newVal = int((value + 0.05) * 10)
    return float(newVal) / float(10)

def roundTo2DecimalPlaces(value):
    newVal = int((value + 0.005) * 100)
    return float(newVal) / float(100)

def roundTo3DecimalPlaces(value):
    newVal = int((value + .0005) * 1000)
    return float(newVal) / float(1000)

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

def generateUrl(protocol, host, port):
    return protocol + "://" + host + ":" + str(port)
