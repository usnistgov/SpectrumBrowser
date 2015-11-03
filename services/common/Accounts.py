import re
import time
from threading import Timer
import AccountLock
import DebugFlags
from Defines import EXPIRE_TIME
from Defines import USER
from Defines import ADMIN
import util
import hashlib
from Defines import STATUS
from Defines import STATUS_MESSAGE

def packageReturn(retval):
    retvalMap = {}
    retvalMap[STATUS] = retval[0]
    retvalMap[STATUS_MESSAGE] = retval[1]
    return retvalMap

def computeMD5hash(password):
    m = hashlib.md5(password).hexdigest()
    return m

def removeExpiredRows(tempMongoRows):
    import sys
    import traceback
    try:
        AccountLock.acquire()
        # remove stale requests
        for tempMongoRow in tempMongoRows.find() :
            currentTime = time.time()
            expireTime = tempMongoRow[EXPIRE_TIME]
            if currentTime > expireTime:
               tempMongoRows.remove({"_id":tempMongoRow["_id"]})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
        AccountLock.release()

    t = Timer(60, removeExpiredRows, [tempMongoRows])
    t.start()
    

    
def isEmailValid(emailAddress):
    pattern = "^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$"
    result = re.findall(pattern, emailAddress)
    if (result):
        return True
    else:
        return False

def isPasswordValid(newPassword):
# The password policy is:            
# At least 14 chars                    
# Contains at least one digit                    
# Contains at least one lower alpha char and one upper alpha char                    
# Contains at least one char within a set of special chars (@#%$^ etc.)                    
# Does not contain space, tab, etc. 
#                   ^                 # start-of-string
#                    (?=.*[0-9])       # a digit must occur at least once
#                    (?=.*[a-z])       # a lower case letter must occur at least once
#                    (?=.*[A-Z])       # an upper case letter must occur at least once
#                    (?=.*[!@#$%^&+=])  # a special character must occur at least once
#                    .{12,}             # anything, at least 12 digits
#                    $                 # end-of-string
    if (DebugFlags.debugRelaxedPasswords):
        # for debug relaxed password mode, we just want to accept all passwords.
        return ["OK", ""]
    else:
        pattern = "((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$"
        result = re.search(pattern, newPassword)
        if result == None:
            return ["INVALPASS", "Please enter a password with 1) at least 12 characters, 2) a digit, 3) an upper case letter, 4) a lower case letter, and 5) a special character(!@#$%^&+=)."]
        else:
            return ["OK", ""]

        
def checkAccountInputs(emailAddress, firstName, lastName, password, privilege):
    util.debugPrint("checkAccountInputs")
    retVal = ["OK", ""]
    if not isEmailValid(emailAddress):
        util.debugPrint("email invalid")
        retVal = ["INVALEMAIL", "Please enter a valid email address."]           
    else:
        retVal = isPasswordValid(password)
        if retVal[0] <> "OK" :
            util.debugPrint("Password invalid")
        elif len(firstName) < 1:
            util.debugPrint("first name invalid - 0 characters")
            retVal = ["INVALFNAME", "Your first name must contain > 0 non-white space characters."]            
        elif len(lastName) < 1:
            util.debugPrint("last name invalid - 0 characters")
            retVal = ["INVALLNAME", "Your last name must contain > 0 non-white space characters."]
        elif privilege != ADMIN and privilege != USER:
            retVal = ["INVALPRIV", "You must enter a privilge of 'admin' or 'user'."]
    util.debugPrint(retVal)
    return retVal   

        
