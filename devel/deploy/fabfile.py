import json
from fabric.api import sudo,local,env,execute,prompt,roles,put,settings,cd,run
from fabric.contrib.files import exists
import subprocess
import os
import time

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

def deploy():
    answer = prompt('Running on Amazon Web Services (y/n)?')
    if answer=='yes' or answer == 'y':
        execute(buildDatabaseAmazon)
    else:
        execute(buildDatabase)
    execute(buildServer)
    execute(firewallConfig)
    execute(configMSOD)
    execute(startMSOD)

def pack():
    local('cp ' + getProjectHome() + '/devel/certificates/cacert.pem ' + getProjectHome() + '/nginx/')
    local('cp ' + getProjectHome() + '/devel/certificates/privkey.pem '  + getProjectHome() + '/nginx/')
    local('tar -cvzf /tmp/flask.tar.gz -C ' + getProjectHome() + ' flask')
    local('tar -cvzf /tmp/nginx.tar.gz -C ' + getProjectHome() + ' nginx')
    local('tar -cvzf /tmp/services.tar.gz -C ' + getProjectHome() + ' services')
    local('tar -cvzf /tmp/unit-tests.tar.gz -C ' + getProjectHome() + ' unit-tests')
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

def cleanLogs() :
    sudo('rm -rf  /var/log/flask')
    sudo('rm -f /var/log/nginx/* /var/log/gunicorn/* /var/log/admin.log /var/log/spectrumbrowser.log ')
    sudo('rm -f /var/log/occupancy.log /var/log/streaming.log /var/log/monitoring.log /var/log/admin.log')

'''Clean spectrumbrowser webserver host'''
@roles('spectrumbrowser')
def cleanWebServer(): #build process for web server
    sudo("/sbin/service msod stop")
    with settings(warn_only=True):
        sudo('rm -rf  /var/log/flask')
        sudo('rm -f /var/log/nginx/* /var/log/gunicorn/* /var/log/admin.log /var/log/spectrumbrowser.log ')
        sudo('rm -f /var/log/occupancy.log /var/log/streaming.log /var/log/monitoring.log /var/log/admin.log')
        sudo('rm -rf /opt/Python-2.7.6 /opt/distribute-0.6.35')
        sudo('rm /usr/local/bin/python2.7 /usr/local/bin/pip2.7')
    cleanLogs()


'''Web Server Host Functions'''
@roles('spectrumbrowser')
def buildServer(): #build process for web server
    sbHome = getSbHome()
    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')
        sudo('mkdir -p ' + sbHome)
        sudo('chown -R spectrumbrowser ' + sbHome)
        sudo('mkdir -p /home/' + env.user + '/.msod/')
        sudo('service msod stop')
        cleanLogs()

    DB_HOST = env.roledefs['database']['hosts'][0]
    WEB_HOST = env.roledefs['spectrumbrowser']['hosts'][0]
    if  DB_HOST != WEB_HOST:
        sudo('yum -y update')
        sudo('yum groupinstall -y "Development tools"')
        sudo('yum install -y python-setuptools')
        sudo('yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel')

        put('rpmforge.repo', '/etc/yum.repos.d/rpmforge.repo', use_sudo=True)
        sudo('rpm --import http://apt.sw.be/RPM-GPG-KEY.dag.txt')
        sudo('yum install -y libffi-devel')
        sudo('rm /etc/yum.repos.d/rpmforge.repo')

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

    # Untar Services
    sudo('tar -xvzf /tmp/flask.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/nginx.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')
    sudo('tar -xvzf /tmp/distribute-0.6.35.tar.gz -C ' + '/opt')

    # Copy over the required files for install
    put('nginx.repo', '/etc/yum.repos.d/nginx.repo', use_sudo=True)
    put('MSODConfig.json.setup', '/home/' +  env.user + '/.msod/MSODConfig.json', use_sudo=True)
    put('MSODConfig.json.setup', sbHome + '/MSODConfig.json', use_sudo=True)
    put(getProjectHome() + '/devel/requirements/install_stack.sh', sbHome + '/install_stack.sh', use_sudo=True)
    put(getProjectHome() + '/devel/requirements/python_pip_requirements.txt', sbHome + '/python_pip_requirements.txt', use_sudo=True)
    put(getProjectHome() + '/devel/requirements/redhat_stack.txt', sbHome + '/redhat_stack.txt', use_sudo=True)
    put('setup-config.py', sbHome + '/setup-config.py', use_sudo=True)
    put(getProjectHome() + '/Makefile', sbHome + '/Makefile', use_sudo=True)
    put('Config.gburg.txt', sbHome + '/Config.txt', use_sudo=True) #TODO - customize initial configuration.

    # Install over python, pip, and distribution tools
    with cd('/opt/Python-2.7.6'):
        if exists('/usr/local/bin/python2.7'):
            run('echo ''python 2.7 found''')
        else:
            sudo("chown -R " + env.user + " /opt/Python-2.7.6")
            sudo('./configure')
            sudo('make altinstall')
            sudo('chown spectrumbrowser /usr/local/bin/python2.7')
    with cd('/opt/distribute-0.6.35'):
        if exists('/usr/local/bin/pip'):
            run('echo ''pip  found''')
        else:
            sudo('chown -R ' + env.user + ' /opt/distribute-0.6.35')
            sudo('/usr/local/bin/python2.7 setup.py  install')
            sudo('/usr/local/bin/easy_install-2.7 pip')

    with cd(sbHome):
        sudo('bash install_stack.sh')
        sudo('make REPO_HOME=' + sbHome + ' install')

    sudo('chown -R spectrumbrowser ' +sbHome)
    sudo('chgrp -R spectrumbrowser ' +sbHome)

    # start services on reboot.
    sudo('chkconfig --del memcached')
    sudo('chkconfig --del msod')
    sudo('chkconfig --del nginx')
    sudo('chkconfig --add nginx')
    sudo('chkconfig --level 3 nginx on')
    sudo('chkconfig --add memcached')
    sudo('chkconfig --level 3 memcached on')
    sudo('chkconfig --add msod')
    sudo('chkconfig --level 3 msod on')

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

@roles('spectrumbrowser')
def startMSOD():
    sudo('service nginx stop')
    #TODO -- for some reason can't start nginx as a service.
    #figure out why later.
    sudo('/usr/sbin/nginx -c /etc/nginx/nginx.conf')
    sudo('service msod stop')
    # For some reason need to start services individually from fabric.
    # Not a huge problem but need to investigate why.
    sudo('service memcached restart')
    time.sleep(5)
    sudo('service msod restart')
    sudo('service msod status')


@roles('spectrumbrowser')
def configMSOD():
    sudo('PYTHONPATH=/opt/SpectrumBrowser/flask:/usr/local/lib/python2.7/site-packages /usr/local/bin/python2.7 ' + getSbHome() + '/setup-config.py -host '\
          + os.environ.get('MSOD_DB_HOST') + ' -f ' + getSbHome() + '/Config.txt')

@roles('spectrumbrowser')
def deployTests(testDataLocation):
    if testDataLocation == None:
        raise Exception('Need test data')
    sudo('mkdir -p /spectrumdb/tests/test-data')
    sudo('tar -xvzf /tmp/unit-tests.tar.gz -C /spectrumdb/tests')
    with cd('/spectrumdb/tests'):
        for f in ['LTE_UL_DL_bc17_bc13_ts109_p1.dat','LTE_UL_DL_bc17_bc13_ts109_p2.dat','LTE_UL_DL_bc17_bc13_ts109_p3.dat','FS0714_173_7236.dat'] :
            put(testDataLocation + '/' + f, '/spectrumdb/tests/test-data/'+f,use_sudo = True)

@roles('spectrumbrowser')
def setupTestData():
    with cd('/spectrumdb'):
        sudo('PYTHONPATH=/opt/SpectrumBrowser/flask:/spectrumdb/tests/unit-tests:/usr/local/lib/python2.7/site-packages/ /usr/local/bin/python2.7 '+\
        ' /spectrumdb/tests/unit-tests/setup_test_sensors.py -t /spectrumdb/tests/test-data -p /spectrumdb/tests/unit-tests')


'''Database Server Host Functions'''
@roles('database')
def buildDatabase():
    sbHome = getSbHome()
    sudo('mkdir -p ' + sbHome)
    put('/tmp/services.tar.gz', '/tmp/services.tar.gz',use_sudo=True)
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)

    with settings(warn_only=True):
        sudo('rm -f /var/log/dbmonitoring.log')

    sudo('install -m 755 ' + sbHome + '/services/dbmonitor/ResourceMonitor.py /usr/bin/dbmonitor')
    sudo('install -m 755 ' + sbHome + '/services/dbmonitor/dbmonitoring-init /etc/init.d/dbmonitor')

    put('mongodb-org-2.6.repo', '/etc/yum.repos.d/mongodb-org-2.6.repo', use_sudo=True)
    sudo('yum -y install mongodb-org')
    put('mongod.conf','/etc/mongod.conf',use_sudo=True)
    sudo('chown mongod /etc/mongod.conf')
    sudo('chgrp mongod /etc/mongod.conf')
    sudo('mkdir -p /spectrumdb')
    sudo('chown  mongod /spectrumdb')
    sudo('chgrp  mongod /spectrumdb')

    DB_HOST = env.roledefs['database']['hosts'][0]
    WEB_HOST = env.roledefs['spectrumbrowser']['hosts'][0]
    if  DB_HOST != WEB_HOST:
        sudo('iptables -P INPUT ACCEPT')
        sudo('iptables -F')
        sudo('iptables -A INPUT -i lo -j ACCEPT')
        sudo('iptables -A INPUT -p tcp --dport 22 -j ACCEPT')
        sudo('iptables -A INPUT -s ' + WEB_HOST + ' -p tcp --dport 27017 -j ACCEPT')
        sudo('iptables -A INPUT -m state --state NEW,ESTABLISHED -j ACCEPT')
        sudo('iptables -A OUTPUT -d ' + WEB_HOST + ' -p tcp --sport 27017 -j ACCEPT')
        sudo('iptables -A OUTPUT -m state --state ESTABLISHED -j ACCEPT')
        sudo('iptables -P INPUT DROP')
        sudo('iptables -P FORWARD DROP')
        sudo('iptables -P OUTPUT ACCEPT')
        sudo('service iptables save')
        sudo('service iptables restart')

        with settings(warn_only=True):
            sudo('yum install -y policycoreutils-python')
            sudo('semanage port -a -t mongod_port_t -p tcp 27017')
            sudo('yum -y update')
            sudo('yum groupinstall -y "Development tools"')
            sudo('yum install -y python-setuptools')
            sudo('yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel')

        put('MSODConfig.json.setup', '/etc/msod/MSODConfig.json', use_sudo=True)

        put('/tmp/Python-2.7.6.tgz', '/tmp/Python-2.7.6.tgz',use_sudo=True)
        sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')

        put('/tmp/distribute-0.6.35.tar.gz' , '/tmp/distribute-0.6.35.tar.gz',use_sudo=True)
        sudo('tar -xvzf /tmp/distribute-0.6.35.tar.gz -C ' + '/opt')

        # Install over python, pip, and distribution tools
        with cd('/opt/Python-2.7.6'):
            if exists('/usr/local/bin/python2.7'):
                run('echo ''python 2.7 found''')
            else:
                sudo("chown -R " + env.user + " /opt/Python-2.7.6")
                sudo('./configure')
                sudo('make altinstall')
                sudo('chown spectrumbrowser /usr/local/bin/python2.7')
        with cd('/opt/distribute-0.6.35'):
            if exists('/usr/local/bin/pip'):
                run('echo ''pip  found''')
            else:
                sudo('chown -R ' + env.user + ' /opt/distribute-0.6.35')
                sudo('/usr/local/bin/python2.7 setup.py  install')
                sudo('/usr/local/bin/easy_install-2.7 pymongo')

    sudo('chkconfig --del mongod')
    sudo('chkconfig --add mongod')
    sudo('chkconfig --level 3 mongod on')
    sudo('chkconfig --del dbmonitor')
    sudo('chkconfig --add dbmonitor')
    sudo('chkconfig --level 3 dbmonitor on')
    sudo('service mongod restart')
    time.sleep(10)
    sudo('service dbmonitor restart')

def checkStatus():
    execute(checkMsodStatus)
    execute(checkDbStatus)

@roles('spectrumbrowser')
def checkMsodStatus():
    sudo('service memcached status')
    sudo('service msod status')

@roles('database')
def checkDbStatus():
    sudo('service mongod status')
    sudo('service dbmonitor status')

'''Amazon Server Host Functions'''
@roles('database')
def buildDatabaseAmazon(): #build process for db server
    sbHome = getSbHome()

    with settings(warn_only=True):
        sudo('rm -f /var/log/dbmonitoring.log')

    sudo('install -m 755 ' + sbHome + '/services/dbmonitor/dbmonitoring-bin /usr/bin/dbmonitor')
    sudo('install -m 755 ' + sbHome + '/services/dbmonitor/dbmonitoring-init /etc/init.d/dbmonitor')

    put('mongodb-org-2.6.repo', '/etc/yum.repos.d/mongodb-org-2.6.repo', use_sudo=True)
    sudo('yum -y install mongodb-org')
    sudo('service mongod stop')
    put('mongod.conf','/etc/mongod.conf',use_sudo=True)
    sudo('chown mongod /etc/mongod.conf')
    sudo('chgrp mongod /etc/mongod.conf')
    #NOTE: SPECIFIC to amazon deployment.
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

    sudo('chkconfig --del mongod')
    sudo('chkconfig --add mongod')
    sudo('chkconfig --level 3 mongod on')
    sudo('chkconfig --del dbmonitor')
    sudo('chkconfig --add dbmonitor')
    sudo('chkconfig --level 3 dbmonitor on')
    sudo('service mongod restart')
    time.sleep(10)
    sudo('service dbmonitor restart')
