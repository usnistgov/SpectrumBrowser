'''
Created on Feb 11, 2015

@author: local
'''
import time
import random
import memcache
import os
from threading import Timer
from Defines import EXPIRE_TIME


class SessionLock:
    def __init__(self):
         self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
         self.key = os.getpid()
         self.mc.set("_memCacheTest",1)
         self.memcacheStarted = (self.mc.get("_memCacheTest") == 1)
         self.mc.set("sessions",{})
     
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
        
    def addSession(self,session):
        activeSessions = self.mc.get("sessions")
        if activeSessions == None:
            activeSessions = {}
        activeSessions[session["sessionId"]] = session
        self.mc.set("sessions",activeSessions)
        
        
    def getSession(self,sessionId):
        activeSessions = self.mc.get("sessions")
        if activeSessions == None:
            return None
        else:
            if sessionId in activeSessions :
                return activeSessions[sessionId]
            else:
                return None
    
    def removeSession(self,sessionId):
        activeSessions = self.mc.get("sessions")
        if sessionId in activeSessions:
            del activeSessions[sessionId]
        self.mc.set("sessions",activeSessions)
    
    def updateSession(self,session):
        self.removeSession(session["sessionId"])
        self.addSession(session)
        
    def gc(self):
        self.acquire()
        activeSessions = self.mc.get("sessions")
        for sessionId in activeSessions.keys():
            session = activeSessions[sessionId]
            if time.time() > session[EXPIRE_TIME]:
                del activeSessions[sessionId]
        self.mc.set("sessions",activeSessions)
        self.release()
        
        
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
    
def getSession(sessionId):
    global _sessionLock
    return _sessionLock.getSession(sessionId)

def addSession(session):
    global _sessionLock
    _sessionLock.addSession(session)
    
def removeSession(sessionId):
    global _sessionLock
    _sessionLock.removeSession(sessionId)
    
def updateSession(session):
    global _sessionLock
    _sessionLock.updateSession(session)
    
def runGc():
    global _sessionLock
    _sessionLock.gc()
    t = Timer(10,runGc)
    t.start()
    
def startSessionExpiredSessionScanner():
    t = Timer(10,runGc)
    t.start()
    