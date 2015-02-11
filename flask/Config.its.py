import pymongo
from pymongo import MongoClient
import os


mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.sysconfig
oldConfig = db.configuration.find_one({})

if oldConfig != None:
    db.configuration.remove(oldConfig)

configuration = {"API_KEY": "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU",\
        "SMTP_SERVER":"localhost", \
        "SMTP_PORT" : 25,\
        "SMTP_SENDER":"jkub@jkub-Precision-M6800.com",\
        "ADMIN_EMAIL_ADDRESS":"jkub@jkub-Precision-M6800.com",\
        "ADMIN_PASSWORD":"12345", \
        "STREAMING_SAMPLING_INTERVAL_SECONDS":15*60,\
        "STREAMING_CAPTURE_SAMPLE_SIZE":10000,\
        "STREAMING_SECONDS_PER_FRAME": 0.05,\
        "STREAMING_FILTER": Defines.MAX_HOLD,\
        STREAMING_SERVER_PORT: 9000,\
        "IS_AUTHENTICATION_REQUIRED": True,\
        "MY_SERVER_ID":"bldr",\
        "MY_SERVER_KEY":"efgh",\
        "PEERS":"Peers.bldr.txt",\
        "PEER_KEYS":"PeerKeys.bldr.txt"}

db.configuration.insert(configuration)

