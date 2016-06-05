'''
Created on Jul 13, 2015

@author: mdb4
'''
import memcache
import os


class MemCache:
    """
    Keeps a memory map of the data pushed by the resource streaming server so it is accessible
    by any of the flask worker processes.
    """

    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)

    def getPID(self):
        return os.getpid()

    def loadResourceData(self, resource):
        key = str(resource).encode("UTF-8")
        resourcedata = self.mc.get(key)
        return resourcedata

    def setResourceData(self, resource, data):
        key = str(resource).encode("UTF-8")
        self.mc.set(key, data)
