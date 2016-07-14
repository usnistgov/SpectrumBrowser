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
Created on Feb 2, 2015

@author: mranga
'''

from pymongo import MongoClient
import Bootstrap
import pymongo
import time


def initConnections():
    global db
    global admindb
    global occpancydb
    global sysconfigdb
    global capturedb
    if "_dbConnectionsInitialized" not in globals():
        global _dbConnectionsInitialized
        _dbConnectionsInitialized = True
        mongodb_host = Bootstrap.getDbHost()
        client = MongoClient(mongodb_host)
        # Let the connection initialize
        time.sleep(1)
        db = client.spectrumdb
        admindb = client.admindb
        sysconfigdb = client.sysconfig
        occpancydb = client.occpancydb
        capturedb = client.capturedb


######################################################################################
# Access to globals should go through here.
def getAccounts():
    initConnections()
    global admindb
    return admindb.accounts


def getTempAccounts():
    initConnections()
    global admindb
    return admindb.tempaccounts


def getSpectrumDb():
    initConnections()
    global db
    return db


def getCaptureDb():
    initConnections()
    global capturedb
    return capturedb


def getCaptureEventDb(sensorId):
    if "captureEvents." + sensorId in getCaptureDb().collection_names():
        return getCaptureDb()["captureEvents." + sensorId]
    else:
        return getCaptureDb().create_collection("captureEvents." + sensorId)


def getDataMessages(sensorId):
    if "dataMessages." + sensorId in getSpectrumDb().collection_names():
        return getSpectrumDb()["dataMessages." + sensorId]
    return getSpectrumDb().create_collection("dataMessages." + sensorId)


def dropDataMessages(sensorId):
    getSpectrumDb().drop_collection("dataMessages." + sensorId)


def getSystemMessages():
    initConnections()
    global db
    return db.systemMessages


def getLocationMessages():
    initConnections()
    global db
    return db.locationMessages


def getTempPasswords():
    initConnections()
    global admindb
    return admindb.tempPasswords


def getSensors():
    initConnections()
    global admindb
    return admindb.sensors


def getTempSensorsCollection():
    initConnections()
    global admindb
    return admindb.tempSensors


def getPeerConfigDb():
    initConnections()
    global sysconfigdb
    return sysconfigdb.peerconfig


def getESAgentDb():
    initConnections()
    global sysconfigdb
    return sysconfigdb.esagents


def getSysConfigDb():
    initConnections()
    global admindb
    return sysconfigdb.configuration


def getScrConfigDb():
    initConnections()
    global sysconfigdb
    return sysconfigdb.scrconfig


def initIndexes():
    getSystemMessages().ensure_index("t", pymongo.DESCENDING)
    getLocationMessages().ensure_index("t", pymongo.DESCENDING)
