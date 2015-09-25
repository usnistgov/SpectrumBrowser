#! /usr/local/bin/python2.7
import time
import sys
import argparse
from ReadDiskUtil import readDiskUtil
from pymongo import MongoClient
import os
import fcntl
import daemon
import daemon.pidfile
import lockfile
import logging
import pwd

# avoid importing util
class pidfile(object):
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


def readResourceUsage(dbpath):
    try:
        while True:
            client = MongoClient('localhost',27017);
            collection = client.systemResources.dbResources
            diskVal = readDiskUtil(dbpath)
            collection.update({}, {'$set': {'Disk': diskVal}}, upsert=True)
            time.sleep(30)

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    launchedFromMain = True
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".dbmonitoring.pid")
    parser.add_argument("--logfile", help="LOG file", default="/tmp/dbmonitoring.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")
    parser.add_argument("--dbpath", help='Database path -- required')
    parser.add_argument("--daemon", help='deamon flag', default= "True")
    args = parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)
    isDaemon = args.daemon == "True"


    if isDaemon:
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
            readResourceUsage(args.dbpath)
    else:
        with pidfile(args.pidfile):
            readResourceUsage(args.dbpath)
