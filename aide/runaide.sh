#!/bin/sh
nice -19 aide --check >> /tmp/aide.out
if [ $? == 0 ] ; then
   echo "AIDE: Security scan found no violations" >> /var/log/aide.out
else
    cat /tmp/aide.out | /opt/SpectrumBrowser/swaks -4  --to mranga@nist.gov --from mranga@nist.gov --server smtp.nist.gov --h-Subject "MSOD: aide Scan Report" --body -
    cat /tmp/aide.out | /opt/SpectrumBrowser/swaks -4 --to bhadresh.savaliya@nist.gov  --from mranga@nist.gov --server smtp.nist.gov --h-Subject "MSOD:  aide Scan Report" --body -
    #cat /tmp/aide.out | /opt/SpectrumBrowser/swaks  --to siirt@nist.gov  --from mranga@nist.gov --server smtp.nist.gov --h-Subject "MSOD: Security Intrusion scan report" --body -
fi
cat /tmp/aide.out  >> /var/log/aide.out

