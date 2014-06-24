
<h2> HTTPD configuration notes </h2>

First, you will need to install httpd and httpd-devel packages. For Centos you can install these using yum
    
    sudo yum install httpd
    sudo yum install httpd-devel

If you don't have root and don't want to disturb the httpd configuration on your server, 
to test things out, copy /etc/httpd/modules to the httpd directory.

This project uses flask. Flask is a python web-services container (not a
full fledged web server). It comes with a test web server for development
purposes but is not recommended for public installation. Flask can work
with several web servers. You will need to install Apache httpd and the
flask wsgi module for flask to be able to work with apache httpd.

    pip install mod_wsgi

The httpd configuration in the conf directory is an example of how you
should configure apache httpd to work with flask. You should customize the
absolute paths in conf/httpd.conf according to where things live on your
system. Do not commit your changes to this file. Make a copy of it to http.conf.mine 
and customize it.

Edit the following file. Again, do not commit your changes. Copy it to another file and
edit httpd.conf.mine to reflect the file name:

    cp flask/wsgi/flask.wsgi flask/wsgi.mine
    vi flask/wsgi/flask.wsgi.mine

Start as follows (under linux):

    httpd -f `pwd`/httpd/conf/httpd.conf.mine

To stop httpd, I just use pkill

    pkill httpd

