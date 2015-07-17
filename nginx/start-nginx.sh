mkdir -p /tmp/logs/nginx
CFG=$HOME/.msod/MSODConfig.json
if [ -f $FILE  ]; then
    echo "Using file $CFG"
else
    print "$CFG not found"
    exit -1
fi
SB_HOME=$(
    python -c 'import json; print json.load(open("'$CFG'"))["SPECTRUM_BROWSER_HOME"]'
)
cp $SB_HOME/devel/certificates/privkey.pem ./
cp $SB_HOME/devel/certificates/cacert.pem ./
nginx -c $SB_HOME/nginx/nginx.conf.test
