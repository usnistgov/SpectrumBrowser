import smtplib
import Config
import traceback
import sys
from email.mime.text import MIMEText
import util
import Accounts

def sendMail(message,receiver, subject):
    if not Config.isMailServerConfigured():
        util.debugPrint("Cant Send mail. Mail server is not configured")
        return
    try:
        util.debugPrint("sendMail: smtpEmail " + Config.getSmtpEmail())
        util.debugPrint("sendMail: smtpServer " + Config.getSmtpServer())
        server = smtplib.SMTP(Config.getSmtpServer() , Config.getSmtpPort(), timeout=30)
        sender = Config.getSmtpEmail()
        message = MIMEText(message)
        message["From"] = Config.getSmtpEmail()
        message["To"] = receiver
        message["Subject"] = subject
        message["Content-Type:"] = "text/html"
        server.sendmail(sender,[receiver],message.as_string())
        server.quit()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.errorPrint("Unexpected error: sendMail")
        util.logStackTrace(sys.exc_info())



if __name__ == '__main__':
    sendMail("cool message", "mranga@nist.gov", "cool subject")
