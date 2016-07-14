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

import random
import time
import util
import SendMail
import threading
import Accounts
import Config
import AccountLock
import DbCollections
from Defines import EXPIRE_TIME
from Defines import SECONDS_PER_HOUR
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
from Defines import TEMP_ACCOUNT_TOKEN


def generateUserAccountPendingAuthorizationEmail(emailAddress,
                                                 serverUrlPrefix):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
              + "You requested a new account for the CAC Measured Spectrum Occupancy Database.\n"\
              + "Your request has been sent to the system administrator for authorization.\n"
    util.debugPrint(message)
    SendMail.sendMail(message, emailAddress, "Account pending authorization")


def generateUserActivateAccountEmail(emailAddress, serverUrlPrefix, token):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    hyperlink_format = '<a href="{link}">{text}</a>'
    urlToClick = serverUrlPrefix + "/spectrumbrowser/activateAccount/" + emailAddress + "/" + str(
        token)
    util.debugPrint("URL to Click for generateUserActivateAccountEmail" +
                    urlToClick)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
              + "You requested a new account for the CAC Measured Spectrum Occupancy Database.\n"\
              + "Please click " + hyperlink_format.format(link=urlToClick, text='here') + " within 2 hours to activate your account\n"\
              + "(or ignore this mail if you did not originate this request)."
    util.debugPrint(message)
    SendMail.sendMail(message, emailAddress, "Account activation link", True)


def generateUserDenyAccountEmail(emailAddress, serverUrlPrefix):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
              + "We regret to inform you that your request for a new account from the CAC Measured Spectrum Occupancy Database was denied.\n"\
              + "Please contact the system administrator for more information.\n"
    util.debugPrint(message)
    SendMail.sendMail(message, emailAddress, "Account information")


def generateAdminAuthorizeAccountEmail(firstName, lastName, emailAddress,
                                       serverUrlPrefix, token):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    hyperlink_format = '<a href="{link}">{text}</a>'
    urlToClickToAuthorize = serverUrlPrefix + "/spectrumbrowser/authorizeAccount/" + emailAddress + "/" + str(
        token)
    util.debugPrint(
        "urlToClickToAuthorize for generateAdminAuthorizeAccountEmail email" +
        urlToClickToAuthorize)
    urlToClickToDeny = serverUrlPrefix + "/spectrumbrowser/denyAccount/" + emailAddress + "/" + str(
        token)
    util.debugPrint(
        "urlToClickToDeny for generateAdminAuthorizeAccountEmail email" +
        urlToClickToDeny)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
              + firstName + " " + lastName + " (" + emailAddress + ") requested a new account for the CAC Measured Spectrum Occupancy Database.\n"\
              + "Please click " + hyperlink_format.format(link=urlToClickToAuthorize, text='here') + " within 48 hours if you wish to authorize the account and email the user,\n"\
              + "or please click " + hyperlink_format.format(link=urlToClickToDeny, text='here') + " within 48 hours if you wish to deny the account and email the user.\n"
    util.debugPrint(message)
    SendMail.sendMail(message, Config.getSmtpEmail(),
                      "Account authorization link", True)


def requestNewAccount(accountData, serverUrlPrefix):
    tempAccounts = DbCollections.getTempAccounts()
    accounts = DbCollections.getAccounts()
    AccountLock.acquire()
    # If valid adminToken or email ends in .mil or .gov, create temp account and email user to authorize.
    # Otherwise, email admin to authorize account creation.
    try:
        util.debugPrint("requestNewAccount")
        emailAddress = accountData[ACCOUNT_EMAIL_ADDRESS].strip()
        firstName = accountData[ACCOUNT_FIRST_NAME].strip()
        lastName = accountData[ACCOUNT_LAST_NAME].strip()
        password = accountData[ACCOUNT_PASSWORD]
        privilege = accountData[ACCOUNT_PRIVILEGE].strip().lower()

        # TODO -- invoke external account manager here (such as LDAP).
        existingAccount = accounts.find_one(
            {ACCOUNT_EMAIL_ADDRESS: emailAddress})
        if existingAccount is not None:
            util.debugPrint("Email already exists as a user account")
            return Accounts.packageReturn([
                "EXISTING",
                "An account already exists for this email address. Please contact the system administrator."
            ])
        else:
            util.debugPrint("account does not exist")
            checkInputs = Accounts.checkAccountInputs(
                emailAddress, firstName, lastName, password, privilege)
            if checkInputs[0] != "OK":
                return Accounts.packageReturn(checkInputs)
            else:
                util.debugPrint("account values valid")
                tempAccountRecord = tempAccounts.find_one(
                    {ACCOUNT_EMAIL_ADDRESS: emailAddress})
                if (tempAccountRecord is not None):
                    # Account is already pending for this email.
                    util.debugPrint("Temp account pending")
                    return Accounts.packageReturn([
                        "PENDING",
                        "A request for a new account with this email address is already pending."
                    ])
                else:
                    util.debugPrint("No temp account yet")
                    passwordHash = Accounts.computeMD5hash(password)
                    random.seed()
                    token = random.randint(1, 100000)
                    # authorization is required for all entities
                    util.debugPrint(
                        "All domains are subject to admin oversight")
                    t = threading.Thread(
                        target=generateAdminAuthorizeAccountEmail,
                        args=(firstName, lastName, emailAddress,
                              serverUrlPrefix, token))
                    t.daemon = True
                    t.start()
                    t2 = threading.Thread(
                        target=generateUserAccountPendingAuthorizationEmail,
                        args=(emailAddress, serverUrlPrefix))
                    t2.daemon = True
                    t2.start()
                    retVal = Accounts.packageReturn([
                        "FORWARDED",
                        "Your request has been forwarded for approval. Please check your email within 2 hours for further action."
                    ])
                    expireTime = time.time() + Config.getAccountRequestTimeoutHours() * SECONDS_PER_HOUR
                    tempAccountRecord = {ACCOUNT_EMAIL_ADDRESS:emailAddress, ACCOUNT_FIRST_NAME:firstName, ACCOUNT_LAST_NAME:lastName, ACCOUNT_PASSWORD:passwordHash, 
                                         EXPIRE_TIME:expireTime, TEMP_ACCOUNT_TOKEN:token, ACCOUNT_PRIVILEGE:privilege}
                    tempAccounts.insert(tempAccountRecord)
                    return retVal
    except:
        return Accounts.packageReturn([
            "NOK",
            "There was an issue creating your account. Please contact the system administrator."
        ])
    finally:
        AccountLock.release()


def activateAccount(email, token):
    AccountLock.acquire()
    try:
        tempAccounts = DbCollections.getTempAccounts()
        accounts = DbCollections.getAccounts()
        account = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS: email,
                                         TEMP_ACCOUNT_TOKEN: token})
        if account is None:
            util.debugPrint(
                "Token not found for email address; invalid request")
            return False
        else:
            # TODO -- invoke external account manager here (such as LDAP).
            existingAccount = accounts.find_one({ACCOUNT_EMAIL_ADDRESS: email})
            if existingAccount is None:
                account[ACCOUNT_CREATION_TIME] = time.time()
                account[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time(
                ) + Config.getTimeUntilMustChangePasswordDays(
                ) * SECONDS_PER_DAY
                account[ACCOUNT_NUM_FAILED_LOGINS] = 0
                account[ACCOUNT_LOCKED] = False
                accounts.insert(account)
                existingAccount = accounts.find_one(
                    {ACCOUNT_EMAIL_ADDRESS: email})
                if existingAccount is not None:
                    accounts.update({"_id": existingAccount["_id"]},
                                    {"$unset": {EXPIRE_TIME: "",
                                                TEMP_ACCOUNT_TOKEN: ""}})
                util.debugPrint("Creating new account")
                tempAccounts.remove({"_id": account["_id"]})
                return True
            else:
                util.debugPrint(
                    "Account already exists. Not creating a new one")
                return False
    except:
        return False
    finally:
        AccountLock.release()


def denyAccount(email, token, urlPrefix):
    # If the admin denies the account creation,
    # The system will send the user a "we regret to inform you..." email that their account
    # was denied.
    AccountLock.acquire()
    try:
        tempAccounts = DbCollections.getTempAccounts()
        account = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS: email,
                                         TEMP_ACCOUNT_TOKEN: token})
        if account is None:
            util.debugPrint(
                "Token not found for email address; invalid request")
            return False
        else:
            # remove email from tempAccounts:
            tempAccounts.remove({"_id": account["_id"]})
            # email user to let them know that their request was denied:
            t = threading.Thread(target=generateUserDenyAccountEmail,
                                 args=(email, urlPrefix))
            t.daemon = True
            t.start()
            return True
    except:
        return False
    finally:
        AccountLock.release()


def authorizeAccount(email, token, urlPrefix):
    # If the admin authorizes the account creation,
    # the user will need to click on a link in their email to activate their account.
    AccountLock.acquire()
    try:
        tempAccounts = DbCollections.getTempAccounts()
        account = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS: email,
                                         TEMP_ACCOUNT_TOKEN: token})
        if account is None:
            util.debugPrint(
                "Token not found for email address; invalid request")
            return False
        else:
            # reset the time clock so that the user has 2 more hours to activate account.
            util.debugPrint("account found, authorizing account")
            account[EXPIRE_TIME] = time.time(
            ) + Config.getAccountUserAcknowHours() * SECONDS_PER_HOUR
            tempAccounts.update({"_id": account["_id"]}, {"$set": account},
                                upsert=False)
            util.debugPrint("changed expired time to 2 hours from now")
            t = threading.Thread(target=generateUserActivateAccountEmail,
                                 args=(email, urlPrefix, token))
            t.daemon = True
            t.start()
            return True
    except:
        return False
    finally:
        AccountLock.release()


def startAccountScanner():
    global _AccountsCreateNewAccountScannerStarted
    if  '_AccountsCreateNewAccountScannerStarted' not in globals():
        # Make sure we do not start multiple scanners.
        _AccountsCreateNewAccountScannerStarted = True
        Accounts.removeExpiredRows(DbCollections.getTempAccounts())
