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

'''
Created on Jun 4, 2015

@author: local
'''

import Bootstrap
Bootstrap.setPath()
import ssl
import traceback
import util
import Config
import sys
import json
import socket
from bitarray import bitarray
import argparse
from multiprocessing import Process
import os
import signal
import Log
import pwd
import logging

_OccupancyConnectionDebug = True

from DataStreamSharedState import MemCache

isSecure = Config.isSecure()

childPids = []


def runOccupancyWorker(conn):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    memcache = MemCache()
    sensorId = None
    try:
        c = ""
        jsonStr = ""
        while c != "}":
            c = conn.recv(1)
            jsonStr = jsonStr + c
        jsonObj = json.loads(jsonStr)
        print "subscription received for " + jsonObj["SensorID"]
        sensorId = jsonObj["SensorID"]
        port = memcache.getPubSubPort(sensorId)
        soc.bind(("localhost", port))
        memcache.incrementSubscriptionCount(sensorId)
        try:
            while True:
                msgstr, addr = sock.recvfrom(1024)
                msg = json.loads(msgstr)
                if sensorId in msg:
                    msgdatabin = bitarray(msg[sensorId])
                    conn.send(msgdatabin.tobytes())
        except:
            print sys.exc_info()
            traceback.print_exc()
            print "Subscriber disconnected"
        finally:
            sock.close()
            memcache.decrementSubscriptionCount(sensorId)

    except:
        tb = sys.exc_info()
        util.logStackTrace(tb)
    finally:
        if conn != None:
            conn.close()
        if sock != None:
            sock.close()


def startOccupancyServer(occupancyServerPort):
    global childPids
    global occupancySock
    occupancySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "OccupancyServerPort", occupancyServerPort
    occupancySock.bind(("0.0.0.0", occupancyServerPort))
    occupancySock.listen(10)
    cert = Config.getCertFile()
    keyfile = Config.getKeyFile()
    conn = None
    while True:
        try:
            print "OccupancyServer: Accepting connections "
            (conn, addr) = occupancySock.accept()
            print "Addr connected ", str(addr)
            if isSecure:
                try:
                    c = ssl.wrap_socket(conn,
                                        server_side=True,
                                        certfile=cert,
                                        keyfile=keyfile)
                    # Was : ssl_version=ssl.PROTOCOL_SSLv23)
                    t = Process(target=runOccupancyWorker, args=(c, ))
                except:
                    if conn != None:
                        conn.close()
                        conn = None
                    occupancySock.close()
                    occupancySock = socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM)
                    occupancySock.bind(("0.0.0.0", occupancyServerPort))
                    occupancySock.listen(10)
                    if _OccupancyConnectionDebug:
                        util.errorPrint(
                            "OccupancyServer: Error accepting connection")
                        traceback.print_exc()
                        util.logStackTrace(sys.exc_info())
                    continue
            else:
                t = Process(target=runOccupancyWorker, args=(conn, ))
            util.debugPrint("OccupancyServer: Accepted a connection from " +
                            str(addr))
            t.start()
            pid = t.pid
            childPids.append(pid)
        except:
            print "OccupancyServer: Error ACCEPTING Connection:"
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            if conn != None:
                conn.close()
                conn = None
            occupancySock.close()
            occupancySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            occupancySock.bind(("0.0.0.0", occupancyServerPort))
            occupancySock.listen(10)


def signal_handler(signo, frame):
    global pidfile
    print('Occupancy Alert: Caught signal! Exitting.')
    for pid in childPids:
        try:
            print "Killing : ", pid
            os.kill(pid, signal.SIGKILL)
        except:
            print str(pid), " Not Found"
    os.remove(pidfile)
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".occupancy.pid")
    parser.add_argument("--logfile",
                        help="LOG file",
                        default="/tmp/occupancy.log")
    parser.add_argument("--username",
                        help="USER name",
                        default="spectrumbrowser")
    parser.add_argument("--groupname",
                        help="GROUP name",
                        default="spectrumbrowser")
    parser.add_argument("--port", help="GROUP name", default="9001")
    parser.add_argument("--daemon", help="daemon switch", default="True")

    args = parser.parse_args()

    daemonFlag = args.daemon == "True"

    if not Config.isConfigured():
        print "System not configured"
        sys.exit(0)
        os._exit(0)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)

    global pidfile
    pidfile = args.pidfile

    if daemonFlag:
        import daemon
        import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile, 'a')
        context.stdout = open(args.logfile, 'a')
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
        Log.configureLogging("occupancy")
        occupancyServerPort = int(args.port)
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
            startOccupancyServer(occupancyServerPort)
    else:
        Log.configureLogging("occupancy")
        with util.pidfile(args.pidfile):
            startOccupancyServer(occupancyServerPort)
