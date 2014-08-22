= How to run the system behind the nginx web server = 

For deployment on a production, you should set up a front end web
server. nginx is the web server of choice.  nginx establishes a
connection with the flask service container and sends requests there
for processing.  nginx establishes a secure connection with the user
agent (http client). Hence, nginx effectively acts as a proxy server -
establishing a connection on both sides and proxying requests back and
forth to one or more service containers. Here are the steps:

# 1. Get and install the nginx web server. Install version 1.7.3
# 2. Start nginx with the nginx.conf that is in this directory.
# 3. Start flask using gunicorn (see the flask directory).

The configuration in this directory is set up to run everything on localhost, port 8443.
You will need to change the address before actual deployment on a production system.
Only secure connections are accepted by nginx, so you will need to point your browser at 
https://localhost:8443 to access the system.

