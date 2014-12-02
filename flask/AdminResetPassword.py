import flaskr as main
from flask import jsonify
import random
import threading
from threading import Timer
import util
import SendMail
import time
import AdminAccounts
accountLock = threading.Lock()
tempPasswords = main.admindb.tempPasswords
accounts = main.admindb.accounts

def generateResetPasswordEmail(emailAddress,serverUrlPrefix, token):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    urlToClick = serverUrlPrefix + "/spectrumbrowser/resetPassword/" +emailAddress+ "?token="+str(token)
    util.debugPrint("URL to Click for reset password email" + urlToClick)
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"You requested to reset your password to a password you entered into " + str(serverUrlPrefix) +"\n"\
    +"Please click here within 2 hours to reset your password\n"\
    +"(or ignore this mail if you did not originate this request):\n"\
    + urlToClick +"\n"
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "reset password link")


def storePasswordAndEmailUser(emailAddress,newPassword,urlPrefix):
    # JEK: Note: we really only need to check the password and not the email here
    # Since we will email the user and know soon enough if the email is invalid.
    if not AdminAccounts.isPasswordValid(newPassword) :
        print "Password invalid"
        return jsonify({"status":"INVALPASS"})
    accountLock.acquire()
    
    try:
        print "storePasswordAndEmailUser", emailAddress,newPassword,urlPrefix
        tempPasswordRecord = tempPasswords.find_one({"emailAddress":emailAddress})
        if tempPasswordRecord == None:
            print "Email not found"
            random.seed()
            token = random.randint(1,100000)
            currentTime = time.time()
            #since this is only stored temporarily for a short time, it is ok to have a temp plain text password
            tempPasswordRecord = {"emailAddress":emailAddress,"password":newPassword,"time":currentTime,"token":token}
            tempPasswords.insert(tempPasswordRecord)
        else:
            print "Email found"
            tempPasswordRecord["password"] = newPassword
            tempPasswordRecord["time"] = time.time()
            tempPasswords.update({"_id":tempPasswordRecord["_id"]},{"$set":tempPasswordRecord},upsert=False)
            token = tempPasswordRecord["token"]


        t = threading.Thread(target=generateResetPasswordEmail,args=(emailAddress,urlPrefix, token))
        t.daemon = True
        t.start()
    except:
        retval = {"status": "NOK"}
        print "NOK"
        return jsonify(retval)
    else:
        retval = {"status": "OK"}
        print "OK"
        return jsonify(retval)

    finally:
        accountLock.release()
        
def activatePassword(email, token):
    accountLock.acquire()
    try:
        account = tempPasswords.find_one({"emailAddress":email, "token":token})
        if account == None:
            util.debugPrint("Token not found; invalid request")
            return False
        else:
            # TODO -- invoke external account manager here (such as LDAP).
            existingAccount = accounts.find_one({"emailAddress":email})
            if existingAccount == None:
                util.debugPrint("Account does not exist, cannot update password")
                return False
            else:
                existingAccount["password"] = newPassword
                existingAccount["time"] = time.time()
                accounts.update({"_id":existingAccount["_id"]},{"$set":existingAccount},upsert=False)
                util.debugPrint("Resetting account password")
                tempPasswords.remove({"_id":account["_id"]})
                return True
    finally:
        accountLock.release()

AdminAccounts.removeExpiredRows(tempPasswords)


