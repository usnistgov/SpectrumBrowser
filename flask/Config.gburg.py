from pymongo import MongoClient
import os
import netifaces
import argparse
import sys

# This is a placeholder. After first system install, we need a page that
# Expects these things to be entered before the system becomes operational.

API_KEY= "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU"
SMTP_SERVER="smtp.nist.gov"
SMTP_PORT = 25
SMTP_SENDER = "mranga@nist.gov"
ADMIN_EMAIL_ADDRESS = "mranga@nist.gov"
ADMIN_PASSWORD = "12345"
# Time between captures.
STREAMING_SAMPLING_INTERVAL_SECONDS = 15*60
# number of spectrums per sample
STREAMING_CAPTURE_SAMPLE_SIZE = 10000
STREAMING_FILTER = "PEAK"
STREAMING_SERVER_PORT = 9000
STREAMING_SECONDS_PER_FRAME = 0.05
IS_AUTHENTICATION_REQUIRED = False
MY_SERVER_ID = None

def add_peer(protocol,host,port):
    mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
    client = MongoClient(mongodb_host)
    db = client.peerconfig
    config  = db.peers.find_one({"host":host,"port":port})
    if config != None:
        db.peers.remove({"host":host,"port":port})
    record =  {"protocol":protocol,"host":host,"port":port}
    db.peers.insert(record)


def add_peer_key(peerId,peerKey):
    mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
    client = MongoClient(mongodb_host)
    db = client.peerconfig
    peerkey  = db.peerkeys.find_one({"PeerId":peerId})
    if peerkey != None:
        db.peerkeys.remove({"PeerId":peerId})
    record = {"PeerId":peerId,"PeerKey":peerKey}
    db.peerkeys.insert(record)



def initialize():
    # A list of base URLS where this server will REGISTER
    # the sensors that it manages. This contains pairs of server
    # base URL and server key.

    PEERS=[{"protocol":"http", "host":"129.6.140.82" ,"port":8000, "key":"efgh"} ,
       {"protocol":"http", "host":"129.6.140.77" ,"port":8000, "key":"abcd"} ]

    mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
    client = MongoClient(mongodb_host)
    db = client.sysconfig
    oldConfig = db.configuration.find_one({})

    if oldConfig != None:
        db.configuration.remove(oldConfig)

    # Determine my host address by looking at the interfaces
    # and the default route (not always foolproof but works
    # most of the time). If you use specific routes,
    # this will not work.
    gws = netifaces.gateways()
    gw = gws['default'][netifaces.AF_INET]
    addrs = netifaces.ifaddresses(gw[1])
    MY_HOST_NAME = addrs[netifaces.AF_INET][0]['addr']


    configuration = {"API_KEY":API_KEY,\
    "SMTP_SERVER":SMTP_SERVER, \
    "SMTP_PORT" : SMTP_PORT,\
    "SMTP_SENDER": SMTP_SENDER,\
    "ADMIN_EMAIL_ADDRESS":ADMIN_EMAIL_ADDRESS,\
    "ADMIN_PASSWORD":ADMIN_PASSWORD, \
    "STREAMING_SAMPLING_INTERVAL_SECONDS":STREAMING_SAMPLING_INTERVAL_SECONDS,\
    "STREAMING_CAPTURE_SAMPLE_SIZE":STREAMING_CAPTURE_SAMPLE_SIZE,\
    "STREAMING_SECONDS_PER_FRAME":STREAMING_SECONDS_PER_FRAME,\
    "STREAMING_FILTER": STREAMING_FILTER,\
    "STREAMING_SERVER_PORT": STREAMING_SERVER_PORT,\
    "IS_AUTHENTICATION_REQUIRED": IS_AUTHENTICATION_REQUIRED,\
    "PEERS":PEERS,\
    "HOST_NAME":MY_HOST_NAME,\
    "MY_SERVER_ID":MY_SERVER_ID,\
    "MY_SERVER_KEY":MY_SERVER_KEY
    }

    db.configuration.insert(configuration)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('action',default="init",help="init add_peer or add_peer_key")
    parser.add_argument('-server_id',help='Server ID -- required')
    parser.add_argument('-secure',default="False",help='Login required flag ')
    parser.add_argument('-server_key',default=None,help="Server key")
    parser.add_argument('-host',help='peer host -- required')
    parser.add_argument('-port', help='peer port -- required')
    parser.add_argument('-protocol',help = 'peer protocol -- required')
    parser.add_argument("-peerid",help="peer ID")
    parser.add_argument("-key",help="peer key")
    args = parser.parse_args()
    action = args.action
    if args.action == "init":
        serverId = args.server_id
        serverKey = args.server_key
        if serverId == None:
            parser.error("Please supply server ID")
        MY_SERVER_ID = serverId
        if args.secure != None :
            if args.secure == "True":
                IS_AUTHENTICATION_REQUIRED = True
            elif args.secure == "False":
                IS_AUTHENTICATION_REQUIRED = False
            else :
                parser.error("Please specify True or false flag for --secure")
        else:
            IS_AUTHENTICATION_REQUIRED = False
        MY_SERVER_KEY = args.server_key
        if MY_SERVER_KEY == None:
            parser.error("Please specify server_key")
        MY_SERVER_KEY = args.server_key
        initialize()
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
        parser.error("Unknown option")






