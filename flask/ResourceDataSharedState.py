'''
Created on Jul 13, 2015

@author: mdb4
'''
import util
import time
import memcache
import os


class MemCache:
    """
    Keeps a memory map of the data pushed by the resource so it is accessible
    by any of the flask worker processes.
    """
    def __init__(self):
       
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.lastdataseen = {}
        self.resourcedata = {}
        self.key = os.getpid()
        
    def getPID(self):
        if self.key == None :
            self.key = os.getpid()
        return self.key

    def loadResourceData(self, resource):
        key = str(resource).encode("UTF-8")
        resourcedata = self.mc.get(key)
        if resourcedata != None:
            self.resourcedata[resource] = resourcedata
        return self.resourcedata

    def setResourceData(self, resource, data):
        key = str(resource).encode("UTF-8")
        self.resourcedata[resource] = data
        self.mc.set(key, data)

    def setLastDataSeenTimeStamp(self, resource, timestamp):
        key = str(resource+"time").encode("UTF-8")
        self.lastdataseen[resource] = timestamp
        self.mc.set(key, timestamp)

    def loadLastDataSeenTimeStamp(self, resource):
        key = str(resource+"time").encode("UTF-8")
        lastdataseen = self.mc.get(key)
        if lastdataseen != None:
            self.lastdataseen[resource] = lastdataseen
        return self.lastdataseen