'''
Created on Jul 13, 2015

@author: mdb4
'''
#import util
#import time
import memcache
import os


class MemCache:
    """
    Keeps a memory map of the data pushed by the resource so it is accessible
    by any of the flask worker processes.
    """
    def __init__(self):
       
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.key = os.getpid()
        
    def getPID(self):
        if self.key == None :
            self.key = os.getpid()
        return self.key

    def loadResourceData(self, resource):
        key = str(resource).encode("UTF-8")
        resourcedata = self.mc.get(key)
        return resourcedata

    def setResourceData(self, resource, data):
        key = str(resource).encode("UTF-8")
        self.mc.set(key, data)

    # def setLastDataSeenTimeStamp(self,  timestamp):
    #    key = str("resouorceUpdatetime").encode("UTF-8")
    #    self.mc.set(key, timestamp)

    # def loadLastDataSeenTimeStamp(self):
    #    key = str("resourceUpdatetime").encode("UTF-8")
    #    lastdataseen = self.mc.get(key)
    #    return lastdataseen