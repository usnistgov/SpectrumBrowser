'''
Created on Feb 11, 2015

@author: local
'''
import time
import random
import memcache
import os

class SessionLock:
    def __init__(self):
         self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
         self.key = os.getpid()
         self.mc.set("_memCacheTest",1)
         self.memcacheStarted = (self.mc.get("_memCacheTest") == 1)
     
    def acquire(self):
        if not self.memcacheStarted:
            print "Memcache is not started. Locking disabled"
            return
        counter = 0
        while True:
            self.mc.add("sessionLock",self.key)
            val = self.mc.get("sessionLock")
            if val == self.key:
                break
            else:
                counter = counter + 1
                assert counter < 30,"AccountLock counter exceeded."
                time.sleep(0.1)
                
    def isAquired(self):
        return self.mc.get("sessionLock") != None
    
    def release(self):
        if not self.memcacheStarted:
            return
        self.mc.delete("sessionLock")
        
global _sessionLock
if not "_sessionLock" in globals():
    _sessionLock = SessionLock()
    
def acquire():
    global _sessionLock
    _sessionLock.acquire()
    
def release():
    global _sessionLock
    _sessionLock.release()

def isAcquired():
    global _sessionLock
    _sessionLock.isAquired()