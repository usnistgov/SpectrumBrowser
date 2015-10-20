#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
'''
Created on Jun 24, 2015

@author: mdb4
'''

import Bootstrap
Bootstrap.setPath()
Bootstrap.setAdminPath()
import util
import argparse
from ResourceDataSharedState import MemCache
import psutil
import sys
import socket
import signal
import Config
import netifaces
import Log
import time
import MemCacheKeys
import lockfile
import logging
import pwd
import os

memCache = None


def readResourceUsage():
    util.debugPrint("ResourceStreaming:dataFromStreamingServer_PID")

    timePerMeasurement = 0.2
    timePerCapture = 1 # 1 sec per capture
    measurementsPerCapture = timePerCapture/timePerMeasurement

    try:
        while True:

            if not "firstTime" in vars():
                firstTime = True
            if not "netSentValuePrev" in vars():
                netSentValuePrev = 0
            if not "netRecvValuePrev" in vars():
                netRecvValuePrev = 0

            cpuData = 0
            vmemData = 0
            netSentData = 0
            netRecvData = 0

            bufferCounter = 0

            while True:
                # all data is by system as a percent usage, could be modified to be by process
                #cpu = p.cpu_percent()

                #vmem = p.virtual_memory()._asdict()['percent']

                cpu = psutil.cpu_percent()

                vmem = psutil.virtual_memory()._asdict()['percent']


                hostName = Config.getHostName()
                monitoredInterface = None
                try:
                    if hostName != "UNKNOWN":
                        ipAddress = socket.gethostbyname(hostName)
                        for interface in netifaces.interfaces():
                            if netifaces.AF_INET in netifaces.ifaddresses(interface):
                                for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                                    if link['addr'] == ipAddress:
                                        monitoredInterface = interface
                                        break
                except:
                    util.errorPrint("Could not resolve hostname " + hostName)

                if monitoredInterface != None:
                    netSent = psutil.net_io_counters(pernic=True)[monitoredInterface]._asdict()['bytes_sent']
                    netRecv = psutil.net_io_counters(pernic=True)[monitoredInterface]._asdict()['bytes_recv']
                else:
                    netSent = 0
                    netRecv = 0


                cpuData = cpuData + cpu
                vmemData = vmemData + vmem
                netSentData = netSentData + netSent
                netRecvData = netRecvData + netRecv

                bufferCounter = bufferCounter + 1

                if bufferCounter == measurementsPerCapture:
                    # Buffer is full so push the data into memcache.
                    bufferCounter = 0
                    # avg values:
                    cpuValue = cpuData/measurementsPerCapture
                    vmemValue = vmemData/measurementsPerCapture
                    netSentValueNew = netSentData/measurementsPerCapture
                    netRecvValueNew = netRecvData/measurementsPerCapture

                    if not firstTime :
                        netSentValue = (netSentValueNew - netSentValuePrev)/timePerCapture
                        netRecvValue = (netRecvValueNew - netRecvValuePrev)/timePerCapture

                    else :
                        netSentValue = 0
                        netRecvValue = 0
                        firstTime = False

                    netSentValuePrev = netSentValueNew
                    netRecvValuePrev = netRecvValueNew

                    memCache.setResourceData(MemCacheKeys.RESOURCEKEYS_CPU, cpuValue)
                    memCache.setResourceData(MemCacheKeys.RESOURCEKEYS_VIRTMEM, vmemValue)
                    memCache.setResourceData(MemCacheKeys.RESOURCEKEYS_NET_SENT, netSentValue)
                    memCache.setResourceData(MemCacheKeys.RESOURCEKEYS_NET_RECV, netRecvValue)

                    break

                sleepTime = timePerMeasurement
                time.sleep(sleepTime)

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        import traceback
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())


def startStreamingServer():
    global memCache
    if memCache == None :
        memCache = MemCache()

    readResourceUsage()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".monitoring.pid")
    parser.add_argument("--logfile", help="LOG file", default="/tmp/monitoring.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")
    parser.add_argument("--daemon", help="daemon flag", default="True")
    args = parser.parse_args()
    daemonFlag = args.daemon == "True"


    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)

    if daemonFlag:
	import daemon
	import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile,'a')
        context.stdout = open(args.logfile,'a')
        context.files_preserve = [fh.stream]
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
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
            Log.configureLogging("monitoring")
            startStreamingServer()
    else:
        with util.pidfile(args.pidfile):
            startStreamingServer()


