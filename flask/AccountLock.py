'''
Created on Jan 28, 2015

@author: local
'''

import time
import random
import memcache
import os
import util

class AccountLock:
    def __init__(self):
         self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
         self.key = os.getpid()
         self.mc.set("_memCacheTest", 1)
         self.memcacheStarted = (self.mc.get("_memCacheTest") == 1)
     
    def acquire(self):
        if not self.memcacheStarted:
            util.errorPrint("Memcache is not started. Locking disabled")
            return
        counter = 0
        while True:
            self.mc.add("accountLock", self.key)
            val = self.mc.get("accountLock")
            if val == self.key:
                break
            else:
                counter = counter + 1
                assert counter < 30, "AccountLock counter exceeded."
                time.sleep(0.1)
    
    def release(self):
        if not self.memcacheStarted:
            return
        self.mc.delete("accountLock")
        
    
        
global _accountLock
if not "_accountLock" in globals():
    _accountLock = AccountLock()
    
def acquire():
    global _accountLock
    _accountLock.acquire()
    
def release():
    global _accountLock
    _accountLock.release()
    
