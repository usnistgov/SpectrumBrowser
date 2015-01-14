import Config
import requests
import threading
import util
from requests.exceptions import RequestException
import GetLocationInfo
import memcache
import random
import time

# stores a table of peer keys generated randomly

peerSystemAndLocationInfo = {}
connectionMaintainer = None

class ConnectionMaintainer :
    def __init__ (self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        random.seed(time.time())
        self.myId = random.randint(0,100)
        
        print "ConnectionMaintainer"
        
    def readPeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        locInfo = self.mc.get("peerSystemAndLocationInfo")
        if locInfo != None:
            peerSystemAndLocationInfo = locInfo
        
    def writePeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        self.mc.set("peerSystemAndLocationInfo", peerSystemAndLocationInfo)
        
    def acquireSem(self):
        self.mc.add("peerConnectionMaintainerSem",self.myId)
        storedId = self.mc.get("peerConnectionMaintainerSem")
        if storedId == self.myId:
            return True
        else:
            return False

    def start(self):
        if self.acquireSem():
            threading.Timer(10.0, self.signIntoPeers).start()

    def signIntoPeers(self):
        #
        util.debugPrint("Starting peer sign in")
        global peerSystemAndLocationInfo
        myHostName = Config.getHostName()
        if myHostName == None:
            print "System not configured - returning"
            return
        # re-start the timer ( do we need to stop first ?)
        self.peers = Config.getPeers()
        threading.Timer(10.0,self.signIntoPeers).start()
        for peer in self.peers:
            if peer["host"] != myHostName:
                peerKey = Config.getServerKey()
                peerProtocol = peer["protocol"]
                peerHost = peer["host"]
                peerPort = peer["port"]
                myServerId = Config.getServerId()
                peerUrl = util.generateUrl(peerProtocol,peerHost,peerPort)
                url = peerUrl + "/federated/peerSignIn/"  + myServerId + "/" + peerKey
                util.debugPrint("Peer URL = " + url)
                if not Config.isAuthenticationRequired():
                    locationInfo = GetLocationInfo.getLocationInfo()
                else:
                    locationInfo = None
                peerUrlPrefix = peerProtocol + "://" + peerHost + ":" + str(peerPort)
                try :
                    r = requests.post(url,data=locationInfo)
                    # Extract the returned token
                    if r.status_code == 200 :
                        jsonObj = r.json()
                        if jsonObj["status"] == "OK":
                            if "locationInfo" in jsonObj:
                                self.readPeerSystemAndLocationInfo()
                                peerSystemAndLocationInfo[peerUrlPrefix] = jsonObj["locationInfo"]
                                self.writePeerSystemAndLocationInfo()
                        else:
                            if peerUrlPrefix in peerSystemAndLocationInfo:
                                del peerSystemAndLocationInfo[peerUrlPrefix]
                            util.debugPrint("Sign in with peer failed")
                    else:
                        util.debugPrint("Sign in with peer failed HTTP Status Code " + str(r.status_code))
                except RequestException:
                    print "Could not contact Peer at "+peerUrl
                    self.readPeerSystemAndLocationInfo()
                    if peerUrlPrefix in peerSystemAndLocationInfo:
                        del peerSystemAndLocationInfo[peerUrlPrefix]
                    self.writePeerSystemAndLocationInfo()

    def getPeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        self.readPeerSystemAndLocationInfo()
        return peerSystemAndLocationInfo


def start() :
    global connectionMaintainer
    connectionMaintainer = ConnectionMaintainer()
    connectionMaintainer.start()
    
def getPeerSystemAndLocationInfo():
    return connectionMaintainer.getPeerSystemAndLocationInfo()
    



