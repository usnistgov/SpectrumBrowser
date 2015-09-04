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
    parser.add_argument("--logfile", help="LOG file", default="/var/log/dbmonitoring.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")
    parser.add_argument("--dbpath", help='Database path -- required')
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
        readResourceUsage(args.dbpath)
