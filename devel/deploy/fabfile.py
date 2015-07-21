import json
from fabric.api import *
from fabric.contrib.files import exists
import subprocess
import os

env.sudo_user = 'root'

# Note: set MSOD_DB_HOST == MSOD_WEB_HOST if you want everything to be configured on a single host.
# Note: use the -u flag when invoking flask for user with a login account on the target host.
env.roledefs = {
    'database' : { 'hosts': [os.environ.get("MSOD_DB_HOST")] },
    'spectrumbrowser' : { 'hosts': [os.environ.get("MSOD_WEB_HOST")] }
}

def pack(): #create a new distribution, pack only the pieces we need
    local ("cp "+ getProjectHome()+ "/devel/certificates/cacert.pem " + getProjectHome() + "/nginx/")
    local ("cp " + getProjectHome() + "/devel/certificates/privkey.pem "  + getProjectHome() + "/nginx/")
    local('tar -cvzf /tmp/flask.tar.gz -C ' + getProjectHome() + ' flask ')
    local('tar -cvzf /tmp/nginx.tar.gz -C ' + getProjectHome() + ' nginx ')
    local('tar -cvzf /tmp/services.tar.gz -C ' + getProjectHome() + ' services ')

    if not os.path.exists("/tmp/Python-2.7.6.tgz"):
        local("wget --no-check-certificate https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz --directory-prefix=/tmp")

    if not os.path.exists("/tmp/distribute-0.6.35.tar.gz"):
        local ("wget --no-check-certificate http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz --directory-prefix=/tmp")


def getSbHome(): #returns the default directory of installation
    return json.load(open(getProjectHome() + '/MSODConfig.json'))["SPECTRUM_BROWSER_HOME"]


def getProjectHome(): #finds the default directory of installation
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()

def deploy(): #build process for target hosts
    execute(buildDatabase)
    execute(buildServer)
    execute(firewallConfig)
    execute(startDB)
    execute(configMSOD)
    execute(startMSOD)

@roles('spectrumbrowser')
def firewallConfig():
    #Run IPTABLES commands on the instance
    sudo("iptables -P INPUT ACCEPT")
    sudo("iptables -F")
    sudo("iptables -A INPUT -i lo -j ACCEPT")
    sudo("iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
    sudo("iptables -A INPUT -p tcp --dport 22 -j ACCEPT")
    sudo("iptables -A INPUT -p tcp --dport 443 -j ACCEPT")
    sudo("iptables -A INPUT -p tcp --dport 9000 -j ACCEPT")
    sudo("iptables -A INPUT -p tcp --dport 9001 -j ACCEPT")
    sudo("iptables -P INPUT DROP")
    sudo("iptables -P FORWARD DROP")
    sudo("iptables -P OUTPUT ACCEPT")
    sudo("iptables -L -v")
    sudo("/sbin/service iptables save")
    sudo("/sbin/service iptables restart")

@roles('spectrumbrowser')
def startMSOD():
    sudo("/sbin/service msod restart")

@roles('database')
def startDB():
    sudo("/sbin/service mongod restart")

@roles('database')
def buildDatabase(): #build process for db server
    sbHome = getSbHome()
    sudo('rm -rf ' + sbHome)

    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')

    sudo('mkdir -p ' + sbHome + '/data/db')
    put('mongodb-org-2.6.repo', "/etc/yum.repos.d/mongodb-org-2.6.repo", use_sudo=True)
    sudo('yum -y install mongodb-org')
    sudo('/sbin/service mongod restart')

@roles('spectrumbrowser')
def configMSOD():
    sbHome = getSbHome()

    with cd(sbHome):
        # Note that this setup is run from the web server.
        # It will contact the db host to configure it so that should be running
        # prior to this script running. Note that MSOD_DB_HOST is the location where mobgodb is running.
        sudo("PYTHONPATH=/opt/SpectrumBrowser/flask:/usr/local/lib/python2.7/site-packages/ /usr/local/bin/python2.7 setup-config.py -host "+ os.environ.get("MSOD_DB_HOST"))



@roles('spectrumbrowser')
def buildServer(): #build process for web server
    sbHome = getSbHome()
    sudo('rm -rf /var/log/flask')
    sudo('rm -f /var/log/nginx/*')
    sudo('rm -f /var/log/gunicorn/*')
    sudo('rm -f /var/log/occupancy.log')
    sudo('rm -f /var/log/streaming.log')

    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')
        sudo('mkdir -p ' + sbHome)
        sudo('chown -R spectrumbrowser ' + sbHome)

    put('/tmp/flask.tar.gz', '/tmp/flask.tar.gz',use_sudo=True)
    put('/tmp/nginx.tar.gz', '/tmp/nginx.tar.gz',use_sudo=True)
    put('/tmp/services.tar.gz', '/tmp/services.tar.gz',use_sudo=True)
    put('/tmp/Python-2.7.6.tgz', '/tmp/Python-2.7.6.tgz',use_sudo=True)
    put('/tmp/distribute-0.6.35.tar.gz' , '/tmp/distribute-0.6.35.tar.gz',use_sudo=True)
    sudo('tar -xvzf /tmp/flask.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/nginx.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')
    sudo('tar -xvzf /tmp/distribute-0.6.35.tar.gz -C ' + '/opt')

    # set the right user permissions so we can cd to the directories we need.
    sudo("chown -R " + env.user + " /opt/distribute-0.6.35")

    put('nginx.repo', '/etc/yum.repos.d/nginx.repo', use_sudo=True)
    put('MSODConfig.json.setup', sbHome + '/MSODConfig.json', use_sudo=True)
    put('python_pip_requirements.txt', sbHome + '/python_pip_requirements.txt', use_sudo=True)
    put('install_stack.sh', sbHome + '/install_stack.sh', use_sudo=True)
    put('redhat_stack.txt', sbHome + '/redhat_stack.txt', use_sudo=True)
    put('setup-config.py', sbHome + '/setup-config.py', use_sudo=True)
    put('msod.sudo',"/etc/sudoers.d/msod",use_sudo=True)
    sudo('chown root /etc/sudoers.d/msod')
    # TODO - This needs to be configurable.
    put('Config.gburg.txt', sbHome + '/Config.gburg.txt', use_sudo=True)
    put(getProjectHome() + '/Makefile', sbHome + '/Makefile', use_sudo=True)
    #install the right python version.

    with cd('/opt/Python-2.7.6'):
        if exists('/usr/local/bin/python2.7'):
            run("echo 'python 2.7 found'")
        else:
            sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')
            sudo("chown -R " + env.user + " /opt/Python-2.7.6")
            sudo('./configure')
            sudo('make altinstall')
            sudo("chown spectrumbrowser /usr/local/bin/python2.7")

    # install the distribution tools (including pip)
    with cd('/opt/distribute-0.6.35'):
        sudo("/usr/local/bin/python2.7 setup.py  install")
        sudo("/usr/local/bin/easy_install-2.7 pip")

    with cd(sbHome):
        sudo('sh install_stack.sh')
        sudo('make REPO_HOME=' + sbHome + ' install')
        sudo("chown -R spectrumbrowser /usr/local/lib/python2.7")
        sudo("chgrp -R spectrumbrowser /usr/local/lib/python2.7")
        sudo("chmod -R go+rX /usr/local/lib/python2.7/")


    sudo("chown -R spectrumbrowser " +sbHome)
    sudo("chgrp -R spectrumbrowser " +sbHome)

@roles('spectrumbrowser')
def startSb():
   sudo("/sbin/service nginx restart")
   sudo("/sbin/service spectrumbrowser restart")

