# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others. 
#This software has been contributed to the public domain. 
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain. 
#As a result, a formal license is not needed to use this software.
# 
#This software is provided "AS IS."  
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.


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
import argparse
from Defines import EXPIRE_TIME
from Defines import SECONDS_PER_DAY
from Defines import ACCOUNT_EMAIL_ADDRESS
from Defines import ACCOUNT_FIRST_NAME
from Defines import ACCOUNT_LAST_NAME
from Defines import ACCOUNT_PASSWORD
from Defines import ACCOUNT_PRIVILEGE
from Defines import ACCOUNT_CREATION_TIME
from Defines import ACCOUNT_PASSWORD_EXPIRE_TIME
from Defines import ACCOUNT_NUM_FAILED_LOGINS
from Defines import ACCOUNT_LOCKED
from Defines import USER_ACCOUNTS
from Defines import STATUS
from Defines import STATUS_MESSAGE
from Defines import USER
from Defines import ADMIN


# This .py code is for the account management from the admin pages:
def packageAccountsReturn(retval):
    retvalMap = {}
    retvalMap["status"] = retval[0]
    retvalMap["statusMessage"] = retval[1]
    retvalMap[USER_ACCOUNTS] = getUserAccounts()
    return retvalMap


def numAdminAccounts():
    numAdmin = DbCollections.getAccounts().find(
        {ACCOUNT_PRIVILEGE: ADMIN}).count()
    util.debugPrint("num admin accounts: " + str(numAdmin))
    return numAdmin


def getDefaultAdminEmailAddress():
    return "admin@nist.gov"


def getDefaultAdminPassword():
    return "Administrator12!"


def timeToDateTime(timeSecs):
    ts = datetime.datetime.fromtimestamp(timeSecs).strftime(
        '%m-%d-%Y %H:%M UTC')
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
            cur["dateAccountCreated"] = timeToDateTime(cur[
                ACCOUNT_CREATION_TIME])
            cur["datePasswordExpires"] = timeToDateTime(cur[
                ACCOUNT_PASSWORD_EXPIRE_TIME])
            del cur[ACCOUNT_CREATION_TIME]
            del cur[ACCOUNT_PASSWORD_EXPIRE_TIME]
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
        account = accounts.find_one({ACCOUNT_EMAIL_ADDRESS: emailAddress})
        if account == None:
            util.debugPrint("Cannot delete account, email not found " +
                            emailAddress)
            retVal = ["INVALUSER", "Account not found."]
        elif numAdmin == 1 and account[ACCOUNT_PRIVILEGE] == ADMIN:
            util.debugPrint("Cannot delete account, last admin account.")
            retVal = [
                "LASTADMIN",
                "Last admin account, cannot perform operation or there would be no admin accounts left."
            ]
        else:
            util.debugPrint("Removing account.")
            accounts.remove({"_id": account["_id"]})
            util.debugPrint("account deleted: " + emailAddress)
            retVal = ["OK", ""]
    except:
        retVal = [
            "NOK",
            "There was an issue on the server, please check the system logs."
        ]
    finally:
        AccountLock.release()
    return packageAccountsReturn(retVal)


# Note this is for manual deletion of all accounts 
# If the admin forgot his password then you would do this.
def deleteAllAdminAccounts():
    AccountLock.acquire()
    DbCollections.getAccounts().remove({ACCOUNT_PRIVILEGE: ADMIN})
    AccountLock.release()


# Note: this for first time system initialization
def deleteAllAccounts():
    AccountLock.acquire()
    DbCollections.getAccounts().remove({})
    AccountLock.release()


def createAccount(accountData):
    # this function is for creating accounts from the admin page rather than users requesting accounts.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        tempAccounts = DbCollections.getTempAccounts()
        util.debugPrint(accountData)
        emailAddress = accountData[ACCOUNT_EMAIL_ADDRESS].strip()
        firstName = accountData[ACCOUNT_FIRST_NAME].strip()
        lastName = accountData[ACCOUNT_LAST_NAME].strip()
        password = accountData[ACCOUNT_PASSWORD]
        privilege = accountData[ACCOUNT_PRIVILEGE].strip().lower()
        tempAccountRecord = tempAccounts.find_one(
            {ACCOUNT_EMAIL_ADDRESS: emailAddress})
        util.debugPrint("search for temp account")
        if tempAccountRecord != None:
            # remove temporary pending account, no real need to inform admin, I do not think:
            util.debugPrint("temp account found")
            tempAccounts.remove({"_id": tempAccountRecord["_id"]})
        util.debugPrint("search for existing account")
        if accounts.find_one({ACCOUNT_EMAIL_ADDRESS: emailAddress}) != None:
            util.debugPrint("Account already exists")
            retVal = ["EXISTING",
                      "An account already exists for this email address."]
        else:
            util.debugPrint("check account inputs")
            util.debugPrint("emailAddress: " + emailAddress + "; firstName= " + firstName + \
                             "; lastName= " + lastName + "; password= " + password + " privilege= " + privilege)
            util.debugPrint("check account inputs")
            checkInputs = Accounts.checkAccountInputs(
                emailAddress, firstName, lastName, password, privilege)
            if checkInputs[0] == "OK":
                util.debugPrint("inputs ok")
                passwordHash = Accounts.computeMD5hash(password)
                account = {ACCOUNT_EMAIL_ADDRESS:emailAddress, ACCOUNT_FIRST_NAME:firstName, \
                           ACCOUNT_LAST_NAME:lastName, ACCOUNT_PASSWORD:passwordHash, ACCOUNT_PRIVILEGE:privilege}
                account[ACCOUNT_CREATION_TIME] = time.time()
                account[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time(
                ) + Config.getTimeUntilMustChangePasswordDays(
                ) * SECONDS_PER_DAY
                account[ACCOUNT_NUM_FAILED_LOGINS] = 0
                account[ACCOUNT_LOCKED] = False
                accounts.insert(account)
                retVal = ["OK", "Account created successfully."]
            else:
                retVal = checkInputs
    except:
        retVal = [
            "NOK",
            "There was an issue on the server, please check the system logs."
        ]
    finally:
        AccountLock.release()
    return packageAccountsReturn(retVal)


def resetAccountExpiration(emailAddress):
    # this function is for resetting account expiration from the admin page.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({ACCOUNT_EMAIL_ADDRESS: emailAddress})
        if account == None:
            util.debugPrint("Account does not exist, cannot reset account")
            retVal = ["INVALUSER", "Account not found."]

        else:
            account[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time(
            ) + Config.getTimeUntilMustChangePasswordDays() * SECONDS_PER_DAY
            accounts.update({"_id": account["_id"]}, {"$set": account},
                            upsert=False)
            retVal = ["OK", "Terrific"]
    except:
        retVal = [
            "NOK",
            "There was an issue on the server, please check the system logs."
        ]
    finally:
        AccountLock.release()
    return packageAccountsReturn(retVal)


def unlockAccount(emailAddress):
    # this function is unlocking account from the admin page.
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({ACCOUNT_EMAIL_ADDRESS: emailAddress})
        if account == None:
            util.debugPrint("Account does not exist, cannot unlock account")
            retVal = ["INVALUSER", "Account not found."]
        else:
            account[ACCOUNT_NUM_FAILED_LOGINS] = 0
            account[ACCOUNT_LOCKED] = False
            accounts.update({"_id": account["_id"]}, {"$set": account},
                            upsert=False)
            retVal = ["OK", ""]
    except:
        retVal = [
            "NOK",
            "There was an issue on the server, please check the system logs."
        ]
    finally:
        AccountLock.release()
    return packageAccountsReturn(retVal)


def togglePrivilegeAccount(emailAddress):
    """
    Reset account expiration from the admin page.
    """
    AccountLock.acquire()
    try:
        accounts = DbCollections.getAccounts()
        account = accounts.find_one({ACCOUNT_EMAIL_ADDRESS: emailAddress})
        if account == None:
            util.debugPrint("Account does not exist, cannot reset account")
            retVal = ["INVALUSER", "Account not found."]
        else:
            if account[ACCOUNT_PRIVILEGE] == ADMIN:
                if numAdminAccounts() == 1:
                    retVal = [
                        "LASTADMIN",
                        "Last admin account, cannot perform operation or there would be no admin accounts left."
                    ]
                else:
                    account[ACCOUNT_PRIVILEGE] = USER
                    accounts.update({"_id": account["_id"]}, {"$set": account},
                                    upsert=False)
                    retVal = ["OK", ""]
            else:
                account[ACCOUNT_PRIVILEGE] = ADMIN
                accounts.update({"_id": account["_id"]}, {"$set": account},
                                upsert=False)
                retVal = ["OK", ""]
    except:
        retVal = [
            "NOK",
            "There was an issue on the server, please check the system logs."
        ]
    finally:
        AccountLock.release()
    return packageAccountsReturn(retVal)


def resetPassword(accountData):
    """
    Reset the password.
    """
    util.debugPrint("resetPassword " + str(accountData))
    userName = accountData[ACCOUNT_EMAIL_ADDRESS].strip()
    password = accountData[ACCOUNT_PASSWORD]
    privilege = accountData[ACCOUNT_PRIVILEGE]
    passwordHash = Accounts.computeMD5hash(password)
    existingAccount = DbCollections.getAccounts().find_one(
        {ACCOUNT_EMAIL_ADDRESS: userName,
         ACCOUNT_PASSWORD: passwordHash})
    if existingAccount == None:
        return {STATUS: "NOK", ERROR_MESSAGE: "Authentication Failure"}
    elif existingAccount[ACCOUNT_LOCKED]:
        return {STATUS: "NOK", ERROR_MESSAGE: "Account Locked"}
    else:
        newPassword = accountData[ACCOUNT_NEW_PASSWORD]
        newPasswordHash = Accounts.computeMD5Hash(newPassword)
        result = Accounts.isPasswordValid(newPassword)
        if result[0] != "OK":
            return Accounts.packageReturn(result)
        else:
            existingAccount[ACCOUNT_PASSWORD] = newPasswordHash
            DbCollections.getAccounts().update({"_id": existingAccount["_id"]},
                                               {"$set": existingAccount},
                                               upsert=False)
            return {STATUS: "OK"}


def add_accounts(filename):
    import json
    data = []
    with open(filename, 'r') as f:
        data = f.read()
    accounts = eval(data)
    for account in accounts:
        createAccount(account)

# Self initialization scaffolding code.
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('action', default="init", help="init (default)")
    parser.add_argument('-f', help='accounts file')
    args = parser.parse_args()
    action = args.action
    if args.action == "init" or args.action == None:
        accountFile = args.f
        if accountFile == None:
            parser.error("Please specify accounts file")
        deleteAllAccounts()
        add_accounts(accountFile)
    else:
        parser.error("Unknown option " + args.action)
