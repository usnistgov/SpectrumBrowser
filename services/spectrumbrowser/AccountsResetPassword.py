import random
import threading
from threading import Timer
import util
import SendMail
import time
import Accounts
import Config
import AccountLock
import DbCollections
from Defines import EXPIRE_TIME
from Defines import SECONDS_PER_DAY
from Defines import SECONDS_PER_HOUR
from Defines import ACCOUNT_EMAIL_ADDRESS
from Defines import ACCOUNT_PASSWORD
from Defines import ACCOUNT_NEW_PASSWORD
from Defines import TEMP_ACCOUNT_TOKEN
from Defines import ACCOUNT_PASSWORD_EXPIRE_TIME
from Defines import ACCOUNT_NUM_FAILED_LOGINS
from Defines import ACCOUNT_LOCKED


def generateResetPasswordEmail(emailAddress, serverUrlPrefix, token):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    urlToClick = serverUrlPrefix + "/spectrumbrowser/resetPassword/" + emailAddress + "/" + str(token)
    util.debugPrint("URL to Click for reset password email" + urlToClick)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    + "You requested to reset your password to a password you entered into " + str(serverUrlPrefix) + "\n"\
    + "Please click here within 2 hours to reset your password\n"\
    + "(or ignore this mail if you did not originate this request):\n"\
    + urlToClick + "\n"
    util.debugPrint(message)
    SendMail.sendMail(message, emailAddress, "reset password link")


def storePasswordAndEmailUser(accountData, urlPrefix):
    
    AccountLock.acquire()
    
    try:
        # JEK: Search for email, if found send email for user to activate reset password.
        # TODO -- invoke external account manager here (such as LDAP).
        emailAddress = accountData[ACCOUNT_EMAIL_ADDRESS].strip()       
        newPassword = accountData[ACCOUNT_NEW_PASSWORD]
        existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress})
        if existingAccount == None:
            util.debugPrint("Email not found as an existing user account")
            return Accounts.packageReturn(["INVALUSER", "Your email does not match an existing user account. Please contact the web administrator."])
        else:
            # JEK: Note: we really only need to check the password and not the email here
            # Since we will email the user and know soon enough if the email is invalid.
            
            # TODO: check to see that new password does not match last 8 passwords:
            retVal = Accounts.isPasswordValid(newPassword)
            if not retVal[0] == "OK" :
                util.debugPrint("Password invalid")
                return Accounts.packageReturn(retVal)
            else:
                util.debugPrint("Password valid")
                passwordHash = Accounts.computeMD5hash(newPassword)
                tempPasswordRecord = DbCollections.getTempPasswords().find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress})
                if tempPasswordRecord == None:
                    util.debugPrint("Email not found")
                    random.seed()
                    token = random.randint(1, 100000)
                    expireTime = time.time() + Config.getAccountUserAcknowHours() * SECONDS_PER_HOUR
                    util.debugPrint("set temp record")
                    # since this is only stored temporarily for a short time, it is ok to have a temp plain text password
                    tempPasswordRecord = {ACCOUNT_EMAIL_ADDRESS:emailAddress, ACCOUNT_PASSWORD:passwordHash, EXPIRE_TIME:expireTime, TEMP_ACCOUNT_TOKEN:token}
                    DbCollections.getTempPasswords().insert(tempPasswordRecord)
                    retval = ["OK", "You have been sent an email with a web link. Please click on the link to reset your password."]
                    util.debugPrint("OK")
                    t = threading.Thread(target=generateResetPasswordEmail, args=(emailAddress, urlPrefix, token))
                    t.daemon = True
                    t.start()
                    return Accounts.packageReturn(retval)
                else:
                    print "Email found"
                    # Password reset is already pending for this email.
                    return Accounts.packageReturn(["PENDING", "You already have a pending request to reset your password. Please check your email."])

    except:
        retval = ["NOK", "There was an issue sending you an email to reset your password. Please contact the web administrator."]
        print "NOK"
        return Accounts.packageReturn(retval)
    finally:
        AccountLock.release()
        
def activatePassword(email, token):
    util.debugPrint("called active password sub")
    AccountLock.acquire()
    try:
        tempPassword = DbCollections.getTempPasswords().find_one({ACCOUNT_EMAIL_ADDRESS:email, TEMP_ACCOUNT_TOKEN:token})
        if tempPassword == None:
            util.debugPrint("Email and token not found; invalid request")
            return False
        else:
            util.debugPrint("Email and token found in temp passwords")
            # TODO -- invoke external account manager here (such as LDAP).
            existingAccount = DbCollections.getAccounts().find_one({ACCOUNT_EMAIL_ADDRESS:email})
            if existingAccount == None:
                util.debugPrint("Account does not exist, cannot reset password")
                return False
            else:
                util.debugPrint("Email found in existing accounts")
                existingAccount[ACCOUNT_PASSWORD] = tempPassword["password"]
                existingAccount[ACCOUNT_NUM_FAILED_LOGINS] = 0
                existingAccount[ACCOUNT_LOCKED] = False
                existingAccount[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time() + Config.getTimeUntilMustChangePasswordDays() * SECONDS_PER_DAY
                DbCollections.getAccounts().update({"_id":existingAccount["_id"]}, {"$set":existingAccount}, upsert=False)
                util.debugPrint("Resetting account password")
                DbCollections.getTempPasswords().remove({"_id":tempPassword["_id"]})
                return True
    except:       
        return False
    finally:
        AccountLock.release()

def startAccountsResetPasswordScanner():
    global _AccountsResetPasswordScanner
    if not "_AccountsResetPasswordScanner" in globals():
        _AccountsResetPasswordScanner = True
        Accounts.removeExpiredRows(DbCollections.getTempPasswords())


