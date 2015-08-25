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
    args = parser.parse_args()

    print "Starting streaming server"
    with util.PidFile(args.pidfile):
        Log.configureLogging("monitoring")
        startStreamingServer()
