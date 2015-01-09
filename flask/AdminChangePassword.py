
from flask import jsonify
import util
import threading
import SendMail



def generateSendEmail(emailAddress,url):
    """
    Generate and send email. This is a thread since the SMTP time is 30 seconds
    """
    message = "This is an automatically generated message from the Spectrum Monitoring System.\n"\
    +"Please change your password by clicking on the following URL: \n"\
    + url 
    util.debugPrint(message)
    SendMail.sendMail(message,emailAddress, "change password link")


def emailUrlToUser(emailAddress,url):
    try:
        t = threading.Thread(target=generateSendEmail,args=(emailAddress,url))
        t.daemon = True
        t.start()
    except:
        retval = {"status": "NOK"}
        return jsonify(retval)
    else:
        retval = {"status": "OK"}
        return jsonify(retval)




