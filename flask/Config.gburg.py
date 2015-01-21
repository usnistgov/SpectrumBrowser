from pymongo import MongoClient
import os

# This is a placeholder. After first system install, we need a page that
# Expects these things to be entered before the system becomes operational.

API_KEY= "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU"
#SMTP_SERVER="smtp.nist.gov"
SMTP_SERVER="localhost"
SMTP_PORT = 25
SMTP_SENDER = "mranga@nist.gov"
ADMIN_EMAIL_ADDRESS = "mranga@nist.gov"
ADMIN_PASSWORD = "12345"
# Time between captures.
STREAMING_SAMPLING_INTERVAL_SECONDS = 15*60
# number of spectrums per sample
STREAMING_CAPTURE_SAMPLE_SIZE = 10000
STREAMING_FILTER = "MAX_HOLD"
STREAMING_SERVER_PORT = 9000
STREAMING_SECONDS_PER_FRAME = 0.05


mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.sysconfig
oldConfig = db.configuration.find_one({})

if oldConfig != None:
    db.configuration.remove(oldConfig)

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
"STREAMING_SERVER_PORT": STREAMING_SERVER_PORT}

db.configuration.insert(configuration)

