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
    + "Your password has been changed to value you entered into " + str(serverUrlPrefix) + "\n"\
    + "If you did not originate the change password request, please contact the system administrator.\n"
    util.debugPrint(message)
    SendMail.sendMail(message, emailAddress, "change password link")


def changePasswordEmailUser(accountData, urlPrefix):
    util.debugPrint("ChangePasswordEmailuser")
    AccountLock.acquire()
    accounts = DbCollections.getAccounts()
    try:   
        # JEK: Search for email/password, if found change password and email user an informational email.
        # TODO -- invoke external account manager here (such as LDAP).
        emailAddress = accountData[ACCOUNT_EMAIL_ADDRESS].strip()       
        newPassword = accountData[ACCOUNT_NEW_PASSWORD]
        oldPassword = Accounts.computeMD5hash(accountData[ACCOUNT_OLD_PASSWORD])
        existingAccount = accounts.find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress, ACCOUNT_PASSWORD:oldPassword})
        if existingAccount == None:
            util.debugPrint("Email and password not found as an existing user account")
            return Accounts.packageReturn(["INVALUSER", "Your email and/or current password are invalid. Please try resetting your password or contact the web administrator."])
        else:
            util.debugPrint("Account valid") 
            # JEK: Note: we really only need to check the password and not the email here
            # Since we will email the user and know soon enough if the email is invalid.
            
            # TODO: check to see that new password does not match last 8 passwords:
            retVal = Accounts.isPasswordValid(newPassword)
            if not retVal[0] == "OK" :
                util.debugPrint("Password invalid")
                return Accounts.packageReturn(retVal)
            else:
                passwordHash = Accounts.computeMD5hash(newPassword)
                util.debugPrint("Password valid")
                existingAccount[ACCOUNT_PASSWORD] = passwordHash
                existingAccount[ACCOUNT_NUM_FAILED_LOGINS] = 0
                existingAccount[ACCOUNT_LOCKED] = False 
                existingAccount[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time() + Config.getTimeUntilMustChangePasswordDays()
                util.debugPrint("Updating found account record")
                accounts.update({"_id":existingAccount["_id"]}, {"$set":existingAccount}, upsert=False)
                util.debugPrint("Changing account password")
                t = threading.Thread(target=generateChangePasswordEmail, args=(emailAddress, urlPrefix))
                t.daemon = True
                t.start()
                retval = ["OK", "Your password has been changed and you have been sent a notification email."]
                return Accounts.packageReturn(retval)
    except:
        retval = ["NOK", "There was an issue changing your password. Please contact the web administrator."]
        return Accounts.packageReturn(retval)
    finally:
        AccountLock.release()



