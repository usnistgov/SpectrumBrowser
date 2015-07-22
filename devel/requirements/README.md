<h1> Deploy system locally using install_stack.sh and Makefile </h1>

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
danderson wheel spectrumbrowser
# You can now work in /opt/SpectrumBrowser without sudo, including git pull, etc.
# TODO: verify this is true for all users, not just the one who did the original clone

# Change directory into the repository root after cloning/pulling
$ cd SpectrumBrowser
# Install the software stack
$ cd devel
$ sudo ./install_stack.sh
$ sudo ./install_mongod.sh
# Follow instructions to log out and back in if GWT was not previously installed
$ cd -
# Edit the DB_PORT_27017_TCP_ADDR field in /opt/SpectrumBrowser/MSODConfig.json
# The default target runs "ant" and the install target installs and/or modifies 
# config files for nginx, gunicorn, and flask
# cd to the root of the SpectumBrowser repository
$ git pull

$ make && sudo make REPO_HOME=`pwd` install
# To build the "demo" target
$ make demo && sudo make REPO_HOME=`pwd` install
```
