import json
from fabric.api import *
import subprocess
import os

env.sudo_user = 'root'

def nist():
    env.roledefs = {
        'database' : {
            'hosts': ["0.0.0.0"],
        },
        'spectrumbrowser' : {
            'hosts': ["0.0.0.0"],
        }
    }
    env.user = 'mranga'

def ntia():
    env.roledefs = {
        'database' : {
            'hosts': ["0.0.0.0"],
        },
        'spectrumbrowser' : {
            'hosts': ["0.0.0.0"],
        }
    }
    env.user = 'khicks'

@roles('database')
def buildDatabase():
    #retrieve home directory and remove existing files
    sbHome = getSbHome()
    sudo("rm -rf " + sbHome)

    # add spectrumbrowser user if he does not exist
    with settings(warn_only=True):
        sudo("adduser --system spectrumbrowser")
    sudo("mkdir -p " + sbHome + "/data/db")
    put("mongodb-org-2.6.repo", sbHome, use_sudo=True)
    sudo("yum -y install mongodb-org")
    
    #config file for mongo. set dpath uncomment bind ip
    
    
    sudo("service mongod restart")

@roles('spectrumbrowser')
def buildServer():
    #retrieve home directory and remove existing files
    sbHome = getSbHome()
    sudo("rm -rf " + sbHome)
    sudo("rm -rf /var/log/flask")
    sudo("rm -f /var/log/nginx/*")
    sudo("rm -f /var/log/gunicorn/*")
    sudo("rm -f /var/log/occupancy.log")
    sudo("rm -f /var/log/streaming.log")

    # add spectrumbrowser user if he does not exist
    with settings(warn_only=True):
        sudo("adduser --system spectrumbrowser")

    # create the spectrumbrowser home and give env.user permissions
    sudo("mkdir -p " + sbHome)
    sudo("chown -R spectrumbrowser " + sbHome)
    sudo("chown -R " + env.user + " " + sbHome)
    sudo("chgrp -R " + env.user + " " + sbHome)

    # copy pieces from the development tree to the target host
    put("/tmp/flask.tar.gz", "/tmp/flask.tar.gz")
    put("/tmp/nginx.tar.gz", "/tmp/nginx.tar.gz")
    put("/tmp/services.tar.gz", "/tmp/services.tar.gz")
    sudo("tar -xvzf /tmp/flask.tar.gz -C " + sbHome)
    sudo("tar -xvzf /tmp/nginx.tar.gz -C " + sbHome)
    sudo("tar -xvzf /tmp/services.tar.gz -C " + sbHome)

    # copy the repo directories to yum
    put("nginx.repo", "/etc/yum.repos.d/nginx.repo", use_sudo=True)
    put("MSODConfig.json.setup", sbHome + "/MSODConfig.json", use_sudo=True)
    put("python_pip_requirements.txt", sbHome + "/python_pip_requirements.txt", use_sudo=True)
    put("install_stack.sh", sbHome + "/install_stack.sh", use_sudo=True)
    put("redhat_stack.txt", sbHome + "/redhat_stack.txt", use_sudo=True)
    put("get-pip.py", sbHome + "/get-pip.py", use_sudo=True)
    put("setup-config.py", sbHome + "/setup-config.py", use_sudo=True)
    put("Config.gburg.txt", sbHome + "/Config.gburg.txt", use_sudo=True)
    put(getProjectHome() + "/Makefile", sbHome + "/Makefile", use_sudo=True)

    dbrole = env.roledefs["database"]
    dbhost = dbrole["hosts"]

    # install the pieces
    with cd(sbHome):
        sudo("sh install_stack.sh")
        sudo("make REPO_HOME=" + sbHome + " install")
        sudo("python setup-config.py -host " + dbhost)

def getProjectHome():
    command = ["git", "rev-parse", "--show-toplevel"]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()

def getSbHome():
    return json.load(open(getProjectHome() + "/MSODConfig.json"))["SPECTRUM_BROWSER_HOME"]

def pack():
    # create a new distribution, pack only the pieces we need
    local('tar -cvzf /tmp/flask.tar.gz ' + '-C ' + getProjectHome() + ' flask')
    local('tar -cvzf /tmp/nginx.tar.gz ' + '-C ' + getProjectHome() + ' nginx')
    local('tar -cvzf /tmp/services.tar.gz ' + '-C ' + getProjectHome() + ' services')

def deploy():
    execute(buildDatabase)
    execute(buildServer)
