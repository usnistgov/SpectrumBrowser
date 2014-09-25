
from flask import Flask, request, abort, make_response
from flask import jsonify
import flaskr as main
from random import randint
import random
import util


# Place-holder. We need to access LDAP (or whatever) here.
def authenticate(userName,password,privilege):
    return True


def authenticateUser(privilege, userName,password):
    """
     Authenticate a user given a requested privilege, userName and password.
    """
    util.debugPrint("authenticate: " + userName + " " + privilege + " password " + password)
    if userName == "guest" and privilege == "user":
       # No password check.
       if not main.debug:
            sessionId = "guest-" + str(random.randint(1, 1000))
       else:
            sessionId = "guest-" + str(123)
       main.sessions[request.remote_addr] = sessionId
       return jsonify({"status":"OK", "sessionId":sessionId}), 200
    elif privilege == "admin":
       # will need to do some lookup here. Just a place holder for now.
       # For now - give him a session id and just let him through.
       if authenticate(userName, password, privilege) :
           if not main.debug:
                sessionId = "admin-" + str(random.randint(1, 1000))
           else :
                sessionId = "admin-" + str(123)
           main.sessions[request.remote_addr] = sessionId
           return jsonify({"status":"OK", "sessionId":sessionId}), 200
       else:
            return jsonify({"status":"NOK", "sessionId":"0"}), 403
    elif privilege == "user":
       # TODO : look up user password and actually authenticate here.
       if authenticate(userName, password, privilege):
           if not main.debug:
                sessionId = "user-" + str(random.randint(1, 1000))
           else :
                sessionId = "user-" + str(123)
           main.sessions[request.remote_addr] = sessionId
           return jsonify({"status":"OK", "sessionId":sessionId}), 200
       else:
            return jsonify({"status":"NOK", "sessionId":"0"}), 403
    else:
       # q = urlparse.parse_qs(query,keep_blank_values=True)
       # TODO deal with actual logins consult user database etc.
       return jsonify({"status":"NOK", "sessionId":sessionId}), 401

   
