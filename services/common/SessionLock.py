'''
Created on Feb 11, 2015

@author: local
'''
import time
import util
import memcache
import os
import timezone
import SendMail
from flask import request
from threading import Timer
from Defines import EXPIRE_TIME
from Defines import SESSIONS
from Defines import SESSION_ID
from Defines import USER_NAME
from Defines import REMOTE_ADDRESS
from Defines import USER
from Defines import ADMIN
from Defines import SESSION_LOGIN_TIME
from Defines import TIME

from Defines import USER_SESSIONS
from Defines import ADMIN_SESSIONS
from Defines import STATUS
from Defines import UNKNOWN

from Defines import STATE
from Defines import PENDING_FREEZE
from Defines import FIFTEEN_MINUTES
from Defines import FROZEN
from Defines import FREEZE_REQUESTER


class SessionLock:
    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.key = os.getpid()
        self.mc.set("_memCacheTest", 1)
        self.memcacheStarted = (self.mc.get("_memCacheTest") == 1)
        self.mc.add(SESSIONS, {})

    def acquire(self):
        if not self.memcacheStarted:
            print "Memcache is not started. Locking disabled"
            return
        counter = 0
        while True:
            self.mc.add("sessionLock", self.key)
            val = self.mc.get("sessionLock")
            if val == self.key:
                break
            else:
                counter = counter + 1
                assert counter < 30, "SessionLock counter exceeded. pid = " + str(val) + " self.key = " + str(self.key)
                time.sleep(0.1)

    def isAquired(self):
        return self.mc.get("sessionLock") != None

    def release(self):
        if not self.memcacheStarted:
            return
        self.mc.delete("sessionLock")

    def addSession(self, session):
	self.acquire()
	try:
           util.debugPrint("addSession : " + str(session))
           activeSessions = self.mc.get(SESSIONS)
           self.mc.delete(SESSIONS)
           if activeSessions == None:
              activeSessions = {}
           activeSessions[session[SESSION_ID]] = session
           self.mc.add(SESSIONS, activeSessions)
           util.debugPrint("sessions:" + str(self.getSessions()))
	finally:
	   self.release()

    def freezeRequest(self, userName):
        self.mc.add(FROZEN, {STATE:PENDING_FREEZE, TIME: time.time(), USER_NAME:userName})

    def freezeRelease(self):
        frozen = self.mc.get(FROZEN)
        if frozen != None :
            self.mc.delete(FROZEN)

    def isFrozen(self, userName):
        frozen = self.mc.get(FROZEN)
        if userName == None:
            return frozen != None
        elif frozen == None:
            return False
        else:
            return frozen[USER_NAME] != userName

    def getFreezeRequester(self):
        frozen = self.mc.get(FROZEN)
        if frozen == None:
            return "UNKNOWN"
        else:
            return frozen[USER_NAME]

    def getSession(self, sessionId):
	self.acquire()
	try:
           activeSessions = self.mc.get(SESSIONS)
           if activeSessions == None:
              return None
           else:
              if sessionId in activeSessions :
                return activeSessions[sessionId]
              else:
                 return None
        finally:
            self.release()

    def removeSession(self, sessionId):
        self.acquire()
        try:
	    util.debugPrint("removeSession : " + sessionId)
            activeSessions = self.mc.get(SESSIONS)
            self.mc.delete(SESSIONS)
            if sessionId in activeSessions:
                del activeSessions[sessionId]
            self.mc.add(SESSIONS, activeSessions)
        finally:
            self.release()

    def removeSessionByAddr(self, userName, remoteAddress):
        self.acquire()
        try:
            activeSessions = self.mc.get(SESSIONS)
            if activeSessions == None:
                return
            self.mc.delete(SESSIONS)
            for sessionId in activeSessions.keys():
                session = activeSessions[sessionId]
                if session[REMOTE_ADDRESS] == remoteAddress and session[USER_NAME] == userName:
                    del activeSessions[sessionId]
                    break
            self.mc.add(SESSIONS, activeSessions)
        finally:
            self.release()

    def removeSessionsByPrivilege(self, privilege):
        self.acquire()
        try:
            activeSessions = self.mc.get(SESSIONS)
            if activeSessions == None:
                return
            self.mc.delete(SESSIONS)
            for sessionId in activeSessions.keys():
                session = activeSessions[sessionId]
                if sessionId.startswith(privilege):
                    del activeSessions[sessionId]
            self.mc.add(SESSIONS, activeSessions)
        finally:
            self.release()

    def findSessionByRemoteAddr(self, sid):
        try :
            remoteAddress = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            util.debugPrint("remoteAddress = " + remoteAddress)
        except:
            remoteAddress = None
        self.acquire()
	try:
           activeSessions = self.mc.get(SESSIONS)
           for sessionId in activeSessions:
               session = activeSessions[sessionId]
               if session[REMOTE_ADDRESS] == remoteAddress and sid != sessionId:
                  return session
           return None
	finally:
	  self.release()

    def updateSession(self, session):
        self.acquire()
	try:
           activeSessions = self.mc.get(SESSIONS)
           if activeSessions == None:
              activeSessions = {}
           sessionId = session[SESSION_ID]
           if  sessionId in activeSessions:
               del activeSessions[sessionId]
               self.mc.delete(SESSIONS)
           activeSessions[session[SESSION_ID]] = session
           self.mc.add(SESSIONS, activeSessions)
	finally:
           self.release()

    def gc(self):
        self.acquire()
	try:
           activeSessions = self.mc.get(SESSIONS)
           if activeSessions == None:
               util.debugPrint("No active sessions")
               # nothing to do.
               return
           self.mc.delete(SESSIONS)
           for sessionId in activeSessions.keys():
               session = activeSessions[sessionId]
               if time.time() > session[EXPIRE_TIME]:
		   util.debugPrint("SessionLock.gc removing : " + sessionId)
                   del activeSessions[sessionId]
           self.mc.add(SESSIONS, activeSessions)
	finally:
           self.release()

    def getSessionCount(self):
        return len(self.getSessions())

    def isUserLoggedIn(self, userName):
        sessions = self.getSessions()
        for session in sessions:
            if session[USER_NAME] == userName:
                return True
        return False

    def checkFreezeRequest(self):
        self.acquire()
        try:
            frozen = self.mc.get(FROZEN)
            currentTime = time.time()
            if frozen != None :
                freezeRequester = frozen[USER_NAME]
                t = frozen[TIME]
                if frozen[STATE] == PENDING_FREEZE and self.getSessionCount() == 0:
                    SendMail.sendMail("No sessions active - please log in within 15 minutes and do your admin actions", \
                                      freezeRequester, "System ready for administrator login")
                    frozen[STATE] = FROZEN
                    frozen[TIME] = time.time()
                    self.mc.set(FROZEN, frozen)
                elif frozen[STATE] == FROZEN and currentTime - t > FIFTEEN_MINUTES \
                    and not self.isUserLoggedIn(freezeRequester):
                    self.mc.delete(FROZEN)
        finally:
                self.release()

    def getSessions(self):
        return self.mc.get(SESSIONS)

def getSessionLock():
    global _sessionLock
    if not "_sessionLock" in globals():
        _sessionLock = SessionLock()
    return _sessionLock

def acquire():
    getSessionLock().acquire()

def release():
    getSessionLock().release()

def isAcquired():
    getSessionLock().isAquired()

def getSession(sessionId):
    return getSessionLock().getSession(sessionId)

def addSession(session):
    getSessionLock().addSession(session)

def removeSessionByAddr(userName, remoteAddr):
    getSessionLock().removeSessionByAddr(userName, remoteAddr)

def removeSession(sessionId):
    getSessionLock().removeSession(sessionId)

def updateSession(session):
    getSessionLock().updateSession(session)

def runGc():
    getSessionLock().gc()
    getSessionLock().checkFreezeRequest()
    t = Timer(10, runGc)
    t.start()

def startSessionExpiredSessionScanner():
    t = Timer(10, runGc)
    t.start()

def getUserSessionCount():
    sessions = getSessionLock().getSessions()
    if sessions == None:
        return 0
    userSessionCount = 0
    for sessionKey in sessions.keys():
        if sessionKey.startswith(USER):
            userSessionCount = userSessionCount + 1
    return userSessionCount

def getAdminSessionCount():
    sessions = getSessionLock().getSessions()
    if sessions == None:
        return 0
    adminSessionCount = 0
    for sessionKey in sessions.keys():
        if sessionKey.startswith(ADMIN):
            adminSessionCount = adminSessionCount + 1
    return adminSessionCount

def isFrozen(userName):
    return getSessionLock().isFrozen(userName)

def freezeRequest(sessionId):
    sessions = getSessionLock().getSessions()
    if sessionId in sessions:
        session = sessions[sessionId]
        userName = session[USER_NAME]
    getSessionLock().freezeRequest(userName)
    return getSessions()

def freezeRelease(sessionId):
    # sessions = getSessionLock().getSessions()
    # if sessionId in sessions:
    #    session = sessions[sessionId]
    #    userName = session[USER_NAME]
    # getSessionLock().freezeRelease(userName)
    getSessionLock().freezeRelease()
    return getSessions()

def findSessionByRemoteAddr(sessionId):
    return getSessionLock().findSessionByRemoteAddr(sessionId)

def removeSessionsByPrivilege(privilege):
    return getSessionLock().removeSessionsByPrivilege(privilege)

def getSessions():
    retval = {}
    sessions = getSessionLock().getSessions()
    userSessions = []
    adminSessions = []

    for sessionKey in sessions.keys():
        session = sessions[sessionKey]
        if sessionKey.startswith(USER):
            userSession = {}
            if session[USER_NAME] != None:
                userSession[USER_NAME] = session[USER_NAME]
            else:
                userSession[USER_NAME] = UNKNOWN
            userSession[SESSION_LOGIN_TIME] = timezone.getDateTimeFromLocalTimeStamp(session[SESSION_LOGIN_TIME])
            userSession[EXPIRE_TIME] = timezone.getDateTimeFromLocalTimeStamp(session[EXPIRE_TIME])
            userSession[REMOTE_ADDRESS] = session[REMOTE_ADDRESS]
            userSessions.append(userSession)
        elif sessionKey.startswith(ADMIN):
            adminSession = {}
            adminSession[USER_NAME] = session[USER_NAME]
            adminSession[SESSION_LOGIN_TIME] = timezone.getDateTimeFromLocalTimeStamp(session[SESSION_LOGIN_TIME])
            adminSession[EXPIRE_TIME] = timezone.getDateTimeFromLocalTimeStamp(session[EXPIRE_TIME])
            adminSession[REMOTE_ADDRESS] = session[REMOTE_ADDRESS]
            adminSessions.append(adminSession)
    retval[FROZEN] = getSessionLock().isFrozen(None)
    retval[FREEZE_REQUESTER] = getSessionLock().getFreezeRequester()
    retval[USER_SESSIONS] = userSessions
    retval[ADMIN_SESSIONS] = adminSessions
    retval[STATUS] = "OK"
    return retval


