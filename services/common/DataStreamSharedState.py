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
import util
import time
import memcache
import os
import socket

STREAMING_SENSOR_DATA = "streaming_sensordata_"
STREAMING_DATA_COUNTER = "streaming_dataCounter"
OCCUPANCY_PORT_COUNTER = "occupancy_PubSubPortCounter"
OCCUPANCY_SUBSCRIPTION_COUNT = "occupancy_PubSubSubscriptionCount_"
OCCUPANCY_PUBSUB_PORT = "occupancy_PubSubPort_"
STREAMING_SOCKET_SERVER_PORT = "streaming_socketServerPort"
STREAMING_LAST_DATA_MESSAGE = "streaming_lastDataMessage_"
STREAMING_TIMESTAMP_PREFIX = "streaming_lastDataSeen_"
STREAMING_SUBSCRIBER_COUNT = "streaming_subscriberCount"
STREAMING_SERVER_PID = "streaming_serverPid_"
SENSOR_ARM_PUBSUB_PORT = "sensor_arm_PubSubPort_"


class MemCache:
    """
    Keeps a memory map of the data pushed by the sensor so it is accessible
    by any of the flask worker processes.
    """

    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.lastDataMessage = {}
        self.lastdataseen = {}
        self.sensordata = {}
        self.dataCounter = {}
        self.dataProducedCounter = {}
        self.dataConsumedCounter = {}
        self.key = os.getpid()
        self.acquire()
        try:
            if self.mc.get(STREAMING_DATA_COUNTER) is None:
                self.mc.set(STREAMING_DATA_COUNTER, self.dataCounter)
            if self.mc.get(OCCUPANCY_PORT_COUNTER) is None:
                self.mc.set(OCCUPANCY_PORT_COUNTER, 0)
        finally:
            self.release()

    def acquire(self):
        return

#counter = 0
#while True:
#    self.mc.add("dataStreamingLock", self.key)
#    val = self.mc.get("dataStreamingLock")
#    if val == self.key:
#        break
#    else:
#        counter = counter + 1
#        assert counter < 30, "dataStreamingLock counter exceeded."
#        time.sleep(0.1)

    def clearLock(self):
        return

    def isAquired(self):
        return self.mc.get("dataStreamingLock") is not None

    def release(self):
        return

    def getPID(self):
        if self.key is None:
            self.key = os.getpid()
        return self.key

    def setSocketServerPort(self, port):
        self.mc.set(STREAMING_SOCKET_SERVER_PORT, port)

    def getSocketServerPort(self):
        port = self.mc.get(STREAMING_SOCKET_SERVER_PORT)
        if port is None:
            return -1
        else:
            return int(port)

    def loadLastDataMessage(self, sensorId, bandName):
        key = str(STREAMING_LAST_DATA_MESSAGE + sensorId + ":" +
                  bandName).encode("UTF-8")
        util.debugPrint("loadLastDataMessage : " + key)
        lastDataMessage = self.mc.get(key)
        if lastDataMessage is not None:
            self.lastDataMessage[sensorId + ":" + bandName] = lastDataMessage
        return self.lastDataMessage

    def setLastDataMessage(self, sensorId, bandName, message):
        key = str(STREAMING_LAST_DATA_MESSAGE + sensorId + ":" +
                  bandName).encode("UTF-8")
        util.debugPrint("setLastDataMessage: key= " + key)
        self.lastDataMessage[sensorId + ":" + bandName] = message
        self.mc.set(key, message)

    def loadSensorData(self, sensorId, bandName):
        key = str(STREAMING_SENSOR_DATA + sensorId + ":" + bandName).encode(
            "UTF-8")
        sensordata = self.mc.get(key)
        if sensordata is not None:
            self.sensordata[sensorId + ":" + bandName] = sensordata
        return self.sensordata

    def setSensorData(self, sensorId, bandName, data):
        key = str(STREAMING_SENSOR_DATA + sensorId + ":" + bandName).encode(
            "UTF-8")
        self.sensordata[sensorId + ":" + bandName] = data
        self.mc.set(key, data)

    def printSensorData(self, sensorId, bandName):
        key = str(STREAMING_SENSOR_DATA + sensorId + ":" + bandName).encode(
            "UTF-8")
        print self.mc.get(key)

    def printLastDataMessage(self, sensorId, bandName):
        key = str(STREAMING_LAST_DATA_MESSAGE + sensorId + ":" +
                  bandName).encode("UTF-8")
        print self.mc.get(key)

    def incrementDataProducedCounter(self, sensorId, bandName):
        key = sensorId + ":" + bandName
        if key in self.dataProducedCounter:
            newCount = self.dataProducedCounter[key] + 1
        else:
            newCount = 1
        self.dataProducedCounter[key] = newCount

    def incrementDataConsumedCounter(self, sensorId, bandName):
        key = sensorId + ":" + bandName
        if key in self.dataConsumedCounter:
            newCount = self.dataConsumedCounter[key] + 1
        else:
            newCount = 1
        self.dataConsumedCounter[key] = newCount

    def setLastDataSeenTimeStamp(self, sensorId, bandName, timestamp):
        key = str(STREAMING_TIMESTAMP_PREFIX + sensorId + ":" +
                  bandName).encode("UTF-8")
        self.mc.set(key, timestamp)

    def loadLastDataSeenTimeStamp(self, sensorId, bandName):
        key = str(STREAMING_TIMESTAMP_PREFIX + sensorId + ":" +
                  bandName).encode("UTF-8")
        lastdataseen = self.mc.get(key)
        if lastdataseen is not None:
            self.lastdataseen[sensorId + ":" + bandName] = lastdataseen
        return self.lastdataseen

    def getPubSubPort(self, sensorId):
        self.acquire()
        try:
            key = str(OCCUPANCY_PUBSUB_PORT + sensorId).encode("UTF-8")
            port = self.mc.get(key)
            if port is not None:
                return int(port)
            else:
                globalPortCounter = int(self.mc.get(OCCUPANCY_PORT_COUNTER))
                port = 20000 + globalPortCounter
                globalPortCounter = globalPortCounter + 1
                self.mc.set(OCCUPANCY_PORT_COUNTER, globalPortCounter)
                self.mc.set(key, port)
                return port
        finally:
            self.release()

    # The port to arm a sensor.
    def getSensorArmPort(self, sensorId):
        self.acquire()
        try:
            key = str(SENSOR_ARM_PUBSUB_PORT + sensorId).encode("UTF-8")
            port = self.mc.get(key)
            if port is not None:
                return int(port)
            else:
                globalPortCounter = int(self.mc.get(OCCUPANCY_PORT_COUNTER))
                port = 20000 + globalPortCounter
                globalPortCounter = globalPortCounter + 1
                self.mc.set(OCCUPANCY_PORT_COUNTER, globalPortCounter)
                self.mc.set(key, str(port))
                return port
        finally:
            self.release()

    def releaseSensorArmPort(self, sensorId):
        self.acquire()
        try:
            key = str(SENSOR_ARM_PUBSUB_PORT + sensorId).encode("UTF-8")
            self.mc.delete(key)
        finally:
            self.release()

    def setStreamingServerPid(self, sensorId):
        self.acquire()
        try:
            pid = os.getpid()
            key = str(STREAMING_SERVER_PID + sensorId).encode("UTF-8")
            self.mc.delete(key)
            self.mc.set(key, str(pid))
        finally:
            self.release()

    def removeStreamingServerPid(self, sensorId):
        self.acquire()
        try:
            key = str(STREAMING_SERVER_PID + sensorId).encode("UTF-8")
            self.mc.set(key, None)
            self.mc.delete(key)
        finally:
            self.release()

    def getStreamingServerPid(self, sensorId):
        key = str(STREAMING_SERVER_PID + sensorId).encode("UTF-8")
        pid = self.mc.get(key)
        if pid is None:
            return -1
        else:
            return int(pid)

    def incrementSubscriptionCount(self, sensorId):
        self.acquire()
        try:
            key = str(OCCUPANCY_SUBSCRIPTION_COUNT + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount is None:
                self.mc.set(key, 1)
            else:
                subscriptionCount = subscriptionCount + 1
                self.mc.set(key, subscriptionCount)
        finally:
            self.release()

    def incrementStreamingListenerCount(self, sensorId):
        self.acquire()
        try:
            key = str(STREAMING_SUBSCRIBER_COUNT + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount is None:
                self.mc.set(key, 1)
            else:
                subscriptionCount = subscriptionCount + 1
                self.mc.set(key, subscriptionCount)
        finally:
            self.release()

    def decrementStreamingListenerCount(self, sensorId):
        self.acquire()
        try:
            key = str(STREAMING_SUBSCRIBER_COUNT + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount is None:
                return
            else:
                subscriptionCount = subscriptionCount - 1
                self.mc.set(key, subscriptionCount)
                if subscriptionCount < 0:
                    util.errorPrint(
                        "DataStreaming: negative subscription count! " +
                        sensorId)
        finally:
            self.release()

    def decrementSubscriptionCount(self, sensorId):
        self.acquire()
        try:
            key = str(OCCUPANCY_SUBSCRIPTION_COUNT + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount is None:
                return
            else:
                subscriptionCount = subscriptionCount - 1
                self.mc.set(key, subscriptionCount)
                if subscriptionCount < 0:
                    util.errorPrint(
                        "DataStreaming: negative subscription count! " +
                        sensorId)
        finally:
            self.release()

    def getSubscriptionCount(self, sensorId):
        try:
            key = str(OCCUPANCY_SUBSCRIPTION_COUNT + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount is None:
                return 0
            else:
                return int(subscriptionCount)
        except:
            return 0

    def getStreamingListenerCount(self, sensorId):
        try:
            key = str(STREAMING_SUBSCRIBER_COUNT + sensorId).encode("UTF-8")
            subscriptionCount = self.mc.get(key)
            if subscriptionCount is None:
                return 0
            else:
                return subscriptionCount
        except:
            return 0


def sendCommandToSensor(sensorId, command):
    memCache = MemCache()
    port = memCache.getSensorArmPort(sensorId)
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.sendto(command, ("localhost", port))
    soc.close()
