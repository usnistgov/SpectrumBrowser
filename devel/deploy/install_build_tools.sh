echo
echo "================== Installing GWT  =================="

did_set_gwt_home=0
set_gwt_home () {
    if [[ -z $1 ]]; then
        echo "set_gwt_home missing parameter" >>/dev/stderr
        exit 1
    fi

    if [[ -f /etc/profile.d/gwt_home.sh ]]; then
        echo "gwt_home.sh found in /etc/profile.d/ but GWT_HOME not in env"
        echo "Log out and back in and ensure GWT_HOME is set"
        echo "Alternately, source /etc/profile.d/gwt_home.sh && sudo -E ${0}"
        exit 1
    fi
        
    did_set_gwt_home=1
    

    echo
    echo "======= Setting GWT_HOME environment variable ======="
    echo "Found gwt-2.6.1 at $1"
    echo "# Created by ${repo_root}/devel/${script_name}" >> /etc/profile.d/gwt_home.sh
    echo "export GWT_HOME=$1" >> /etc/profile.d/gwt_home.sh

    return 0
}

if [[ -d ${GWT_HOME} ]] && [[ $(basename ${GWT_HOME}) == "gwt-2.6.1" ]]; then
    # Best case: GWT_HOME is set and points to version 2.6.1
    echo "Found gwt-2.6.1 at ${GWT_HOME}"
elif GWT_HOME=$(find /opt -type d -name 'gwt-2.6.1') && [[ -d ${GWT_HOME} ]]; then
    # Next best case: we find 2.6.1 and set GWT_HOME to it
    echo "Found gwt-2.6.1 at ${GWT_HOME}"
    set_gwt_home ${GWT_HOME}
else
    # Worst case: install
    wget -P /tmp http://storage.googleapis.com/gwt-releases/gwt-2.6.1.zip
    unzip /tmp/gwt-2.6.1 -d /opt
    rm -f /tmp/gwt-2.6.1.zip
    set_gwt_home /opt/gwt-2.6.1
fi

if (( $did_set_gwt_home )); then
    echo
    echo "You must 'source /etc/profile.d/gwt_home.sh' or log out and back in before continuing"
fi
echo
echo "============== Installing apache-ant =============="
wget  https://www.apache.org/dist/ant/binaries/apache-ant-1.9.5-bin.tar.gz -P /opt/apache-ant-1.9.5-bin.tar.gz
tar -xvzf /opt/apache-ant-1.9.5-bin.tar.gz  -C /opt/apache-ant

echo "Download jdk1.7 from oracle. Unpack it and install it. Setup your PATH to include $JAVA_HOME/bin"
echo "Add /opt/apache-ant/bin" to your PATH variable.
