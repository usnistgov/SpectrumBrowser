from flask import jsonify
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


def generateChangePasswordEmail(emailAddress,serverUrlPrefix):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"Your password has been changed to value you entered into " + str(serverUrlPrefix) +"\n"\
    +"If you did not originate the change password request, please contact the system administrator.\n"
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "change password link")


def changePasswordEmailUser(emailAddress, oldPassword, newPassword, urlPrefix):
    util.debugPrint("ChangePasswordEmailuser")
    AccountLock.acquire()
    accounts = DbCollections.getAccounts()
    try:   
        # JEK: Search for email/password, if found change password and email user an informational email.
        # TODO -- invoke external account manager here (such as LDAP).
        existingAccount = accounts.find_one({ACCOUNT_EMAIL_ADDRESS:emailAddress, ACCOUNT_PASSWORD:oldPassword})
        if existingAccount == None:
            util.debugPrint("Email and password not found as an existing user account")
            return jsonify({"status":"INVALUSER"})
        else:
            util.debugPrint("Account valid") 
            # JEK: Note: we really only need to check the password and not the email here
            # Since we will email the user and know soon enough if the email is invalid.
            if not Accounts.isPasswordValid(newPassword) :
                util.debugPrint("Password invalid")
                return jsonify({"status":"INVALPASS"})
            else:
                util.debugPrint("Password valid")
                existingAccount[ACCOUNT_PASSWORD] = newPassword
                existingAccount[ACCOUNT_NUM_FAILED_LOGINS] = 0
                existingAccount[ACCOUNT_LOCKED] = False 
                existingAccount[ACCOUNT_PASSWORD_EXPIRE_TIME] = time.time()+Config.getTimeUntilMustChangePasswordDays()
                print newPassword
                print existingAccount
                util.debugPrint("Updating found account record")
                accounts.update({"_id":existingAccount["_id"]},{"$set":existingAccount},upsert=False)
                util.debugPrint("Changing account password")
                t = threading.Thread(target=generateChangePasswordEmail,args=(emailAddress, urlPrefix))
                t.daemon = True
                t.start()
                retval = {"status": "OK"}
                return jsonify(retval)
    except:
        retval = {"status": "NOK"}
        return jsonify(retval)
    finally:
        AccountLock.release()



