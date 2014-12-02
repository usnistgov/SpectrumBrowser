import smtplib
import Config
import traceback
import sys
from email.mime.text import MIMEText

def sendMail(message,receiver, subject):
    try:
        print "sendMail", Config.getSmtpSender(), receiver
        server = smtplib.SMTP(Config.getSmtpServer() , Config.getSmtpPort(), timeout=30)
        sender = Config.getSmtpSender()
        message = MIMEText(message)
        message["From"] = Config.getSmtpSender()
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
