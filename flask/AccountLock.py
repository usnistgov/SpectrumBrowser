'''
Created on Jan 28, 2015

@author: local
'''

import time
import random
import memcache

class AccountLock:
    def __init__(self):
         self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
         self.key = random.randint(0,10000000)
    
    def acquire(self):
        counter = 0
        while True:
            self.mc.add("accountLock",self.key)
            val = self.mc.get("accountLock")
            if val == self.key:
                break
            else:
                counter = counter + 1
                assert counter < 30,"AccountLock counter exceeded."
                time.sleep(1)
    
    def release(self):
        self.mc.delete("accountLock")
        
global _accountLock
if not "_accountLock" in globals():
    _accountLock = AccountLock()
    
def acquire():
    _accountLock.aquire()
    
def release():
    _accountLock.release()