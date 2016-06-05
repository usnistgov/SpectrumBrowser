import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=0)


def getPeerSystemAndLocationInfo():
    locInfo = mc.get("peerSystemAndLocationInfo")
    if locInfo != None:
        peerSystemAndLocationInfo = locInfo
    else:
        peerSystemAndLocationInfo = {}
    return peerSystemAndLocationInfo
