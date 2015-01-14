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
SCAN_TIME = 10.0

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
            print "ConnectionMaintainer-- starting",self.myId
            threading.Timer(SCAN_TIME, self.signIntoPeers).start()

    def signIntoPeers(self):
        util.debugPrint("Starting peer sign in")
        myHostName = Config.getHostName()
        if myHostName == None:
            print "System not configured - returning"
            return
        # re-start the timer ( do we need to stop first ?)
        self.peers = Config.getPeers()
        threading.Timer(SCAN_TIME,self.signIntoPeers).start()
        self.getPeerSystemAndLocationInfo()
        for peer in self.peers:
            if peer["host"] != myHostName:
                peerKey = Config.getServerKey()
                peerProtocol = peer["protocol"]
                peerHost = peer["host"]
                peerPort = peer["port"]
                myServerId = Config.getServerId()
                peerUrl = util.generateUrl(peerProtocol,peerHost,peerPort)
                currentTime = time.time()
                self.readPeerSystemAndLocationInfo()
                if peerUrl in peerSystemAndLocationInfo:
                    lastTime = peerSystemAndLocationInfo[peerUrl]["time"]
                    if currentTime - lastTime < SCAN_TIME/2 :
                       continue
                url = peerUrl + "/federated/peerSignIn/"  + myServerId + "/" + peerKey
                util.debugPrint("Peer URL = " + url)
                if not Config.isAuthenticationRequired():
                    locationInfo = GetLocationInfo.getLocationInfo()
                else:
                    locationInfo = None
                try :
                    r = requests.post(url,data=str(locationInfo))
                    # Extract the returned token
                    if r.status_code == 200 :
                        jsonObj = r.json()
                        if jsonObj["status"] == "OK":
                            if "locationInfo" in jsonObj:
                                self.readPeerSystemAndLocationInfo()
                                locationInfo = jsonObj["locationInfo"]
                                locationInfo["time"] = time.time()
                                peerSystemAndLocationInfo[peerUrl] = locationInfo
                                self.writePeerSystemAndLocationInfo()
                        else:
                            if peerUrl in peerSystemAndLocationInfo:
                                del peerSystemAndLocationInfo[peerUrl]
                            util.debugPrint("Sign in with peer failed")
                    else:
                        util.debugPrint("Sign in with peer failed HTTP Status Code " + str(r.status_code))
                except RequestException:
                    print "Could not contact Peer at "+peerUrl
                    self.readPeerSystemAndLocationInfo()
                    if peerUrl in peerSystemAndLocationInfo:
                        del peerSystemAndLocationInfo[peerUrl]
                    self.writePeerSystemAndLocationInfo()

    def getPeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        self.readPeerSystemAndLocationInfo()
        return peerSystemAndLocationInfo
    
    def setPeerSystemAndLocationInfo(self,url,systemAndLocationInfo):
        global peerSystemAndLocationInfo
        self.readPeerSystemAndLocationInfo()
        peerSystemAndLocationInfo[url] = systemAndLocationInfo
        self.writePeerSystemAndLocationInfo()


def start() :
    global connectionMaintainer
    connectionMaintainer = ConnectionMaintainer()
    connectionMaintainer.start()
    
def getPeerSystemAndLocationInfo():
    return connectionMaintainer.getPeerSystemAndLocationInfo()

def setPeerSystemAndLocationInfo(url,systemAndLocationInfo):
    systemAndLocationInfo["time"] = time.time()
    connectionMaintainer.setPeerSystemAndLocationInfo(url, systemAndLocationInfo)
    



