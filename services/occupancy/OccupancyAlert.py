#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
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
import zmq
import json
import socket
from bitarray import bitarray
import argparse
from multiprocessing import Process
import os
import signal
import Log
import time
import daemon
import daemon.pidfile
import lockfile
import logging
import pwd

from DataStreamSharedState import MemCache

isSecure = Config.isSecure()

childPids = []

def runOccupancyWorker(conn):

    context = zmq.Context()
    sock = context.socket(zmq.SUB)
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
        sock.setsockopt_string(zmq.SUBSCRIBE, unicode(""))
        sock.connect("tcp://localhost:" + str(memcache.getPubSubPort(sensorId)))
        memcache.incrementSubscriptionCount(sensorId)
        try :
            while True:
                msg = sock.recv_pyobj()
                if sensorId in msg:
                    msgdatabin = bitarray(msg[sensorId])
                    conn.send(msgdatabin.tobytes())
        except:
            print sys.exc_info()
            traceback.print_exc()
            print "Subscriber disconnected"
        finally:
            memcache.decrementSubscriptionCount(sensorId)

    except:
        tb = sys.exc_info()
        util.logStackTrace(tb)
    finally:
        if conn != None:
            conn.close()
        if sock != None:
            sock.close()


def startOccupancyServer(socket):
        global childPids
        while True:
            try :
                print "OccupancyServer: Accepting connections "
                (conn, addr) = socket.accept()
                if isSecure:
                    try :
                        cert = Config.getCertFile()

                        c = ssl.wrap_socket(conn,server_side = True, certfile = cert, keyfile=Config.getKeyFile(),ssl_version=ssl.PROTOCOL_SSLv3  )

                        t = Process(target=runOccupancyWorker, args=(c,))
                    except:
                        print "CertFile = ",cert
                        traceback.print_exc()
                        conn.close()
                        util.errorPrint("OccupancyServer: Error accepting connection")
                        util.logStackTrace(sys.exc_info())
                        continue
                else:
                    t = Process(target=runOccupancyWorker, args=(conn,))
                util.debugPrint("OccupancyServer: Accepted a connection from " + str(addr))
                t.start()
                pid = t.pid
                childPids.append(pid)
            except:
                traceback.print_exc()

def signal_handler(signo, frame):
        print('Occupancy Alert: Caught signal! Exitting.')
        for pid in childPids:
            try:
                print "Killing : " , pid
                os.kill(pid, signal.SIGKILL)
            except:
                print str(pid), " Not Found"


if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".occupancy.pid")
    parser.add_argument("--logfile", help="LOG file", default="/var/log/occupancy.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")

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
        time.sleep(10)
        occupancySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occupancyServerPort = Config.getOccupancyAlertPort()
        print "OccupancyServer: port = ", occupancyServerPort
        if occupancyServerPort != -1 :
            occupancySock.bind(('0.0.0.0', occupancyServerPort))
            occupancySock.listen(10)
            occupancyServer = startOccupancyServer(occupancySock)
            occupancyServer.start()
        else:
            print "Not starting occupancy server"
