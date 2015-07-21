rm *.pem *.csr *.crt
openssl genrsa -out privkey.pem 1024
openssl req -new -key privkey.pem -out server.csr
openssl x509 -req -days 3660 -in server.csr -signkey privkey.pem -out cacert.pem
openssl x509 -in server.csr -out dummy.crt -req -signkey privkey.pem -days 3650
cp privkey.pem ../../nginx/
cp cacert.pem ../../nginx/
