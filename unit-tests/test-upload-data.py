#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others. 
#This software has been contributed to the public domain. 
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain. 
#As a result, a formal license is not needed to use this software.
# 
#This software is provided "AS IS."  
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.


import unittest
import json
import requests
import argparse
import os
import json

BINARY_INT8 = "Binary - int8"
BINARY_INT16 = "Binary - int16"
BINARY_FLOAT32 = "Binary - float32"
ASCII = "ASCII"
class  TestUploadData(unittest.TestCase):
   def setUp(self):
        global host
	global filename
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        r = requests.post("https://"+ host + ":" + str(8443) + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.token = resp["sessionId"]
	self.sensorId = "NorfolkTest"
	self.sensorId = 'NorfolkTest'
	sensorConfig = json.load(open("NorfolkTest.config.json"))
	url = "https://" + host + ":" + str(8443) + "/admin/addSensor/" + self.token
	r = requests.post(url, data = json.dumps(sensorConfig), verify = False)
	self.assertTrue(r.status_code == 200 )
		
    	self.f = open(filename)


   def getDataTypeLength(self,dataType):
       if dataType == BINARY_FLOAT32:
           return 4
       elif dataType == BINARY_INT8:
           return 1
       else:
           return 1

   def getDataType(self,jsonData):
      return jsonData["DataType"]


   def getNumberOfMeasurements(self,jsonData):
       return int(jsonData["nM"])

   def getNumberOfFrequencyBins(self,jsonData):
       return int(jsonData["mPar"]["n"])

   # Read ascii from a file descriptor.
   def readAsciiFromFile(self):
       fileDesc = self.f
       csvValues = ""
       while True:
           char = fileDesc.read(1)
           if char == "[":
               csvValues += "["
               break
       while True:
           char = fileDesc.read(1)
           csvValues += char
           if char == "]":
               break
       return csvValues

   def readDataFromFileDesc(self,dataType, count):
      fileDesc = self.f
      if dataType != ASCII :
          dataTypeLength = self.getDataTypeLength(dataType)
          dataBytes = fileDesc.read(dataTypeLength * count)
      else:
          dataBytes = self.readAsciiFromFile()
      return dataBytes


   def readHeader(self):
       	headerLengthStr = ""
       	while True:
            c = self.f.read(1)
            if c == "" :
                print "Done reading file"
                return
            if c == '\r':
                if headerLengthStr != "":
                    break
            elif c == '\n':
                if headerLengthStr != "":
                    break
            else:
                headerLengthStr = headerLengthStr + c
        print "headerLengthStr = " , headerLengthStr
        jsonHeaderLength = int(headerLengthStr.rstrip())
        jsonStringBytes = self.f.read(jsonHeaderLength)
	return headerLengthStr,jsonStringBytes

   def testUploadData(self):
	url = "https://" + host + ":" + str(443)+ "/spectrumdb/upload"
	while True:
	   headerLengthStr,headerString = self.readHeader()
	   jsonData = json.loads(headerString)
	   jsonData["SensorID"] = self.sensorId
	   headerJsonStr = json.dumps(jsonData,indent=4)
	   if jsonData["Type"] == "Loc":
	      resp = requests.post(url,data=str(len(headerJsonStr)) + "\n" + headerJsonStr,verify=False)
	      print str(resp.status_code)
	      self.assertTrue(resp.status_code == 200)
           elif jsonData["Type"] == "Sys":
	      messageBytes = ""
              if "Cal" in jsonData:
                  calStr = jsonData["Cal"]
                  n = jsonData["Cal"]["mPar"]["n"]
                  nM = jsonData["Cal"]["nM"]
                  sensorId = jsonData["SensorID"]
                  if n * nM != 0 :
                      dataType = jsonData["Cal"]["DataType"]
                      lengthToRead = n * nM
                      messageBytes = self.readDataFromFileDesc(dataType, lengthToRead)
	      messageToPost = headerJsonStr + messageBytes
	      print messageToPost
	      resp = requests.post(url,data=str(len(headerJsonStr)) + "\n" + messageToPost, verify =False)
	      print "status_code ", resp.status_code
	      self.assertTrue(resp.status_code == 200)
	   elif jsonData["Type"] == "Data":
               nM = self.getNumberOfMeasurements(jsonData)
               n = self.getNumberOfFrequencyBins(jsonData)
               lengthToRead = n * nM
	       dataType = self.getDataType(jsonData)
               messageBytes = self.readDataFromFileDesc(dataType, lengthToRead)
	       messageToPost = headerJsonStr + messageBytes
	       print messageToPost
	       resp = requests.post(url,data=str(len(headerJsonStr)) + "\n" + messageToPost, verify =False)
	       self.assertTrue(resp.status_code == 200)
	       break
		
   def tearDown(self):
	url = "https://" + host + ":" + str(8443) + "/admin/purgeSensor/" + self.sensorId + "/" + self.token
	r = requests.post(url,  verify = False)
        r = requests.post("https://"+ host + ":" + str(8443) + "/admin/logOut/"  + self.token, verify=False)
		
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host",help="Server host.")
    parser.add_argument("-file",help="Data file.")
    args = parser.parse_args()
    global filename
    global host
    host = args.host
    if host == None:
        host = os.environ.get("MSOD_WEB_HOST")

    if host == None :
        print "Require host and web port"
        os._exit()

    filename = args.file
    if filename == None:
	filename = "NorfolkTestSample.txt"

    if not os.path.exists(filename):
        print "Require data file -file argument."
        os._exit()
	
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUploadData)
    unittest.TextTestRunner(verbosity=2).run(suite)
