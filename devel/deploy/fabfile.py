import json
from fabric.api import sudo, local, env, execute, prompt, roles, put, settings, cd, run
from fabric.contrib.files import exists
import subprocess
import os
import time
from fabric.network import ssh

ssh.util.log_to_file("paramiko.log", 10)

env.sudo_user = 'root'

if os.environ.get('MSOD_DB_HOST') is None:
    print(
        'Please set the environment variable MSOD_DB_HOST to the IP address where your DB Server is located.'
    )
    os._exit(1)
if os.environ.get('MSOD_WEB_HOST') is None:
    print(
        'Please set the environment variable MSOD_WEB_HOST to the IP address where your WEB Server is located.'
    )
    os._exit(1)

env.roledefs = {
    'database': {
        'hosts': [os.environ.get('MSOD_DB_HOST')],
    },
    'spectrumbrowser': {
        'hosts': [os.environ.get('MSOD_WEB_HOST')]
    }
}


def deploy():
    ''' Deploy a system on $MSOD_WEB_HOST and a database on $MSOD_DB_HOST '''
    global mongodbAnswer
    mongodbAnswer = 'n'
    aideAnswer = prompt('Setup Aide IDS after installation complete (y/n)?')
    amazonAnswer = prompt('Running on Amazon Web Services (y/n)?')
    mongodbAnswer = prompt('Install Enterprise Mongodb (y/n)?')
    execute(buildServer)
    if amazonAnswer == 'yes' or amazonAnswer == 'y':
        execute(buildDatabaseAmazon)
    else:
        execute(buildDatabase)
    execute(firewallConfig)
    execute(configMSOD)
    if aideAnswer == 'yes' or aideAnswer == 'y':
        print "This takes a while..."
        execute(setupAide)
    execute(startMSOD)

@roles('spectrumbrowser')
def update():
    ''' Update a system on $MSOD_WEB_HOST and a database on $MSOD_DB_HOST '''
    # Zip Needed Services locally
    sbHome = getSbHome()
    put('/tmp/flask.tar.gz', '/tmp/flask.tar.gz', use_sudo=True)
    put('/tmp/nginx.tar.gz', '/tmp/nginx.tar.gz', use_sudo=True)
    put('/tmp/services.tar.gz', '/tmp/services.tar.gz', use_sudo=True)
    # Unzip Needed Services on target
    sudo('tar -xvzf /tmp/flask.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/nginx.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)
    with cd(sbHome):
        sudo('make REPO_HOME=' + sbHome + ' install')
    # Copy Needed Files
    put('mongod.conf', '/etc/mongod.conf', use_sudo=True)

    # Update Users and Permission
    sudo('chown mongod /etc/mongod.conf')
    sudo('chgrp mongod /etc/mongod.conf')
    sudo('chown mongod /spectrumdb')
    sudo('chgrp mongod /spectrumdb')
    sudo('chown -R spectrumbrowser ' + sbHome)
    sudo('service dbmonitor restart')
    execute(startMSOD)


@roles('spectrumbrowser')
def buildServer():
    ''' Set up the web service on target $MSOD_WEB_HOST '''
    sbHome = getSbHome()
    localHome = getProjectHome()

    # Create Needed Directories
    sudo('mkdir -p ' + sbHome + ' /home/' + env.user + '/.msod/ /root/.msod/')
    sudo('mkdir -p ' + sbHome + '/flask/static/spectrumbrowser/generated/')
    sudo('mkdir -p ' + getSbHome() + '/certificates')

    # Create Users and Permissions
    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')
        sudo('chown -R spectrumbrowser ' + sbHome)

    # Copy Needed Files
    if not exists(sbHome + '/certificates/privkey.pem'):
        print "Using a dummy private key"
        put(localHome + '/devel/certificates/privkey.pem',
            sbHome + '/certificates/privkey.pem',
            use_sudo=True)
    if not exists(sbHome + '/certificates/cacert.pem'):
        put(localHome + '/devel/certificates/cacert.pem',
            sbHome + '/certificates/cacert.pem',
            use_sudo=True)
    if not exists(sbHome + '/certificates/sslcert.txt'):
        print "Using a dummy certificatey"
        put(localHome + '/devel/certificates/dummy.crt',
            sbHome + '/certificates/sslcert.txt',
            use_sudo=True)
    # For the python SSL connections still use the dummy certs. TODO -- check this.
    put(localHome + '/devel/certificates/dummy.crt',
        sbHome + '/certificates/dummy.crt',
        use_sudo=True)
    put(localHome + '/devel/certificates/privkey.pem',
        sbHome + '/certificates/dummyprivkey.pem',
        use_sudo=True)
    put(localHome + '/devel/requirements/python_pip_requirements.txt',
        sbHome + '/python_pip_requirements.txt',
        use_sudo=True)
    put(localHome + '/devel/requirements/install_stack.sh',
        sbHome + '/install_stack.sh',
        use_sudo=True)
    put(localHome + '/devel/requirements/redhat_stack.txt',
        sbHome + '/redhat_stack.txt',
        use_sudo=True)
    put('MSODConfig.json.setup', '/root/.msod/MSODConfig.json', use_sudo=True)
    put('MSODConfig.json.setup', sbHome + '/MSODConfig.json', use_sudo=True)
    put('setup-config.py', sbHome + '/setup-config.py', use_sudo=True)
    put(localHome + '/Makefile', sbHome + '/Makefile', use_sudo=True)
    put('nginx.repo', '/etc/yum.repos.d/nginx.repo', use_sudo=True)
    put('Config.gburg.txt',
        sbHome + '/Config.txt',
        use_sudo=True)  #TODO - customize initial configuration.

    # Zip Needed Services locally
    put('/tmp/flask.tar.gz', '/tmp/flask.tar.gz', use_sudo=True)
    put('/tmp/nginx.tar.gz', '/tmp/nginx.tar.gz', use_sudo=True)
    put('/tmp/services.tar.gz', '/tmp/services.tar.gz', use_sudo=True)
    put('../requirements/Python-2.7.6.tgz',
        '/tmp/Python-2.7.6.tgz',
        use_sudo=True)
    put('../requirements/distribute-0.6.35.tar.gz',
        '/tmp/distribute-0.6.35.tar.gz',
        use_sudo=True)

    # Unzip Needed Services on target
    sudo('tar -xvzf /tmp/flask.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/nginx.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')
    sudo('tar -xvzf /tmp/distribute-0.6.35.tar.gz -C ' + '/opt')

    DB_HOST = env.roledefs['database']['hosts'][0]
    WEB_HOST = env.roledefs['spectrumbrowser']['hosts'][0]

    # Install All Utilities
    # Note: This needs to be there on the web server before python can be built.
    sudo('yum groupinstall -y "Development tools" --skip-broken')
    sudo(
        'yum install -y python-setuptools tk-devel gdbm-devel db4-devel libpcap-devel xz-devel')
    sudo(
        'yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel')
    put('rpmforge.repo', '/etc/yum.repos.d/rpmforge.repo', use_sudo=True)
    sudo('rpm --import http://apt.sw.be/RPM-GPG-KEY.dag.txt')
    sudo('yum install -y libffi-devel')
    sudo('rm /etc/yum.repos.d/rpmforge.repo')
    with settings(warn_only=True):
        sudo('setsebool -P httpd_can_network_connect 1')

    # Install Python and Distribution Tools
    with cd('/opt/Python-2.7.6'):
        if exists('/usr/local/bin/python2.7'):
            run('echo ' 'python 2.7 found' '')
        else:
            sudo('yum -y install gcc')
            sudo("chown -R " + env.user + " /opt/Python-2.7.6")
            sudo('./configure')
            sudo('make altinstall')
            sudo('chown spectrumbrowser /usr/local/bin/python2.7')
            sudo('chgrp spectrumbrowser /usr/local/bin/python2.7')
            sudo('yum -y erase gcc')

    with cd('/opt/distribute-0.6.35'):
        if exists('/usr/local/bin/pip'):
            run('echo ' 'pip  found' '')
        else:
            sudo('chown -R ' + env.user + ' /opt/distribute-0.6.35')
            sudo('/usr/local/bin/python2.7 setup.py  install')
            sudo('/usr/local/bin/easy_install-2.7 pip')

    with cd(sbHome):
        sudo('bash install_stack.sh')
        sudo('make REPO_HOME=' + sbHome + ' install')

    # Update Users and Permission
    sudo('chown -R spectrumbrowser ' + sbHome)
    sudo('chgrp -R spectrumbrowser ' + sbHome)

    # Install All Services
    sudo('chkconfig --add memcached')
    sudo('chkconfig --add msod')
    sudo('chkconfig --add nginx')
    sudo('chkconfig --level 3 memcached on')
    sudo('chkconfig --level 3 msod on')
    sudo('chkconfig --level 3 nginx on')
    sudo('chkconfig cups off')
    sudo('service cups stop')


@roles('database')
def buildDatabase():
    ''' Build a database on a (non-amazon) VM target $MSOD_DB_HOST'''

    # get the sbHome variable.
    sbHome = getSbHome()
    localHome = getProjectHome()

    # Create Needed Directories
    sudo('mkdir -p ' + sbHome + ' /spectrumdb /etc/msod')

    # Create Users and Permissions
    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')
        sudo('chown -R spectrumbrowser ' + sbHome)

    # Copy Needed Files
    put('MSODConfig.json.setup', '/etc/msod/MSODConfig.json', use_sudo=True)
    sudo('chown spectrumbrowser /etc/msod/MSODConfig.json')

    global mongodbAnswer
    if mongodbAnswer == 'yes' or mongodbAnswer == 'y':
        put('mongodb-enterprise.repo',
            '/etc/yum.repos.d/mongodb-enterprise-2.6.repo',
            use_sudo=True)
        sudo('yum install -y mongodb-enterprise')
    else:
        put('mongodb-org-2.6.repo',
            '/etc/yum.repos.d/mongodb-org-2.6.repo',
            use_sudo=True)
        sudo('yum install -y mongodb-org')

    # Zip Needed Services
    put('/tmp/services.tar.gz', '/tmp/services.tar.gz', use_sudo=True)
    put('../requirements/Python-2.7.6.tgz',
        '/tmp/Python-2.7.6.tgz',
        use_sudo=True)
    put('../requirements/distribute-0.6.35.tar.gz',
        '/tmp/distribute-0.6.35.tar.gz',
        use_sudo=True)

    # Unzip Needed Services
    sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)
    sudo('tar -xvzf /tmp/Python-2.7.6.tgz -C ' + '/opt')
    sudo('tar -xvzf /tmp/distribute-0.6.35.tar.gz -C ' + '/opt')

    # Firewall Rules and Permissions
    DB_HOST = env.roledefs['database']['hosts'][0]
    WEB_HOST = env.roledefs['spectrumbrowser']['hosts'][0]
    if DB_HOST != WEB_HOST:
        sudo('iptables -P INPUT ACCEPT')
        sudo('iptables -F')
        sudo('iptables -A INPUT -i lo -j ACCEPT')
        sudo('iptables -A INPUT -p tcp --dport 22 -j ACCEPT')
        sudo('iptables -A INPUT -s ' + WEB_HOST +
             ' -p tcp --dport 27017 -j ACCEPT')
        sudo('iptables -A INPUT -m state --state NEW,ESTABLISHED -j ACCEPT')
        sudo('iptables -A OUTPUT -d ' + WEB_HOST +
             ' -p tcp --sport 27017 -j ACCEPT')
        sudo('iptables -A OUTPUT -m state --state ESTABLISHED -j ACCEPT')
        sudo('service iptables save')
        sudo('service iptables restart')

        # Install All Utilities
        with settings(warn_only=True):
            sudo('yum groupinstall -y "Development tools"')
            sudo(
                'yum install -y python-setuptools tk-devel gdbm-devel db4-devel libpcap-devel xz-devel policycoreutils-python lsb')
            sudo(
                'yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel')
            sudo('semanage port -a -t mongod_port_t -p tcp 27017')

        sudo('install -m 755 ' + sbHome +
             '/services/dbmonitor/ResourceMonitor.py /usr/bin/dbmonitor')
        sudo('install -m 755 ' + sbHome +
             '/services/dbmonitor/dbmonitoring-init /etc/init.d/dbmonitor')

        # Install Python and Distribution Tools
        with cd('/opt/Python-2.7.6'):
            if exists('/usr/local/bin/python2.7'):
                run('echo ' 'python 2.7 found' '')
            else:
                sudo("chown -R " + env.user + " /opt/Python-2.7.6")
                sudo('./configure')
                sudo('make altinstall')
                sudo('chown spectrumbrowser /usr/local/bin/python2.7')
        with cd('/opt/distribute-0.6.35'):
            if exists('/usr/local/bin/pip'):
                run('echo ' 'pip  found' '')
            else:
                sudo('chown -R ' + env.user + ' /opt/distribute-0.6.35')
                sudo('/usr/local/bin/python2.7 setup.py  install')
        sudo('/usr/local/bin/easy_install-2.7 pymongo')
        sudo('/usr/local/bin/easy_install-2.7 python-daemon')
    else:
        sudo('yum install mongodb-org')
        sudo('chown -R spectrumbrowser /opt/SpectrumBrowser')

    # Copy Needed Files
    put('mongod.conf', '/etc/mongod.conf', use_sudo=True)

    # Update Users and Permission
    sudo('chown mongod /etc/mongod.conf')
    sudo('chgrp mongod /etc/mongod.conf')
    sudo('chown mongod /spectrumdb')
    sudo('chgrp mongod /spectrumdb')

    # Install All Services
    sudo('chkconfig --add mongod')
    sudo('chkconfig dbmonitor off')
    sudo('chkconfig mongod --levels 3')
    sudo('chkconfig dbmonitor --levels 3 on')
    sudo('service mongod restart')
    time.sleep(10)
    sudo('service dbmonitor restart')


def undeploy():
    ''' undeploy server and database on target hosts'''
    execute(tearDownServer)
    execute(tearDownDatabase)


@roles('spectrumbrowser')
def tearDownServer():
    ''' uninstall server on target $MSOD_WEB_HOST '''
    sbHome = getSbHome()
    answer = prompt('Undeploy server on ' + os.environ.get('MSOD_WEB_HOST') +
                    ' (y/n)?')
    if answer != 'y' and answer != 'Y':
        print "aborting"
        return

    # Copy Needed Files
    put(getProjectHome() + '/devel/requirements/redhat_unstack.txt',
        sbHome + '/redhat_unstack.txt',
        use_sudo=True)
    put(getProjectHome() + '/devel/requirements/uninstall_stack.sh',
        sbHome + '/uninstall_stack.sh',
        use_sudo=True)

    # Stop All Running Services
    sudo('service msod stop')
    sudo('service memcached stop')
    sudo('service nginx stop')

    # Remove All Services
    sudo('chkconfig --del memcached')
    sudo('chkconfig --del msod')
    sudo('chkconfig --del nginx')

    # Uninstall All Installed Utilities
    with settings(warn_only=True):
        with cd(sbHome):
            sudo('bash uninstall_stack.sh')
            sudo('make REPO_HOME=' + sbHome + ' uninstall')
            sudo(
                'yum remove -y python-setuptools readline-devel tk-devel gdbm-devel db4-devel libpcap-devel')
            sudo(
                'yum remove -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel xz-devel')

    # Remove SPECTRUM_BROWSER_HOME Directory
    with settings(warn_only=True):
        sudo('rm -r ' + sbHome + ' /home/' + env.user + '/.msod/ /root/.msod/')
        sudo('userdel -r spectrumbrowser')

    # Clean Remaining Files
    sudo('rm -rf  /var/log/flask')
    sudo(
        'rm -f /var/log/nginx/* /var/log/gunicorn/* /var/log/admin.log /var/log/federation.log /var/log/servicecontrol.log')
    sudo(
        'rm -f /var/log/occupancy.log /var/log/streaming.log /var/log/monitoring.log /var/log/spectrumdb.log')


@roles('database')
def tearDownDatabase():
    ''' undeploy database on target $MSOD_DB_HOST '''
    sbHome = getSbHome()
    answer = prompt('Undeploy database on ' + os.environ.get('MSOD_DB_HOST') +
                    ' (y/n)?')
    if answer != 'y' and answer != 'Y':
        print "aborting"
        return

    # Stop All Running Services
    sudo('service dbmonitor stop')
    sudo('service mongod stop')

    # Remove All Services
    sudo('chkconfig --del dbmonitor')
    sudo('chkconfig --del mongod')

    # Uninstall All Installed Utilities
    with settings(warn_only=True):
        sudo('rm /usr/bin/dbmonitor')
        sudo('rm /etc/init.d/dbmonitor')
        sudo('rm /etc/mongod.conf')
        sudo(
            'yum remove -y python-setuptools readline-devel tk-devel gdbm-devel db4-devel libpcap-devel')
        sudo(
            'yum remove -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel xz-devel policycoreutils-python')
        sudo('yum erase -y $(rpm -qa | grep mongodb-enterprise)')
        sudo('yum erase -y $(rpm -qa | grep mongodb-org)')
        sudo('/usr/local/bin/pip uninstall -y pymongo')
        sudo('/usr/local/bin/pip uninstall -y python-daemon')

    # Remove SPECTRUM_BROWSER_HOME Directory
    with settings(warn_only=True):
        sudo('rm -r ' + sbHome + ' /spectrumdb /etc/msod')
        sudo('userdel -r spectrumbrowser')
        sudo('userdel -r mongod')

    # Clean Remaining Files
    sudo('rm -rf  /var/log/mongodb')
    sudo('rm -f /var/log/dbmonitoring.log')


@roles("spectrumbrowser")
def setupAide():
    ''' Set up the aide IDS on target $MSOD_WEB_HOST '''
    put(getProjectHome() + '/aide/aide.conf', "/etc/aide.conf", use_sudo=True)
    put(getProjectHome() + '/aide/runaide.sh',
        "/opt/SpectrumBrowser/runaide.sh",
        use_sudo=True)
    put(getProjectHome() + '/aide/swaks',
        "/opt/SpectrumBrowser/swaks",
        use_sudo=True)
    sudo("chown root /etc/aide.conf")
    sudo("chmod 0600 /etc/aide.conf")
    sudo("chmod u+x /opt/SpectrumBrowser/swaks")
    sudo("chown root /opt/SpectrumBrowser/swaks")
    sudo("chmod u+x /opt/SpectrumBrowser/runaide.sh")
    sudo("chown root /opt/SpectrumBrowser/runaide.sh")
    sudo("aide --init")
    sudo("mv -f /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz")


def Help():
    ''' print help text '''
    print ""
    print "Setup MSOD_WEB_HOST and MSOD_DB_HOST environment variables to the target IP "
    print "addresses of the hosts where you want to deploy. These can be the same host. "
    print "You should have sudo permission at these hosts."
    print ""
    print "Build everything locally:"
    print ""
    print "cd ../; ant "
    print ""
    print "Then issue the following command "
    print ""
    print "fab pack deploy"
    print ""
    print "To set up the test data use 'fab deployTests' and 'fab deployTestData'"
    print "mail mranga@nist.gov if you run into problems"


def pack():
    ''' Package local build for deployment on $MSOD_WEB_HOST and $MSOD_DB_HOST. Run ant before this. Run fab deploy after pack. '''
    local('cp ' + getProjectHome() + '/devel/certificates/cacert.pem ' +
          getProjectHome() + '/nginx/')
    local('cp ' + getProjectHome() + '/devel/certificates/privkey.pem ' +
          getProjectHome() + '/nginx/')
    local('tar -cvzf /tmp/flask.tar.gz -C ' + getProjectHome() + ' flask')
    local('tar -cvzf /tmp/nginx.tar.gz -C ' + getProjectHome() + ' nginx')
    local('tar -cvzf /tmp/services.tar.gz -C ' + getProjectHome() +
          ' services')

    if not os.path.exists('../requirements/Python-2.7.6.tgz'):
        local(
            'wget --no-check-certificate https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz --directory-prefix=../requirements')
    if not os.path.exists('../requirements/distribute-0.6.35.tar.gz'):
        local(
            'wget --no-check-certificate http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz --directory-prefix=../requirements')


def getSbHome():
    return json.load(open(getProjectHome() + '/MSODConfig.json'))[
        'SPECTRUM_BROWSER_HOME']


def getProjectHome():
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()


@roles('spectrumbrowser')
def firewallConfig():
    ''' Setup firewall Rules and Permissions on $MSOD_WEB_HOST '''
    sudo('iptables -P INPUT ACCEPT')
    sudo('iptables -F')
    sudo('iptables -A INPUT -i lo -j ACCEPT')
    sudo('iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 22 -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 443 -j ACCEPT')
    sudo('iptables -A INPUT -p tcp --dport 8443 -j ACCEPT')
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
    ''' Start the MSOD service on $MSOD_WEB_HOST. '''
    # Note that this returns 1 if successful so we need
    # warn_only = True
    sudo('chown -R spectrumbrowser /opt/SpectrumBrowser/services')
    sudo('chgrp -R spectrumbrowser /opt/SpectrumBrowser/services')
    sudo('chown spectrumbrowser /etc/msod/MSODConfig.json')
    with settings(warn_only=True):
        sudo('setenforce 0')
    sudo('service nginx restart')
    sudo('service msod stop')
    sudo('service memcached restart')
    time.sleep(5)
    sudo('service msod restart')
    sudo('service msod status')
    with settings(warn_only=True):
        sudo('setenforce 1')


@roles('spectrumbrowser')
def configMSOD():
    """Setup a default configuration for the server so you can log into it as admin"""
    sudo('PYTHONPATH=/opt/SpectrumBrowser/services/common:/usr/local/lib/python2.7/site-packages /usr/local/bin/python2.7 ' 
    + getSbHome() + '/setup-config.py -host ' + os.environ.get('MSOD_WEB_HOST') + ' -f ' + getSbHome() + '/Config.txt')


@roles('spectrumbrowser')
def deployTests(testDataLocation):
    ''' Deploy test data on target machine. Invoke using deployTests:/path/to/test/data '''
    ''' Note that the following files need to be present at path/to/test/data: '''
    ''' LTE_UL_DL_bc17_bc13_ts109_p1.dat,'LTE_UL_DL_bc17_bc13_ts109_p2.dat,LTE_UL_DL_bc17_bc13_ts109_p3.dat,v14FS0714_173_24243.dat '''
    # Invoke this using
    # fab deployTests:/path/to/test/data
    # /path/to/test/data is where you put the test data files (see blow)
    local('tar -cvzf /tmp/unit-tests.tar.gz -C ' + getProjectHome() +
          ' unit-tests')
    put('/tmp/unit-tests.tar.gz', '/tmp/unit-tests.tar.gz', use_sudo=True)
    if testDataLocation is None:
        raise Exception('Need test data')
    sudo('mkdir -p /tests/test-data')
    sudo('tar -xvzf /tmp/unit-tests.tar.gz -C /tests')
    with cd('/tests'):
        for f in ['LTE_UL_DL_bc17_bc13_ts109_p1.dat',
                  'LTE_UL_DL_bc17_bc13_ts109_p2.dat',
                  'LTE_UL_DL_bc17_bc13_ts109_p3.dat',
                  'v14FS0714_173_24243.dat']:
            put(testDataLocation + '/' + f,
                '/tests/test-data/' + f,
                use_sudo=True)


@roles('spectrumbrowser')
def setupTestData():
    ''' Upload the test data into the database. Run after deployTests target.  '''
    with cd('/tests'):
        sudo(
            'PYTHONPATH=/opt/SpectrumBrowser/services/common:/tests/unit-tests:/usr/local/lib/python2.7/site-packages/ /usr/local/bin/python2.7 /tests/unit-tests/setup_test_sensors.py -t /tests/test-data -p /tests/unit-tests')


def checkStatus():
    ''' Check the status of the MSOD services on $MSOD_WEB_HOST and Database Service running on $MSOD_DB_HOST '''
    execute(checkMsodStatus)
    execute(checkDbStatus)


@roles('spectrumbrowser')
def checkMsodStatus():
    ''' check the run status of MSOD services and memcached on $MSOD_WEB_HOST '''
    sudo('service memcached status')
    sudo('service msod status')


@roles('database')
def checkDbStatus():
    ''' check the run status of db components. '''
    sudo('service mongod status')
    sudo('service dbmonitor status')


@roles('database')
def buildDatabaseAmazon():  #build process for db server
    '''Amazon Server database setup Functions'''
    sbHome = getSbHome()

    with settings(warn_only=True):
        sudo('rm -f /var/log/dbmonitoring.log')

    sudo('install -m 755 ' + sbHome +
         '/services/dbmonitor/dbmonitoring-bin /usr/bin/dbmonitor')
    sudo('install -m 755 ' + sbHome +
         '/services/dbmonitor/dbmonitoring-init /etc/init.d/dbmonitor')

    put('mongodb-org-2.6.repo',
        '/etc/yum.repos.d/mongodb-org-2.6.repo',
        use_sudo=True)
    sudo('yum -y install mongodb-org')
    sudo('service mongod stop')
    put('mongod.conf', '/etc/mongod.conf', use_sudo=True)
    sudo('chown mongod /etc/mongod.conf')
    sudo('chgrp mongod /etc/mongod.conf')
    #NOTE: SPECIFIC to amazon deployment.
    answer = prompt('Create filesystem for DB and logging (y/n)?')
    if answer == 'y' or answer == 'yes':
        with settings(warn_only=True):
            sudo('umount /spectrumdb')
        # These settings work for amazon. Customize this.
        sudo('mkfs -t ext4 /dev/xvdf')
        sudo('mkfs -t ext4 /dev/xvdj')
        sudo('mkdir /var/log/mongodb')
        sudo('mkdir /var/log/nginx')
        sudo('chown mongod /var/log/mongdb')
        sudo('chgrp mongod /var/log/mongodb')
    #Put all the ebs data on /spectrumdb
    if exists('/spectrumdb'):
        run('echo ' 'Found /spectrumdb' '')
    else:
        sudo('mkdir /spectrumdb')
    sudo('chown  mongod /spectrumdb')
    sudo('chgrp  mongod /spectrumdb')

    with settings(warn_only=True):
        sudo('mount /dev/xvdf /spectrumdb')

    with settings(warn_only=True):
        sudo('mount /dev/xvdj /var/log')

    sudo('chkconfig --del mongod')
    sudo('chkconfig --add mongod')
    sudo('chkconfig --level 3 mongod on')
    sudo('chkconfig --del dbmonitor')
    sudo('chkconfig --add dbmonitor')
    sudo('chkconfig --level 3 dbmonitor on')
    sudo('service mongod restart')
    time.sleep(10)
    sudo('service dbmonitor restart')
