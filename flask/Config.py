from pymongo import MongoClient
import os
import netifaces
import argparse
import sys
import json
from json import dumps

mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
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
    if configuration == None:
        return "UNKNOWN"
    return configuration["API_KEY"]

def getSmtpServer():
    if configuration == None:
        return "UNKNOWN"
    return configuration["SMTP_SERVER"]

def getSmtpPort():
    if configuration == None:
        return 0
    return configuration["SMTP_PORT"]

def getAdminEmailAddress():
    if configuration == None:
        return "unknown@nist.gov"
    return configuration["ADMIN_EMAIL_ADDRESS"]

def getAdminPassword():
    if configuration == None:
        return "admin"
    return configuration["ADMIN_PASSWORD"]

def getStreamingSamplingIntervalSeconds():
    if configuration == None:
        return -1
    return configuration["STREAMING_SAMPLING_INTERVAL_SECONDS"]

def getStreamingCaptureSampleSizeSeconds():
    if configuration == None:
        return -1
    return configuration["STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS"]

def getStreamingFilter():
    if configuration == None:
        return "UNKNOWN"
    return configuration["STREAMING_FILTER"]

def getStreamingServerPort():
    if configuration == None:
        return -1
    if "STREAMING_SERVER_PORT" in configuration:
        return configuration["STREAMING_SERVER_PORT"]
    else:
        return -1

def isStreamingSocketEnabled():
    if configuration != None and "STREAMING_SERVER_PORT" in configuration \
        and configuration["STREAMING_SERVER_PORT"] != -1:
        return True
    else:
        return False
    
def getStreamingSecondsPerFrame() :
    if configuration == None:
        return -1
    return configuration["STREAMING_SECONDS_PER_FRAME"]

def isAuthenticationRequired():
    if configuration == None:
        return False
    return configuration["IS_AUTHENTICATION_REQUIRED"]

def getSoftStateRefreshInterval():
    if configuration == None:
        return 30
    else:
        return configuration["SOFT_STATE_REFRESH_INTERVAL"]

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
    if configuration == None:
        return "UNKNOWN"
    return configuration["HOST_NAME"]

def getPublicPort():
    if configuration == None:
        return 8000
    else:
        return configuration["PUBLIC_PORT"]
    

def getServerKey():
    if configuration == None:
        return "UNKNOWN"
    return configuration["MY_SERVER_KEY"]

def getServerId():
    if configuration == None:
        return "UNKNOWN"
    return configuration["MY_SERVER_ID"]

def isSecure():
    if configuration == None:
        return "UNKNOWN"
    return configuration["IS_SECURE"]

def reloadConfig():
    if getSysConfigDb() != None:
        global configuration
        configuration = getSysConfigDb().find_one({})


def verifySystemConfig(sysconfig):
    unknown = "UNKNOWN"
    if sysconfig["HOST_NAME"] == unknown or sysconfig["MY_SERVER_ID"] == unknown \
       or sysconfig["MY_SERVER_KEY"] == unknown :
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
    # A list of base URLS where this server will REGISTER
    # the sensors that it manages. This contains pairs of server
    # base URL and server key.
    #TODO - verify correct password.
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
        return
    del cfg["_id"]
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
    cfg = getSysConfigDb().find_one()
    if cfg == None:
        return None
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
    if "SMTP_SERVER" in cfg and cfg["SMTP_SERVER"] != None and \
        cfg["SMTP_SERVER"] != "UNKNOWN" and "SMTP_PORT" in cfg and cfg["SMTP_PORT"] != 0 :
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
