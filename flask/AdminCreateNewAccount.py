import flaskr as main
from flask import jsonify
import random
import time
import util
import SendMail
from flask import abort
import threading
from threading import Timer

accountLock = threading.Lock()
tempAccounts = main.admindb.tempAccounts
accounts = main.admindb.accounts

TWO_HOURS = 2*60*60

def scan_temp_requests():
    accountLock.acquire()
    try:
        # remove stale requests
        for tempAccount in tempAccounts.find() :
            currentTime = time.time()
            creationTime = tempAccount["time"]
            if currentTime - creationTime > TWO_HOURS:
               tempAccounts.remove({"_id":tempAccount["_id"]})
    finally:
        accountLock.release()

    t = Timer(10,scan_temp_requests)
    t.start()


def adminRequestNewAccount(adminToken, emailAddress,firstName,lastName,password,serverUrlPrefix):
    accountLock.acquire()
    #If valid adminToken or email ends in .mil or .gov, create temp account and email user to authorize.
    #Otherwise, email admin to authorize account creation.
    try:
        print "adminCreateNewAccount", emailAddress,firstName,lastName,password,serverUrlPrefix
        tempAccountRecord = tempAccounts.find_one({"emailAddress":emailAddress})
        if tempAccountRecord == None:
            # TODO use one way hash to store the password.
            random.seed()
            token = random.randint(1,100000)
            currentTime = time.time()
            #TODO -- compute a one way hash of the password here.
            tempAccountRecord = {"emailAddress":emailAddress,"firstName":firstName,"lastName":lastName,"password":password,"time":currentTime,"token":token}
            tempAccounts.insert(tempAccountRecord)
        else:
            tempAccountRecord["firstName"] = firstName
            tempAccountRecord["lastName"] = lastName
            tempAccountRecord["time"] = time.time()
            tempAccounts.update({"_id":tempAccountRecord["_id"]},{"$set":tempAccountRecord},upsert=False)
            token = tempAccountRecord["token"]

        urlToClick = serverUrlPrefix + "/admin/activate/"+str(token)
        util.debugPrint("URL to Click " + urlToClick)
        message ="Hello " + firstName + " " + lastName + ",\n" \
                +"You requested an account from " + str(serverUrlPrefix) +"\n"\
                +"Please click here to activate within 2 hours \n"\
                +"(or ignore this mail if you did not originate this request):\n"\
                +urlToClick+"\n"
        SendMail.sendMail(message,emailAddress,"Your Account Activation Request")
    finally:
        accountLock.release()

    return jsonify({"status":"OK"})

def activateAccount(email, token):
    accountLock.acquire()
    try:
        account = tempAccounts.find_one({"token":token})
        if account == None:
            util.debugPrint("Token not found; invalid request")
            return False
        else:
            currentTime = time.time()
            creationTime = account["time"]
            if currentTime - creationTime > TWO_HOURS:
                util.debugPrint("Expired!")
                abort(403)
                return False
            else:
                # TODO -- invoke your external account manager here (such as LDAP).
                existingAccount = accounts.find_one({"emailAddress":account["emailAddress"]})
                if existingAccount == None:
                    accounts.insert(account)
                    util.debugPrint("Creating new account")
                else:
                    util.debugPrint("Account already exists. Not creating a new one")
                return True
    finally:
        accountLock.release()

scan_temp_requests()
