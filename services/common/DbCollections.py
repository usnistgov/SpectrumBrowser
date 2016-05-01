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
    if not "_dbConnectionsInitialized" in globals():
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


