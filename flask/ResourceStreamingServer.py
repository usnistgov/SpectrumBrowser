'''
Created on Jun 24, 2015

@author: mdb4
'''

import util
import argparse
from ResourceDataSharedState import MemCache
from StreamingServer import MemCache as SensorMemCache
import psutil
import traceback
import sys
import gevent
import Defines


memCache = None
sensMemCache = None
    
    
def readResourceUsage(sysPID):
    util.debugPrint("ResourceStreaming:dataFromStreamingServer_PID")
    
    #p = psutil.Process(sysPID) # more exact to process
    timePerMeasurement = 0.01
    measurementsPerCapture = 1/timePerMeasurement # 1 sec per capture
    
    try:
        while True:
            
            cpuData = 0
            vmemData = 0
            diskData = 0
                
            bufferCounter = 0
               
            while True:
                # all data is by system as a percent usage, could be modified to be by process
                #cpu = p.cpu_percent()
            
                #vmem = p.virtual_memory()._asdict()['percent']
                
                # Basic data
                
                cpu = psutil.cpu_percent()
                
                vmem = psutil.virtual_memory()._asdict()['percent']
            
                disk = psutil.disk_usage('/')._asdict()['percent'] # disk usage for home path '/'
                    
                cpuData = cpuData + cpu
                vmemData = vmemData + vmem
                diskData = diskData + disk
                
                bufferCounter = bufferCounter + 1
                
                if bufferCounter == measurementsPerCapture:
                    # Buffer is full so push the data into memcache.
                    util.debugPrint("Inserting Data message")
                    bufferCounter = 0
                    # avg values over 1 sec:
                    cpuValue = cpuData/measurementsPerCapture
                    vmemValue = vmemData/measurementsPerCapture
                    diskValue = diskData/measurementsPerCapture
                    
                    memCache.setResourceData(Defines.RESOURCEKEYS[0], cpuValue)
                    memCache.setResourceData(Defines.RESOURCEKEYS[1], vmemValue)
                    memCache.setResourceData(Defines.RESOURCEKEYS[2], diskValue)
                    
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
        
    global sensMemCache
    if sensMemCache == None :
        sensMemCache = SensorMemCache() # BUG, this instance may not point to the instance where StreamingServer is operating, needs more testing

    sysPID = sensMemCache.getPID()
    readResourceUsage(sysPID)
    
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".resourceStreaming.pid")
    args = parser.parse_args()
    
    print "Starting streaming server"
    with util.PidFile(args.pidfile):
        startStreamingServer()

