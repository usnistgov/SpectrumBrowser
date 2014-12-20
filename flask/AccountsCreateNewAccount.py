import flaskr as main
from flask import jsonify
import random
import time
import util
import SendMail
from flask import abort
import threading
from threading import Timer
import Accounts
import Config

accountLock = threading.Lock()
tempAccounts = main.admindb.tempAccounts
accounts = main.admindb.accounts
TWO_HOURS = 2*60*60
TWO_DAYS = 48*60*60

def generateUserAccountPendingAuthorizationEmail(emailAddress,serverUrlPrefix):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"You requested a new account from: " + str(serverUrlPrefix) +"\n"\
    +"Your request has been send to the administrator for authorization.\n"
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "Account pending authorization")

def generateUserActivateAccountEmail(emailAddress,serverUrlPrefix, token):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    urlToClick = serverUrlPrefix + "/spectrumbrowser/activateAccount/" +emailAddress+ "?token="+str(token)
    util.debugPrint("URL to Click for generateUserActivateAccountEmail" + urlToClick)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"You requested a new account from: " + str(serverUrlPrefix) +"\n"\
    +"Please click here within 2 hours to activate your account\n"\
    +"(or ignore this mail if you did not originate this request):\n"\
    + urlToClick +"\n"
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "Account activation link")
    
    
def generateUserDenyAccountEmail(emailAddress,serverUrlPrefix):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"We regret to information you that your request for a new account from: " + str(serverUrlPrefix) +" was denied.\n"\
    +"Please access the system administrator for more information.\n"
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "Account information")
    
def generateAdminAuthorizeAccountEmail(emailAddress,serverUrlPrefix, token):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    urlToClickToAuthorize = serverUrlPrefix + "/spectrumbrowser/authorizeAccount/" +emailAddress+ "?token="+str(token)+"&urlPrefix="+serverUrlPrefix
    util.debugPrint("urlToClickToAuthorize for generateAdminAuthorizeAccountEmail email" + urlToClickToAuthorize)
    urlToClickToDeny = serverUrlPrefix + "/spectrumbrowser/denyAccount/" +emailAddress+ "?token="+str(token)+"&urlPrefix="+serverUrlPrefix
    util.debugPrint("urlToClickToDeny for generateAdminAuthorizeAccountEmail email" + urlToClickToDeny)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"A user requested a new account from: " + str(serverUrlPrefix) +"\n"\
    +"Please click here within 48 hours if you wish to authorize the account and email the user.\n"\
    + urlToClickToAuthorize +"\n"\
    +"or please click here within 48 hours if you wish to deny the account and email the user.\n"\
    + urlToClickToDeny +"\n"
    util.debugPrint(message)
    SendMail.sendMail(message,Config.getAdminEmailAddress(), "Account authorization link")

def requestNewAccount(emailAddress,firstName,lastName,newPassword,serverUrlPrefix):

    accountLock.acquire()
    #If valid adminToken or email ends in .mil or .gov, create temp account and email user to authorize.
    #Otherwise, email admin to authorize account creation.
    try:
        util.debugPrint("requestNewAccount"+ emailAddress+firstName+lastName+newPassword+serverUrlPrefix)
        # TODO -- invoke external account manager here (such as LDAP).
        existingAccount = accounts.find_one({"emailAddress":emailAddress})
        if existingAccount <> None:
            util.debugPrint("Email already exists as a user account")
            return jsonify({"status":"EXISTING"})
        else: 
            util.debugPrint("account does not exist")
            if not Accounts.isPasswordValid(newPassword) :
                util.debugPrint("Password invalid")
                return jsonify({"status":"INVALPASS"})
            else:
                util.debugPrint("Password valid")
                tempAccountRecord = tempAccounts.find_one({"emailAddress":emailAddress})
                if (tempAccountRecord <> None):
                    # Account is already pending for this email.
                    util.debugPrint("Temp account pending")
                    return jsonify({"status":"PENDING"})
                else:
                    util.debugPrint("No temp account yet")
                    # We decided it is ok not to hash the password here, since it is just temporary (2 hrs or less) until we stored it in LDAP.
                    random.seed()
                    token = random.randint(1,100000)
                    #give admin more time to authorize account, than a .gov or .mil user to activate account:
                    if emailAddress.endswith(".gov") or emailAddress.endswith(".mil"):
                        util.debugPrint(".gov or .mil email")
                        t = threading.Thread(target=generateUserActivateAccountEmail,args=(emailAddress,serverUrlPrefix, token))
                        t.daemon = True
                        t.start()
                        retVal = jsonify({"status":"OK"})
                        expireTime = time.time()+TWO_HOURS
                    else:
                        # add an email to user that request has been forwarded to admin &
                        # when admin authorizes account, send email to user to user to activate account, to ensure email valid.
                        util.debugPrint("Not .gov or .mil email")
                        t = threading.Thread(target=generateAdminAuthorizeAccountEmail,args=(emailAddress,serverUrlPrefix, token))
                        t.daemon = True
                        t.start()
                        t2 = threading.Thread(target=generateUserAccountPendingAuthorizationEmail,args=(emailAddress,serverUrlPrefix))
                        t2.daemon = True
                        t2.start()
                        retVal = jsonify({"status":"FORWARDED"})  
                        expireTime = time.time()+TWO_DAYS                       
                    tempAccountRecord = {"emailAddress":emailAddress,"firstName":firstName,"lastName":lastName,"password":newPassword,"expireTime":expireTime,"token":token}
                    tempAccounts.insert(tempAccountRecord)
                    return retVal  
    except:
        retval = {"status": "NOK"}
        return jsonify(retval)  
    finally:
        accountLock.release()
        


def activateAccount(email, token):
    accountLock.acquire()
    try:
        account = tempAccounts.find_one({"emailAddress":email, "token":token})
        if account == None:
            util.debugPrint("Token not found for email address; invalid request")
            return False
        else:
            # TODO -- invoke your external account manager here (such as LDAP).
            existingAccount = accounts.find_one({"emailAddress":email})
            if existingAccount == None:
                accounts.insert(account)
                util.debugPrint("Creating new account")
                tempAccounts.remove({"_id":account["_id"]})
                return True
            else:
                util.debugPrint("Account already exists. Not creating a new one")
                return False
    except:       
        return False
    finally:
        accountLock.release()
        
def denyAccount(email, token, urlPrefix):
    # If the admin denies the account creation, 
    # The system will send the user a "we regret to inform you..." email that their account 
    # was denied. 
    accountLock.acquire()
    try:
        account = tempAccounts.find_one({"emailAddress":email, "token":token})
        if account == None:
            util.debugPrint("Token not found for email address; invalid request")
            return False
        else:
            # remove email from tempAccounts:
            tempAccounts.remove({"_id":account["_id"]})
            # email user to let them know that their request was denied:
            t = threading.Thread(target=generateUserDenyAccountEmail,args=(email,urlPrefix))
            t.daemon = True
            t.start()
            return True
    except:       
        return False
    finally:
        accountLock.release()
        
def authorizeAccount(email, token, urlPrefix):
    # If the admin authorizes the account creation, 
    # the user will need to click on a link in their email to activate their account.
    accountLock.acquire()
    try:
        account = tempAccounts.find_one({"emailAddress":email, "token":token})
        if account == None:
            util.debugPrint("Token not found for email address; invalid request")
            return False
        else:
            # reset the time clock so that the user has 2 more hours to activate account.
            util.debugPrint("account found, authorizing account")
            account["expireTime"] = time.time()+TWO_HOURS
            tempAccounts.update({"_id":account["_id"]},{"$set":account},upsert=False)
            util.debugPrint("changed expired time to 2 hours from now")
            t = threading.Thread(target=generateUserActivateAccountEmail,args=(email,urlPrefix, token))
            t.daemon = True
            t.start()
            return True
    except:       
        return False
    finally:
        accountLock.release()



Accounts.removeExpiredRows(tempAccounts)
