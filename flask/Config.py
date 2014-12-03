from pymongo import MongoClient
import os

mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.sysconfig
configuration = db.configuration.find_one({})

def getApiKey() :
    return configuration["API_KEY"]

def getSmtpSender() :
    return configuration["SMTP_SENDER"]

def getSmtpServer():
    return configuration["SMTP_SERVER"]

def getSmtpPort():
    return configuration["SMTP_PORT"]

def getAdminEmailAddress():
    return configuration["ADMIN_EMAIL_ADDRESS"]

def getAdminPassword():
    return configuration["ADMIN_PASSWORD"]

def getStreamingSamplingIntervalSeconds():
    return configuration["STREAMING_SAMPLING_INTERVAL_SECONDS"]

def getStreamingCaptureSampleSize():
    return configuration["STREAMING_CAPTURE_SAMPLE_SIZE"]

def getStreamingFilter():
    return configuration["STREAMING_FILTER"]

def getStreamingServerPort():
    return configuration["STREAMING_SERVER_PORT"]

def isStreamingSocketEnabled():
    if "STREAMING_SERVER_PORT" in configuration:
        return True
    else:
        return False
def getStreamingSecondsPerFrame() :
    return configuration["STREAMING_SECONDS_PER_FRAME"]

def isAuthenticationRequired():
    return configuration["IS_AUTHENTICATION_REQUIRED"]

def getPeers():
    return configuration["PEERS"]

def getHostName() :
    return configuration["HOST_NAME"]

def getServerKey():
    return configuration["MY_SERVER_KEY"]

def getServerId():
    return configuration["MY_SERVER_ID"]

def reload():
    configuration = db.configuration.find_one({})



