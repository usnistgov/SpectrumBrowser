import flaskr as main
import util
from flask import request,make_response,jsonify


def getAdminBandInfo(bandName):
    """
    get an admin frequency band info for the input bandName
    """
    util.debugPrint("getAdminBandInfo")
    query = { "bandName": bandName }
    util.debugPrint(query)
    bandThreshold = main.db.adminThreshold.find_one(query)
    del bandThreshold["_id"]
    util.debugPrint(bandThreshold)
    util.debugPrint(jsonify(bandThreshold))
    return jsonify(bandThreshold)


