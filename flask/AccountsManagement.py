import flaskr as main
from flask import jsonify
import re
import time
import util
import threading
import Accounts
import Config
import datetime
from threading import Timer
import AccountLock
import DbCollections
from Defines import EXPIRE_TIME
from Defines import SECONDS_PER_DAY

# This .py code is for the account management from the admin pages:

def numAdminAccounts():
    numAdmin = DbCollections.getAccounts().find({ "privilege":"admin"}).count()
    util.debugPrint("num admin accounts: "+str(numAdmin))
    return numAdmin
    

def getDefaultAdminEmailAddress():
    return "admin@nist.gov"

def getDefaultAdminPassword():
    return "Administrator12!"

def timeToDateTime(timeSecs):
    ts = datetime.datetime.fromtimestamp(timeSecs).strftime('%m-%d-%Y %H:%M UTC') 
    return ts

def getUserAccounts():
    util.debugPrint("AccountsManagement.getUserAccounts")
    userAccounts = []
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        allAccounts = accounts.find()
        for cur in allAccounts:
            del cur["_id"]
            cur["dateAccountCreated"] = timeToDateTime(cur["timeAccountCreated"])
            cur["datePasswordExpires"]= timeToDateTime(cur["timePasswordExpires"])
            del cur["timeAccountCreated"]
            del cur["timePasswordExpires"]
            userAccounts.append(cur)
    except:       
        userAccounts = []
    finally:
        AccountLock.release()
    return userAccounts    
        
def deleteAccount(emailAddress):
    
    AccountLock.acquire()
    try:
        numAdmin = numAdminAccounts()
        util.debugPrint("delete account.")
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({"emailAddress":emailAddress})
        if account == None:
            util.debugPrint("Cannot delete account, email not found " + emailAddress)
            retVal = "INVALUSER"
        elif numAdmin == 1 and account["privilege"] == "admin":
            util.debugPrint("Cannot delete account, last admin account.")
            retVal = "LASTADMIN"
        else:    
            util.debugPrint("Removing account.")
            accounts.remove({"_id":account["_id"]})
            util.debugPrint("account deleted: "+emailAddress)
            retVal = "OK"
    except:       
        retVal = "NOK"
    finally:
        AccountLock.release()    
    return retVal



def createAccount(accountData):
    # this function is for creating accounts from the admin page rather than users requesting accounts.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        tempAccounts = DbCollections.getTempAccounts()
        util.debugPrint(accountData)
        emailAddress = accountData["emailAddress"].strip()       
        firstName = accountData["firstName"].strip()
        lastName = accountData["lastName"].strip()
        password = accountData["password"]
        privilege = accountData["privilege"].strip().lower()
        tempAccountRecord = tempAccounts.find_one({"emailAddress":emailAddress})
        util.debugPrint("search for temp account")       
        if tempAccountRecord != None:
            # remove temporary pending account, no real need to inform admin, I do not think:
            util.debugPrint("temp account found") 
            tempAccounts.remove({"_id":tempAccountRecord["_id"]})
        util.debugPrint("search for existing account")  
        if accounts.find_one({"emailAddress":emailAddress}) != None:
            util.debugPrint("Account already exists")
            retVal = "EXISTING" 
        else:
            util.debugPrint("check account inputs")
            util.debugPrint("emailAddress: " + emailAddress+ "; firstName= " +  firstName +\
                             "; lastName= " + lastName+ "; password= " +password+ " privilege= " + privilege)
            util.debugPrint("check account inputs")
            if Accounts.checkAccountInputs(emailAddress, firstName,lastName,password, privilege) == "OK":
                util.debugPrint("inputs ok") 
                account = {"emailAddress":emailAddress,"firstName":firstName, \
                           "lastName":lastName,"password":password, "privilege":privilege}
                account["timeAccountCreated"] = time.time()
                account["timePasswordExpires"] = time.time()+Config.getTimeUntilMustChangePasswordDays()*SECONDS_PER_DAY
                account["numFailedLoginAttempts"] = 0
                account["accountLocked"] = False  
                accounts.insert(account)
                retVal = "OK"
    except:
        retVal = "NOK"
    finally:
            AccountLock.release()
    return retVal

def resetAccountExpiration(emailAddress):
    # this function is for resetting account expiration from the admin page.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({"emailAddress":emailAddress})
        if  account == None:
            util.debugPrint("Account does not exist, cannot reset account")
            retVal = "INVALUSER"
        else:
            account["timePasswordExpires"] = time.time()+Config.getTimeUntilMustChangePasswordDays()*SECONDS_PER_DAY
            accounts.update({"_id":account["_id"]},{"$set":account},upsert=False)
            retVal = "OK"
    except:
        retVal = "NOK"
    finally:
            AccountLock.release()
    return retVal


def unlockAccount(emailAddress):
    # this function is unlocking account from the admin page.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({"emailAddress":emailAddress})
        if  account == None:
            util.debugPrint("Account does not exist, cannot unlock account")
            retVal = "INVALUSER"
        else:
            account["numFailedLoginAttempts"] = 0
            account["accountLocked"] = False  
            accounts.update({"_id":account["_id"]},{"$set":account},upsert=False)
            retVal = "OK"
    except:
        retVal = "NOK"
    finally:
            AccountLock.release()
    return retVal

def togglePrivilegeAccount(emailAddress):
    # this function is for resetting account expiration from the admin page.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({"emailAddress":emailAddress})
        if  account == None:
            util.debugPrint("Account does not exist, cannot reset account")
            retVal = "INVALUSER"
        else:
            if account["privilege"] == "admin":
                if numAdminAccounts() == 1:
                    retVal = "LASTADMIN"
                else:
                    account["privilege"] = "user"
                    accounts.update({"_id":account["_id"]},{"$set":account},upsert=False)
                    retVal = "OK"
            else:
                account["privilege"] = "admin"
                accounts.update({"_id":account["_id"]},{"$set":account},upsert=False)
                retVal = "OK"           
    except:
        retVal = "NOK"
    finally:
            AccountLock.release()
    return retVal


        
