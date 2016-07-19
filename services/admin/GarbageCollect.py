#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 Untied States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.
'''
Created on Feb 11, 2015

@author: local
'''
import DbCollections
import DataMessage
import LocationMessage
import Message
import SensorDb
from Defines import STATIC_GENERATED_FILE_LOCATION
from Defines import SECONDS_PER_DAY, SENSOR_ID, DISABLED, FFT_POWER
import pymongo
import SessionLock
import time
import msgutils
import util
import os
import shutil
from threading import Timer


class RepeatingTimer(object):
    """
        Ref: https://gist.github.com/alexbw/1187132
        USAGE:
        from time import sleep
        def myFunction(inputArgument):
                print(inputArgument)

        r = RepeatingTimer(0.5, myFunction, "hello")
        r.start(); sleep(2); r.interval = 0.05; sleep(2); r.stop()

        """

    def __init__(self, interval, function, *args, **kwargs):
        super(RepeatingTimer, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.function = function
        self.interval = interval

    def start(self):
        self.callback()

    def stop(self):
        self.interval = False

    def callback(self):
        if self.interval:
            self.function(*self.args, **self.kwargs)
            t = Timer(self.interval,
                      self.callback, )
            t.daemon = True
            t.start()


def runGarbageCollector(sensorId):
    SessionLock.acquire()
    try:
        userCount = SessionLock.getUserSessionCount()
        if userCount != 0:
            return {"status": "NOK",
                    "ErrorMessage": "Active user session detected"}
        sensorObj = SensorDb.getSensorObj(sensorId)
        if sensorObj is None:
            return {"status": "NOK", "ErrorMessage": "Sensor Not found"}
        if sensorObj.getSensorStatus() != DISABLED:
            return {"status": "NOK",
                    "ErrorMessage": "Sensor is ENABLED  -- DISABLE it first"}

        dataRetentionDuration = sensorObj.getSensorDataRetentionDurationMonths(
        )
        dataRetentionTime = dataRetentionDuration * 30 * SECONDS_PER_DAY
        cur = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})
        dataMessages = cur.sort('t', pymongo.ASCENDING)
        currentTime = time.time()
        locationMessage = None
        for msg in dataMessages:
            insertionTime = Message.getInsertionTime(msg)
            if currentTime - dataRetentionTime >= insertionTime:
                DbCollections.getDataMessages(sensorId).remove(msg)
            else:
                break

            # Now redo our book keeping summary fields.
        cur = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})
        dataMessages = cur.sort('t', pymongo.ASCENDING)
        locationMessages = DbCollections.getLocationMessages().find(
            {SENSOR_ID: sensorId})
        for locationMessage in locationMessages:
            LocationMessage.clean(locationMessage)
            DbCollections.getLocationMessages().update(
                {"_id": locationMessage["_id"]}, {"$set": locationMessage},
                upsert=False)
        sensorObj.cleanSensorStats()
        # Clean up the cached data in the LocationObj and sensorObj
        for jsonData in dataMessages:
            lastLocationPost = msgutils.getLocationMessage(jsonData)
            LocationMessage(lastLocationPost).clean()

        dataMessages = cur.sort('t', pymongo.ASCENDING)
        for jsonData in dataMessages:
            freqRange = DataMessage.getFreqRange(jsonData)
            minPower = DataMessage.getMinPower(jsonData)
            maxPower = DataMessage.getMaxPower(jsonData)
            if DataMessage.getMeasurementType(jsonData) == FFT_POWER:
                minOccupancy = DataMessage.getMinOccupancy(jsonData)
                maxOccupancy = DataMessage.getMaxOccupancy(jsonData)
                meanOccupancy = DataMessage.getMeanOccupancy(jsonData)
                sensorObj.updateMinOccupancy(freqRange, minOccupancy)
                sensorObj.updateMaxOccupancy(freqRange, maxOccupancy)
                sensorObj.updateOccupancyCount(freqRange, meanOccupancy)
                LocationMessage.updateMaxBandOccupancy(lastLocationPost, freqRange,
                                                       maxOccupancy)
                LocationMessage.updateMinBandOccupancy(lastLocationPost, freqRange,
                                                       minOccupancy)
                LocationMessage.updateOccupancySum(lastLocationPost, freqRange,
                                                   meanOccupancy)
            else:
                occupancy = DataMessage.getOccupancy(jsonData)
                sensorObj.updateMinOccupancy(freqRange, occupancy)
                sensorObj.updateMaxOccupancy(freqRange, occupancy)
                sensorObj.updateOccupancyCount(freqRange, occupancy)
                LocationMessage.updateMaxBandOccupancy(lastLocationPost, freqRange,
                                                       occupancy)
                LocationMessage.updateMinBandOccupancy(lastLocationPost, freqRange,
                                                       occupancy)
                LocationMessage.updateOccupancySum(lastLocationPost, freqRange,
                                                   occupancy)

            DbCollections.getLocationMessages().update(
                {"_id": lastLocationPost["_id"]}, {"$set": lastLocationPost},
                upsert=False)
            # Garbage collect the unprocessed data messages.
            cur = DbCollections.getUnprocessedDataMessages(sensorId).find({SENSOR_ID: sensorId})
            if cur is not None:
                dataMessages = cur.sort('t', pymongo.ASCENDING)
                for msg in dataMessages:
                    insertionTime = Message.getInsertionTime(msg)
                    if currentTime - dataRetentionTime >= insertionTime:
                        DbCollections.getUnprocessedDataMessages(sensorId).remove(msg)
                    else:
                        break

        return {"status": "OK", "sensors": SensorDb.getAllSensors()}
    finally:
        SessionLock.release()


def scanGeneratedDirs():
    """
        Scan generated directories and remove any if they are over 2 days old.
        """
    dname = util.getPath(STATIC_GENERATED_FILE_LOCATION)
    subdirs = os.listdir(dname)
    for dirname in subdirs:
        fname = os.path.join(dname, dirname)
        if os.path.isdir(fname) and dirname.startswith("user"):
            mtime = os.path.getmtime(fname)
            current_time = time.time()
            if current_time - mtime > 2 * SECONDS_PER_DAY:
                shutil.rmtree(fname)
