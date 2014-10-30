import struct
from struct import *
import json
import pymongo
import os
from os import path
from os import makedirs
from pprint import pprint
from json import JSONEncoder
from pymongo import MongoClient
from pymongo import ASCENDING
from bson.objectid import ObjectId
from bson.json_util import dumps

mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.spectrumdb


BAND_DATA = [{"bandName":"Radar", "freqRange": {"minFreqHz":3550000000, "maxFreqHz":3650000000}, "occupancyThresdholddBm":-85.5}, 
{"bandName":"LTE", "freqRange": {"minFreqHz":700000000, "maxFreqHz":800000000}, "occupancyThresdholddBm":-77} ]

    

def put_data():
    """
    put data in the database. 
    """
    db.adminThreshold.insert(BAND_DATA)
   





if __name__ == "__main__":

    put_data()
    # Michael's buggy data.
    #putDataFromFile(filename)


