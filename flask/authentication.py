import flaskr as main
from flask import jsonify
import random
import util
import Config
import time
import threading
import Accounts
import sys
import traceback
import AccountLock
TWO_HOURS = 2 * 60 * 60
SIXTY_DAYS = 60 * 60 * 60 * 60
sessionLock = threading.Lock()



def checkSessionId(sessionId):
 
    sessionFound = False
    if main.debug :
        sessionFound = True
    else:
        sessionLock.acquire() 
        try :
            session = main.getSessions().find_one({"sessionId":sessionId})
            if session <> None:
                sessionFound = True
                session["expireTime"] = time.time() + TWO_HOURS
                main.getSessions().update({"_id":session["_id"]}, {"$set":session}, upsert=False)
                util.debugPrint("updated session ID expireTime")
        except:
            util.debugPrint("Problem checking sessionKey " + sessionId)
        finally:
            sessionLock.release()  
    return sessionFound

# Place holder. We need to look up the database for whether or not this is a valid sensor key.
def authenticateSensor(sensorId, sensorKey):
    return True

def logOut(sessionId):
    sessionLock.acquire() 
    logOutSuccessful = False
    try :
        util.debugPrint("Logging off " + sessionId)
        session = main.getSessions().find_one({"sessionId":sessionId}) 
        if session == None:
            util.debugPrint("When logging off could not find the following session key to delete:" + sessionId)
        else:
            main.getSessions().remove({"_id":session["_id"]})
            logOutSuccessful = True
    except:
        util.debugPrint("Problem logging off " + sessionId)
    finally:
        sessionLock.release() 
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

def generatePeerSessionKey():
    sessionId = generateSessionKey("peer")
    addSessionKey(sessionId, "peerUser")

def generateSessionKey(privilege):
    util.debugPrint("generateSessionKey ")
    try:
        sessionId = -1
        uniqueSessionId = False
        num = 0
        sessionLock.acquire()
        # try 5 times to get a unique session id
        while (not uniqueSessionId) and (num < 5):
            # JEK: I used time.time() as my random number so that if a user wants to create
            # main.getSessions() from 2 browsers on the same machine, the time should ensure uniqueness
            # especially since time goes down to msecs.
            # JEK I am thinking that we do not need to add remote_address to the sessionId to get uniqueness,
            # so I took out +request.remote_addr
            sessionId = privilege + "-" + str("{0:.6f}".format(time.time())).replace(".", "") + str(random.randint(1, 100000))
            util.debugPrint("SessionKey in loop = " + str(sessionId))            
            session = main.getSessions().find_one({"sessionId":sessionId}) 
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
        sessionLock.release() 
    util.debugPrint("SessionKey = " + str(sessionId))      
    return sessionId   

def addSessionKey(sessionId, userName):
    util.debugPrint("addSessionKey")
    if sessionId <> -1:
        sessionLock.acquire()
        try :
            session = main.getSessions().find_one({"sessionId":sessionId}) 
            if session == None:
                newSession = {"sessionId":sessionId, "userName":userName, "timeLogin":time.time(), "expireTime":time.time() + TWO_HOURS}
                main.getSessions().insert(newSession)
                return True
            else:
                util.debugPrint("session key already exists, we should never reach since only should generate unique session keys")
                return False
        except:
            util.debugPrint("Problem adding sessionKey " + sessionId)
            return False
        finally:
            sessionLock.release()      
    else:
        return False
 
def IsAccountLocked(userName):
    AccountLocked = False
    if Config.isAuthenticationRequired():
        AccountLock.acquire()
        try :
            existingAccount = main.getAccounts().find_one({"emailAddress":userName})    
            if existingAccount <> None:               
                if existingAccount["AccountLocked"] == True:
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
    elif not Config.isConfigured() and privilege == "admin":
        if userName == Config.getDefaultAdminEmailAddress() and password == Config.getDefaultAdminPassword():
            authenicationSuccessful = True
        else:
            authenicationSuccessful = False
    else:
        AccountLock.acquire()
        try :
            util.debugPrint("finding existing account")
            existingAccount = main.getAccounts().find_one({"emailAddress":userName, "password":password, "privilege":privilege})

            if existingAccount == None:
                util.debugPrint("did not find email and password ") 
                existingAccount = main.getAccounts().find_one({"emailAddress":userName})    
                if existingAccount != None:
                    util.debugPrint("account exists, but user entered wrong password "+ password + " / " + existingAccount["password"])                    
                    numFailedLoggingAttempts = existingAccount["numFailedLoggingAttempts"] + 1
                    existingAccount["numFailedLoggingAttempts"] = numFailedLoggingAttempts
                    if numFailedLoggingAttempts == 5:                 
                        existingAccount["AccountLocked"] = True 
                    main.getAccounts().update({"_id":existingAccount["_id"]}, {"$set":existingAccount}, upsert=False)                           
            else:
                util.debugPrint("found email and password ") 
                if existingAccount["AccountLocked"] == False:
                    util.debugPrint("user passed login authentication.")           
                    existingAccount["numFailedLoggingAttempts"] = 0
                    existingAccount["AccountLocked"] = False 
                    # Place-holder. We need to access LDAP (or whatever) here.
                    main.getAccounts().update({"_id":existingAccount["_id"]}, {"$set":existingAccount}, upsert=False)
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
    util.debugPrint("authenticateUser: " + userName + " privilege: " + privilege + " password " + password)
    if privilege == "admin" or privilege == "user":
        if IsAccountLocked(userName):
            return jsonify({"status":"ACCLOCKED", "sessionId":"0"})
        else:
            # Authenticate will will work whether passwords are required or not (authenticate = true if no pwd req'd)
            if authenticate(privilege, userName, password) :
                sessionId = generateSessionKey(privilege)
                addedSuccessfully = addSessionKey(sessionId, userName)
                if addedSuccessfully:
                    return jsonify({"status":"OK", "sessionId":sessionId})
                else:
                    return jsonify({"status":"INVALSESSION", "sessionId":"0"})
            else:
                util.debugPrint("invalid user will be returned: ")
                return jsonify({"status":"INVALUSER", "sessionId":"0"})   
    else:
        # q = urlparse.parse_qs(query,keep_blank_values=True)
        # TODO deal with actual logins consult user database etc.
        return jsonify({"status":"NOK", "sessionId":"0"}), 401

# TODO -- this will be implemented after the admin stuff
# has been implemented.
def isUserRegistered(emailAddress):
    UserRegistered = False
    if Config.isAuthenticationRequired():
        AccountLock.acquire()
        try :
            existingAccount = main.getAccounts().find_one({"emailAddress":emailAddress})
            if existingAccount <> None:
                UserRegistered = True
        except:
            util.debugPrint("Problem checking if user is registered " + emailAddress)
        finally:
            AccountLock.release()    

    return UserRegistered

global AuthenticationRemoveExpiredRowsScanner
if not "AuthenticationRemovedExpiredRowsScanner" in globals():
    AuthenticationRemoveExpiredRowsScanner = True
    Accounts.removeExpiredRows(main.getSessions())



