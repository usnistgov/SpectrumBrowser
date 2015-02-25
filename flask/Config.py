# Set up various globals to prevent scanners from kicking in.

from pymongo import MongoClient
import os
import netifaces
import argparse
import sys
import json
from json import dumps


mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
global configuration
configuration = None
if client.sysconfig.configuration != None:
    configuration = client.sysconfig.configuration.find_one({})


def getDb():
    db = client.sysconfig
    return db

def getPeerConfigDb():
    return getDb().peerconfig

def getSysConfigDb():
    return getDb().configuration

def getApiKey() :
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["API_KEY"]

def getHostName() :
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["HOST_NAME"]

def getPublicPort():
    global configuration
    if configuration == None:
        return 8000
    else:
        return configuration["PUBLIC_PORT"]

def getServerId():
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["MY_SERVER_ID"]


def getServerKey():
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["MY_SERVER_KEY"]


def getProtocol():
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["PROTOCOL"] 

def isSecure():
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["PROTOCOL"] == "https"


def getSoftStateRefreshInterval():
    global configuration
    if configuration == None:
        return 30
    else:
        return configuration["SOFT_STATE_REFRESH_INTERVAL"]

def getSmtpServer():
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["SMTP_SERVER"]

def getSmtpPort():
    global configuration

    if configuration == None:
        return 0
    return configuration["SMTP_PORT"]

def getSmtpEmail():
    global configuration

    if configuration == None:
        return 0
    return configuration["SMTP_EMAIL_ADDRESS"]


def getStreamingSamplingIntervalSeconds():
    global configuration

    if configuration == None:
        return -1
    return configuration["STREAMING_SAMPLING_INTERVAL_SECONDS"]

def getStreamingCaptureSampleSizeSeconds():
    global configuration

    if configuration == None:
        return -1
    return configuration["STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS"]

def getStreamingSecondsPerFrame() :
    global configuration
    if configuration == None:
        return -1
    return configuration["STREAMING_SECONDS_PER_FRAME"]

def getStreamingFilter():
    global configuration
    if configuration == None:
        return "UNKNOWN"
    return configuration["STREAMING_FILTER"]

def getStreamingServerPort():
    global configuration
    if configuration == None:
        return -1
    if "STREAMING_SERVER_PORT" in configuration:
        return configuration["STREAMING_SERVER_PORT"]
    else:
        return -1

def isStreamingSocketEnabled():
    global configuration
    if configuration != None and "STREAMING_SERVER_PORT" in configuration \
        and configuration["STREAMING_SERVER_PORT"] != -1:
        return True
    else:
        return False
    


def isAuthenticationRequired():
    global configuration
    if configuration == None:
        return False
    return configuration["IS_AUTHENTICATION_REQUIRED"]

def getUseLDAP():
    global configuration
    if configuration == None:
        return False
    return configuration["USE_LDAP"]

def getTimeUntilMustChangePasswordSeconds():
    global configuration
    # typically 60 days
    if configuration == None:
        return -1
    return configuration["CHANGE_PASSWORD_INTERVAL_SECONDS"]

def getAccountRequestTimeoutSeconds():
    global configuration
    # typically 48 hours
    if configuration == None:
        return -1
    return configuration["ACCOUNT_REQUEST_TIMEOUT_SECONDS"]

def getAccountUserEmailAckSeconds():
    global configuration
    # typically 2 hours
    if configuration == None:
        return -1
    return configuration["ACCOUNT_USER_EMAIL_ACK_SECONDS"]



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
    


def reloadConfig():
    if getSysConfigDb() != None:
        global configuration
        configuration = getSysConfigDb().find_one({})


def verifySystemConfig(sysconfig):
    import Accounts
    unknown = "UNKNOWN"
    print(json.dumps(sysconfig,indent=4))
    if sysconfig["HOST_NAME"] == unknown or sysconfig["MY_SERVER_ID"] == unknown \
       or sysconfig["MY_SERVER_KEY"] == unknown  \
       or (sysconfig["PROTOCOL"] != "http" and sysconfig["PROTOCOL"] != "https") :
        return False
    else:
        return True


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
    global AccountsCreateNewAccountScannerStarted
    AccountsCreateNewAccountScannerStarted = True
    global AccountsResetPasswordScanner
    AccountsResetPasswordScanner = True
    global connectionMaintainer
    connectionMaintainer = True
    global AuthenticationRemoveExpiredRowsScanner
    AuthenticationRemoveExpiredRowsScanner = True
    db = getSysConfigDb()
    oldConfig = db.find_one({})

    if oldConfig != None:
        db.remove(oldConfig)
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
    config["HOST_NAME"] = MY_HOST_NAME
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

def getSystemConfig():
    import Accounts
    cfg = getSysConfigDb().find_one()
    if cfg == None:
        config = { "API_KEY":"UNKNOWN", "HOST_NAME":"UNKNOWN", "PUBLIC_PORT":8000, \
            "MY_SERVER_ID": "UNKNOWN", "MY_SERVER_KEY": "UNKNOWN", "PROTOCOL":"http", \
            "SOFT_STATE_REFRESH_INTERVAL":30, \
            "SMTP_SERVER":"localhost", "SMTP_PORT":25, "SMTP_EMAIL_ADDRESS": "UNKNOWN",  \
            "STREAMING_SAMPLING_INTERVAL_SECONDS":15*60, "STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS":10, \
            "STREAMING_SECONDS_PER_FRAME":0.05, "STREAMING_FILTER": "MAX_HOLD", "STREAMING_SERVER_PORT":9000, \
            "IS_AUTHENTICATION_REQUIRED":False, "USE_LDAP":False, \
            "ACCOUNT_USER_EMAIL_ACK_SECONDS":2*60*60, \
            "CHANGE_PASSWORD_INTERVAL_SECONDS":60*24*60*60, "ACCOUNT_REQUEST_TIMEOUT_SECONDS":48*60*60}
        return config
    #"PEERS":"Peers.gburg.txt",\
    #"PEER_KEYS":"PeerKeys.gburg.txt"
    if "PEERS" in cfg:
        del cfg["PEERS"]
    if "PEER_KEYS" in cfg:
        del cfg["PEER_KEYS"]
    del cfg["_id"]
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



def isMailServerConfigured():
    cfg = getSysConfigDb().find_one()
    if "SMTP_SERVER" in cfg and cfg["SMTP_SERVER"] != None and cfg["SMTP_SERVER"] != "UNKNOWN" \
        and "SMTP_PORT" in cfg and cfg["SMTP_PORT"] != 0 and \
        "SMTP_EMAIL_ADDRESS" in cfg and cfg["SMTP_EMAIL_ADDRESS"] != None and cfg["SMTP_EMAIL_ADDRESS"] != "UNKNOWN":
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
    args = parser.parse_args()
    action = args.action
    if args.action == "init" or args.action == None:
        cfgFile = args.f
        for peer in getPeerConfigDb().peers.find():
            getPeerConfigDb().peers.remove(peer)
        for peerkey in getPeerConfigDb().peerkeys.find():
            getPeerConfigDb().peerkeys.remove(peerkey)
        for c in getSysConfigDb().find():
            getSysConfigDb().remove(c)
        if cfgFile == None:
            parser.error("Please specify cfg file")
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
    else:
        parser.error("Unknown option "+args.action)
    printConfig()
