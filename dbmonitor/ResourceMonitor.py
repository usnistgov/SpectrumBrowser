import time
import sys
import argparse
from ReadDiskUtil import readDiskUtil
from pymongo import MongoClient
import signal
import os
import fcntl

# Want to avoid importing anything from the source tree.
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

def readResourceUsage():
    try:
        while True:
            client = MongoClient('localhost',27017);
            collection = client.systemResources.dbResources
            diskVal = readDiskUtil(args.dbpath)
            collection.update({'Disk': diskVal}, {'$set': {'Disk': diskVal}}, upsert=True)
            time.sleep(30)

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        import traceback
        traceback.print_exc()

def signal_handler(signo, frame):
    print('Disk monitor : Caught signal! Exiting.')
    # DO NOT invoke os._exit

if __name__ == '__main__':
    launchedFromMain = True
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".dbmonitoring.pid")
    parser.add_argument('--dbpath', help='Database path -- required')
    args = parser.parse_args()

    # DO NOT import util - this module needs to stand alone.
    with PidFile(args.pidfile):
        readResourceUsage()
