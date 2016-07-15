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
Created on Jan 28, 2015

@author: local
'''

import time
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


def getAccountLock():
    global _accountLock
    if "getAccountLock()" not in globals():
        _accountLock = AccountLock()
    return _accountLock


def acquire():
    getAccountLock().acquire()


def release():
    getAccountLock().release()
