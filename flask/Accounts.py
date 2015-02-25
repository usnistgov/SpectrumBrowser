import flaskr as main
import re
import time
import util
import threading
from threading import Timer
accountLock = threading.Lock()


accountLock = threading.Lock()

def removeExpiredRows(tempMongoRows):
    accountLock.acquire()
    try:
        # remove stale requests
        for tempMongoRow in tempMongoRows.find() :
            currentTime = time.time()
            expireTime = tempMongoRow["expireTime"]
            if currentTime  > expireTime:
               tempMongoRows.remove({"_id":tempMongoRow["_id"]})
    finally:
        accountLock.release()

    t = Timer(60,removeExpiredRows, [tempMongoRows])
    t.start()
    

    
def isEmailValid(emailAddress):
    pattern = "^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$"
    result = re.findall(pattern, emailAddress)
    if (result):
        return True
    else:
        return False

def isPasswordValid(newPassword):
#The password policy is:            
#At least 14 chars                    
# Contains at least one digit                    
#Contains at least one lower alpha char and one upper alpha char                    
# Contains at least one char within a set of special chars (@#%$^ etc.)                    
# Does not contain space, tab, etc. 
#                   ^                 # start-of-string
#                    (?=.*[0-9])       # a digit must occur at least once
#                    (?=.*[a-z])       # a lower case letter must occur at least once
#                    (?=.*[A-Z])       # an upper case letter must occur at least once
#                    (?=.*[!@#$%^&+=])  # a special character must occur at least once
#                    .{12,}             # anything, at least 12 digits
#                    $                 # end-of-string
    if (main.debugRelaxedPasswords == True):
        # for debug relaxed password mode, we just want to accept all passwords.
        return True
    else:
        pattern = "((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$"
        result = re.findall(pattern, newPassword)
        if (result):
            return True
        else:
            return False


def checkAccountInputs(emailAddress, firstName,lastName,password, privilege):
    retVal = "OK"
    util.debugPrint("checkAccountInputs")
    if not isEmailValid(emailAddress):
        util.debugPrint("email invalid")
        retVal = "INVALEMAIL"           
    elif not isPasswordValid(password) :
        util.debugPrint("Password invalid")
        retVal = "INVALPASS"
    elif len(firstName) == 0:
        util.debugPrint("first name invalid - 0 characters")
        retVal = "INVALFNAME"             
    elif len(lastName) == 0:
        util.debugPrint("last name invalid - 0 characters")
        retVal = "INVALLNAME"
    elif privilege != "admin" and privilege != "user":
        retVal = "INVALPRIV"
    util.debugPrint(retVal)
    return retVal   

        
