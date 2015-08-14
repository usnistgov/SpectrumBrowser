# Set up various globals to prevent scanners from kicking in.

import os
import argparse
import sys
import json
import memcache
import util
from DbCollections import getPeerConfigDb
from DbCollections import getSysConfigDb
from DbCollections import getScrConfigDb
from Defines import UNKNOWN
from Defines import API_KEY
from Defines import HOST_NAME
from Defines import PUBLIC_PORT
from Defines import PROTOCOL
from Defines import IS_AUTHENTICATION_REQUIRED
from Defines import USE_LDAP
from Defines import ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS
from Defines import CHANGE_PASSWORD_INTERVAL_DAYS
from Defines import ACCOUNT_REQUEST_TIMEOUT_HOURS
from Defines import ACCOUNT_USER_ACKNOW_HOURS
from Defines import MY_SERVER_ID
from Defines import MY_SERVER_KEY
from Defines import SMTP_PORT
from Defines import SMTP_SERVER
from Defines import SMTP_EMAIL_ADDRESS
from Defines import STREAMING_SERVER_PORT
from Defines import OCCUPANCY_ALERT_PORT
from Defines import SOFT_STATE_REFRESH_INTERVAL
from Defines import USER_SESSION_TIMEOUT_MINUTES
from Defines import ADMIN_SESSION_TIMEOUT_MINUTES
from Defines import CERT
from Defines import MAP_WIDTH
from Defines import MAP_HEIGHT
from Defines import SPEC_WIDTH
from Defines import SPEC_HEIGHT
from Defines import CHART_WIDTH
from Defines import CHART_HEIGHT
from Defines import PRIV_KEY
from Defines import MONGO_DIR


mc = memcache.Client(['127.0.0.1:11211'], debug=0)

global configuration
configuration = None
if getSysConfigDb() != None:
    configuration = getSysConfigDb().find_one({})
    if mc.get("sysconfig") == None:
        mc.set("sysconfig", configuration)
    else:
        mc.replace("sysconfig", configuration)

def readConfig():
    global configuration
    configuration = mc.get("sysconfig")
    return configuration

def writeConfig(config):
    if mc.get("sysconfig") == None:
        mc.set("sysconfig", config)
    else:
        mc.replace("sysconfig",config)

def writeScrConfig(config):
    if mc.get("scrconfig") == None:
        mc.set("scrconfig", config)
    else:
        mc.replace("scrconfig", config)

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

def getSmtpEmail():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[SMTP_EMAIL_ADDRESS]

def getDefaultConfig():
    defaultConfig = { API_KEY: UNKNOWN, \
                    HOST_NAME: UNKNOWN, PUBLIC_PORT:8443, PROTOCOL:"https" , IS_AUTHENTICATION_REQUIRED: False, \
                    MY_SERVER_ID: UNKNOWN, MY_SERVER_KEY: UNKNOWN,  SMTP_PORT: 25, SMTP_SERVER: "localhost", \
                    SMTP_EMAIL_ADDRESS: UNKNOWN, \
                    STREAMING_SERVER_PORT: 9000, OCCUPANCY_ALERT_PORT:9001, SOFT_STATE_REFRESH_INTERVAL:30, \
                    USE_LDAP:False, ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS:5, \
                    CHANGE_PASSWORD_INTERVAL_DAYS:60, ACCOUNT_USER_ACKNOW_HOURS:2, \
                    USER_SESSION_TIMEOUT_MINUTES:30, \
                    ADMIN_SESSION_TIMEOUT_MINUTES:15, \
                    ACCOUNT_REQUEST_TIMEOUT_HOURS:48, \
                    CERT:"dummy.crt",
                    MONGO_DIR:"/spectrumdb"}
    return defaultConfig

def getDefaultScreenConfig():
    defaultScreenConfig = {MAP_WIDTH: 800, MAP_HEIGHT: 800, \
                           SPEC_WIDTH: 800, SPEC_HEIGHT: 400, \
                           CHART_WIDTH: 8, CHART_HEIGHT: 4}
    return defaultScreenConfig

def getScreenConfig():
    cfg = getScrConfigDb().find_one({})
    if cfg == None:
        return getDefaultScreenConfig()
    del cfg["_id"]
    return cfg

def isScrConfigured():
    cfg = getScrConfigDb().find_one()
    return cfg != None

def setScreenConfig(configuration):
    db = getScrConfigDb()
    oldConfig = db.find_one({})

    if oldConfig != None:
        db.remove(oldConfig)
    db.insert(configuration)
    reloadScrConfig()
    return True

def getStreamingServerPort():
    global configuration
    readConfig()
    if configuration == None:
        return -1
    if STREAMING_SERVER_PORT in configuration:
        return configuration[STREAMING_SERVER_PORT]
    else:
        return -1

def getMongoDir():
    global configuration
    readConfig()
    if configuration == None:
        return None
    return configuration[MONGO_DIR]

def getOccupancyAlertPort():
    global configuration
    if configuration == None:
        return -1
    if OCCUPANCY_ALERT_PORT in configuration:
        return configuration[OCCUPANCY_ALERT_PORT]
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

def getUseLDAP():
    global configuration
    readConfig()
    if configuration == None:
        return False
    return configuration[USE_LDAP]
def getNumFailedLoginAttempts():
    global configuration
    # typically 3
    readConfig()
    if configuration == None:
        return -1
    return configuration[ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS]

def getTimeUntilMustChangePasswordDays():
    global configuration
    # typically 60 days
    readConfig()
    if configuration == None:
        return -1
    return configuration[CHANGE_PASSWORD_INTERVAL_DAYS]

def getAccountRequestTimeoutHours():
    global configuration
    # typically 48 hours
    readConfig()
    if configuration == None:
        return -1
    return configuration[ACCOUNT_REQUEST_TIMEOUT_HOURS]

def getAccountUserAcknowHours():
    global configuration
    readConfig()
    # typically 2 hours
    if configuration == None:
        return -1
    return configuration[ACCOUNT_USER_ACKNOW_HOURS]

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
    peers = getPeerConfigDb().peers.find()
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

def getUserSessionTimeoutMinutes():
    global configuration
    readConfig()
    if configuration == None:
        return 30
    else:
        return configuration[USER_SESSION_TIMEOUT_MINUTES]

def getAdminSessionTimeoutMinutes():
    global configuration
    readConfig()
    if configuration == None:
        return 15
    else:
        return configuration[ADMIN_SESSION_TIMEOUT_MINUTES]

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
    return configuration[PROTOCOL] == "https"

def reloadConfig():
    global configuration
    if getSysConfigDb() != None:
        configuration = getSysConfigDb().find_one({})
        writeConfig(configuration)

def reloadScrConfig():
    global configuration
    if getScrConfigDb() != None:
        configuration = getScrConfigDb().find_one({})
        writeScrConfig(configuration)

def printSysConfig():
    for f in getSysConfigDb().find({}):
        del f["_id"]
        print json.dumps(f, indent=4)
        util.debugPrint("SysConfig = " + json.dumps(f, indent=4))

def verifySystemConfig(sysconfig):
    print(json.dumps(sysconfig, indent=4))
    if sysconfig[HOST_NAME] == UNKNOWN:
        return False, "Host name invalid"
    elif sysconfig[MY_SERVER_ID] == UNKNOWN:
        return False, "Server ID invalid"
    elif sysconfig[MY_SERVER_KEY] == UNKNOWN:
        return False, "Server Key invalid"
    elif (sysconfig[PROTOCOL] != "http" and sysconfig[PROTOCOL] != "https") :
        return False, "Invalid access protocol (should be HTTP or HTTPS)"
    elif (not os.path.exists(sysconfig[CERT])):
        return False, "Certificate File Not Found "
    else:
        return True,"OK"

def getAccessProtocol():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[PROTOCOL]

def addPeer(protocol, host, port):
    db = getPeerConfigDb()
    config = db.peers.find_one({"host":host, "port":port})
    if config != None:
        db.peers.remove({"host":host, "port":port})
    record = {"protocol":protocol, "host":host, "port":port}
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
    config = db.peers.find_one({"host":host, "port":port})
    if config != None:
        db.peers.remove({"host":host, "port":port})

def add_peer_key(peerId,peerKey):
    db = getPeerConfigDb()
    peerkey = db.peerkeys.find_one({"PeerId":peerId})
    if peerkey != None:
        db.peerkeys.remove({"PeerId":peerId})
    record = {"PeerId":peerId, "key":peerKey}
    db.peerkeys.insert(record)

def add_inbound_peers(peerKeys):
    db = getPeerConfigDb()
    for peerKey in peerKeys:
        peerkey = db.peerkeys.find_one({"PeerId":peerKey["PeerId"]})
        if peerkey != None:
            db.peerkeys.remove({"PeerId":peerKey["PeerId"]})
        db.peerkeys.insert(peerKey)

def addInboundPeer(peer):
    db = getPeerConfigDb()
    peerkey = db.peerkeys.find_one({"PeerId":peer["PeerId"]})
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
    db = getSysConfigDb()
    oldConfig = db.find_one({})

    if oldConfig != None:
        db.remove(oldConfig)
    db.insert(configuration)
    reloadConfig()
    return True

def parse_config_file(filename):
    import netifaces
    f = open(filename)
    configStr = f.read()
    config = eval(configStr)
    gws = netifaces.gateways()
    gw = gws['default'][netifaces.AF_INET]
    addrs = netifaces.ifaddresses(gw[1])
    MY_HOST_NAME = addrs[netifaces.AF_INET][0]['addr']
    config[HOST_NAME] = MY_HOST_NAME
    return config

def parse_local_config_file(filename):
    f = open(filename)
    configStr = f.read()
    config = eval(configStr)
    return config

def parse_peers_config(filename):
    f = open(filename)
    configStr = f.read()
    config = eval(configStr)
    return config

def printConfig():
    cfg = getSysConfigDb().find_one()
    if cfg == None:
        util.debugPrint("Configuration is cleared")
    else:
        del cfg["_id"]
    jsonStr = json.dumps(cfg, sort_keys=True, indent=4)
    util.debugPrint("Configuration: " + jsonStr)
    for peer in getPeerConfigDb().peers.find():
        del peer["_id"]
        jsonStr = json.dumps(peer, sort_keys=True, indent=4)
        util.debugPrint("Peer : " + jsonStr)
    for peerKey in getPeerConfigDb().peerkeys.find():
        del peerKey["_id"]
        jsonStr = json.dumps(peerKey, sort_keys=True, indent=4)
        util.debugPrint("PeerKey : " + jsonStr)

def getSystemConfig():
    cfg = getSysConfigDb().find_one()
    if cfg == None:
        return cfg
    # "PEERS":"Peers.gburg.txt",\
    # "PEER_KEYS":"PeerKeys.gburg.txt"
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

def getCertFile():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    return configuration[CERT]

def getKeyFile():
    global configuration
    readConfig()
    if configuration == None:
        return UNKNOWN
    dirname = os.path.dirname(os.path.realpath(getCertFile()))
    return dirname + "/privkey.pem"

def getGeneratedDataPath():
    protocol = getAccessProtocol()
    url = protocol + ":" + "//" + getHostName() + ":" + str(getPublicPort()) + "/spectrumbrowser/generated"
    return url

def isMailServerConfigured():
    cfg = getSysConfigDb().find_one()
    if SMTP_SERVER in cfg and cfg[SMTP_SERVER] != None and cfg[SMTP_SERVER] != UNKNOWN \
        and SMTP_PORT in cfg and cfg[SMTP_PORT] != 0 and \
        SMTP_EMAIL_ADDRESS in cfg and cfg[SMTP_EMAIL_ADDRESS] != None and cfg[SMTP_EMAIL_ADDRESS] != UNKNOWN:
        return True
    else:
        return False



# Self initialization scaffolding code.
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('action', default="init", help="init (default) addPeer or add_peer_key")
    parser.add_argument('-f', help='Cfg file')
    parser.add_argument('-host', help='peer host -- required')
    parser.add_argument('-port', help='peer port -- required')
    parser.add_argument('-protocol', help='peer protocol -- required')
    parser.add_argument("-peerid", help="peer ID")
    parser.add_argument("-peer_key", help="peer key")
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
            # TODO -- more checking needed here.
            parser.error("Please specify -host -port and -protocol")
            sys.exit()
        else:
            addPeer(host, port, protocol)
    elif action == 'inboundPeer':
        args = parser.parse_args()
        peerId = args.peerid
        peerKey = args.key
        if peerId == None or peerKey == None:
            parser.error("Please supply peerId and peerKey")
        add_peer_key(peerId, peerKey)
    elif action == "clear":
        delete_config()
    else:
        parser.error("Unknown option " + args.action)
    printConfig()
