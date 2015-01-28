import flaskr as main
from flask import jsonify
import util
import time
import threading
import SendMail
import Accounts
import AccountLock
SIXTY_DAYS = 60*60*60*60


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
    accounts = main.getAccounts()
    try:   
        # JEK: Search for email/password, if found change password and email user an informational email.
        # TODO -- invoke external account manager here (such as LDAP).
        existingAccount = accounts.find_one({"emailAddress":emailAddress, "password":oldPassword})
        #existingAccount = accounts.find_one({"emailAddress":emailAddress})
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
                existingAccount["password"] = newPassword
                existingAccount["numFailedLoggingAttempts"] = 0
                existingAccount["accountLocked"] = False 
                existingAccount["timePasswordExpires"] = time.time()+SIXTY_DAYS
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



