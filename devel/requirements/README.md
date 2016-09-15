
<h2> Installing requirements </h2>
  
  Install python dependencies.
  
        pip -r requirements.txt 

<h2> Detailed instructions for developers </h2>

Note: It is recommended that you use the fab install procedure in (devel/deploy)[../devel/deploy]

```bash
# Clone the SpectrumBrowser repo. /opt will be the preferred location for deployment systems
# but any location should be correctly handled.
$ cd /opt && sudo git clone https://<+GITHUB_USERNAME+>@github.com/usnistgov/SpectrumBrowser.git
$ sudo groupadd --system spectrumbrowser
$ sudo useradd --system spectrumbrowser -g spectrumbrowser
$ sudo chown --recursive spectrumbrowser:spectrumbrowser /opt/SpectrumBrowser
$ sudo chmod --recursive g+w /opt/SpectrumBrowser/
$ sudo usermod --append --groups spectrumbrowser $(whoami)
# Log out of the VM and back in. You should see "spectrumbrowser" when you type groups:
$ groups
<user-name> wheel spectrumbrowser
$ sudo chmod +x install_stack.sh install_mongod.sh install_build_tools.sh
# note that install_mongod.sh needs fix so for the moment as a workaround do a manual install of mongod:
# access the website https://wwww.mongodb.org then download version 2.6.10 untar it under /opt
# You can now work in /opt/SpectrumBrowser without sudo, including git pull, etc.

# TODO: verify this is true for all users, not just the one who did the original clone

# Change directory into the repository root after cloning/pulling
$ cd SpectrumBrowser
# Install the dependencies and build tools
$ cd devel/requirements
$ sudo ./install_stack.sh
$ sudo ./install_mongod.sh
$ sudo ./install_build_tools.sh
# Follow instructions to log out and back in if GWT was not previously installed
$ cd -
$ git pull
## To set up a development environment
# Copy MSODConfig.json to $HOME/.msod/MSODConfig.json
# Edit the DB_PORT_27017_TCP_ADDR field and other parameters in $HOME/.msod/MSODConfig.json
# The default target runs "ant" and the install target installs and/or modifies 
# config files for nginx, gunicorn, and flask
# cd to the root of the SpectumBrowser repository
## To set up a production environment

$ make && sudo make REPO_HOME=`pwd` install
# To build the "demo" target
$ make demo && sudo make REPO_HOME=`pwd` install
```
