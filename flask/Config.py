from pymongo import MongoClient
import os
import netifaces
import argparse
import sys
mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.sysconfig
configuration = db.configuration.find_one({})

def getApiKey() :
    return configuration["API_KEY"]

def getSmtpSender() :
    return configuration["SMTP_SENDER"]

def getSmtpServer():
    return configuration["SMTP_SERVER"]

def getSmtpPort():
    return configuration["SMTP_PORT"]

def getAdminEmailAddress():
    return configuration["ADMIN_EMAIL_ADDRESS"]

def getAdminPassword():
    return configuration["ADMIN_PASSWORD"]

def getStreamingSamplingIntervalSeconds():
    return configuration["STREAMING_SAMPLING_INTERVAL_SECONDS"]

def getStreamingCaptureSampleSize():
    return configuration["STREAMING_CAPTURE_SAMPLE_SIZE"]

def getStreamingFilter():
    return configuration["STREAMING_FILTER"]

def getStreamingServerPort():
    return configuration["STREAMING_SERVER_PORT"]

def isStreamingSocketEnabled():
    if "STREAMING_SERVER_PORT" in configuration:
        return True
    else:
        return False
def getStreamingSecondsPerFrame() :
    return configuration["STREAMING_SECONDS_PER_FRAME"]

def isAuthenticationRequired():
    return configuration["IS_AUTHENTICATION_REQUIRED"]

def getPeers():
    peers =  getPeerConfigDb().peers.find()
    retval = []
    for peer in peers:
        retval.append(peer)
    return retval

def getHostName() :
    return configuration["HOST_NAME"]

def getServerKey():
    return configuration["MY_SERVER_KEY"]

def getServerId():
    return configuration["MY_SERVER_ID"]

def isSecure():
    return configuration["IS_SECURE"]

def reload():
    configuration = db.configuration.find_one({})

def getDb():
    mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
    client = MongoClient(mongodb_host)
    return client

def getPeerConfigDb():
    return getDb().peerconfig

def getSysConfigDb():
    return getDb().sysconfig


def add_peer(protocol,host,port):
    db = getPeerConfigDb()
    config  = db.peers.find_one({"host":host,"port":port})
    if config != None:
        db.peers.remove({"host":host,"port":port})
    record =  {"protocol":protocol,"host":host,"port":port}
    db.peers.insert(record)
    
def add_peer_record(peerRecords):
    db = getPeerConfigDb()
    for peerRecord in peerRecords:
        config = db.peers.find_one({"host":peerRecord["host"], "port":peerRecord["port"]})
        if config != None:
            db.peers.remove({"host":peerRecord["host"], "port":peerRecord["port"]})
        db.peers.insert(peerRecord)


def add_peer_key(peerId,peerKey):
    db = getPeerConfigDb()
    peerkey  = db.peerkeys.find_one({"PeerId":peerId})
    if peerkey != None:
        db.peerkeys.remove({"PeerId":peerId})
    record = {"PeerId":peerId,"key":peerKey}
    db.peerkeys.insert(record)
    
def add_peer_keys(peerKeys):
    for peerKey in peerKeys:
        peerkey  = db.peerkeys.find_one({"PeerId":peerKey["PeerId"]})
        if peerkey != None:
            db.peerkeys.remove({"PeerId":peerKey["PeerId"]})
        record = {"PeerId":peerKey["PeerId"],"key":peerKey["key"]}
        db.peerkeys.insert(record)



def initialize(configuration):
    # A list of base URLS where this server will REGISTER
    # the sensors that it manages. This contains pairs of server
    # base URL and server key.
    db = getSysConfigDb()
    oldConfig = db.configuration.find_one({})

    if oldConfig != None:
        db.configuration.remove(oldConfig)

    db.configuration.insert(configuration)
    
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

# Self initialization scaffolding code.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('action',default="init",help="init (default) add_peer or add_peer_key")
    parser.add_argument('-f',help='Cfg file')
    parser.add_argument('-host',help='peer host -- required')
    parser.add_argument('-port', help='peer port -- required')
    parser.add_argument('-protocol',help = 'peer protocol -- required')
    parser.add_argument("-peerid",help="peer ID")
    parser.add_argument("-key",help="peer key")
    args = parser.parse_args()
    action = args.action
    if args.action == "init" or args.action == None:
        cfgFile = args.f
        for peer in getPeerConfigDb().peers.find():
            getPeerConfigDb().peers.remove(peer)
        for peerkey in getPeerConfigDb().peerkeys.find():
            getPeerConfigDb().peerkeys.remove(peerkey)
        for c in db.configuration.find():
            db.configuration.remove(c)
        if cfgFile == None:
            parser.error("Please specify cfg file")
        configuration = parse_config_file(cfgFile)
        initialize(configuration)
        if "PEERS" in configuration:
            peersFile = configuration["PEERS"]
            peerRecords = parse_peers_config(peersFile)
            add_peer_record(peerRecords)
        if "PEER_KEYS" in configuration:
            peerKeysFile = configuration["PEER_KEYS"]
            peerKeys = parse_peers_config(peerKeysFile)
            add_peer_keys(peerKeys)
    elif action == 'add_peer':
        host = args.host
        port = int(args.port)
        protocol = args.protocol
        if host == None or port == None or protocol == None:
            #TODO -- more checking needed here.
            parser.error("Please specify -host -port and -protocol")
            sys.exit()
        else:
            add_peer(host,port,protocol)
    elif action == 'add_peer_key':
        args = parser.parse_args()
        peerId = args.peerid
        peerKey = args.key
        if peerId == None or peerKey == None:
            parser.error("Please supply peerId and peerKey")
        add_peer_key(peerId,peerKey)
    else:
        parser.error("Unknown option "+args.action)
