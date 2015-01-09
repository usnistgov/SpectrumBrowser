
from flask import request
from flask import jsonify
import flaskr as main
import random
import util
import socket
import Config

def checkSessionId(sessionId):
    if main.debug :
        return True
    elif main.sessions[request.remote_addr] == None :
        return False
    elif main.sessions[request.remote_addr] != sessionId :
        return False
    return True

# Place holder. We need to look up the database for whether or not this is a valid sensor key.
def authenticateSensor(sensorId, sensorKey):
    return True

def logOut(sessionId):
    if request.remote_addr in main.sessions:
        sessionId = main.sessions[request.remote_addr]
        util.debugPrint("Logging off " + sessionId)
        del main.sessions[request.remote_addr]
        # TODO -- clean up the session here.
    return True

def authenticate(userName, password, privilege):
    print userName,password,privilege, Config.getAdminPassword()
    if userName == "admin" and password != Config.getAdminPassword():
        return False
    else:
        # Place-holder. We need to access LDAP (or whatever) here.
        return True

def authenticatePeer(peerServerId,password):
    peerRecord = Config.findInboundPeer(peerServerId)
    if peerRecord == None:
        return False
    else:
        return password == peerRecord["key"]

def generateGuestToken():
    # No password check.
    if not main.debug:
        sessionId = "guest-" + str(random.randint(1, 1000))
    else:
        sessionId = "guest-" + str(123)
    return sessionId

def generateUserToken():
    if not main.debug:
        sessionId = "user-" + str(random.randint(1, 1000))
    else :
        sessionId = "user-" + str(123)
    return sessionId

def generateAdminToken():
    if not main.debug:
        sessionId = "admin-" + str(random.randint(1, 1000))
    else :
        sessionId = "admin-" + str(123)
    return sessionId

def generatePeerSessionKey():
    if not main.debug:
        sessionId = "peer-" + str(random.randint(1, 1000))
    else :
        sessionId = "peer-" + str(123)
    return sessionId

def addSessionKey(hostName, sessionKey):
    try :
        main.sessions[socket.gethostbyname(hostName)] = sessionKey
        return True
    except:
        util.debugPrint("Problem resolving host name " + hostName)
        return False

def authenticateUser(privilege, userName, password):
    """
     Authenticate a user given a requested privilege, userName and password.
    """
    util.debugPrint("authenticate: " + userName + " " + privilege + " password " + password)
    if userName == "guest" and privilege == "user":
       sessionId = generateGuestToken()
       main.sessions[request.remote_addr] = sessionId
       return jsonify({"status":"OK", "sessionId":sessionId}), 200
    elif privilege == "admin":
       # will need to do some lookup here. Just a place holder for now.
       # For now - give him a session id and just let him through.
       if authenticate(userName, password, privilege) :
           sessionId = generateAdminToken()
           addSessionKey(request.remote_addr, sessionId)
           return jsonify({"status":"OK", "sessionId":sessionId}), 200
       else:
            return jsonify({"status":"NOK", "sessionId":"0"}), 403
    elif privilege == "user":
       # TODO : look up user password and actually authenticate here.
       if authenticate(userName, password, privilege):
           sessionId = generateUserToken()
           addSessionKey(request.remote_addr, sessionId)
           return jsonify({"status":"OK", "sessionId":sessionId}), 200
       else:
            return jsonify({"status":"NOK", "sessionId":"0"}), 403
    elif privilege == "peer":
        if authenticate(userName, password, privilege):
            sessionId = generatePeerSessionKey()
            addSessionKey(request.remote_addr, sessionId)
            return jsonify({"status":"OK", "sessionId":sessionId}), 200
        else:
            return jsonify({"status":"NOK", "sessionId":"0"}), 403
    else:
       # q = urlparse.parse_qs(query,keep_blank_values=True)
       # TODO deal with actual logins consult user database etc.
       return jsonify({"status":"NOK", "sessionId":sessionId}), 401

# TODO -- this will be implemented after the admin stuff
# has been implemented.
def isUserRegistered(emailAddress):
    return True





