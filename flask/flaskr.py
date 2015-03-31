from flask import Flask, request, Response,abort, make_response
from flask import jsonify
from flask import render_template
import random
import json
import os
import matplotlib as mpl
mpl.use('Agg')
import urlparse
import populate_db
import sys
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
from flask_sockets import Sockets
import traceback
import GetLocationInfo
import GetDailyMaxMinMeanStats
import util
import GeneratePowerVsTime
import GenerateSpectrum
import GenerateSpectrogram
import GetDataSummary
import GetOneDayStats
import GarbageCollect
import msgutils
import SensorDb
import Config
import DataStreaming
import time
from flask.ext.cors import CORS 
import DbCollections
from Defines import TIME_ZONE_KEY
from Defines import FFT_POWER
from Defines import SENSOR_KEY
from Defines import LAT
from Defines import LON
from Defines import ALT
from Defines import SENSOR_ID
from Defines import SWEPT_FREQUENCY
from Defines import UNKNOWN
from Defines import TEMP_ACCOUNT_TOKEN

from Defines import ADMIN
from Defines import USER
import DebugFlags
import AccountsResetPassword
import SessionLock
import subprocess
import os

UNIT_TEST_DIR= "./unit-tests"



global launchedFromMain

if not Config.isConfigured() :
    print "Please configure system using admin interface"

#sessions = {}
secureSessions = {}
gwtSymbolMap = {}

# move these to another module



launchedFromMain = False
app = Flask(__name__, static_url_path="")
cors = CORS(app)
sockets = Sockets(app)
random.seed()



#####################################################################################
#Note: This has to go here after the definition of some globals.
import AccountsCreateNewAccount
import AccountsChangePassword
import AccountsResetPassword
import AccountsManagement
import authentication
import GenerateZipFileForDownload
import DataStreaming
import PeerConnectionManager

flaskRoot = os.environ['SPECTRUM_BROWSER_HOME'] + "/flask/"
PeerConnectionManager.start()
AccountsCreateNewAccount.startAccountScanner()
AccountsResetPassword.startAccountsResetPasswordScanner()
SessionLock.startSessionExpiredSessionScanner()
SensorDb.startSensorDbScanner()

if not DebugFlags.isStandAloneStreamingServer():
    DataStreaming.startStreamingServer()
#SpectrumMonitor.startMonitoringServer()
#Config.printConfig()

##################################################################################

def load_symbol_map(symbolMapDir):
    files = [ symbolMapDir + f for f in os.listdir(symbolMapDir) if os.path.isfile(symbolMapDir + f) and os.path.splitext(f)[1] == ".symbolMap" ]
    if len(files) != 0:
        symbolMap = files[0]
        symbolMapFile = open(symbolMap)
        lines = symbolMapFile.readlines()
        for line in lines:
            if line[0] == "#":
                continue
            else:
                pieces = line.split(',')
                lineNo = pieces[-2]
                fileName = pieces[-3]
                symbol = pieces[0]
                gwtSymbolMap[symbol] = {"file":fileName, "line" : lineNo}

def loadGwtSymbolMap():
    symbolMapDir = util.getPath("static/WEB-INF/deploy/spectrumbrowser/symbolMaps/")
    load_symbol_map(symbolMapDir)
    symbolMapDir = util.getPath("static/WEB-INF/deploy/admin/symbolMaps/")
    load_symbol_map(symbolMapDir)

def decodeStackTrace (stackTrace):
    lines = stackTrace.split()
    for line in lines :
        pieces = line.split(":")
        if pieces[0] in gwtSymbolMap :
            print gwtSymbolMap.get(pieces[0])
            file = gwtSymbolMap.get(pieces[0])["file"]
            lineNo = gwtSymbolMap.get(pieces[0])["line"]
            util.debugPrint( file + " : " + lineNo + " : " + pieces[1])
            
# Note this is a nested function.
def testcase(original_function):
    def testcase_decorator(*args, **kwargs):
        try:
            if DebugFlags.getGenerateTestCaseFlag():
                p = urlparse.urlparse(request.url)
                urlpath = p.path
                pieces = urlpath.split("/")
                method = pieces[2]
                testFile = DebugFlags.getUnitTestFile()
                httpMethod = request.method
                response = original_function(*args, **kwargs)
                result = response.get_data()
                statusCode = response.status_code
                body = request.data
                testMap = {}
                testMap["statusCode"]=statusCode
                testMap["testedFunction"] = method
                testMap["httpRequestMethod"] = httpMethod
                if not Config.isSecure():
                    testMap["requestUrl"] = request.url
                else:
                    testMap["requestUrl"] = request.url.replace("http:","https:")
                if body != None:
                    testMap["requestBody"] = body
                testMap["expectedResponse"] = result
                toWrite = json.dumps(testMap,indent=4)
                if os.path.exists(testFile):
                    f = open(testFile,"a+")
                    f.write(",\n")
                else:
                    f = open(testFile,"w+")
                f.write(toWrite)
                f.write("\n")
                f.close()
                return response
            else:
                return  original_function(*args, **kwargs)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise   
    return testcase_decorator
    

######################################################################################

@app.route("/api/<path:path>",methods=["GET"])
@app.route("/generated/<path:path>", methods=["GET"])
@app.route("/myicons/<path:path>", methods=["GET"])
@app.route("/spectrumbrowser/<path:path>", methods=["GET"])
def getFile(path):
    util.debugPrint("getFile()")
    p = urlparse.urlparse(request.url)
    urlpath = p.path
    util.debugPrint(urlpath)
    util.debugPrint(urlpath[1:])
    if DebugFlags.generateTestCase:
        pieces = urlpath.split("/")
        testFile = UNIT_TEST_DIR+"/unit-test.json"
        if pieces[1] == "generated":
            testMap = {}
            testMap["statusCode"]= 200
            testMap["httpRequestMethod"] = "GET"
            testMap["requestUrl"] = request.url
            toWrite = json.dumps(testMap,indent=4)
            if os.path.exists(testFile):
                f = open(testFile,"a+")
                f.write(",\n")
            else:
                f = open(testFile,"w+")
            f.write(toWrite)
            f.close()
    return app.send_static_file(urlpath[1:])

# The admin clicks here (from link in an admin email address) when activating an account
# The email here is the users email, not the admin's email:
@app.route("/spectrumbrowser/authorizeAccount/<email>/<token>",methods=["GET"])
def authorizeAccount(email,token):
    """
    System admin can authorize an account (for accounts that do not end in .mil or .gov) which is currently stored in temp accounts.
    After the admin authorizes the account, the user will have to click on a link in their email to activate their account
    which also ensures that their email is valid.

    URL Path:
    - email: user's email for denying the account.
    - token: token in temp accounts, one for each email.

    """
    @testcase
    def authorizeAccountWorker(email, token):
        try:
            util.debugPrint("authorizeAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)    
            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc) 
            if AccountsCreateNewAccount.authorizeAccount(email.strip(), int(token),urlPrefix):
                return render_template('AccountTemplate.html', string1="The user account was authorized and the user was sent an email message to active their account.", string2="")
                #return app.send_static_file("account_authorized.html")
            else:
                return render_template('AccountTemplate.html', string1="There was an error processing your request. Check the server logs.", string2="")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return authorizeAccountWorker(email, token)
     
# The admin clicks here (from link in an admin email address) when denying an account
# The email here is the users email, not the admin's email:
@app.route("/spectrumbrowser/denyAccount/<email>/<token>",methods=["GET"])
def denyAccount(email, token):
    """
    System admin can deny an account (for accounts that do not end in .mil or .gov) which is currently stored in temp accounts.

    URL Path:
    -email: user's email for denying the account.
    - token: token in temp accounts, one for each email.
    """
    @testcase
    def denyAccountWorker(email, token):
        try:
            util.debugPrint("denyAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc) 
            if AccountsCreateNewAccount.denyAccount(email.strip(), int(token), urlPrefix):
    			return render_template('AccountTemplate.html', string1="User account was denied and the user was sent an email message to inform them of the denial.", string2="")
            else:
                return render_template('AccountTemplate.html', string1="There was an error processing your request. Check the server logs.", string2="")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return denyAccountWorker(email, token)
# The user clicks here (from link in an email address) when activating an account
# Look up the account to active based on email address and token - to make sure unique
@app.route("/spectrumbrowser/activateAccount/<email>/<token>",methods=["GET"])
def activateAccount(email, token):
    """
    Activate an account that is currently stored in temp accounts.

    URL Path:
    -email: user's email for activating account.
    - token: token in temp accounts, one for each email.
    """
    @testcase
    def activateAccountWorker(email, token):
        try:
            util.debugPrint("activateAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc) 
            if AccountsCreateNewAccount.activateAccount(email.strip(), int(token)):
                return render_template('AccountTemplate.html', string1="Your account was successfully created. You can log in here:", string2=urlPrefix)
            else:
                return render_template('AccountTemplate.html', string1="Sorry, there was an issue creating your account.", string2="Please contact your system administrator.")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return activateAccountWorker(email, token)
     
    
@app.route("/spectrumbrowser/requestNewAccount", methods=["POST"])
def requestNewAccount():
    """
    When a user requests a new account, if their email ends in .mil or .gov, we can create
    an account without an admin authorizing it and all we need to do is store the temp
    account and send the user an email to click on to activate the account.
    
    If their email does not end in .mil or .gov & no adminToken, we need to save the temp account,
    as "Waiting admin authorization" and send an email to the admin to authorize the account.
    If the admin authorizes the account creation, the temp account will change to 
    "Waiting User Activation" and the
    user will need to click on a link in their email to activate their account.
    Otherwise, the system will send the user a "we regret to inform you..." email that their account 
    was denied. 

    URL Path:

    URL Args:
        JSON data structure of account info.

    """
    @testcase
    def requestNewAccountWorker():
        try:
            util.debugPrint("requestNewAccount")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            
            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc)           
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsCreateNewAccount.requestNewAccount(accountData, urlPrefix))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return requestNewAccountWorker()

    

@app.route("/spectrumbrowser/changePassword", methods=["POST"])
def changePassword():
    """
    Change to a new password and email user.

    URL Path:

    URL Args (required):
    - JSON structure of change password data  
    """
    @testcase
    def changePasswordWorker():
        try:
            util.debugPrint("changePassword")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc)           
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsChangePassword.changePasswordEmailUser(accountData, urlPrefix))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace("Unexpected error:" + str(sys.exc_info()[0]))
            raise
    return changePasswordWorker()

# The user clicks here (from link in an email address) when resetting an account password
# Look up the password based on email address and token - to make sure unique
@app.route("/spectrumbrowser/resetPassword/<email>/<token>",methods=["GET"])
def resetPassword(email, token):
    """
    Store new password data and email user a url to click to reset their password.
    The email click ensures a valid user is resetting the password.

    URL Path:
    -email: user's email for resetting password.
    - token: token for resetting the password for the user 

    """
    @testcase
    def resetPasswordWorker(email, token):
        try:
            util.debugPrint("resetPassword")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc)    
            if AccountsResetPassword.activatePassword(email.strip(), int(token)):
                return render_template('AccountTemplate.html', string1="Your password was successfully reset. You can log in here:", string2=urlPrefix)
            else:
                return render_template('AccountTemplate.html', string1="Sorry, there was an issue resetting your account.", string2="Please contact your system administrator.")
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return resetPasswordWorker(email, token)

@app.route("/spectrumbrowser/requestNewPassword", methods=["POST"])
def requestNewPassword():
    """

    Send email to the user with a url link to reset their password to their newly specified value.

    URL Path:

    URL Args (required):
     - JSON structure of change password data  
    """
    @testcase
    def requestNewPasswordWorker():
        try:
            util.debugPrint("request new Password")
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)      

            p = urlparse.urlparse(request.url)
            urlPrefix = str(p.scheme) + "://" + str(p.netloc)           
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify(AccountsResetPassword.storePasswordAndEmailUser(accountData, urlPrefix)) 
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return requestNewPasswordWorker()


@app.route("/federated/peerSignIn/<peerServerId>/<peerKey>",methods=["POST"])
def peerSignIn(peerServerId, peerKey):
    """
    Handle authentication request from federated peer and send our location information.
    """
    try :
        if not Config.isConfigured():
            util.debugPrint("Please configure system")
            abort(500)
        util.debugPrint("peerSignIn " + peerServerId + "/" + peerKey)
        rc =  authentication.authenticatePeer(peerServerId,peerKey)
        # successfully authenticated? if so, return the location info for ALL
        # sensors.
        util.debugPrint("Status : " + str(rc))
        retval = {}
        if rc:
            requestStr = request.data
            if requestStr != None:
                remoteAddr = request.remote_addr
                jsonData = json.loads(requestStr)
                Config.getPeers()
                protocol = Config.getAccessProtocol()
                peerUrl = protocol+ "//" + jsonData["HostName"] + ":" + str(jsonData["PublicPort"])
                PeerConnectionManager.setPeerUrl(peerServerId,peerUrl)
                PeerConnectionManager.setPeerSystemAndLocationInfo(peerUrl,jsonData["locationInfo"])
            retval["Status"] = "OK"
            retval["HostName"] = Config.getHostName()
            retval["Port"] = Config.getPublicPort()
            if not Config.isAuthenticationRequired():
                locationInfo = GetLocationInfo.getLocationInfo()
                retval["locationInfo"] = locationInfo
            return jsonify(retval)
        else:
            retval["Status"] = "NOK"
            return jsonify(retval)
    except :
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise



@app.route("/", methods=["GET"])
@app.route("/spectrumbrowser", methods=["GET"])
def userEntryPoint():
    util.debugPrint("root()")
    return app.send_static_file("app.html")

@app.route("/admin", methods=["GET"])
def adminEntryPoint():
    util.debugPrint("admin")
    return app.send_static_file("admin.html")

@app.route("/admin/getUserAccounts/<sessionId>",methods=["POST"])
def getUserAccounts(sessionId):
    """
    get user accounts.
    
    URL Path:
    
        sessionId: session ID of the admin login session.
        
    """
    @testcase
    def getUserAccountsWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("getUserAccounts")
            userAccounts = AccountsManagement.getUserAccounts()
            retval = {"userAccounts":userAccounts, "status":"OK", "statusMessage":""}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getUserAccountsWorker(sessionId)

@app.route("/admin/deleteAccount/<emailAddress>/<sessionId>", methods=["POST"])
def deleteAccount(emailAddress, sessionId):
    """
    delete user account
    
        
    URL Path:
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none
    
        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    def deleteAccountWorker(emailAddress,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("deleteAccount")
            return jsonify(AccountsManagement.deleteAccount(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return deleteAccountWorker(emailAddress,sessionId)
    

@app.route("/admin/unlockAccount/<emailAddress>/<sessionId>", methods=["POST"])
def unlockAccount(emailAddress, sessionId):
    """
    unlock user account
    
        
    URL Path:
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none
    
        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def unlockAccountWorker(emailAddress, sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("unlockAccount")
            return jsonify(AccountsManagement.unlockAccount(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return unlockAccountWorker(emailAddress,sessionId)

@app.route("/admin/togglePrivilegeAccount/<emailAddress>/<sessionId>", methods=["POST"])
def togglePrivilegeAccount(emailAddress, sessionId):
    """
    delete user accounts
    
        
    URL Path:
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none
    
        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def togglePrivilegeAccountWorker(emailAddress,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("togglePrivilegeAccount")
            return jsonify(AccountsManagement.togglePrivilegeAccount(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return togglePrivilegeAccountWorker(emailAddress,sessionId)

@app.route("/admin/resetAccountExpiration/<emailAddress>/<sessionId>", methods=["POST"])
def resetAccountExpiration(emailAddress, sessionId):
    """
    delete user accounts
    
        
    URL Path:
    - emailAddress : The email address of the account to delete.
    - sessionId: session ID of the admin login session.

    URL Args (required):
    none
    
        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def resetAccountExpirationWorker(emailAddress,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("resetAccountExpiration")
            return jsonify(AccountsManagement.resetAccountExpiration(emailAddress))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return resetAccountExpirationWorker(emailAddress,sessionId)

@app.route("/admin/createAccount/<sessionId>", methods=["POST"])
def createAccount(sessionId):
    """
    create user account
    
    URL Path:
        sessionId : login session ID
 
     URL Args (required):       
        - JSON string of account info
        
        HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def createAccountWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("createAccount")
            requestStr = request.data
            accountData = json.loads(requestStr)
            return jsonify( AccountsManagement.createAccount(accountData))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return createAccountWorker(sessionId)



@app.route("/admin/authenticate/<privilege>/<userName>", methods=['POST'])
@app.route("/spectrumbrowser/authenticate/<privilege>/<userName>", methods=['POST'])
def authenticate(privilege, userName):
    """

    Authenticate the user given his username and password from the requested browser page or return
    an error if the user cannot be authenticated.

    URL Path:

    - browser page : Type of web page where the request came from (spectrumbrowser or admin).
    - userName : user login name.
    URL Args:

    - None

    Return codes:

    - 200 OK if authentication is OK
            On success, a JSON document with the following information is returned.
        - sessionId : The login session ID to be used for subsequent interactions
            with this service.
    - 403 Forbidden if authentication fails.

    """
    @testcase
    def authenticateWorker(privilege,userName):
        try:
            if not Config.isConfigured() and privilege == USER:
                util.debugPrint("Please configure system")
                abort(500)
            p = urlparse.urlparse(request.url)
            urlpath = p.path
            if not Config.isConfigured() and urlpath[0] == "spectrumbrowser" :
                util.debugPrint("attempt to access spectrumbrowser before configuration -- please configure")
                abort(500)
            userName = userName.strip()
            password = request.args.get("password", None)
            util.debugPrint( "flask authenticate " + userName + " " + str(password) + " " + privilege)
            if password == None:
                return util.formatError("password missing"),400
            else:
                return authentication.authenticateUser(privilege,userName,password)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return authenticateWorker(privilege,userName)
    
@app.route("/spectrumbrowser/isAuthenticationRequired",methods=['POST'])
def isAuthenticationRequired():
    @testcase
    def isAuthenticationRequiredWorker():
        """
        Return true if authentication is required.
        """
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if Config.isAuthenticationRequired():
                return jsonify({"AuthenticationRequired": True})
            else:
                return jsonify({"AuthenticationRequired": False, "SessionToken":authentication.generateGuestToken()})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return isAuthenticationRequiredWorker()



@app.route("/admin/logOut/<sessionId>", methods=['POST'])
@app.route("/spectrumbrowser/logOut/<sessionId>", methods=['POST'])
#@testcase
def logOut(sessionId):
    """
    Log out of an existing session.

    URL Path:

        sessionId : The session ID to log out.

    """
    @testcase
    def logOutWorker(sessionId):
        try:
            authentication.logOut(sessionId)
            return jsonify({"status":"OK"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return logOutWorker(sessionId)


@app.route("/admin/getSystemConfig/<sessionId>", methods=["POST"])
def getSystemConfig(sessionId):
    """
    get system configuration.
    
    URL Path:
    
        sessionId : Session ID of the login session.
        
    """
    @testcase
    def getSystemConfigWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            systemConfig = Config.getSystemConfig()
            if systemConfig == None:
                config = Config.getDefaultConfig()
                return jsonify(config)
            else:
                return jsonify(systemConfig)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getSystemConfigWorker(sessionId)
    
@app.route("/admin/getPeers/<sessionId>",methods=["POST"])
def getPeers(sessionId):
    """
    get outbound peers.
    
    URL Path:
    
        sessionId: session ID of the login session.
        
    """
    @testcase
    def getPeersWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            peers = Config.getPeers()
            retval = {"peers":peers}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getPeersWorker(sessionId)

@app.route("/admin/removePeer/<host>/<port>/<sessionId>", methods=["POST"])
def removePeer(host,port,sessionId):
    """
    remove outbound peer.
    
    URL Path:
        host: Host of peer to remove
        port: port or peer to remove
        sessionId : login session ID
    """
    @testcase
    def removePeerWorker(host,port,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            Config.removePeer(host,int(port))
            peers = Config.getPeers()
            retval = {"peers":peers}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return removePeerWorker(host,port,sessionId)

@app.route("/admin/addPeer/<host>/<port>/<protocol>/<sessionId>", methods=["POST"])
def addPeer(host,port,protocol,sessionId):
    """
    add an outbound peer
    
    URL Path:
        host : Host of peer to add.
        port : port of peer
        protocol : http or https
        sessionId : login session id.
    """
    @testcase
    def addPeerWorker(host,port,protocol,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            # TODO -- parameter checking.
            Config.addPeer(protocol,host,int(port))
            peers = Config.getPeers()
            retval = {"peers":peers}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return addPeerWorker(host,port,protocol,sessionId)

@app.route("/admin/getInboundPeers/<sessionId>",methods=["POST"])
def getInboundPeers(sessionId):
    """
    get a list of inbound peers.
    
    URL path:
    sessionID = session ID of the login
    
    URL Args: None
    
    Returns : JSON formatted string containing the inbound Peers accepted by this server.
    
    """
    @testcase
    def getInboundPeersWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            peerKeys = Config.getInboundPeers()
            retval = {"inboundPeers":peerKeys}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getInboundPeersWorker(sessionId)

@app.route("/admin/deleteInboundPeer/<peerId>/<sessionId>", methods=["POST"])
def deleteInboundPeer(peerId, sessionId):
    """
    Delete an inbound peer record.
    """
    @testcase
    def deleteInboundPeerWorker(peerId,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN) :
                abort(403)
            Config.deleteInboundPeer(peerId)
            peerKeys = Config.getInboundPeers()
            retval = {"inboundPeers":peerKeys}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return deleteInboundPeerWorker(peerId,sessionId)

@app.route("/admin/addInboundPeer/<sessionId>", methods=["POST"])
def addInboundPeer(sessionId):
    """
    Add an inbound peer.
    """
    @testcase
    def addInboundPeerWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN) :
                abort(403)
            requestStr = request.data
            peerConfig = json.loads(requestStr)
            util.debugPrint("peerConfig " + json.dumps(peerConfig, indent=4))
            Config.addInboundPeer(peerConfig)
            peers = Config.getInboundPeers()
            retval = {"inboundPeers":peers}
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return addInboundPeerWorker(sessionId)
    
@app.route("/admin/setSystemConfig/<sessionId>",methods=["POST"])
def setSystemConfig(sessionId):
    """
    set system configuration
    URL Path:
        sessionId the session Id of the login in session.
        
    URL Args: None
        
    Request Body:
        A JSON formatted string containing the system configuration.
    """
    @testcase
    def setSystemConfigWorker(sessionId):
        try:
            util.debugPrint("setSystemConfig : " + sessionId)
            if not authentication.checkSessionId(sessionId,ADMIN):
                abort(403)
            util.debugPrint("passed authentication")
            requestStr = request.data
            systemConfig = json.loads(requestStr)
            (statusCode,message) = Config.verifySystemConfig(systemConfig)
            if not statusCode:
                util.debugPrint("did not verify sys config")
                return jsonify({"Status":"NOK","ErrorMessage":message})
        
            util.debugPrint("setSystemConfig " + json.dumps(systemConfig,indent=4,))
            if Config.setSystemConfig(systemConfig):
                return jsonify({"Status":"OK"})
            else:
                return jsonify({"Status":"NOK","ErrorMessage":"Unknown"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return setSystemConfigWorker(sessionId)
    
@app.route("/admin/addSensor/<sessionId>",methods=["POST"])
def addSensor(sessionId):
    """
    Add a sensor to the system or return error if the sensor does not exist.
    URL Path:
        sessionId the session Id of the login in session.
        
    URL Args: None
        
    Request Body:
        A JSON formatted string containing the sensor configuration.
    
    """
    @testcase
    def addSensorWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system",500)
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found.",403)
            requestStr = request.data
            sensorConfig = json.loads(requestStr)
            return jsonify(SensorDb.addSensor(sensorConfig)) 
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return addSensorWorker(sessionId)

@app.route("/admin/toggleSensorStatus/<sensorId>/<sessionId>",methods=["POST"]) 
def toggleSensorStatus(sensorId,sessionId): 
    @testcase
    def toggleSensorStatusWorker(sensorId,sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system",500)
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found.",403)
            return jsonify(SensorDb.toggleSensorStatus(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return toggleSensorStatusWorker(sensorId,sessionId)
   
@app.route("/admin/purgeSensor/<sensorId>/<sessionId>",methods=["POST"])
def purgeSensor(sensorId,sessionId):
    @testcase
    def purgeSensorWorker(sensorId,sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system",500)
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found.",403)
            return jsonify(SensorDb.purgeSensor(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return purgeSensorWorker(sensorId,sessionId)

@app.route("/admin/updateSensor/<sessionId>",methods=["POST"])
def updateSensor(sessionId):
    @testcase
    def updateSensorWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system",500)
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found.",403)
            requestStr = request.data
            sensorConfig = json.loads(requestStr)
            return jsonify(SensorDb.updateSensor(sensorConfig))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return updateSensorWorker(sessionId)
        
        
@app.route("/admin/getSystemMessages/<sensorId>/<sessionId>",methods=["POST"])
def getSystemMessages(sensorId,sessionId):
    @testcase
    def getSystemMessagesWorker(sensorId,sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                return make_response("Please configure system",500)
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found.",403)
            return jsonify(GenerateZipFileForDownload.generateSysMessagesZipFileForDownload(sensorId, sessionId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getSystemMessagesWorker(sensorId,sessionId)
    
@app.route("/admin/getSensorInfo/<sessionId>",methods=["POST"])
def getSensorInfo(sessionId):
    @testcase
    def getSensorInfoWorker(sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found",403)
            response = SensorDb.getSensors()
            return jsonify(response)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getSensorInfoWorker(sessionId)

@app.route("/admin/recomputeOccupancies/<sensorId>/<sessionId>",methods=["POST"])
def recomputeOccupancies(sensorId,sessionId):
    @testcase
    def recomputeOccupanciesWorker(sensorId,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found",403)
            return jsonify(GetDataSummary.recomputeOccupancies(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return recomputeOccupanciesWorker(sensorId,sessionId)

@app.route("/admin/garbageCollect/<sensorId>/<sessionId>",methods=["POST"])
def garbageCollect(sensorId,sessionId):
    @testcase
    def garbageCollectWorker(sensorId,sessionId):
        try:
            if not authentication.checkSessionId(sessionId,ADMIN):
                return make_response("Session not found",403)
            return jsonify(GarbageCollect.runGarbageCollector(sensorId))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return garbageCollectWorker(sensorId,sessionId)
    

###################################################################################

@app.route("/spectrumbrowser/getLocationInfo/<sessionId>", methods=["POST"])
def getLocationInfo(sessionId):
    """

    Get the location and system messages for all sensors.

    URL Path:

    - sessionid : The session ID for the login session.

    URL Args:

    - None

    HTTP return codes:

        - 200 OK if the call completed successfully.
        On success this returns a JSON formatted document
        containing a list of all the System and Location messages
        in the database. Additional information is added to the
        location messages (i.e.  the supported frequency bands of
        the sensor). Sensitive information such as sensor Keys are
        removed from the returned document.  Please see the MSOD
        specification for documentation on the format of these JSON
        messages. This API is used to populate the top level view (the map)
        that summarizes the data. Shown below is an example interaction
        (consult the MSOD specification for details):

        Request:

        ::

           curl -X POST http://localhost:8000/spectrumbrowser/getLocationInfo/guest-123

        Returns the following jSON document:

        ::

            {
                "locationMessages": [
                    {
                    ALT: 143.5,
                    LAT: 39.134374999999999,
                    LON: -77.215337000000005,
                    "Mobility": "Stationary",
                    "SensorID": "ECR16W4XS",
                    "TimeZone": "America/New_York",
                    "Type": "Loc"Type,
                    "Ver": "1.0.9",
                    "sensorFreq": [ # An array of frequency bands supported (inferred
                                    # from the posted data messages)
                        "703967500:714047500",
                        "733960000:744040000",
                        "776967500:787047500",
                        "745960000:756040000"
                    ],
                    "t": 1404964924,
                    "tStartLocalTime": 1404950524,
                    }, ....
                ],
                "systemMessages": [
                {
                    "Antenna": {
                    "Model": "Unknown (whip)",
                    "Pol": "VL",
                    "VSWR": "NaN",
                    "XSD": "NaN",
                    "bwH": 360.0,
                    "bwV": "NaN",
                    "fHigh": "NaN",
                    "fLow": "NaN",
                    "gAnt": 2.0,
                    "lCable": 0.5,
                    "phi": 0.0,
                    "theta": "N/A"
                    }
                "COTSsensor": {
                    "Model": "Ettus USRP N210 SBX",
                    "fMax": 4400000000.0,
                    "fMin": 400000000.0,
                    "fn": 5.0,
                    "pMax": -10.0
                },
                Defines.CAL: "N/A",
                "Preselector": {
                    "enrND": "NaN",
                    "fHighPassBPF": "NaN",
                    "fHighStopBPF": "NaN",
                    "fLowPassBPF": "NaN",
                    "fLowStopBPF": "NaN",
                    "fnLNA": "NaN",
                    "gLNA": "NaN",
                    "pMaxLNA": "NaN"
                },
                "SensorID": "ECR16W4XS",
                "Type": "Sys",
                "Ver": "1.0.9",
                "t": 1404964924
                },....
            ]
            }

        - 403 Forbidden if the session ID is not found.

    """
    @testcase
    def getLocationInfoWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            peerSystemAndLocationInfo = PeerConnectionManager.getPeerSystemAndLocationInfo()
            retval=GetLocationInfo.getLocationInfo()
            retval["peers"] = peerSystemAndLocationInfo
            return jsonify(retval)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getLocationInfoWorker(sessionId)



@app.route("/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<startTime>/<dayCount>/<sys2detect>/<fmin>/<fmax>/<sessionId>", methods=["POST"])
def getDailyStatistics(sensorId, startTime, dayCount, sys2detect, fmin, fmax, sessionId):
    """

    Get the daily statistics for the given start time, frequency band and day count for a given sensor ID

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in the UTC time zone specified as a second offset from 1.1.1970:0:0:0 (UTC).
    - dayCount : The number days for which we want the statistics.
    - sessionId : The session ID of the login session.
    - fmin : min freq in MHz of the band of interest.
    - fmax : max freq in MHz of the band of interest.
    - sessionId: login session ID.

    URL args (optional):

    - subBandMinFreq : the min freq of the sub band of interest (contained within a band supported by the sensor).
    - subBandMaxFreq: the max freq of the sub band of interest (contained within a band supported by the sensor).

    If the URL args are not specified, the entire frequency band is used for computation.

    HTTP return codes:

    - 200 OK if the call returned without errors.
        Returns a JSON document containing the daily statistics for the queried sensor returned as an array of JSON
        records. Here is an example interaction (using UNIX curl to send the request):

    Request:

    ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDailyMaxMinMeanStats/ECR16W4XS/1404907200/5/745960000/756040000/guest-123

    Which returns the following response (annotated and abbreviated):

    ::

        {
        "channelCount": 56, # The number of channels
        "cutoff": -75.0,    # The cutoff for occupancy computations.
        "maxFreq": 756040000.0, # Max band freq. in Hz.
        "minFreq": 745960000.0, # Min band freq in Hz.
        "startDate": "2014-07-09 00:00:00 EDT", # The formatted time stamp.
        "tmin": 1404892800, # The universal time stamp.
        "values": {
            "0": {          # The hour offset from start time.
                "maxOccupancy": 0.05, # Max occupancy
                "meanOccupancy": 0.01,# Mean occupancy
                "minOccupancy": 0.01  # Min occupancy.
            }, ... # There is an array of such structures

        }
        }


    - 403 Forbidden if the session ID was not found.
    - 404 Not Found if the sensor data was not found.

    """
    @testcase
    def getDailyStatisticsWorker(sensorId, startTime, dayCount, sys2detect, fmin, fmax, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            util.debugPrint("getDailyMaxMinMeanStats : " + sensorId + " " + startTime + " " + dayCount)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            subBandMinFreq = int(request.args.get("subBandMinFreq", fmin))
            subBandMaxFreq = int(request.args.get("subBandMaxFreq", fmax))
            return GetDailyMaxMinMeanStats.getDailyMaxMinMeanStats(sensorId, startTime, dayCount,sys2detect, fmin, fmax,subBandMinFreq,subBandMaxFreq, sessionId)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise
    return getDailyStatisticsWorker(sensorId, startTime, dayCount, sys2detect, fmin, fmax, sessionId)


@app.route("/spectrumbrowser/getAcquisitionCount/<sensorId>/<sys2detect>/<fstart>/<fstop>/<tstart>/<daycount>/<sessionId>", methods=["POST"])
def getAcquisitionCount(sensorId, sys2detect, fstart, fstop, tstart, daycount, sessionId):

    """

    Get the acquistion count from a sensor given the start date and day count.

    URL Path:
        - sensorId : the sensor Id of interest
        - sys2detect : the system to detect
        - fstart : The start frequency
        - fstop : The end frequency
        - tstart : The acquistion start time
        - daycount : the number of days
    """
    @testcase
    def getAcquisitionCountWorker(sensorId, sys2detect, fstart, fstop, tstart, daycount, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
    
            return GetDataSummary.getAcquistionCount(sensorId,sys2detect,\
                    int(fstart),int(fstop),int(tstart),int(daycount))
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getAcquisitionCountWorker(sensorId, sys2detect, fstart, fstop, tstart, daycount, sessionId)

@app.route("/spectrumbrowser/getDataSummary/<sensorId>/<lat>/<lon>/<alt>/<sessionId>", methods=["POST"])
#@testcase
def getDataSummary(sensorId, lat, lon, alt, sessionId):
    """

    Get the sensor data summary  for the sensor given its ID, latitude and longitude.

    URL Path:

    - sensorId: Sensor ID of interest.
    - lat : Latitude
    - lon: Longitude
    - alt: Altitude
    - sessionId : Login session ID

    URL args (optional):

    - minFreq : Min band frequency of a band supported by the sensor.
            if this parameter is not specified then the min freq of the sensor is used.
    - maxFreq : Max band frequency of a band supported by the sensor.
            If this parameter is not specified, then the max freq of the sensor is used.
    - minTime : Universal start time (seconds) of the interval we are
            interested in. If this parameter is not specified, then the acquisition
            start time is used.
    - sys2detect: The system to detect
    - dayCount : The number of days for which we want the data. If this
            parameter is not specified, then the interval from minTime to the end of the
            available data is used.

    HTTP return codes:

    - 200 OK Success. Returns a JSON document with a summary of the available
    data in the time range and frequency band of interest.
    Here is an example Request using the unix curl command:

    ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDataSummary/Cotton1/40/-105.26/1676/guest-123

    Here is an example of the JSON document (annotated) returned in response :

    ::

        {
          "maxFreq": 2899500000, # max Freq the band of interest for the sensor (hz)
                                 #for period of interest
          "minFreq": 2700500000, # min freq of the band of interest for  sensor (hz)
                                 #for period of interest
          "maxOccupancy": 1.0, # max occupancy for the results of the query for period of interest
          "meanOccupancy": 0.074, # Mean Occupancy for the results of the query for period of interest
          "minOccupancy": 0.015, # Min occupancy for the results of the query for period of interest
          "measurementType": SWEPT_FREQUENCY,# Measurement type
          "readingsCount": 882, # acquistion count in interval of interest.
          "tAquisitionEnd": 1403899158, # Timestamp (universal time) for end acquisition
                                        # in interval of interest.
          "tAquisitionEndFormattedTimeStamp": "2014-06-27 09:59:18 MDT", #Formatted timestamp
                                                                         #for end acquistion
          "tAquistionStart": 1402948665, # universal timestamp for start of acquisition
          "tAquisitionStartFormattedTimeStamp": "2014-06-16 09:57:45 MDT",# Formatted TS for start of acq.
          "tEndReadings": 1403899158, # universal Timestamp for end of available readings.
          "tEndDayBoundary": 1403863200, # Day boundary of the end of available data (i.e 0:0:0 next day)
          "tEndReadingsLocalTime": 1403877558.0, # Local timestamp for end of readings.
          "tEndLocalTimeFormattedTimeStamp": "2014-06-27 09:59:18 MDT", # formatted TS for end of interval.
          "tStartReadings": 1402948665  # universal timestamp for start of available readings.
          "tStartDayBoundary": 1402912800.0, # Day boundary (0:0:0 next day) timestamp
                                             # for start of available readings.
          "tStartLocalTime": 1402927065, # Local timestamp for start of available readings
          "tStartLocalTimeFormattedTimeStamp": "2014-06-16 09:57:45 MDT", # formatted timestamp for the
                                                                          # start of interval of interest.
          "acquistionCount": 5103, # Available number of acquisitions for sensor
          "acquistionMaxOccupancy": 1.0, # Max occupancy over all the aquisitions
                                         #for sensor in band of interest.
          "acquistionMinOccupancy": 0.0, # Min occupancy over all aquisitions
                                         #for sensor in band of interest.
          "aquistionMeanOccupancy": 0.133 # Mean occupancy over all aquisitions
                                         #for sensor in band of interest.
          }

    - 403 Forbidden if the session ID is not recognized.
    - 404 Not Found if the location message for the sensor ID is not found.

    """
    @testcase
    def getDataSummaryWorker(sensorId, lat, lon, alt, sessionId):
        util.debugPrint("getDataSummary")
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                util.debugPrint("SessionId not found")
                abort(403)
            longitude = float(lon)
            latitude = float(lat)
            alt = float(alt)
            locationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:sensorId,\
                                                                             LON:longitude, LAT:latitude, ALT:alt})
            if locationMessage == None:
                util.debugPrint("Location Message not found")
                abort(404)
            return GetDataSummary.getDataSummary(sensorId,locationMessage)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getDataSummaryWorker(sensorId,lat,lon,alt,sessionId)



@app.route("/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def getOneDayStats(sensorId, startTime,sys2detect, minFreq, maxFreq, sessionId):
    """

    Get the statistics for a given sensor given a start time for a single day of data.
    The time is rounded to the start of the day boundary.
    Times for this API are specified as the time in the UTC time domain as a second offset from 1.1.1970:0:0:0
    (i.e. universal time; not local time)

    URL Path:

    - sensorId: Sensor ID for the sensor of interest.
    - startTime: start time within the day boundary of the acquisitions of interest.
    - minFreq: Minimum Frequency in MHz of the band of interest.
    - maxFreq: Maximum Frequency in MHz of the band of interest.
    - sys2detect: the system to detect.
    - sessionId: login Session ID.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK on success. Returns a JSON document with the path to the generated image of the spectrogram.
    - 403 Forbidden if the session ID was not found.
    - 404 Not found if the data was not found.

    """
    @testcase
    def getOneDayStatsWorker(sensorId, startTime,sys2detect, minFreq, maxFreq, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                util.debugPrint("SessionId not found")
                abort(403)
            minFreq = int(minFreq)
            maxFreq = int(maxFreq)
            return GetOneDayStats.getOneDayStats(sensorId,startTime,sys2detect,minFreq,maxFreq)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return getOneDayStatsWorker(sensorId, startTime,sys2detect, minFreq, maxFreq, sessionId)

@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId, startTime, sys2detect,minFreq, maxFreq, sessionId):
    """

    Generate the single acquisiton spectrogram image for FFT-Power readings. The
    spectrogram is used by the GUI to put up an image of the spectrogram.
    This API also returns the occupancy array for the generated image.
    An image for the spectrogram is generated by the server and a path
    to that image is returned.  Times for this API are specified as the
    time in the UTC time domain (universal time not local time) as a second offset from
    1.1.1970:0:0:0 UTC time.

    URL Path:

        - sensorId is the sensor ID of interest.
        - startTime - the acquisition  time stamp  for the data message for FFT power.
        - sys2detect - the system to detect
        - minFreq - The minimum frequency of the frequency band of interest.
        - maxFreq - The maximum frequency of the frequency band of interest.
        - sessionId - Login session Id.

    HTTP Return codes:

       - 200 OK On Success this returns a JSON document containing the following information.
            - "spectrogram": File resource containing the generated spectrogram.
            - "cbar": path to the colorbar for the spectrogram.
            - "maxPower": Max power for the spectrogram
            - "minPower": Min power for the spectrogram.
            - "cutoff": Power cutoff for occupancy.
            - "noiseFloor" : Noise floor.
            - "maxFreq": max frequency for the spectrogram.
            - "minFreq": minFrequency for the spectrogram.
            - "minTime": min time for the spectrogram.
            - "timeDelta": Time delta for the spectrogram window.
            - "prevAcquisition" : Time of the previous acquistion (or -1 if no acquistion exists).
            - "nextAcquisition" : Time of the next acquistion (or -1 if no acquistion exists).
            - "formattedDate" : Formatted date for the aquisition.
            - "image_width": Image width of generated image (pixels).
            - "image_height": Image height of generated image (pixels).
            - "timeArray" : Time array for occupancy returned as offsets from the start time of the acquistion.
            - "occpancy" : Occupancy occupancy for each spectrum of the spectrogram. This is returned as a one dimensional array.
            Each occupancy point in the array corresponds to the time offset recorded in the time array.
       - 403 Forbidden if the session ID is not recognized.
       - 404 Not Found if the message for the given time is not found.

    """
    @testcase
    def generateSingleAcquisitionSpectrogramWorker(sensorId, startTime, sys2detect,minFreq, maxFreq, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            startTimeInt = int(startTime)
            minfreq = int(minFreq)
            maxfreq = int(maxFreq)
            query = { SENSOR_ID: sensorId}
            msg = DbCollections.getDataMessages(sensorId).find_one(query)
            if msg == None:
                util.debugPrint("Sensor ID not found " + sensorId)
                abort(404)
            if msg["mType"] == FFT_POWER:
                query = { SENSOR_ID: sensorId, "t": startTimeInt, "freqRange": msgutils.freqRange(sys2detect,minfreq, maxfreq)}
                util.debugPrint(query)
                msg = DbCollections.getDataMessages(sensorId).find_one(query)
                if msg == None:
                    errorStr = "Data message not found for " + startTime
                    util.debugPrint(errorStr)
                    response = make_response(util.formatError(errorStr), 404)
                    return response
                result = GenerateSpectrogram.generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg, sessionId)
                if result == None:
                    errorStr = "Illegal Request"
                    response = make_response(util.formatError(errorStr), 400)
                    return response
                else:
                    return result
            else :
                util.debugPrint("Only FFT-Power type messages supported")
                errorStr = "Illegal Request"
                response = make_response(util.formatError(errorStr), 400)
                return response
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return generateSingleAcquisitionSpectrogramWorker(sensorId, startTime, sys2detect,minFreq, maxFreq, sessionId)
    

@app.route("/spectrumbrowser/generateSingleDaySpectrogramAndOccupancy/<sensorId>/<startTime>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleDaySpectrogram(sensorId, startTime, sys2detect, minFreq, maxFreq, sessionId):
    """

    Generate a single day spectrogram for Swept Frequency measurements as an image on the server.

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in UTC as a second offset from 1.1.1970:0:0:0 in the UTC time zone.
    - sys2detect : The system to detect.
    - minFreq: the min freq of the band of interest.
    - maxFreq: the max freq of the band of interest.
    - sessionId: The login session ID.

    URL Args:

    - subBandMinFreq : Sub band minimum frequency (should be contained in a frequency band supported by the sensor).
    - subBandMaxFreq : Sub band maximum frequency (should be contained in a frequency band supported by the sensor).

    HTTP Return Codes:

    - 403 Forbidden if the session ID is not found.
    - 200 OK if success. Returns a JSON document with a path to the generated spectrogram (which can be later used to access the image).

    """
    @testcase
    def generateSingleDaySpectrogramWorker(sensorId, startTime, sys2detect, minFreq, maxFreq, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            startTimeInt = int(startTime)
            minfreq = int(minFreq)
            maxfreq = int(maxFreq)
            print request
            subBandMinFreq = int(request.args.get("subBandMinFreq", minFreq))
            subBandMaxFreq = int(request.args.get("subBandMaxFreq", maxFreq))
            query = { SENSOR_ID: sensorId}
            msg = DbCollections.getDataMessages(sensorId).find_one(query)
            if msg == None:
                util.debugPrint("Sensor ID not found " + sensorId)
                abort(404)
                query = { SENSOR_ID: sensorId, "t":{"$gte" : startTimeInt}, "freqRange":msgutils.freqRange(sys2detect,minfreq, maxfreq)}
                util.debugPrint(query)
                msg = DbCollections.getDataMessages(sensorId).find_one(query)
                if msg == None:
                    errorStr = "Data message not found for " + startTime
                    util.debugPrint(errorStr)
                    return make_response(util.formatError(errorStr), 404)
            if msg["mType"] == SWEPT_FREQUENCY :
                return GenerateSpectrogram.generateSingleDaySpectrogramAndOccupancyForSweptFrequency\
                        (msg, sessionId, startTimeInt,sys2detect,minfreq, maxfreq, subBandMinFreq, subBandMaxFreq)
            else:
                errorStr = "Illegal message type"
                util.debugPrint(errorStr)
                return make_response(util.formatError(errorStr), 400)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return generateSingleDaySpectrogramWorker(sensorId, startTime, sys2detect, minFreq, maxFreq, sessionId)



@app.route("/spectrumbrowser/generateSpectrum/<sensorId>/<start>/<timeOffset>/<sessionId>", methods=["POST"])
#@testcase
def generateSpectrum(sensorId, start, timeOffset, sessionId):
    """

    Generate the spectrum image for a given start time and time offset from that start time.

    URL Path:

    - sensorId: Sensor ID of interest.
    - start: start time in the UTC time zone as an offset from 1.1.1970:0:0:0 UTC.
    - timeOffset: time offset from the start time in seconds.
    - sessionId: The session ID of the login session.

    URL Args: None

    HTTP return codes:
    - 403 Forbidden if the session ID is not recognized.
    - 200 OK if the request was successfully processed.
      Returns a JSON document with a URI to the generated image.

    """
    @testcase
    def generateSpectrumWorker(sensorId, start, timeOffset, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            startTime = int(start)
            # get the type of the measurement.
            msg = DbCollections.getDataMessages(sensorId).find_one({SENSOR_ID:sensorId})
            if msg["mType"] == FFT_POWER:
                msg = DbCollections.getDataMessages(sensorId).find_one({SENSOR_ID:sensorId, "t":startTime})
                if msg == None:
                    errorStr = "dataMessage not found "
                    util.debugPrint(errorStr)
                    abort(404)
                milisecOffset = int(timeOffset)
                return GenerateSpectrum.generateSpectrumForFFTPower(msg, milisecOffset, sessionId)
            else :
                secondOffset = int(timeOffset)
                time = secondOffset + startTime
                util.debugPrint("time " + str(time))
                msg = DbCollections.getDataMessages(sensorId).find_one({SENSOR_ID:sensorId, "t":{"$gte": time}})
                minFreq = int(request.args.get("subBandMinFrequency", msg["mPar"]["fStart"]))
                maxFreq = int(request.args.get("subBandMaxFrequency", msg["mPar"]["fStop"]))
                if msg == None:
                    errorStr = "dataMessage not found "
                    util.debugPrint(errorStr)
                    abort(404)
                return GenerateSpectrum.generateSpectrumForSweptFrequency(msg, sessionId, minFreq, maxFreq)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return generateSpectrumWorker(sensorId, start, timeOffset, sessionId)


@app.route("/spectrumbrowser/generateZipFileFileForDownload/<sensorId>/<startTime>/<days>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
#@testcase
def generateZipFileForDownload(sensorId, startTime, days,sys2detect, minFreq, maxFreq, sessionId):
    """

    Generate a Zip file file for download.

    URL Path:

    - sensorId : The sensor ID of interest.
    - startTime : Start time as a second offset from 1.1.1970:0:0:0 UTC in the UTC time Zone.
    - sys2detect : The system to detect.
    - minFreq : Min freq of the band of interest.
    - maxFreq : Max Freq of the band of interest.
    - sessionId : Login session ID.

    URL Args:

    - None.

    HTTP Return Codes:

    - 200 OK successful execution. A JSON document containing a path to the generated Zip file is returned.
    - 403 Forbidden if the sessionId is invalid.
    - 404 Not found if the requested data was not found.

    """
    @testcase
    def generateZipFileForDownloadWorker(sensorId, startTime, days,sys2detect, minFreq, maxFreq, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            return GenerateZipFileForDownload.generateZipFileForDownload(sensorId, startTime, days,sys2detect, minFreq, maxFreq, sessionId)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return generateZipFileForDownloadWorker(sensorId, startTime, days,sys2detect, minFreq, maxFreq, sessionId)


@app.route("/spectrumbrowser/emailDumpUrlToUser/<emailAddress>/<sessionId>", methods=["POST"])
def emailDumpUrlToUser(emailAddress, sessionId):
    """

    Send email to the given user when his requested dump file becomes available.

    URL Path:

    - emailAddress : The email address of the user.
    - sessionId : the login session Id of the user.

    URL Args (required):

    - urlPrefix : The url prefix that the web browser uses to access the data later (after the zip has been generated).
    - uri : The path used to access the zip file (previously returned from GenerateZipFileForDownload).

    HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    @testcase
    def emailDumpUrlToUserWorker(emailAddress, sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            uri = request.args.get("uri", None)
            util.debugPrint(uri)
            if  uri == None :
                abort(400)
            url = Config.getGeneratedDataPath() + "/" + uri
            return GenerateZipFileForDownload.emailDumpUrlToUser(emailAddress, url, uri)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise

    return emailDumpUrlToUserWorker(emailAddress, sessionId)


@app.route("/spectrumbrowser/checkForDumpAvailability/<sessionId>", methods=["POST"])
def checkForDumpAvailability(sessionId):
    """

    Check for availability of a previously generated dump file.

    URL Path:

    - sessionId: The session ID of the login session.

    URL Args (required):

    - uri : A URI pointing to the generated file to check for.

    HTTP Return Codes:

    - 200 OK if success
      Returns a json document {status: OK} file exists.
      Returns a json document {status:NOT_FOUND} if the file does not exist.
    - 400 Bad request. If the URL args are not present.
    - 403 Forbidden if the sessionId is invalid.

    """
    @testcase
    def checkForDumpAvailabilityWorker(sessionId):
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            uri = request.args.get("uri", None)
            util.debugPrint(uri)
            if  uri == None :
                util.debugPrint("URI not specified.")
                abort(400)
            if  GenerateZipFileForDownload.checkForDumpAvailability(uri):
                return jsonify({"status":"OK"})
            else:
                return jsonify({"status":"NOT_FOUND"})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return checkForDumpAvailabilityWorker(sessionId)



@app.route("/spectrumbrowser/generatePowerVsTime/<sensorId>/<startTime>/<freq>/<sessionId>", methods=["POST"])
def generatePowerVsTime(sensorId, startTime, freq, sessionId):
    """

    URL Path:

    - sensorId : the sensor ID of interest.
    - startTime: The start time of the aquisition.
    - freq : The frequency of interest.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK. Returns a JSON document containing the path to the generated image.
    - 404 Not found. If the aquisition was not found.

    """
    @testcase
    def generatePowerVsTimeWorker(sensorId, startTime, freq, sessionId):
    
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            msg = DbCollections.getDataMessages(sensorId).find_one({SENSOR_ID:sensorId})
            if msg == None:
                util.debugPrint("Message not found")
                abort(404)
            if msg["mType"] == FFT_POWER:
                msg = DbCollections.getDataMessages(sensorId).find_one({SENSOR_ID:sensorId, "t":int(startTime)})
                if msg == None:
                    errorMessage = "Message not found"
                    util.debugPrint(errorMessage)
                    abort(404)
                freqHz = int(freq)
                return GeneratePowerVsTime.generatePowerVsTimeForFFTPower(msg, freqHz, sessionId)
            else:
                msg = DbCollections.getDataMessages(sensorId).find_one({SENSOR_ID:sensorId, "t": {"$gt":int(startTime)}})
                if msg == None:
                    errorMessage = "Message not found"
                    util.debugPrint(errorMessage)
                    abort(404)
                freqHz = int(freq)
                return GeneratePowerVsTime.generatePowerVsTimeForSweptFrequency(msg, freqHz, sessionId)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise
    return generatePowerVsTimeWorker(sensorId, startTime, freq, sessionId)


@app.route("/spectrumbrowser/getLastAcquisitionTime/<sensorId>/<sys2detect>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def getLastAcquisitionTime(sensorId,sys2detect,minFreq,maxFreq,sessionId):
    @testcase
    def getAcquisitionTimeWorker(sensorId,sys2detect,minFreq,maxFreq,sessionId):
        """
        get the timestamp of the last acquisition
    
    
        """
        try:
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            timeStamp = msgutils.getLastAcquisitonTimeStamp(sensorId,sys2detect,minFreq,maxFreq)
            return jsonify({"aquisitionTimeStamp": timeStamp})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise
    return getAcquisitionTimeWorker(sensorId,sys2detect,minFreq,maxFreq,sessionId)



@app.route("/spectrumbrowser/getLastSensorAcquisitionTimeStamp/<sensorId>/<sessionId>", methods=["POST"])
def getLastSensorAcquisitionTime(sensorId,sessionId):
    @testcase
    def getLastSensorAcquisitionTimeWorker(sensorId,sessionId):
        try: 
            if not Config.isConfigured():
                util.debugPrint("Please configure system")
                abort(500)
            if not authentication.checkSessionId(sessionId,USER):
                abort(403)
            timeStamp = msgutils.getLastSensorAcquisitionTimeStamp(sensorId)
            return jsonify({"aquisitionTimeStamp": timeStamp})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise
    return getLastSensorAcquisitionTimeWorker(sensorId,sessionId)





@app.route("/spectrumdb/upload", methods=["POST"])
def upload() :
    """

    Upload sensor data to the database. The format is as follows:

        lengthOfDataMessageHeader<CRLF>DataMessageHeader Data

    Note that the data should immediately follow the DataMessage header (no space or CRLF).

    URL Path:

    - None

    URL Parameters:

    - None.

    Return Codes:

    - 200 OK if the data was successfully put into the MSOD database.
    - 403 Forbidden if the sensor key is not recognized.

    """
    try:
        msg = request.data
        util.debugPrint(msg)
        sensorId = msg[SENSOR_ID]
        key = msg[SENSOR_KEY]
        if not authentication.authenticateSensor(sensorId,key):
            abort(403)
        populate_db.put_message(msg)
        return "OK"
    except:
        util.logStackTrace(sys.exc_info())
        traceback.print_exc()
        raise

#==============================================================================================

@app.route("/sensordata/getStreamingPort/<sensorId>", methods=["POST"])
def getStreamingPort(sensorId):
    """
    Get a list of port that sensor can use to stream data using TCP.
    """
    @testcase
    def getStreamingPortWorker(sensorId):
        try:
            util.debugPrint("getStreamingPort : " + sensorId )
          
            return DataStreaming.getSocketServerPort(sensorId)
        except:
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise
    return getStreamingPortWorker(sensorId)
    
@app.route("/sensordata/getMonitoringPort/<sensorId>",methods=["POST"])
def getMonitoringPort(sensorId):
    """
    get port to the spectrum monitor to register for alerts.
    """
    @testcase
    def getMonitoringPortWorker(sensorId):
        try:
            util.debugPrint("getSpectrumMonitorPort")
            return DataStreaming.getSpectrumMonitoringPort(sensorId)
        except:
            util.logStackTrace(sys.exc_info())
            traceback.print_exc()
            raise
    return getMonitoringPortWorker(sensorId)

    
@sockets.route("/sensordata", methods=["POST", "GET"])
def getSensorData(ws):
    util.debugPrint("getSensorData")
    try:
        DataStreaming.getSensorData(ws)
    except:
        util.logStackTrace( sys.exc_info())
        traceback.print_exc()
        raise


#===============================================================================
# @sockets.route("/spectrumdb/stream", methods=["POST"])
# def datastream(ws):
#     DataStreaming.dataStream(ws)
#===============================================================================


@app.route("/log", methods=["POST"])
def log():
    if DebugFlags.debug:
        data = request.data
        jsonValue = json.loads(data)
        message = jsonValue["message"]
        exceptionInfo = jsonValue["ExceptionInfo"]
        if len(exceptionInfo) != 0 :
            util.errorPrint( "Client Log Message : " + message)
            util.errorPrint("Client Exception Info:")
            for i in range(0, len(exceptionInfo)):
                util.errorPrint( "Exception Message:")
                exceptionMessage = exceptionInfo[i]["ExceptionMessage"]
                util.errorPrint("Client Stack Trace :")
                stackTrace = exceptionInfo[i]["StackTrace"]
                util.errorPrint(exceptionMessage)
                decodeStackTrace(stackTrace)
        else:
            util.debugPrint( "Client Log Message : " + message)

    return "OK"

#=====================================================================
# For debugging.
#=====================================================================
@app.route("/getDebugFlags",methods=["POST"])
def getDebugFlags():
    retval = {}
    #debug = True
    retval["debug"] = DebugFlags.getDebugFlag()
    retval["disableSessionIdCheck"] = DebugFlags.getDisableSessionIdCheckFlag()
    retval["generateTestCase"] = DebugFlags.getGenerateTestCaseFlag()
    retval["debugRelaxedPasswords"] = DebugFlags.getDebugRelaxedPasswordsFlag()
    retval["disableAuthentication"] = DebugFlags.getDisableAuthenticationFlag()
    return jsonify(retval)

# @app.route("/spectrumbrowser/login", methods=["POST"])
# def login() :
#    sessionId = random.randint(0,1000)
#    returnVal = {}
#    returnVal["status"] = "OK"
#    returnVal["sessionId"] = sessionId
#    secureSessions[request.remote_addr] = sessionId
#    return JSONEncoder().encode(returnVal)


if __name__ == '__main__':
    launchedFromMain = True
    loadGwtSymbolMap()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['CORS_HEADERS'] = 'Content-Type'
    # app.run('0.0.0.0',port=8000,debug="True")
    app.debug = True
    if Config.isConfigured():
        server = pywsgi.WSGIServer(('0.0.0.0', 8000), app, handler_class=WebSocketHandler)
    else:
        server = pywsgi.WSGIServer(('localhost', 8000), app, handler_class=WebSocketHandler)
    server.serve_forever()
