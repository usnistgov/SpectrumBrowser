import subprocess
import sys
import traceback
import os
import time
import argparse
import signal
from ReadDiskUtil import readDiskUtil



if __name__ == '__main__':
    launchedFromMain = True
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".dbmonitoring.pid")
    parser.add_argument('--dbpath', help='Database path -- required')
    args = parser.parse_args()

    with util.PidFile(args.pidfile):
        Log.configureLogging("dbmonitor")
        disk = readDiskUtil(args.dbpath)
        time.sleep(60)
        
