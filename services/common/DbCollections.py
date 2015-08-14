'''
Created on Feb 2, 2015

@author: local
'''

from pymongo import MongoClient
import Bootstrap
import pymongo


mongodb_host = Bootstrap.getDbHost()

client = MongoClient(mongodb_host)
db = client.spectrumdb
admindb = client.admindb
sysconfigdb = client.sysconfig
occpancydb = client.occpancydb

######################################################################################
# Access to globals should go through here.
def getAccounts():
    return admindb.accounts

def getTempAccounts():
    return admindb.tempaccounts

def getSpectrumDb():
    return db

def getDataMessages(sensorId):
    if "dataMessages." + sensorId in getSpectrumDb().collection_names():
        return getSpectrumDb()["dataMessages." + sensorId]
    return getSpectrumDb().create_collection("dataMessages." + sensorId)

def dropDataMessages(sensorId):
    getSpectrumDb().drop_collection("dataMessages." + sensorId)

def getSystemMessages():
    return db.systemMessages

def getLocationMessages():
    return db.locationMessages

def getTempPasswords():
    return admindb.tempPasswords

def getSensors():
    return admindb.sensors

def getTempSensorsCollection():
    return admindb.tempSensors

def getPeerConfigDb():
    return sysconfigdb.peerconfig

def getSysConfigDb():
    return sysconfigdb.configuration

def getScrConfigDb():
    return sysconfigdb.scrconfig

def initIndexes():
    getSystemMessages().ensure_index("t", pymongo.DESCENDING)
    getLocationMessages().ensure_index("t", pymongo.DESCENDING)


