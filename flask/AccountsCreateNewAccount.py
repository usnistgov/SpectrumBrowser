from flask import jsonify
import random
import time
import util
import SendMail
import threading
from threading import Timer
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
    urlToClick = serverUrlPrefix + "/spectrumbrowser/activateAccount/" +emailAddress+ "?"+TEMP_ACCOUNT_TOKEN+"="+str(token)+"&urlPrefix="+serverUrlPrefix
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
    urlToClickToAuthorize = serverUrlPrefix + "/spectrumbrowser/authorizeAccount/" +emailAddress+ "?"+TEMP_ACCOUNT_TOKEN+"="+str(token)+"&urlPrefix="+serverUrlPrefix
    util.debugPrint("urlToClickToAuthorize for generateAdminAuthorizeAccountEmail email" + urlToClickToAuthorize)
    urlToClickToDeny = serverUrlPrefix + "/spectrumbrowser/denyAccount/" +emailAddress+ "?"+TEMP_ACCOUNT_TOKEN+"="+str(token)+"&urlPrefix="+serverUrlPrefix
    util.debugPrint("urlToClickToDeny for generateAdminAuthorizeAccountEmail email" + urlToClickToDeny)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"A user requested a new account from: " + str(serverUrlPrefix) +"\n"\
    +"Please click here within 48 hours if you wish to authorize the account and email the user.\n"\
    + urlToClickToAuthorize +"\n"\
    +"or please click here within 48 hours if you wish to deny the account and email the user.\n"\
    + urlToClickToDeny +"\n"
    util.debugPrint(message)
    SendMail.sendMail(message,Config.getSmtpEmail(), "Account authorization link")

def requestNewAccount(emailAddress,firstName,lastName,newPassword,serverUrlPrefix):
    tempAccounts = DbCollections.getTempAccounts()
    accounts = DbCollections.getAccounts()
    AccountLock.acquire()
    #If valid adminToken or email ends in .mil or .gov, create temp account and email user to authorize.
    #Otherwise, email admin to authorize account creation.
    try:
        util.debugPrint("requestNewAccount"+ emailAddress+firstName+lastName+newPassword+serverUrlPrefix)
        # TODO -- invoke external account manager here (such as LDAP).
        existingAccount = accounts.find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress})
        if existingAccount <> None:
            util.debugPrint("Email already exists as a user account")
            return jsonify({"status":"EXISTING"})
        else: 
            util.debugPrint("account does not exist")
            if not Accounts.isPasswordValid(newPassword) :
                util.debugPrint("Password invalid")
                return jsonify({"status":"INVALPASS"})
            elif len(firstName) == 0:
                util.debugPrint("first name invalid - 0 characters")
                return jsonify({"status":"INVALFNAME"})               
            elif len(lastName) == 0:
                util.debugPrint("last name invalid - 0 characters")
                return jsonify({"status":"INVALLNAME"})               
            else:
                util.debugPrint("Password valid")
                tempAccountRecord = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress})
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
                        expireTime = time.time()+Config.getAccountUserAcknowHours()*SECONDS_PER_HOUR
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
                        expireTime = time.time()+Config.getAccountRequestTimeoutHours()*SECONDS_PER_HOUR                      
                    tempAccountRecord = {ACCOUNT_EMAIL_ADDRESS:emailAddress,ACCOUNT_FIRST_NAME:firstName,ACCOUNT_LAST_NAME:lastName,ACCOUNT_PASSWORD:newPassword,\
                                         EXPIRE_TIME:expireTime,TEMP_ACCOUNT_TOKEN:token, ACCOUNT_PRIVILEGE:"user"}
                    tempAccounts.insert(tempAccountRecord)
                    return retVal  
    except:
        retval = {"status": "NOK"}
        return jsonify(retval)  
    finally:
        AccountLock.release()
        


def activateAccount(email, token):
    AccountLock.acquire()
    try:
        tempAccounts = DbCollections.getTempAccounts()
        accounts = DbCollections.getAccounts()
        account = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS:email, TEMP_ACCOUNT_TOKEN:token})
        if account == None:
            util.debugPrint("Token not found for email address; invalid request")
            return False
        else:
            # TODO -- invoke external account manager here (such as LDAP).
            existingAccount = accounts.find_one({ACCOUNT_EMAIL_ADDRESS:email})
            if existingAccount == None:
                account[ACCOUNT_CREATION_TIME] = time.time()
                account[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time()+Config.getTimeUntilMustChangePasswordDays()*SECONDS_PER_DAY
                account[ACCOUNT_NUM_FAILED_LOGINS] = 0
                account[ACCOUNT_LOCKED] = False  
                account[ACCOUNT_PRIVILEGE] = "user"             
                accounts.insert(account)
                existingAccount = accounts.find_one({ACCOUNT_EMAIL_ADDRESS:email})
                if existingAccount != None:
                    accounts.update({"_id":existingAccount["_id"]},{"$unset":{EXPIRE_TIME: "", TEMP_ACCOUNT_TOKEN:""}})
                util.debugPrint("Creating new account")
                tempAccounts.remove({"_id":account["_id"]})
                return True
            else:
                util.debugPrint("Account already exists. Not creating a new one")
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
        account = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS:email, TEMP_ACCOUNT_TOKEN:token})
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
        AccountLock.release()
        
def authorizeAccount(email, token, urlPrefix):
    # If the admin authorizes the account creation, 
    # the user will need to click on a link in their email to activate their account.
    AccountLock.acquire()
    try:
        tempAccounts = DbCollections.getTempAccounts()
        account = tempAccounts.find_one({ACCOUNT_EMAIL_ADDRESS:email, TEMP_ACCOUNT_TOKEN:token})
        if account == None:
            util.debugPrint("Token not found for email address; invalid request")
            return False
        else:
            # reset the time clock so that the user has 2 more hours to activate account.
            util.debugPrint("account found, authorizing account")
            account[EXPIRE_TIME] = time.time()+Config.getAccountUserAcknowHours()*SECONDS_PER_HOUR
            tempAccounts.update({"_id":account["_id"]},{"$set":account},upsert=False)
            util.debugPrint("changed expired time to 2 hours from now")
            t = threading.Thread(target=generateUserActivateAccountEmail,args=(email,urlPrefix, token))
            t.daemon = True
            t.start()
            return True
    except:       
        return False
    finally:
        AccountLock.release()

def startAccountScanner():
    global _AccountsCreateNewAccountScannerStarted
    if not '_AccountsCreateNewAccountScannerStarted' in globals():
        # Make sure we do not start multiple scanners.
        _AccountsCreateNewAccountScannerStarted = True
        Accounts.removeExpiredRows(DbCollections.getTempAccounts())
