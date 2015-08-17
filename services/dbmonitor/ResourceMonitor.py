import subprocess
import sys
import traceback
import os
import time
import argparse
import signal
from ReadDiskUtil import readDiskUtil
from pymongo import MongoClient

def readResourceUsage(dV):
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

                client = MongoClient('localhost',27017);
                db = client['systemResources']
                collection = db['dbResources']
                collection.insert({'DISK': dV})


                sleepTime = timePerMeasurement
                time.sleep(sleepTime)

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        import traceback
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())


if __name__ == '__main__':
    launchedFromMain = True
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".dbmonitoring.pid")
    parser.add_argument('--dbpath', help='Database path -- required')
    args = parser.parse_args()

    with util.PidFile(args.pidfile):
        Log.configureLogging("dbmonitor")
        diskVal = readDiskUtil(args.dbpath)
        time.sleep(30)
        readResourceUsage(diskVal)
        
