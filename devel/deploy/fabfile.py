import json
from fabric.api import *
import subprocess
import os


env.user = 'mranga'

# Right now everything runs on a single host. We'll split into two hosts
# (one for DB and one for server later)
if os.environ.get("MSOD_WEB_HOST") == None:
    print  "Please set the environment variable MSOD_WEB_HOST to the IP address where you wish to deploy."
    os._exit(1)
env.hosts = [os.environ.get("MSOD_WEB_HOST")]
#the locations where things get deployed. Edit this.
#spectrumbrowser is the location for the spectrumbrowser
#database is the location for the database. TODO - finish this for a multi site deployment.
#env.roledefs = {'spectrumbrowser':["129.6.142.157"], 'database':["129.6.142.157"]}

def getProjectHome():
    command = ["git", "rev-parse", "--show-toplevel"]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = p.communicate()
    return out.strip()

def getSbHome():
    return json.load(open(getProjectHome() + "/MSODConfig.json"))["SPECTRUM_BROWSER_HOME"]

def pack():
    # create a new distribution
    # pack only the pieces we need.
    local ("cp "+ getProjectHome()+ "/devel/certificates/cacert.pem " + getProjectHome() + "/nginx/")
    local ("cp " + getProjectHome() + "/devel/certificates/privkey.pem "  + getProjectHome() + "/nginx/")
    local('tar -cvzf /tmp/flask.tar.gz '+ '-C ' + getProjectHome() + ' flask ')
    local('tar -cvzf /tmp/nginx.tar.gz ' + '-C ' + getProjectHome() + ' nginx' )
    local('tar -cvzf /tmp/services.tar.gz '+ '-C ' + getProjectHome() + ' services')

def deploy():
    sbHome = getSbHome()
    run("sudo rm -rf " + sbHome)
    run("sudo rm -rf /var/log/flask/")
    run("sudo rm -f /var/log/nginx/*")
    run("sudo rm -f /var/log/gunicorn/*")
    run("sudo rm -f /var/log/occupancy.log")
    run("sudo rm -f /var/log/streaming.log")
    #Add spectrubrowser user if he does not exist.
    with settings(warn_only=True):
        run("sudo adduser spectrumbrowser")
    #create the spectrumbrowser home
    run("sudo mkdir -p "+sbHome)
    run("sudo chown -R " + env.user + " " + sbHome)
    run("sudo chgrp -R " + env.user + " " + sbHome)
    # Logging directories.
    #run("sudo mkdir -p /var/log/flask")
    #run("sudo chown " + env.user + " /var/log/flask")
    #run("sudo chgrp " + env.user + " /var/log/flask")
    # Copy the temp msod config file
    run("mkdir -p /home/"+ env.user + "/.msod")
    put("MSODConfig.json.setup", "/home/" + env.user + "/.msod/MSODConfig.json")
    # Copy our certs.
    #Copy various pieces from the development tree to the target host
    put("/tmp/services.tar.gz","/tmp/services.tar.gz")
    put("/tmp/flask.tar.gz","/tmp/flask.tar.gz")
    put("/tmp/nginx.tar.gz","/tmp/nginx.tar.gz")
    put(getProjectHome() + "/MSODConfig.json",sbHome+"/MSODConfig.json")
    run("sudo tar -xvzf /tmp/flask.tar.gz -C " + sbHome)
    run("sudo tar -xvzf /tmp/nginx.tar.gz -C " + sbHome)
    run("sudo tar -xvzf /tmp/services.tar.gz -C " + sbHome)
    run("sudo chown -R " + env.user + " " + sbHome)
    #Copy the repo directories to yum
    put ("nginx.repo","/tmp/nginx.repo")
    run("sudo mv /tmp/nginx.repo /etc/yum.repos.d/nginx.repo")
    put("mongodb-org-2.6.repo", "/tmp/mongodb-org-2.6.repo")
    run("sudo mv /tmp/mongodb-org-2.6.repo /etc/yum.repos.d/mongodb-org-2.6.repo")
    put("python_pip_requirements.txt", sbHome + "/python_pip_requirements.txt")
    put("install_stack.sh",sbHome + "/install_stack.sh")
    put("redhat_stack.txt",sbHome + "/redhat_stack.txt")
    put("get-pip.py",sbHome + "/get-pip.py")
    put("setup-config.py",sbHome+"/setup-config.py")
    put("Config.gburg.txt",sbHome + "/Config.gburg.txt")
    put(getProjectHome()+"/Makefile", sbHome + "/Makefile")
    #install the pieces.
    with cd(sbHome):
        run("sudo sh install_stack.sh")
        run("sudo make REPO_HOME=" + sbHome + " install")
        run("sudo /sbin/service mongod restart")
        run("sleep 10")
        run("python setup-config.py -host "+ os.environ.get("MSOD_WEB_HOST"))
    # BUG - For some reason, nginx gives me a "bad gateway"
    # when I bring it up as a service. We need to fix this.
    run("sudo /sbin/service nginx stop")
    #WORKAROUND - just start nginx directly.Not sure why it
    #is flaky when started as a service.
    run("sudo /usr/sbin/nginx -c /etc/nginx/nginx.conf")
    run("sudo chown -R spectrumbrowser " +sbHome)
    run("sudo chgrp -R spectrumbrowser " +sbHome)
    #Run IPTABLES commands on the instance
    run("sudo iptables -P INPUT ACCEPT")
    run("sudo iptables -F")
    run("sudo iptables -A INPUT -i lo -j ACCEPT")
    run("sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
    run("sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT")
    run("sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT")
    run("sudo iptables -A INPUT -p tcp --dport 9000 -j ACCEPT")
    run("sudo iptables -A INPUT -p tcp --dport 9001 -j ACCEPT")
    run("sudo iptables -P INPUT DROP")
    run("sudo iptables -P FORWARD DROP")
    run("sudo iptables -P OUTPUT ACCEPT")
    run("sudo iptables -L -v")
    run("sudo /sbin/service iptables save")
    run("sudo /sbin/service iptables restart")
    run("sudo /sbin/service msod restart")
    #BUGBUG - this restart should not be necesssary. Investigate this.
    run("sudo /sbin/service spectrumbrowser restart")
