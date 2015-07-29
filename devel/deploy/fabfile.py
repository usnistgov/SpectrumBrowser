import json
from fabric.api import *
from fabric.contrib.files import exists
import subprocess
import os

env.sudo_user = 'root'

if os.environ.get('MSOD_DB_HOST') == None:
    print('Please set the environment variable MSOD_DB_HOST to the IP address where your DB Server is located.')
    os._exit(1)
if os.environ.get('MSOD_WEB_HOST') == None:
    print('Please set the environment variable MSOD_WEB_HOST to the IP address where your WEB Server is located.')
    os._exit(1)

env.roledefs = {
    'database' : { 
        'hosts': [os.environ.get('MSOD_DB_HOST')],
    },
    'spectrumbrowser' : { 
        'hosts': [os.environ.get('MSOD_WEB_HOST')]
    }
}

def pack():
    local('cp ' + getProjectHome() + '/devel/certificates/cacert.pem ' + getProjectHome() + '/nginx/')
    local('cp ' + getProjectHome() + '/devel/certificates/privkey.pem '  + getProjectHome() + '/nginx/')
    local('tar -cvzf /tmp/flask.tar.gz -C ' + getProjectHome() + ' flask')
    local('tar -cvzf /tmp/nginx.tar.gz -C ' + getProjectHome() + ' nginx')
    local('tar -cvzf /tmp/services.tar.gz -C ' + getProjectHome() + ' services')
    if not os.path.exists('/tmp/Python-2.7.6.tgz'):
        local('wget --no-check-certificate https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz --directory-prefix=/tmp')
    if not os.path.exists('/tmp/distribute-0.6.35.tar.gz'):
        local ('wget --no-check-certificate http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz --directory-prefix=/tmp')

def getSbHome():
    return json.load(open(getProjectHome() + '/MSODConfig.json'))['SPECTRUM_BROWSER_HOME']

def getProjectHome():
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()

def deploy():
    execute(buildServer)
    execute(firewallConfig)
    answer = prompt('Running on Amazon Web Services (y/n)?')
    if answer=='yes' or answer == 'y':
        execute(buildDatabaseAmazon)
    else:
        execute(buildDatabase)
    execute(configMSOD)
    execute(startMSOD)

@roles('database')
def buildDatabase():
    put('mongodb-org-2.6.repo', '/etc/yum.repos.d/mongodb-org-2.6.repo', use_sudo=True)
    sudo('yum -y install mongodb-org')

    DB_HOST = env.roledefs['database']['hosts']
    WEB_HOST = env.roledefs['spectrumbrowser']['hosts']
    
    if not DB_HOST == WEB_HOST:   
        sudo('iptables -F')
        sudo('iptables -A INPUT -s ' + WEB_HOST + ' -p tcp --dport 27017 -j ACCEPT')
        sudo('iptables -A INPUT -m state --state NEW,ESTABLISHED -j ACCEPT')
        sudo('iptables -A OUTPUT -d ' + WEB_HOST + ' -p tcp --sport 27017 -j ACCEPT')
        sudo('iptables -A OUPUT -m state --state ESTABLISHED -j ACCEPT')
        sudo('service iptables save')
        sudo('service iptables restart')

    sudo('service mongod restart')

@roles('spectrumbrowser')
def buildServer():
    sbHome = getSbHome()
    sudo('rm -rf ' + sbHome)
    sudo('rm -rf /var/log/flask')
    sudo('rm -f /var/log/nginx/*')
    sudo('rm -f /var/log/gunicorn/*')
    sudo('rm -f /var/log/occupancy.log')
    sudo('rm -f /var/log/streaming.log')

    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')
        sudo('mkdir -p ' + sbHome)
        sudo('chown -R spectrumbrowser ' + sbHome)

    # Copy over the services, nginx, and flask.
    put('/tmp/flask.tar.gz', '/tmp/flask.tar.gz',use_sudo=True)
    put('/tmp/nginx.tar.gz', '/tmp/nginx.tar.gz',use_sudo=True)
    put('/tmp/services.tar.gz', '/tmp/services.tar.gz',use_sudo=True)
    put('/tmp/Python-2.7.6.tgz', '/tmp/Python-2.7.6.tgz',use_sudo=True)
    put('/tmp/distribute-0.6.35.tar.gz' , '/tmp/distribute-0.6.35.tar.gz',use_sudo=True)

    # Copy over the certificates.
    sudo('mkdir -p ' + getSbHome() + '/certificates')
    put(getProjectHome() + '/devel/certificates/privkey.pem' , getSbHome() + '/certificates/privkey.pem',use_sudo = True )
    put(getProjectHome() + '/devel/certificates/cacert.pem' , getSbHome() + '/certificates/cacert.pem' , use_sudo = True)
    put(getProjectHome() + '/devel/certificates/dummy.crt', getSbHome() + '/certificates/dummy.crt', use_sudo = True)

    sudo('tar -xvzf /tmp/flask.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/nginx.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')
    sudo('tar -xvzf /tmp/distribute-0.6.35.tar.gz -C ' + '/opt')

    # set the right user permissions so we can cd to the directories we need.
    sudo('chown -R ' + env.user + ' /opt/distribute-0.6.35')

    # Copy over the required files for install
    put('nginx.repo', '/etc/yum.repos.d/nginx.repo', use_sudo=True)
    put('MSODConfig.json.setup', sbHome + '/MSODConfig.json', use_sudo=True)
    put(getProjectHome() + '/devel/requirements/install_stack.sh', sbHome + '/install_stack.sh', use_sudo=True)
    put(getProjectHome() + '/devel/requirements/python_pip_requirements.txt', sbHome + '/python_pip_requirements.txt', use_sudo=True)
    put(getProjectHome() + '/devel/requirements/redhat_stack.txt', sbHome + '/redhat_stack.txt', use_sudo=True)
    put('setup-config.py', sbHome + '/setup-config.py', use_sudo=True)
    put('msod.sudo','/etc/sudoers.d/msod', use_sudo=True)
    sudo("chown root /etc/sudoers.d/msod")
    sudo("chgrp root /etc/sudoers.d/msod")
    put(getProjectHome() + '/Makefile', sbHome + '/Makefile', use_sudo=True)
    put('Config.gburg.txt', sbHome + '/Config.txt', use_sudo=True) #TODO - customize initial configuration.
    
    # Copy over python, pip, and distribution tools if needed   
    if exists('/usr/local/bin/python2.7'):
        run('echo ''python 2.7 found''')
    else:
        with cd('/opt/Python-2.7.6'):        
            sudo('./configure')
            sudo('make altinstall')
            sudo('chown spectrumbrowser /usr/local/bin/python2.7')
        with cd('/opt/distribute-0.6.35'):
            sudo('/usr/local/bin/python2.7 setup.py  install')
            sudo('/usr/local/bin/easy_install-2.7 pip')

    with cd(sbHome):
        sudo('sh install_stack.sh')
        sudo('make REPO_HOME=' + sbHome + ' install')

    sudo('chown -R spectrumbrowser ' +sbHome)
    sudo('chgrp -R spectrumbrowser ' +sbHome)

@roles('spectrumbrowser')
def firewallConfig():
    #Run IPTABLES commands on the instance
    sudo('iptables -P INPUT ACCEPT')
    sudo('iptables -F')
    sudo('iptables -A INPUT -i lo -j ACCEPT')
    sudo('iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 22 -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 443 -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 9000 -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 9001 -j ACCEPT')
    sudo('iptables -P INPUT DROP')
    sudo('iptables -P FORWARD DROP')
    sudo('iptables -P OUTPUT ACCEPT')
    sudo('iptables -L -v')
    sudo('service iptables save')
    sudo('service iptables restart')

@roles('database')
def buildDatabaseAmazon():
    put('mongodb-org-2.6.repo', '/etc/yum.repos.d/mongodb-org-2.6.repo', use_sudo=True)
    sudo('yum -y install mongodb-org')
    sudo('service mongod stop')
    put('mongod.conf','/etc/mongod.conf',use_sudo=True)
    sudo('chown mongod /etc/mongod.conf')
    sudo('chgrp mongod /etc/mongod.conf')

    answer = prompt('Create partition for DB (y/n)?')
    if answer == 'y' or answer == 'yes':
        with settings(warn_only=True):
            sudo('umount /spectrumdb')
        # These settings work for amazon. Customize this.
        sudo('mkfs -t ext4 /dev/xvdf')
    #Put all the ebs data on /spectrumdb
    if exists('/spectrumdb'):
        run('echo ''Found /spectrumdb''')
    else:
        sudo('mkdir /spectrumdb')
    sudo('chown  mongod /spectrumdb')
    sudo('chgrp  mongod /spectrumdb')

    with settings(warn_only=True):
        sudo('mount /dev/xvdf /spectrumdb')

    sudo('service mongod restart')

@roles('spectrumbrowser')
def startMSOD():
    sudo('service nginx stop')
    sudo('service msod restart')
    #TODO -- for some reason can't start nginx as a service.
    #figure out why later.
    sudo('/usr/sbin/nginx -c /etc/nginx/nginx.conf')

@roles('database')
def startDB():
    sudo('service mongod restart')

@roles('spectrumbrowser')
def configMSOD():
    sudo('PYTHONPATH=/opt/SpectrumBrowser/flask:/usr/local/lib/python2.7/site-packages /usr/local/bin/python2.7 ' + getSbHome() + '/setup-config.py -host '\
          + os.environ.get('MSOD_DB_HOST') + ' -f ' + getSbHome() + '/Config.txt')

