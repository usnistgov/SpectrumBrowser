from pymongo import MongoClient
import os

mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.sysconfig

def getApiKey() :
    configuration = db.configuration.find_one({})
    return configuration["API_KEY"]

def getSmtpSender() :
    configuration = db.configuration.find_one({})
    return configuration["SMTP_SENDER"]

def getSmtpServer():
    configuration = db.configuration.find_one({})
    return configuration["SMTP_SERVER"]

def getSmtpPort():
    configuration = db.configuration.find_one({})
    return configuration["SMTP_PORT"]

def getAdminEmailAddress():
    configuration = db.configuration.find_one({})
    return configuration["ADMIN_EMAIL_ADDRESS"]

def getAdminPassword():
    configuration = db.configuration.find_one({})
    return configuration["ADMIN_PASSWORD"]

def getStreamingSamplingIntervalSeconds():
    configuration = db.configuration.find_one({})
    return configuration["STREAMING_SAMPLING_INTERVAL_SECONDS"]

def getStreamingCaptureSampleSize():
    configuration = db.configuration.find_one({})
    return configuration["STREAMING_CAPTURE_SAMPLE_SIZE"]

def getStreamingFilter():
    configuration = db.configuration.find_one({})
    return configuration["STREAMING_FILTER"]

def getStreamingSecondsPerFrame() :
    configuration = db.configuration.find_one({})
    return configuration["STREAMING_SECONDS_PER_FRAME"]



