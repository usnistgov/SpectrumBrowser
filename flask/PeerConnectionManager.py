import Config
import requests
import threading
import util
from requests.exceptions import RequestException
import GetLocationInfo
import memcache
import time
import json
import os

# stores a table of peer keys generated randomly
global peerSystemAndLocationInfo
global peerUrlMap

peerSystemAndLocationInfo = {}
peerUrlMap = {}

class ConnectionMaintainer :
    def __init__ (self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.myId = os.getpid()
        
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
            threading.Timer(Config.getSoftStateRefreshInterval(), self.signIntoPeers).start()
            
    def setPeerUrl(self,peerId,peerUrl):
        global peerUrlMap
        urlMap = self.mc.get("peerUrlMap")
        if urlMap != None:
            peerUrlMap = urlMap
        peerUrlMap[peerId] = peerUrl
        self.mc.set("peerUrlMap",peerUrlMap)
        
    def readPeerUrlMap(self):
        urlMap = self.mc.get("peerUrlMap")
        if urlMap != None:
            global peerUrlMap
            peerUrlMap = urlMap
            
    

    def signIntoPeers(self):
        global peerSystemAndLocationInfo
        #util.debugPrint("Starting peer sign in")
        myHostName = Config.getHostName()
        if myHostName == None:
            print "System not configured - returning"
            return
        # Load the cache
        self.readPeerUrlMap()
        self.readPeerSystemAndLocationInfo()
        inboundPeers = Config.getInboundPeers()
        for inboundPeer in inboundPeers:
            peerId = inboundPeer["PeerId"]
            if peerId in peerUrlMap:
                peerUrl = peerUrlMap[peerId]
                if peerUrl in peerSystemAndLocationInfo:
                    currentTime = time.time()
                    if currentTime - peerSystemAndLocationInfo[peerUrl]["_time"] > \
                        2*Config.getSoftStateRefreshInterval():
                        del peerSystemAndLocationInfo[peerUrl]
        self.writePeerSystemAndLocationInfo()                
        # re-start the timer ( do we need to stop first ?)
        self.peers = Config.getPeers()
        threading.Timer(Config.getSoftStateRefreshInterval(),self.signIntoPeers).start()
        # If user authentication is required, we export nothing.
        if not Config.isAuthenticationRequired():
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
                        lastTime = peerSystemAndLocationInfo[peerUrl]["_time"]
                        if currentTime - lastTime < Config.getSoftStateRefreshInterval()/2 :
                            continue
                    url = peerUrl + "/federated/peerSignIn/"  + myServerId + "/" + peerKey
                    util.debugPrint("Peer URL = " + url)
                    locationInfo = GetLocationInfo.getLocationInfo()
                    postData = {}
                    try :
                        if locationInfo != None:
                            postData["PublicPort"] = Config.getPublicPort()
                            postData["HostName"] = Config.getHostName()
                            postData["locationInfo"] = locationInfo
                            r = requests.post(url,data=json.dumps(postData))
                        else:
                            r = requests.post(url)   
                        # Extract the returned token
                        if r.status_code == 200 :
                            jsonObj = r.json()
                            if jsonObj["status"] == "OK":
                                if "locationInfo" in jsonObj:
                                    self.readPeerSystemAndLocationInfo()
                                    locationInfo = jsonObj["locationInfo"]
                                    locationInfo["_time"] = time.time()
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
    if not "connectionMaintainer" in globals():
        connectionMaintainer = ConnectionMaintainer()
        connectionMaintainer.start()
    
def getPeerSystemAndLocationInfo():
    global connectionMaintainer
    return connectionMaintainer.getPeerSystemAndLocationInfo()

def setPeerSystemAndLocationInfo(url,systemAndLocationInfo):
    systemAndLocationInfo["_time"] = time.time()
    connectionMaintainer.setPeerSystemAndLocationInfo(url, systemAndLocationInfo)
    
def setPeerUrl(peerId,peerUrl):
    global connectionMaintainer
    connectionMaintainer.setPeerUrl(peerId,peerUrl)
    
def getPeerUrl(peerId):
    global connectionMaintainer
    connectionMaintainer.readPeerUrlMap()
    if peerId in peerUrlMap:
        return peerUrlMap[peerId]
    else:
        return None
    



