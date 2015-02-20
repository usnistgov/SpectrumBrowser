# Set up various globals to prevent scanners from kicking in.

from pymongo import MongoClient
import os
import netifaces
import argparse
import sys
import json
from json import dumps
import memcache
import DbCollections
import Accounts
from Defines import ADMIN_EMAIL_ADDRESS 
from Defines import UNKNOWN 
from Defines import ADMIN_PASSWORD
from Defines import API_KEY
from Defines import HOST_NAME 
from Defines import PUBLIC_PORT
from Defines import PROTOCOL
from Defines import IS_AUTHENTICATION_REQUIRED 
from Defines import MY_SERVER_ID 
from Defines import MY_SERVER_KEY 
from Defines import SMTP_PORT 
from Defines import SMTP_SERVER 
from Defines import ADMIN_USER_FIRST_NAME 
from Defines import ADMIN_USER_LAST_NAME 
from Defines import STREAMING_SERVER_PORT 
from Defines import SOFT_STATE_REFRESH_INTERVAL 

mc = memcache.Client(['127.0.0.1:11211'], debug=0)
mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
global configuration
configuration = None
if client.sysconfig.configuration != None:
    configuration = client.sysconfig.configuration.find_one({})
    if mc.get("sysconfig") == None:
        mc.set("sysconfig",configuration)
    else:
        mc.replace("sysconfig",configuration)
        
admindb = client.admindb


def readConfig():
    global configuration
    configuration = mc.get("sysconfig")
    return configuration
    
def writeConfig(config):
    if mc.get("sysconfig") == None:
        mc.set("sysconfig",config)
    else:
        mc.replace("sysconfig",config)
    

def deleteAdminAccount():
    accounts = DbCollections.getAccounts()
    adminAccounts = accounts.find(({"privilege":"admin"}))
    for account in adminAccounts:
        accounts.remove(account)
        
def deleteAccounts():
    DbCollections.getAccounts().drop()
        
def resetAdminPassword(password):
    accounts = DbCollections.getAccounts()
    adminAccount = accounts.find_one(({"privilege":"admin"}))
    if adminAccount != None:
        adminAccount["password"] = password
        accounts.update({"emailAddress":adminAccount["emailAddress"]},{"$set":adminAccount},upsert=False) 

def getDb():
    db = client.sysconfig
    return db

def getPeerConfigDb():
    return getDb().peerconfig

def getSysConfigDb():
    return getDb().configuration

def getApiKey() :
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[API_KEY]

def getSmtpServer():
    global configuration
    if configuration == None:
        return UNKNOWN
    return configuration[SMTP_SERVER]

def getSmtpPort():
    global configuration
    readConfig()
    if configuration == None:
        return 0
    return configuration[SMTP_PORT]

def getDefaultAdminEmailAddress():
    return "admin@nist.gov"
    
    
def getDefaultAdminPassword():
    return "admin"

def getDefaultConfig():
    defaultConfig = { ADMIN_EMAIL_ADDRESS: UNKNOWN, ADMIN_PASSWORD: UNKNOWN, API_KEY: UNKNOWN, \
                    HOST_NAME: UNKNOWN, PUBLIC_PORT:8000, PROTOCOL:"https" , IS_AUTHENTICATION_REQUIRED: False, \
                    MY_SERVER_ID: UNKNOWN, MY_SERVER_KEY: UNKNOWN,  SMTP_PORT: 0, SMTP_SERVER: UNKNOWN, \
                    ADMIN_USER_FIRST_NAME:UNKNOWN, ADMIN_USER_LAST_NAME:UNKNOWN,\
                    STREAMING_SERVER_PORT: 9000, SOFT_STATE_REFRESH_INTERVAL:30}
    return defaultConfig



def getStreamingServerPort():
    global configuration
    readConfig()
    if configuration == None:
        return -1
    if STREAMING_SERVER_PORT in configuration:
        return configuration[STREAMING_SERVER_PORT]
    else:
        return -1

def isStreamingSocketEnabled():
    global configuration
    readConfig()
    if configuration != None and STREAMING_SERVER_PORT in configuration \
        and configuration[STREAMING_SERVER_PORT] != -1:
        return True
    else:
        return False
    

def isAuthenticationRequired():
    global configuration
    readConfig()
    if configuration == None:
        return False
    return configuration[IS_AUTHENTICATION_REQUIRED]

def getSoftStateRefreshInterval():
    global configuration
    readConfig()
    if configuration == None:
        return 30
    else:
        return configuration[SOFT_STATE_REFRESH_INTERVAL]

def getPeers():
    if getPeerConfigDb().peers == None:
        return []
    peers =  getPeerConfigDb().peers.find()
    retval = []
    if peers != None:
        for peer in peers:
            del peer["_id"]
            retval.append(peer)
    return retval

def getHostName() :
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[HOST_NAME]

def getPublicPort():
    global configuration
    readConfig()
    if configuration == None:
        return 8000
    else:
        return configuration[PUBLIC_PORT]
    

def getServerKey():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[MY_SERVER_KEY]

def getServerId():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[MY_SERVER_ID]

def isSecure():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration["IS_SECURE"]

def reloadConfig():
    global configuration
    if getSysConfigDb() != None:
        configuration = getSysConfigDb().find_one({})
        writeConfig(configuration)
        
def printSysConfig():
    for f in getSysConfigDb().find({}):
        del f["_id"]
        print json.dumps(f,indent=4)


def verifySystemConfig(sysconfig):
    print(json.dumps(sysconfig,indent=4))
    if sysconfig[HOST_NAME] == UNKNOWN:
        return False, "Host name invalid"
    elif sysconfig[MY_SERVER_ID] == UNKNOWN:
        return False, "Server ID invalid"
    elif sysconfig[MY_SERVER_KEY] == UNKNOWN:
        return False,"Server Key invalid"
    elif not Accounts.isPasswordValid(sysconfig[ADMIN_PASSWORD]) :
        return False,"Invalid Admin password"
    elif (sysconfig[PROTOCOL] != "http" and sysconfig[PROTOCOL] != "https") :
        return False,"Invalid access protocol (should be HTTP or HTTPS)"
    else:
        return True,"OK"
    
def getAccessProtocol():
    global configuration
    return configuration[PROTOCOL]
    
    
def getSensorConfigExpiryTimeHours():
    #TODO -- put this in configuration
    return 24


def addPeer(protocol,host,port):
    db = getPeerConfigDb()
    config  = db.peers.find_one({"host":host,"port":port})
    if config != None:
        db.peers.remove({"host":host,"port":port})
    record =  {"protocol":protocol,"host":host,"port":port}
    db.peers.insert(record)
    reloadConfig()
    
def add_peer_record(peerRecords):
    db = getPeerConfigDb()
    for peerRecord in peerRecords:
        config = db.peers.find_one({"host":peerRecord["host"], "port":peerRecord["port"]})
        if config != None:
            db.peers.remove({"host":peerRecord["host"], "port":peerRecord["port"]})
        db.peers.insert(peerRecord)
        
def removePeer(host,port):
    db = getPeerConfigDb()
    config = db.peers.find_one({"host":host,"port":port})
    if config != None:
        db.peers.remove({"host":host,"port":port})


def add_peer_key(peerId,peerKey):
    db = getPeerConfigDb()
    peerkey  = db.peerkeys.find_one({"PeerId":peerId})
    if peerkey != None:
        db.peerkeys.remove({"PeerId":peerId})
    record = {"PeerId":peerId,"key":peerKey}
    db.peerkeys.insert(record)
    
def add_inbound_peers(peerKeys):
    db = getPeerConfigDb()
    for peerKey in peerKeys:
        peerkey  = db.peerkeys.find_one({"PeerId":peerKey["PeerId"]})
        if peerkey != None:
            db.peerkeys.remove({"PeerId":peerKey["PeerId"]})
        db.peerkeys.insert(peerKey)
        
def addInboundPeer(peer):
    db = getPeerConfigDb()
    peerkey  = db.peerkeys.find_one({"PeerId":peer["PeerId"]})
    if peerkey != None:
        db.peerkeys.remove({"PeerId":peer["PeerId"]})
    db.peerkeys.insert(peer)

def findInboundPeer(peerId):
    db = getPeerConfigDb()
    return db.peerkeys.find_one({"PeerId":peerId})

def getInboundPeers():
    db = getPeerConfigDb()
    peerKeys = db.peerkeys.find()
    retval = []
    for cur in peerKeys:
        del cur["_id"]
        retval.append(cur)
    return retval

def deleteInboundPeer(peerId):
    db = getPeerConfigDb()
    db.peerkeys.remove({"PeerId":peerId})
    

def setSystemConfig(configuration):
    global _AccountsCreateNewAccountScannerStarted
    _AccountsCreateNewAccountScannerStarted = True
    global _AccountsResetPasswordScanner
    _AccountsResetPasswordScanner = True
    global connectionMaintainer
    connectionMaintainer = True
    global AuthenticationRemoveExpiredRowsScanner
    AuthenticationRemoveExpiredRowsScanner = True
    import AccountsCreateNewAccount
    db = getSysConfigDb()
    oldConfig = db.find_one({})

    if oldConfig != None:
        db.remove(oldConfig)

    adminFirstName = configuration[ADMIN_USER_FIRST_NAME]
    adminLastName = configuration[ADMIN_USER_LAST_NAME]
    adminPassword = configuration[ADMIN_PASSWORD]
    adminEmailAddress = configuration[ADMIN_EMAIL_ADDRESS]
    AccountsCreateNewAccount.removeAccount(adminEmailAddress)
    AccountsCreateNewAccount.createAdminAccount(adminEmailAddress, adminFirstName, adminLastName, adminPassword)
    del configuration[ADMIN_USER_FIRST_NAME]
    del configuration[ADMIN_USER_LAST_NAME]
    del configuration[ADMIN_PASSWORD]
    del configuration[ADMIN_EMAIL_ADDRESS]
    db.insert(configuration)

    reloadConfig()
    return True
    
def parse_config_file(filename):
    f = open(filename)
    configStr = f.read()
    config = eval(configStr)
    gws = netifaces.gateways()
    gw = gws['default'][netifaces.AF_INET]
    addrs = netifaces.ifaddresses(gw[1])
    MY_HOST_NAME = addrs[netifaces.AF_INET][0]['addr']
    config[HOST_NAME] = MY_HOST_NAME
    return config

def parse_peers_config(filename):
    f = open(filename)
    configStr = f.read()
    config = eval(configStr)
    return config

def printConfig():
    cfg = getSysConfigDb().find_one()
    if cfg == None:
        print "Configuration is cleared"
    else:
        del cfg["_id"]
        print cfg
    jsonStr = json.dumps(cfg,sort_keys=True,indent=4)
    print "Configuration: " , jsonStr
    for peer in getPeerConfigDb().peers.find():
        del peer["_id"]
        jsonStr = json.dumps(peer,sort_keys=True,indent=4)
        print "Peer : " , jsonStr
    for peerKey in getPeerConfigDb().peerkeys.find():
        del peerKey["_id"]
        jsonStr = json.dumps(peerKey,sort_keys=True,indent=4)
        print "PeerKey : ",jsonStr
    for account in DbCollections.getAccounts().find():
        del account["_id"]
        print account
        
def getSystemConfig():
    import Accounts
    cfg = getSysConfigDb().find_one()
    if cfg == None:
        return None
    if "PEERS" in cfg:
        del cfg["PEERS"]
    if "PEER_KEYS" in cfg:
        del cfg["PEER_KEYS"]
    del cfg["_id"]
    # Populate the admin account information.
    adminAccount = Accounts.getAdminAccount()
    del adminAccount["_id"]
    print json.dumps(adminAccount, indent=4)
    cfg[ADMIN_USER_FIRST_NAME] = adminAccount["firstName"]
    cfg[ADMIN_USER_LAST_NAME] = adminAccount["lastName"]
    cfg[ADMIN_PASSWORD] = adminAccount["password"]
    cfg[ADMIN_EMAIL_ADDRESS] = adminAccount["emailAddress"]
    return cfg

def isConfigured():
    cfg = getSysConfigDb().find_one()
    return cfg != None

def delete_config():
    for peer in getPeerConfigDb().peers.find():
        getPeerConfigDb().peers.remove(peer)
    for peerkey in getPeerConfigDb().peerkeys.find():
        getPeerConfigDb().peerkeys.remove(peerkey)
    for c in getSysConfigDb().find():
        getSysConfigDb().remove(c)
    deleteAccounts()

def reset_admin_password(adminPassword):
    resetAdminPassword(adminPassword)
    
def getGeneratedDataPath():
    protocol = getAccessProtocol()
    url = protocol + ":" + "//" + getHostName() +  ":" + str(getPublicPort()) + "/generated"
    return url

def isMailServerConfigured():
    cfg = getSysConfigDb().find_one()
    if SMTP_SERVER in cfg and cfg[SMTP_SERVER] != None and \
        cfg[SMTP_SERVER] != UNKNOWN and SMTP_PORT in cfg and cfg[SMTP_PORT] != 0 :
        return True
    else:
        return False


# Self initialization scaffolding code.
if __name__ == "__main__":
   
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('action',default="init",help="init (default) addPeer or add_peer_key")
    parser.add_argument('-f',help='Cfg file')
    parser.add_argument('-host',help='peer host -- required')
    parser.add_argument('-port', help='peer port -- required')
    parser.add_argument('-protocol',help = 'peer protocol -- required')
    parser.add_argument("-peerid",help="peer ID")
    parser.add_argument("-peer_key",help="peer key")
    parser.add_argument("-password", help="new admin password")
    args = parser.parse_args()
    action = args.action
    if args.action == "init" or args.action == None:
        cfgFile = args.f
        if cfgFile == None:
            parser.error("Please specify cfg file")
        delete_config()
        for peer in getPeerConfigDb().peers.find():
            getPeerConfigDb().peers.remove(peer)
        for peerkey in getPeerConfigDb().peerkeys.find():
            getPeerConfigDb().peerkeys.remove(peerkey)
        for c in getSysConfigDb().find():
            getSysConfigDb().remove(c)
       
        configuration = parse_config_file(cfgFile)
        setSystemConfig(configuration)
        if "PEERS" in configuration:
            peersFile = configuration["PEERS"]
            peerRecords = parse_peers_config(peersFile)
            add_peer_record(peerRecords)
        if "PEER_KEYS" in configuration:
            peerKeysFile = configuration["PEER_KEYS"]
            peerKeys = parse_peers_config(peerKeysFile)
            add_inbound_peers(peerKeys)
    elif action == 'outboundPeer':
        host = args.host
        port = int(args.port)
        protocol = args.protocol
        if host == None or port == None or protocol == None:
            #TODO -- more checking needed here.
            parser.error("Please specify -host -port and -protocol")
            sys.exit()
        else:
            addPeer(host,port,protocol)
    elif action == 'inboundPeer':
        args = parser.parse_args()
        peerId = args.peerid
        peerKey = args.key
        if peerId == None or peerKey == None:
            parser.error("Please supply peerId and peerKey")
        add_peer_key(peerId,peerKey)
    elif action == "clear":
        delete_config()
    elif action == "resetAdminPassword":
        newPass = args.password
        if newPass == None:
            parser.error("Please supply new password")
        reset_admin_password(newPass)
    else:
        parser.error("Unknown option "+args.action)
    printConfig()
