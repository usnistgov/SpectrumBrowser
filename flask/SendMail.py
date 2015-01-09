import smtplib
import Config
import traceback
import sys
from email.mime.text import MIMEText
import util

def sendMail(message,receiver, subject):
    if not Config.isMailServerConfigured():
        util.debugPrint("Cant Send mail. Mail server is not configured")
        return
    try:
        util.debugPrint(Config.getAdminEmailAddress())
        util.debugPrint(Config.getSmtpServer())
        server = smtplib.SMTP(Config.getSmtpServer() , Config.getSmtpPort(), timeout=30)
        sender = Config.getAdminEmailAddress()
        message = MIMEText(message)
        message["From"] = Config.getAdminEmailAddress()
        message["To"] = receiver
        message["Subject"] = subject
        message["Content-Type:"] = "text/html"
        server.sendmail(sender,[receiver],message.as_string())
        server.quit()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()



if __name__ == '__main__':
    sendMail("http://www.gmail.com","mranga@gmail.com")
