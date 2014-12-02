import flaskr as main
from flask import jsonify
import random
import time
import util
import SendMail
from flask import abort
import threading
from threading import Timer
import AdminAccounts

accountLock = threading.Lock()
tempAccounts = main.admindb.tempAccounts
accounts = main.admindb.accounts

def adminRequestNewAccount(adminToken, emailAddress,firstName,lastName,password,serverUrlPrefix):
    # TODO -- check the password for legal string here.
    if not AdminAccounts.isPasswordValid(password) :
        return jsonify({"status":"FAIL"})

    accountLock.acquire()
    #If valid adminToken or email ends in .mil or .gov, create temp account and email user to authorize.
    #Otherwise, email admin to authorize account creation.
    try:
        print "adminRequestNewAccount", emailAddress,firstName,lastName,password,serverUrlPrefix
        tempAccountRecord = tempAccounts.find_one({"emailAddress":emailAddress})
        if tempAccountRecord == None:
            # We decided it is ok not to hash the password here, since it is just temporary (2 hrs or less) until we stored it in LDAP.
            random.seed()
            token = random.randint(1,100000)
            currentTime = time.time()
            tempAccountRecord = {"emailAddress":emailAddress,"firstName":firstName,"lastName":lastName,"password":password,"time":currentTime,"token":token}
            tempAccounts.insert(tempAccountRecord)
        else:
            tempAccountRecord["firstName"] = firstName
            tempAccountRecord["lastName"] = lastName
            tempAccountRecord["password"] = password
            tempAccountRecord["time"] = time.time()
            tempAccounts.update({"_id":tempAccountRecord["_id"]},{"$set":tempAccountRecord},upsert=False)
            token = tempAccountRecord["token"]

        urlToClick = serverUrlPrefix + "/admin/activate/"+str(token)
        util.debugPrint("URL to Click " + urlToClick)
        # TODO -- if this request is not from .gov or .mil, then forward it to admin for approval.
        if emailAddress.endswith(".gov") or emailAddress.endswith(".mil"):
            message ="Hello " + firstName + " " + lastName + ",\n" \
                +"You requested an account from " + str(serverUrlPrefix) +"\n"\
                +"Please click here to activate within 2 hours \n"\
                +"(or ignore this mail if you did not originate this request):\n"\
                +urlToClick+"\n"
            SendMail.sendMail(message,emailAddress,"Your Account Activation Request")
            return jsonify({"status":"OK"})
        else:
            print "TODO -- forward the request to admin"
            return jsonify({"status":"FORWARDED"})
    finally:
        accountLock.release()
        


def activateAccount(email, token):
    accountLock.acquire()
    try:
        account = tempAccounts.find_one({"emailAddress":email, "token":token})
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
                existingAccount = accounts.find_one({"emailAddress":email})
                if existingAccount == None:
                    accounts.insert(account)
                    util.debugPrint("Creating new account")
                else:
                    util.debugPrint("Account already exists. Not creating a new one")
                return True
    finally:
        accountLock.release()

AdminAccounts.removeExpiredRows(tempAccounts)
