'''
Created on Feb 11, 2015

@author: local
'''
import time
import util
import memcache
import os
from threading import Timer
from Defines import EXPIRE_TIME
from Defines import SESSIONS
from Defines import SESSION_ID
from Defines import USER_NAME
from Defines import REMOTE_ADDRESS
from Defines import USER
from Defines import ADMIN

global _sessionLock

class SessionLock:
    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.key = os.getpid()
        self.mc.set("_memCacheTest",1)
        self.memcacheStarted = (self.mc.get("_memCacheTest") == 1)
        self.mc.add(SESSIONS,{})
     
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
                assert counter < 30,"SessionLock counter exceeded."
                time.sleep(0.1)
                
    def isAquired(self):
        return self.mc.get("sessionLock") != None
    
    def release(self):
        if not self.memcacheStarted:
            return
        self.mc.delete("sessionLock")
        
    def addSession(self,session):
        util.debugPrint("addSession : " + str(session))
        activeSessions = self.mc.get(SESSIONS)
        self.mc.delete(SESSIONS)
        if activeSessions == None:
            activeSessions = {}
        activeSessions[session[SESSION_ID]] = session
        self.mc.add(SESSIONS,activeSessions)
        print "sessions:" + str( self.getSessions())
        
    def getSession(self,sessionId):
        activeSessions = self.mc.get(SESSIONS)
        if activeSessions == None:
            return None
        else:
            if sessionId in activeSessions :
                return activeSessions[sessionId]
            else:
                return None
    
    def removeSession(self,sessionId):
        self.acquire()
        activeSessions = self.mc.get(SESSIONS)
        self.mc.delete(SESSIONS)
        if sessionId in activeSessions:
            del activeSessions[sessionId]
        self.mc.add(SESSIONS,activeSessions)
        self.release()
        
    def removeSessionByAddr(self,userName, remoteAddress):
        self.acquire()
        activeSessions = self.mc.get(SESSIONS)
        self.mc.delete(SESSIONS)
        for sessionId in activeSessions:
            session = activeSessions[sessionId]
            if session[REMOTE_ADDRESS] == remoteAddress and session[USER_NAME] == userName:
                del activeSessions[sessionId]
                break
        self.mc.add(SESSIONS,activeSessions)
        self.release()
        
    
    def updateSession(self,session):
        self.acquire()
        activeSessions = self.mc.get(SESSIONS)
        sessionId = session[SESSION_ID]
        if sessionId in activeSessions:
            del activeSessions[sessionId]
            self.mc.delete(SESSIONS)
        activeSessions[session[SESSION_ID]] = session
        self.mc.add(SESSIONS,activeSessions)
        self.release()
        
        
    def gc(self):
        self.acquire()
        activeSessions = self.mc.get(SESSIONS)
        if activeSessions == None:
            util.debugPrint("No active sessions")
            # nothing to do.
            return
        self.mc.delete(SESSIONS)
        for sessionId in activeSessions.keys():
            session = activeSessions[sessionId]
            if time.time() > session[EXPIRE_TIME]:
                del activeSessions[sessionId]
        self.mc.add(SESSIONS,activeSessions)
        self.release()
        
    def getSessions(self):
        return self.mc.get(SESSIONS)
        
        
if not "_sessionLock" in globals():
    global _sessionLock
    _sessionLock = SessionLock()
else:
    "SessionLock found"
    
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
    
def removeSessionByAddr(userName,remoteAddr):
    global _sessionLock
    _sessionLock.removeSessionByAddr(userName,remoteAddr)
    
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
    
def getUserSessionCount():
    global _sessionLock
    sessions = _sessionLock.getSessions()
    if sessions == None:
        return 0
    userSessionCount = 0
    for sessionKey in sessions.keys():
        if sessionKey.startswith(USER):
            userSessionCount = userSessionCount + 1
    return userSessionCount

def getAdminSessionCount():
    global _sessionLock
    sessions = _sessionLock.getSessions()
    if sessions == None:
        return 0
    adminSessionCount = 0
    for sessionKey in sessions.keys():
        if sessionKey.startswith(ADMIN):
            adminSessionCount = adminSessionCount + 1
    return adminSessionCount
        
    