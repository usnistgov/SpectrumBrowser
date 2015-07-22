'''
Created on Jun 24, 2015

@author: mdb4
'''

import util
import argparse
from ResourceDataSharedState import MemCache
#from StreamingServer import MemCache as SensorMemCache
import psutil
import traceback
import sys
import gevent
import Defines
import os
import signal



memCache = None
sensMemCache = None
    
    
def readResourceUsage():
    util.debugPrint("ResourceStreaming:dataFromStreamingServer_PID")
    
    #p = psutil.Process(sysPID) # more exact to process
    timePerMeasurement = 0.01
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
            diskData = 0
            netSentData = 0
            netRecvData = 0
            
                            
            bufferCounter = 0
               
            while True:
                # all data is by system as a percent usage, could be modified to be by process
                #cpu = p.cpu_percent()
            
                #vmem = p.virtual_memory()._asdict()['percent']
                
                cpu = psutil.cpu_percent()
                
                vmem = psutil.virtual_memory()._asdict()['percent']
            
                disk = psutil.disk_usage('/')._asdict()['percent'] # Ranga plans to refactor the path
                    
                netSent = psutil.net_io_counters()._asdict()['bytes_sent']
                
                netRecv = psutil.net_io_counters()._asdict()['bytes_recv']
                
                # using psutil.network_io_counters(pernic=True) gives counters by interface.  See the psutil documentation
          
                cpuData = cpuData + cpu
                vmemData = vmemData + vmem
                diskData = diskData + disk
                netSentData = netSentData + netSent
                netRecvData = netRecvData + netRecv
                
                bufferCounter = bufferCounter + 1
                
                if bufferCounter == measurementsPerCapture:
                    # Buffer is full so push the data into memcache.
                    bufferCounter = 0
                    # avg values:
                    cpuValue = cpuData/measurementsPerCapture
                    vmemValue = vmemData/measurementsPerCapture
                    diskValue = diskData/measurementsPerCapture
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
                    
                    memCache.setResourceData(Defines.RESOURCEKEYS_CPU, cpuValue)
                    memCache.setResourceData(Defines.RESOURCEKEYS_VIRTMEM, vmemValue)
                    memCache.setResourceData(Defines.RESOURCEKEYS_DISK, diskValue)
                    memCache.setResourceData(Defines.RESOURCEKEYS_NET_SENT, netSentValue)
                    memCache.setResourceData(Defines.RESOURCEKEYS_NET_RECV, netRecvValue)
                    
                    break
                    
                # 1 millisecond between measurements
                sleepTime = timePerMeasurement
                gevent.sleep(sleepTime)
           
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        

def startStreamingServer():
    # The following code fragment is executed when the module is loaded.
    global memCache
    if memCache == None :
        memCache = MemCache()
        
    #global sensMemCache
    #if sensMemCache == None :
    #    sensMemCache = SensorMemCache() # BUG, this instance may not point to the instance where StreamingServer is operating, needs more testing

    #sysPID = sensMemCache.getPID() This code block will be used if data is requested by process '''
    readResourceUsage()
    
def signal_handler(signo, frame):
    print('ResourceStreamingServer : Caught signal! Exitting.')
    os._exit(0)   
        
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".resourceStreaming.pid")
    args = parser.parse_args()
    
    print "Starting streaming server"
    with util.PidFile(args.pidfile):
        startStreamingServer()

