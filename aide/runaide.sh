#!/bin/sh
FILENAME=/tmp/aide.out
nice -19 /usr/sbin/aide --check > $FILENAME
FILESIZE=$(stat -c%s "$FILENAME")
if [ $FILESIZE == 0 ] ; then
   echo /bin/date >> /var/log/aide.out
   echo "AIDE: Security scan found no violations" >> /var/log/aide.out
elif grep -F "### All files match AIDE database. Looks okay" /tmp/aide.out ; then
   echo /bin/date >> /var/log/aide.out
   echo "AIDE: Security scan found no violations" >> /var/log/aide.out
else
    cat /tmp/aide.out | /opt/SpectrumBrowser/swaks -4  --to mranga@nist.gov --from mranga@nist.gov --server smtp.nist.gov --h-Subject "MSOD: aide Scan Report" --body -
    cat /tmp/aide.out | /opt/SpectrumBrowser/swaks -4 --to bhadresh.savaliya@nist.gov  --from mranga@nist.gov --server smtp.nist.gov --h-Subject "MSOD:  aide Scan Report" --body -
    #cat /tmp/aide.out | /opt/SpectrumBrowser/swaks  --to siirt@nist.gov  --from mranga@nist.gov --server smtp.nist.gov --h-Subject "MSOD: Security Intrusion scan report" --body -
fi
cat /tmp/aide.out  >> /var/log/aide.out

