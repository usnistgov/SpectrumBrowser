import Config
import requests
import authentication
import sys
import traceback
import threading
import util
from requests.exceptions import RequestException
import GetLocationInfo

# stores a table of peer keys generated randomly

peerSessionKeys = {}
peerSystemAndLocationInfo = {}
connectionMaintainer = None

class ConnectionMaintainer :
    def __init__ (self):
        self.peers = Config.getPeers()

    def start(self):
        if self.peers != None:
           threading.Timer(10.0, self.signIntoPeers).start()

    def signIntoPeers(self):
        #
        global peerSystemAndLocationInfo
        myHostName = Config.getHostName()
        # re-start the timer ( do we need to stop first ?)
        threading.Timer(10.0,self.signIntoPeers).start()
        for peer in self.peers:
            if peer["host"] != myHostName:
                peerKey = Config.getServerKey()
                peerProtocol = peer["protocol"]
                peerHost = peer["host"]
                peerPort = peer["port"]
                myServerId = Config.getServerId()
                peerUrl = util.generateUrl(peerProtocol,peerHost,peerPort)
                peerSessionKey = authentication.generatePeerSessionKey()
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
                    print "StatusCode = " + str(r.status_code)
                    if r.status_code == 200 :
                        jsonObj = r.json()
                        util.debugPrint(jsonObj)
                        if jsonObj["status"] == "OK":
                            if "locationInfo" in jsonObj:
                                print jsonObj["locationInfo"]
                                peerSystemAndLocationInfo[peerUrlPrefix] = jsonObj["locationInfo"]
                        else:
                            if peerUrlPrefix in peerSystemAndLocationInfo:
                                del peerSystemAndLocationInfo[peerUrlPrefix]
                            util.debugPrint("Sign in with peer failed")
                    else:
                        util.debugPrint("Sign in with peer failed HTTP Status Code " + str(r.status_code))
                except RequestException:
                     print "Could not contact Peer at "+peerUrl
                     if peerUrlPrefix in peerSystemAndLocationInfo:
                        del peerSystemAndLocationInfo[peerUrlPrefix]

    def getPeerSystemAndLocationInfo(self):
        return peerSystemAndLocationInfo

    def getPeerSessionKey(self,peerUrl):
        if peerUrl in peerSessionKeys:
            return peerSessionKeys[peerUrl]
        else:
            return None

    def registerSensorWithPeer(self,peer,sensorId):
        try :
            # first login to the peer. We need an account to login
            if Config.isSecure():
                myBaseUrl = "https://" + Config.getHostName()
            else:
                myBaseUrl = "http://" + Config.getHostName()
            peerSessionKey = peerSessionKeys[peer]
            globals.session
            url = peer + "/registerSensorWithPeer/" + sensorId + "/" + peerSessionKey
            args = {"url":myBaseUrl}
            r = requests.post(url,args)
            jsonObj = r.json()
            if jsonObj["status"] != "OK":
                util.debugPrint("REGISTRATION of " + sensorId+ " with " + peer + " failed")
            else:
                util.debugPrint("REGISTRATION of " + sensorId+ " with " + peer + " succeded")
        except RequestException:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()


def start() :
    global connectionMaintainer
    connectionMaintainer = ConnectionMaintainer()
    connectionMaintainer.start()
    
def getPeerSystemAndLocationInfo():
    return connectionMaintainer.getPeerSystemAndLocationInfo()
    



