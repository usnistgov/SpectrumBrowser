
<h2> HTTPD configuration notes </h2>

Flask is a service container (not a full fledged web server). It comes
with a test web server for development purposes but is not recommeded
for public installation. Flask can work with several web servers. You
will need to install Apache httpd and the flask wsgi module for flask
to be able to work with apache httpd.

    pip install mod_wsgi

The httpd configuration in the conf directory is an example of how you
should configure apache httpd to work with flask. You should modify the
absolute paths in conf/httpd.conf according to where things live on your
system. Start as follows

    httpd -f `pwd`/conf/httpd.conf

To stop httpd, I just use pkill

    pkill httpd

