import json
from fabric.api import *
import subprocess
import sys

env.sudo_user = 'root'

def rhosts(username=None, database=None, web=None):
    """sets username and hosts for default roles"""
    print('Login User (%s): Database Host (%s) Web Server Host (%s)' % (username, database, web))

    if not username:
        print 'The username (%s) is not valid.' % username
        sys.exit(1)
    if not database:
        print 'The database host (%s) is not valid.' % username
        sys.exit(1)
    if not web:
        print 'The web server host (%s) is not valid.' % username
        sys.exit(1)

    env.roledef = {
        'database' : {
            'hosts': [database],
        },
        'spectrumbrowser' : {
            'hosts': [web],
        }
    }

    env.user = username


def pack():
    """create a new distribution, pack only the pieces we need"""
    local ("cp "+ getProjectHome()+ "/devel/certificates/cacert.pem " + getProjectHome() + "/nginx/")
    local ("cp " + getProjectHome() + "/devel/certificates/privkey.pem "  + getProjectHome() + "/nginx/")
    local('tar -cvzf /tmp/flask.tar.gz -C ' + getProjectHome() + ' flask ')
    local('tar -cvzf /tmp/nginx.tar.gz -C ' + getProjectHome() + ' nginx ')
    local('tar -cvzf /tmp/services.tar.gz -C ' + getProjectHome() + ' services ')


def getSbHome():
    """returns the default directory of installation"""
    return json.load(open(getProjectHome() + '/MSODConfig.json'))["SPECTRUM_BROWSER_HOME"]


def getProjectHome():
    """finds the default directory of installation"""
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()


def deploy():
    """build process for target hosts"""
    execute(buildDatabase)
    execute(buildServer)


@roles('database')
def buildDatabase():
    """build process for db server"""
    sbHome = getSbHome()
    sudo('rm -rf ' + sbHome)

    with settings(warn_only=True):
        sudo('adduser --system spectrumbrowser')

    sudo('mkdir -p ' + sbHome + '/data/db')
    put('mongodb-org-2.6.repo', '/etc/yum.repos.d/mongodb-org-2.6.repo', use_sudo=True)
    sudo('yum -y install mongodb-org')
    sudo('service mongod restart')


@roles('spectrumbrowser')
def buildServer():
       """build process for web server"""
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

       put('/tmp/flask.tar.gz', '/tmp/flask.tar.gz')
       put('/tmp/nginx.tar.gz', '/tmp/nginx.tar.gz')
       put('/tmp/services.tar.gz', '/tmp/services.tar.gz')
       sudo('tar -xvzf /tmp/flask.tar.gz -C ' + sbHome)
       sudo('tar -xvzf /tmp/nginx.tar.gz -C ' + sbHome)
       sudo('tar -xvzf /tmp/services.tar.gz -C ' + sbHome)

       put('nginx.repo', '/etc/yum.repos.d/nginx.repo', use_sudo=True)
       put('MSODConfig.json.setup', sbHome + '/MSODConfig.json', use_sudo=True)
       put('python_pip_requirements.txt', sbHome + '/python_pip_requirements.txt', use_sudo=True)
       put('install_stack.sh', sbHome + '/install_stack.sh', use_sudo=True)
       put('redhat_stack.txt', sbHome + '/redhat_stack.txt', use_sudo=True)
       put('get-pip.py', sbHome + '/get-pip.py', use_sudo=True)
       put('setup-config.py', sbHome + '/setup-config.py', use_sudo=True)
       put('Config.gburg.txt', sbHome + '/Config.gburg.txt', use_sudo=True)
       put(getProjectHome() + '/Makefile', sbHome + '/Makefile', use_sudo=True)

       dbrole = env.roledefs['database']
       dbhost = dbrole['hosts']

       with cd(sbHome):
           sudo('sh install_stack.sh')
           sudo('make REPO_HOME=' + sbHome + ' install')
           sudo('python setup-config.py -host ' + dbhost)
