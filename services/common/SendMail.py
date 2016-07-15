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

import smtplib
import Config
import traceback
import sys
from email.mime.text import MIMEText
import util


def sendMail(message, receiver, subject, link=False):
    if not Config.isMailServerConfigured():
        util.debugPrint("Cant Send mail. Mail server is not configured")
        return
    try:
        util.debugPrint("sendMail: smtpEmail " + Config.getSmtpEmail())
        util.debugPrint("sendMail: smtpServer " + Config.getSmtpServer())
        server = smtplib.SMTP(Config.getSmtpServer(),
                              Config.getSmtpPort(),
                              timeout=30)
        sender = Config.getSmtpEmail()
        if link:
            message = MIMEText(message, 'html')
        else:
            message = MIMEText(message)
        message["From"] = Config.getSmtpEmail()
        message["To"] = receiver
        message["Subject"] = subject
        #message["Content-Type:"] = "text/html"
        server.sendmail(sender, [receiver], message.as_string())
        server.quit()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.errorPrint("Unexpected error: sendMail")
        util.logStackTrace(sys.exc_info())


if __name__ == '__main__':
    sendMail("cool message", "mranga@nist.gov", "cool subject")
