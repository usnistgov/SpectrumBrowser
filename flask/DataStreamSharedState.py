'''
Created on Jun 4, 2015

@author: local
'''
import util
import time
import memcache
import os

class MemCache:
    """
    Keeps a memory map of the data pushed by the sensor so it is accessible
    by any of the flask worker processes.
    """
    def acquire(self):
        counter = 0
        while True:
            self.mc.add("dataStreamingLock",self.key)
            val = self.mc.get("dataStreamingLock")
            if val == self.key:
                break
            else:
                counter = counter + 1
                assert counter < 30,"dataStreamingLock counter exceeded."
                time.sleep(0.1)
                
    def isAquired(self):
        return self.mc.get("dataStreamingLock") != None
    
    def release(self):
        self.mc.delete("dataStreamingLock")
    
    
    
    def __init__(self):
        #self.mc = memcache.Client(['127.0.0.1:11211'], debug=0,cache_cas=True)
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.lastDataMessage = {}
        self.lastdataseen = {}
        self.sensordata = {}
        self.dataCounter = {}
        self.dataProducedCounter = {}
        self.dataConsumedCounter = {}
        self.key = os.getpid()
        self.acquire()
        if self.mc.get("dataCounter") == None:
            self.mc.set("dataCounter",self.dataCounter)
        if self.mc.get("PubSubPortCounter") == None:
            self.mc.set("PubSubPortCounter",0)
        self.release()

        
        
    def setSocketServerPort(self,port):
        self.acquire()
        socketServerPort = self.mc.get("socketServerPort")
        if socketServerPort == None:
            socketServerPort = []
        socketServerPort.append(port)
        self.mc.set("socketServerPort",socketServerPort)
        self.release()
        
    def getNumberOfWorkers(self):
        socketServerPort = self.mc.get("socketServerPort")
        if socketServerPort == None:
            return 0
        else :
            return len(socketServerPort)
    
    def getSocketServerPorts(self):
        return self.mc.get("socketServerPort")


    def loadLastDataMessage(self,sensorId,bandName):
        key = str("lastDataMessage_"+sensorId + ":" + bandName).encode("UTF-8")
        util.debugPrint( "loadLastDataMessage : " + key)
        lastDataMessage = self.mc.get(key)
        if lastDataMessage != None:
            self.lastDataMessage[sensorId + ":" + bandName] = lastDataMessage
        return self.lastDataMessage

    def setLastDataMessage(self,sensorId,bandName,message):
        key = str("lastDataMessage_"+sensorId+":"+bandName).encode("UTF-8")
        util.debugPrint( "setLastDataMessage: key= " + key)
        self.lastDataMessage[sensorId+":"+bandName] = message
        self.mc.set(key,message)

    def loadSensorData(self,sensorId,bandName):
        key = str("sensordata_"+sensorId+":" + bandName).encode("UTF-8")
        sensordata = self.mc.get(key)
        if sensordata != None:
            self.sensordata[sensorId + ":" + bandName] = sensordata
        return self.sensordata

    def setSensorData(self,sensorId,bandName,data):
        key = str("sensordata_"+sensorId + ":" + bandName).encode("UTF-8")
        self.sensordata[sensorId + ":" + bandName] = data
        self.mc.set(key,data)
        
    def printSensorData(self,sensorId,bandName):
        key = str("sensordata_"+sensorId + ":" + bandName).encode("UTF-8")
        print self.mc.get(key)
        
    def printLastDataMessage(self,sensorId,bandName):
        key = str("lastDataMessage_"+sensorId+":"+bandName).encode("UTF-8")
        print self.mc.get(key)


    def incrementDataProducedCounter(self,sensorId,bandName):
        key  = sensorId + ":" + bandName
        if key in self.dataProducedCounter:
            newCount = self.dataProducedCounter[key]+1
        else:
            newCount = 1
        self.dataProducedCounter[key] = newCount


    def incrementDataConsumedCounter(self,sensorId,bandName):
        key = sensorId + ":" + bandName
        if key in self.dataConsumedCounter:
            newCount = self.dataConsumedCounter[key]+1
        else:
            newCount = 1
        self.dataConsumedCounter[key] = newCount


    def setLastDataSeenTimeStamp(self,sensorId,bandName,timestamp):
        key = str("lastdataseen_"+ sensorId + ":" + bandName).encode("UTF-8")
        self.mc.set(key,timestamp)

    def loadLastDataSeenTimeStamp(self,sensorId,bandName):
        key = str("lastdataseen_"+sensorId + ":" + bandName).encode("UTF-8")
        lastdataseen = self.mc.get(key)
        if lastdataseen != None:
            self.lastdataseen[sensorId+ ":" +bandName] = lastdataseen
        return self.lastdataseen
    
    def getPubSubPort(self,sensorId):
        self.acquire()
        try:
            key = str("PubSubPort_"+ sensorId).encode("UTF-8")
            port = self.mc.get(key)
            if port != None:
                return int(port)
            else:
                globalPortCounterKey = str("PubSubPortCounter").encode("UTF-8")
                globalPortCounter = int(self.mc.get(globalPortCounterKey))    
                port = 10000 + globalPortCounter 
                globalPortCounter = globalPortCounter + 1
                self.mc.set(globalPortCounterKey,globalPortCounter)
                self.mc.set(key,port)
                return port
        finally:
            self.release()
        
    def incrementSubscriptionCount(self,sensorId):
        self.acquire()
        try:
            key = str("PubSubSubscriptionCount_" + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount == None:
                self.mc.set(key,1)
            else:
                subscriptionCount = subscriptionCount + 1
                self.mc.set(key,subscriptionCount)
        finally:
            self.release()
            
    def decrementSubscriptionCount(self,sensorId):
        self.acquire()
        try:
            key = str("PubSubSubscriptionCount_" + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount == None:
                return
            else:
                subscriptionCount = subscriptionCount - 1
                self.mc.set(key,subscriptionCount)
                if subscriptionCount < 0:
                    util.errorPrint("DataStreaming: negative subscription count! " + sensorId)
        finally:
            self.release()
            
    def getSubscriptionCount(self,sensorId):
            
        key = str("PubSubSubscriptionCount_" + sensorId).encode("UTF-8")
        subscriptionCount = self.mc.get(key)
        if subscriptionCount == None:
            return 0
        else:
            return subscriptionCount   
