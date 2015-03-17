from flask import jsonify
import random
import util
import Config
import time
import threading
import Accounts
import AccountsManagement
import sys
import traceback
from __builtin__ import True
import AccountLock
import DbCollections
import DebugFlags
import json
from flask import request

#expire time for sessions
from Defines import EXPIRE_TIME

#session info
from Defines import USER_NAME

#account info
from Defines import ACCOUNT_NUM_FAILED_LOGINS
from Defines import ACCOUNT_LOCKED
from Defines import ACCOUNT_EMAIL_ADDRESS
from Defines import ACCOUNT_PASSWORD
from Defines import ACCOUNT_PRIVILEGE


from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import ENABLED
from Defines import SENSOR_STATUS
from Defines import REMOTE_ADDRESS
from Defines import SESSION_ID
from Defines import SESSION_LOGIN_TIME

import SessionLock



#TODO -- figure out how to get the remote IP address from a web socket.
def checkSessionId(sessionId):
    try :
        remoteAddress = request.remote_addr
    except:
        remoteAddress = None
 
    sessionFound = False
    if DebugFlags.disableSessionIdCheck :
        sessionFound = True
    else:
        SessionLock.acquire() 
        try :
            session = SessionLock.getSession(sessionId)
            if session != None and remoteAddress == None or session[REMOTE_ADDRESS] == remoteAddress:
                sessionFound = True
                if sessionId.startswith("user"):
                    delta = Config.getUserSessionTimeoutMinutes()*60
                else:
                    delta = Config.getAdminSessionTimeoutMinutes()*60
                expireTime = time.time() + delta
                session[EXPIRE_TIME] = expireTime
                SessionLock.updateSession(session)
                util.debugPrint("updated session ID expireTime")
        except:
            util.debugPrint("Problem checking sessionKey " + sessionId)
        finally:
            SessionLock.release()  
    return sessionFound

# Place holder. We need to look up the database for whether or not this is a valid sensor key.
def authenticateSensor(sensorId, sensorKey):
    record = DbCollections.getSensors().find_one({SENSOR_ID:sensorId,SENSOR_KEY:sensorKey})
    if record != None and record[SENSOR_STATUS] == ENABLED : 
        return True
    else:
        return False
    
def logOut(sessionId):
    SessionLock.acquire() 
    logOutSuccessful = False
    try :
        util.debugPrint("Logging off " + sessionId)
        session =SessionLock.getSession(sessionId) 
        if session == None:
            util.debugPrint("When logging off could not find the following session key to delete:" + sessionId)
        else:
            SessionLock.removeSession(session[SESSION_ID])
            logOutSuccessful = True
    except:
        util.debugPrint("Problem logging off " + sessionId)
    finally:
        SessionLock.release() 
    return logOutSuccessful

def authenticatePeer(peerServerId, password):
    peerRecord = Config.findInboundPeer(peerServerId)
    if peerRecord == None:
        return False
    else:
        return password == peerRecord["key"]

def generateGuestToken():
    sessionId = generateSessionKey("user")
    addedSuccessfully = addSessionKey(sessionId, "guest")
    return sessionId


def generateSessionKey(privilege):
    util.debugPrint("generateSessionKey ")
    try:
        sessionId = -1
        uniqueSessionId = False
        num = 0
        SessionLock.acquire()
        # try 5 times to get a unique session id
        while (not uniqueSessionId) and (num < 5):
            # JEK: I used time.time() as my random number so that if a user wants to create
            # DbCollections.getSessions() from 2 browsers on the same machine, the time should ensure uniqueness
            # especially since time goes down to msecs.
            # JEK I am thinking that we do not need to add remote_address to the sessionId to get uniqueness,
            # so I took out +request.remote_addr
            sessionId =  privilege + "-" + str("{0:.6f}".format(time.time())).replace(".", "") + str(random.randint(1, 100000))
            util.debugPrint("SessionKey in loop = " + str(sessionId))            
            session = SessionLock.getSession(sessionId)
            if session == None:
                uniqueSessionId = True       
            else:
                num = num + 1
        if num == 5:
            util.debugPrint("Fix unique session key generation code. We tried 5 times to get a unique session key and then we gave up.") 
            sessionId = -1
    except:     
        util.debugPrint("Problem generating sessionKey " + str(sessionId))  
        sessionId = -1
    finally:
        SessionLock.release() 
    util.debugPrint("SessionKey = " + str(sessionId))      
    return sessionId   

def addSessionKey(sessionId, userName):
    util.debugPrint("addSessionKey")
    remoteAddress = request.remote_addr
    if sessionId <> -1:
        SessionLock.acquire()
        try :
            util.debugPrint("getSession")
            session = SessionLock.getSession(sessionId) 
            util.debugPrint("gotSession")
            if session == None:
                #expiry time for Admin is 15 minutes.
                if sessionId.startswith("admin"):
                    delta = Config.getUserSessionTimeoutMinutes()*60
                else:
                    delta = Config.getAdminSessionTimeoutMinutes()*60
                util.debugPrint("newSession")
                newSession = {SESSION_ID:sessionId, USER_NAME:userName, REMOTE_ADDRESS: remoteAddress, SESSION_LOGIN_TIME:time.time(), EXPIRE_TIME:time.time() + delta}
                util.debugPrint("addSession")
                SessionLock.addSession(newSession)
                return True
            else:
                util.debugPrint("session key already exists, we should never reach since only should generate unique session keys")
                return False
        except:
            util.debugPrint("Problem adding sessionKey " + sessionId)
            return False
        finally:
            SessionLock.release()      
    else:
        return False
 

def IsAccountLocked(userName):
    AccountLocked = False
    if Config.isAuthenticationRequired():
        AccountLock.acquire()
        try :
            existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:userName})    
            if existingAccount <> None:               
                if existingAccount[ACCOUNT_LOCKED] == True:
                    AccountLocked = True
        except:
            util.debugPrint("Problem authenticating user " + userName )
        finally:
            AccountLock.release()   
    return AccountLocked
    
def authenticate(privilege, userName, password):
    print userName, password, Config.isAuthenticationRequired()
    authenicationSuccessful = False
    util.debugPrint("authenticate check database")
    if not Config.isAuthenticationRequired() and privilege == "user":
        authenicationSuccessful = True
    elif AccountsManagement.numAdminAccounts() == 0 and privilege == "admin":
        util.debugPrint("No admin accounts, using default email and password")
        if userName == AccountsManagement.getDefaultAdminEmailAddress() and password == AccountsManagement.getDefaultAdminPassword():
            util.debugPrint("Default admin authenticated")
            authenicationSuccessful = True
        else:
            util.debugPrint("Default admin not authenticated")
            authenicationSuccessful = False
    elif AccountsManagement.numAdminAccounts() == 0 and userName == AccountsManagement.getDefaultAdminEmailAddress() and password == AccountsManagement.getDefaultAdminPassword():
    #        util.debugPrint("No admin accounts, user must login to admin page and create an account before using spectrum browser")            
    # I think that an admin should be allowed to login to spectrum browser page
        util.debugPrint("Default admin authenticated")
        authenicationSuccessful = True
    else:
        AccountLock.acquire()
        try :
            util.debugPrint("finding existing account")
            # if we only need 'user' or higher privilege, then we only need to look for email & password, not privilege:
            if privilege == "user":
                existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:userName, ACCOUNT_PASSWORD:password})
            else:
                # otherwise, we need to look for 'admin' privilege in addition to email & password:
                existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:userName, ACCOUNT_PASSWORD:password, ACCOUNT_PRIVILEGE:privilege})
            if existingAccount == None:
                util.debugPrint("did not find email and password ") 
                existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:userName})    
                if existingAccount != None :
                    util.debugPrint("account exists, but user entered wrong password or attempted admin log in")                    
                    numFailedLoginAttempts = existingAccount[ACCOUNT_NUM_FAILED_LOGINS] + 1
                    existingAccount[ACCOUNT_NUM_FAILED_LOGINS] = numFailedLoginAttempts
                    if numFailedLoginAttempts == Config.getNumFailedLoginAttempts():                 
                        existingAccount[ACCOUNT_LOCKED] = True 
                    DbCollections.getAccounts().update({"_id":existingAccount["_id"]}, {"$set":existingAccount}, upsert=False)                           
            else:
                util.debugPrint("found email and password ") 
                if existingAccount[ACCOUNT_LOCKED] == False:
                    util.debugPrint("user passed login authentication.")           
                    existingAccount[ACCOUNT_NUM_FAILED_LOGINS] = 0
                    existingAccount[ACCOUNT_LOCKED] = False 
                    # Place-holder. We need to access LDAP (or whatever) here.
                    DbCollections.getAccounts().update({"_id":existingAccount["_id"]}, {"$set":existingAccount}, upsert=False)
                    util.debugPrint("user login info updated.")
                    authenicationSuccessful = True
        except:
            util.debugPrint("Problem authenticating user " + userName + " password: " + password)
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
        finally:
            AccountLock.release()    
    return authenicationSuccessful

def authenticateUser(privilege, userName, password):
    """
     Authenticate a user given a requested privilege, userName and password.
    """
    remoteAddr = request.remote_addr
    util.debugPrint("authenticateUser: " + userName + " privilege: " + privilege + " password " + password)
    if privilege == "admin" or privilege == "user":
        if IsAccountLocked(userName):
            return jsonify({"status":"ACCLOCKED", SESSION_ID:"0"})
        else:
            # Authenticate will will work whether passwords are required or not (authenticate = true if no pwd req'd)
            # Only one admin login allowed at a given time.
            if privilege == "admin" :
                SessionLock.removeSessionByAddr(userName,remoteAddr)
                if SessionLock.getAdminSessionCount() != 0:
                    return jsonify({"status":"NOSESSIONS",SESSION_ID:"0"})
            if authenticate(privilege, userName, password) :
                sessionId = generateSessionKey(privilege)
                addedSuccessfully = addSessionKey(sessionId, userName)
                if addedSuccessfully:
                    return jsonify({"status":"OK", SESSION_ID:sessionId})
                else:
                    return jsonify({"status":"INVALSESSION", SESSION_ID:"0"})
            else:
                util.debugPrint("invalid user will be returned: ")
                return jsonify({"status":"INVALUSER", SESSION_ID:"0"})   
    else:
        # q = urlparse.parse_qs(query,keep_blank_values=True)
        # TODO deal with actual logins consult user database etc.
        return jsonify({"status":"NOK", SESSION_ID:"0"}), 401

def isUserRegistered(emailAddress):
    UserRegistered = False
    if Config.isAuthenticationRequired():
        AccountLock.acquire()
        try :
            existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress})
            if existingAccount <> None:
                UserRegistered = True
        except:
            util.debugPrint("Problem checking if user is registered " + emailAddress)
        finally:
            AccountLock.release()    
    return UserRegistered




