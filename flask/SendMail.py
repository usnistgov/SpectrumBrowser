import smtplib
import Config
import traceback
import sys
from email.mime.text import MIMEText

def sendMail(message,receiver, subject):
    try:
        server = smtplib.SMTP(Config.SMTP_SERVER , Config.SMTP_PORT, timeout=30)
        sender = Config.SMTP_SENDER
        message = MIMEText(message)
        message["From"] = Config.SMTP_USER
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
