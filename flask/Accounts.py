import re
import time
from threading import Timer
import AccountLock
import DebugFlags
import DbCollections

def removeExpiredRows(tempMongoRows):
    import sys
    import traceback
    try:
        AccountLock.acquire()
        # remove stale requests
        for tempMongoRow in tempMongoRows.find() :
            currentTime = time.time()
            expireTime = tempMongoRow["expireTime"]
            if currentTime  > expireTime:
               tempMongoRows.remove({"_id":tempMongoRow["_id"]})
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
    finally:
        AccountLock.release()

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
    if (DebugFlags.debugRelaxedPasswords == True):
        # for debug relaxed password mode, we just want to accept all passwords.
        return True
    else:
        pattern = "((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$"
        result = re.findall(pattern, newPassword)
        if (result):
            return True
        else:
            return False
        
def getAdminAccount():
    accounts = DbCollections.getAccounts()
    account = accounts.find_one({"privilege": "admin"})
    return account

def delAdminAccount():
    accounts = DbCollections.getAccounts().find({"privilege":"admin"})
    DbCollections.getAccounts().remove(accounts)

      

        
