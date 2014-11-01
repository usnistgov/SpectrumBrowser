import flaskr as main
from flask import jsonify
import random
import time
import util
import SendMail
from flask import abort

def adminCreateNewAccount(emailAddress,firstName,lastName,password,serverUrlPrefix):
    print emailAddress,firstName,lastName,password
    token = random.randint(1,100000)
    currentTime = time.time()
    tempAccount = main.db.tempAccount
    # TODO use one way hash to store the password.
    tempAccount = {"emailAddress":emailAddress,"firstName":firstName,"lastName":lastName,"password":password,"time":currentTime,"token":token}
    tempAccount.insert(tempAccount)
    urlToClick = serverUrlPrefix + "/admin/accountActivation/"+token;
    message = "<p>Hello!<br/> You requested an account from " + serverUrlPrefix + "<br/>" +\
              "Please click here to activate within 2 hours : <br/>" +\
              "<a href=\""+urlToClick+"/>"
    SendMail.sendMail(message,emailAddress,"Your Account Activation Request")
    return jsonify({"status":"OK"})

def activate(token):
    tempAccount = main.db.tempAccount
    account = tempAccount.findOne({"token":token})
    if account == None:
       util.debugPrint("Token not found; invalid request")
       return False
    else:
       currentTime = time.time()
       creationTime = account["time"]
       if currentTime - creationTime < 2*60*60:
            abort(403)
       # TODO -- invoke your external account manager here (such as LDAP).
       util.debugPrint("Creating new account")
       return True
