# TODO -- put these in mongo
API_KEY= "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU"
#SMTP_SENDER="mranga@nist.gov"
#SMTP_SERVER="smtp.nist.gov"
#SMTP_PORT = 25
#SMTP_USER = "mranga@nist.gov"

SMTP_SENDER="jkub@jkub-Precision-M6800.com "
# The following server name did not work, so I changed to localhost:
#SMTP_SERVER="mike-Precision-M6500.com"
SMTP_SERVER="localhost"
SMTP_PORT = 25
SMTP_USER = "jkub@jkub-Precision-M6800.com"

# Time between captures.
STREAMING_SAMPLING_INTERVAL_SECONDS = 15*60
# number of spectrums per sample
STREAMING_CAPTURE_SAMPLE_SIZE = 10000
STREAMING_FILTER = "PEAK"
