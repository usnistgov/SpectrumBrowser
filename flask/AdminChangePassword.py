import flaskr as main
from flask import jsonify
import util
import threading
import SendMail
import authentication
accountLock = threading.Lock()
accounts = main.admindb.accounts


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
    accountLock.acquire()
    try:
        # JEK: Search for email/password, if found change password and email user an informational email.
        # TODO -- invoke external account manager here (such as LDAP).
        existingAccount = accounts.find_one({"emailAddress":email, "password":oldPassword})
        if account == None:
            util.debugPrint("Email and password not found as an existing user account")
            return jsonify({"status":"INVALUSER"})
        else:
            if not AdminAccounts.isPasswordValid(newPassword) :
                print "Password invalid"
                return jsonify({"status":"INVALPASS"})
            else:
                existingAccount["password"] = newPassword
                existingAccount["time"] = time.time()
                accounts.update({"_id":existingAccount["_id"]},{"$set":existingAccount},upsert=False)
                util.debugPrint("Changing account password")
                t = threading.Thread(target=generateChangePasswordEmail,args=(emailAddress, urlPrefix))
                t.daemon = True
                t.start()
    except:
        retval = {"status": "NOK"}
        return jsonify(retval)
    else:
        retval = {"status": "OK"}
        return jsonify(retval)
    finally:
        accountLock.release()



