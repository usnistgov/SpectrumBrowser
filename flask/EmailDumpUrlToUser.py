import threading
import flask
from flask import Flask, request,  abort, make_response
from flask import jsonify
import time
import os
import util


# Watch for the dump file to appear and mail to the user supplied
# email address to notify the user that it is available.

def watchForFileAndSendMail(emailAddress,url,uri):
    """
    Watch for the dump file to appear and send an email to the user
    after it has appeared.
    """
    for i in range(0,100):
        filePath = util.getPath("static/generated/" + uri)
        if os.path.exists(filePath):
            message = "This is an automatically generated message.\n"\
            +"The requested data has been generated\n"\
            +"Please retrieve your data from the following URL: "\
            + url \
            + "\nYou must retrieve this file within 24 hours."
            # TODO : send this message via SMTP but we need a functioning 
            # email account for that.
            util.debugPrint(message)
            
            return
        else:
            time.sleep(30)

    message =  "This is an automatically generated message.\n"\
    +"Tragically, the requested data could not be generated\n"
    debugPrint(message)


def emailDumpUrlToUser(emailAddress,url,uri):
    t = threading.Thread(target=watchForFileAndSendMail,args=(emailAddress,url,uri))
    t.daemon = True
    t.start()
    retval = {"status": "OK"}
    return jsonify(retval)


