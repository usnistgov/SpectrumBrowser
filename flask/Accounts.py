import flaskr as main
import re
import time
import util
import threading
from threading import Timer

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