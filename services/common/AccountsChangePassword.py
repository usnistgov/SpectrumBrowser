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


import util
import time
import threading
import SendMail
import Accounts
import Config
import AccountLock
import DbCollections
from Defines import SECONDS_PER_DAY
from Defines import ACCOUNT_EMAIL_ADDRESS
from Defines import ACCOUNT_PASSWORD
from Defines import ACCOUNT_PASSWORD_EXPIRE_TIME
from Defines import ACCOUNT_NUM_FAILED_LOGINS
from Defines import ACCOUNT_LOCKED
from Defines import ACCOUNT_OLD_PASSWORD
from Defines import ACCOUNT_NEW_PASSWORD


def generateChangePasswordEmail(emailAddress, serverUrlPrefix):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    + "Your password has been changed to value you entered into " + str(serverUrlPrefix + "/spectrumbrowser") + "\n"\
    + "If you did not originate the change password request, please contact the system administrator.\n"
    util.debugPrint(message)
    SendMail.sendMail(message, emailAddress, "change password link")


def changePasswordEmailUser(accountData, urlPrefix, sendEmail=True):
    util.debugPrint("ChangePasswordEmailuser")
    AccountLock.acquire()
    accounts = DbCollections.getAccounts()
    try:
        # JEK: Search for email/password, if found change password and email user an informational email.
        # TODO -- invoke external account manager here (such as LDAP).
        emailAddress = accountData[ACCOUNT_EMAIL_ADDRESS].strip()
        newPassword = accountData[ACCOUNT_NEW_PASSWORD]
        oldPassword = Accounts.computeMD5hash(accountData[
            ACCOUNT_OLD_PASSWORD])
        existingAccount = accounts.find_one(
            {ACCOUNT_EMAIL_ADDRESS: emailAddress,
             ACCOUNT_PASSWORD: oldPassword})

        activeAccount = DbCollections.getAccounts().find_one(
            {ACCOUNT_EMAIL_ADDRESS: emailAddress})
        failedLogins = activeAccount[ACCOUNT_NUM_FAILED_LOGINS]

        if existingAccount is None and activeAccount is not None:
            if failedLogins == (Config.getNumFailedLoginAttempts() - 2):
                util.debugPrint(
                    "Email and password combination are not correct. Account (1) try from being locked.")
                failedLogins = activeAccount[ACCOUNT_NUM_FAILED_LOGINS] + 1
                activeAccount[ACCOUNT_NUM_FAILED_LOGINS] = failedLogins
                messageBlock = [
                    "INVALCREDS",
                    "Your account is about to be locked. Please contact the system administrator for further assistance."
                ]
            elif failedLogins < Config.getNumFailedLoginAttempts():
                util.debugPrint(
                    "Email and password combination are not correct.")
                failedLogins = activeAccount[ACCOUNT_NUM_FAILED_LOGINS] + 1
                activeAccount[ACCOUNT_NUM_FAILED_LOGINS] = failedLogins
                messageBlock = [
                    "INVALUSER",
                    "Your email and current password combination are invalid. Please try retyping your password credentials again or contact the system administrator."
                ]
            else:
                util.debugPrint("The account is now locked.")
                activeAccount[ACCOUNT_LOCKED] = True
                messageBlock = [
                    "INVALLOCK",
                    "Your account is now locked. Please contact the system administrator for further assistance."
                ]

            DbCollections.getAccounts().update({"_id": activeAccount["_id"]},
                                               {"$set": activeAccount},
                                               upsert=False)
            return Accounts.packageReturn(messageBlock)

        elif existingAccount is None and activeAccount is None:
            util.debugPrint(
                "The specified email address is not registered with this system.")
            return Accounts.packageReturn([
                "INVALCREDS",
                "The specified email address is not registered with this system. Please contact the system administrator for further assistance."
            ])
        else:
            util.debugPrint("Account valid")
            # JEK: Note: we really only need to check the password and not the email here
            # Since we will email the user and know soon enough if the email is invalid.

            # TODO: check to see that new password does not match last 8 passwords:
            retVal = Accounts.isPasswordValid(newPassword)
            if not retVal[0] == "OK":
                util.debugPrint("Password invalid")
                return Accounts.packageReturn(retVal)
            else:
                passwordHash = Accounts.computeMD5hash(newPassword)
                util.debugPrint("Password valid")
                existingAccount[ACCOUNT_PASSWORD] = passwordHash
                existingAccount[ACCOUNT_NUM_FAILED_LOGINS] = 0
                existingAccount[ACCOUNT_LOCKED] = False
                existingAccount[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time(
                ) + Config.getTimeUntilMustChangePasswordDays(
                ) * SECONDS_PER_DAY
                util.debugPrint("Updating found account record")
                accounts.update({"_id": existingAccount["_id"]},
                                {"$set": existingAccount},
                                upsert=False)
                util.debugPrint("Changing account password")
                if sendEmail:
                    t = threading.Thread(target=generateChangePasswordEmail,
                                         args=(emailAddress, urlPrefix))
                    t.daemon = True
                    t.start()
                retval = [
                    "OK",
                    "Your password has been changed and you have been sent a notification email."
                ]
                return Accounts.packageReturn(retval)
    except:
        retval = [
            "NOK",
            "There was an issue changing your password. Please contact the system administrator."
        ]
        return Accounts.packageReturn(retval)
    finally:
        AccountLock.release()
