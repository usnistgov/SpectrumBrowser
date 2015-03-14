'''
Created on Feb 2, 2015

@author: local
'''

from pymongo import MongoClient
import os

mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.spectrumdb
admindb = client.admindb
sysconfigdb = client.sysconfig

######################################################################################
# Access to globals should go through here.
def getAccounts():
    return admindb.accounts

def getTempAccounts():
    return admindb.tempaccounts

def getSpectrumDb():
    return db


def getDataMessages():
    return db.dataMessages

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

