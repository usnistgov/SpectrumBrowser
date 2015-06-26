echo "Pem passphrase is ranga"
mkdir -p /tmp/logs/nginx
$NGINX_HOME/install/sbin/nginx -c $SPECTRUM_BROWSER_HOME/nginx/nginx.conf.test
