import json
from fabric.api import *
import subprocess
import os


env.user = 'root'

# Right now everything runs on a single host. We'll split into two hosts
# (one for DB and one for server later)
if os.environ.get("MSOD_WEB_HOST") == None:
    print  "Please set the environment variable MSOD_WEB_HOST to the IP address where you wish to deploy."
    os._exit(1)
env.hosts = [os.environ.get("MSOD_WEB_HOST")]
#the locations where things get deployed. Edit this.
#spectrumbrowser is the location for the spectrumbrowser
#database is the location for the database
env.roledefs = {'spectrumbrowser':["129.6.142.157"], 'database':["129.6.142.157"]}

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
    local('tar -cvzf /tmp/flask.tar.gz ../flask')
    local('tar -cvzf /tmp/nginx.tar.gz ../nginx')
    local('tar -cvzf /tmp/services.tar.gz ../services')

def deploy():
    sbHome = getSbHome()
    #Add spectrubrowser user if he does not exist.
    with settings(warn_only=True):
        run("adduser spectrumbrowser")
    #create the spectrumbrowser home
    run("mkdir -p "+sbHome)
    #Copy various pieces from the development tree to the target host
    put("/tmp/services.tar.gz","/tmp/services.tar.gz")
    put("/tmp/flask.tar.gz","/tmp/flask.tar.gz")
    put("/tmp/nginx.tar.gz","/tmp/nginx.tar.gz")
    put("../MSODConfig.json",sbHome+"/MSODConfig.json")
    run("tar -xvzf /tmp/flask.tar.gz -C " + sbHome)
    run("tar -xvzf /tmp/nginx.tar.gz -C " + sbHome)
    run("tar -xvzf /tmp/services.tar.gz -C " + sbHome)
    #Copy the repo directories to yum
    put("nginx.repo","/etc/yum.repos.d/nginx.repo")
    put("mongodb-org-2.6.repo", "/etc/yum.repos.d/mongodb-org-2.6.repo")
    put("python_pip_requirements.txt", sbHome + "/python_pip_requirements.txt")
    put("install_stack.sh",sbHome + "/install_stack.sh")
    put("redhat_stack.txt",sbHome + "/redhat_stack.txt")
    put("get-pip.py",sbHome + "/get-pip.py")
    run("chown -R spectrumbrowser " +sbHome)
    put(getProjectHome()+"/Makefile", sbHome + "/Makefile")
    #install the pieces.
    with cd(sbHome):
        run("sh install_stack.sh")
        run("make REPO_HOME=" + sbHome + " install")
    #Run IPTABLES commands on the instance
    run("iptables -A INPUT -p tcp --dport 9000 -j ACCEPT")
    run("iptables -A INPUT -p tcp --dport 9001 -j ACCEPT")
    run("iptables -A INPUT -p tcp --dport 443 -j ACCEPT")
    run("iptables -A INPUT -j DROP")
    run("/sbin/service/iptables restart")
