import flaskr as main
from flask import abort
from flask import jsonify
import json
import os
import sys
import traceback
import flaskr as globals
import util
import threading
import SendMail
import time
import authentication


def generateChangePasswordEmail(emailAddress,url):
    """
    Generate and send email. This is a thread since the SMTP timeout is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"Please change your password by clicking on the following URL: \n"\
    + url 
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "change password link")


def storePasswordEmailUser(emailAddress,oldPassword, newPassword):
    # JEK: Note: we really only need to check the password and not the email here
    # Since we will be emailing the user and know soon enough if the email is invalid.
    if not authentication.isPasswordValid(newPassword) :
        return jsonify({"status":"FAIL"})
    try:
        t = threading.Thread(target=generateChangePasswordEmail,args=(emailAddress,url))
        t.daemon = True
        t.start()
    except:
        retval = {"status": "NOK"}
        return jsonify(retval)
    else:
        retval = {"status": "OK"}
        return jsonify(retval)




