mongod -dbpath data/db&
pid=$!
disown $pid
echo $pid > .mongod.pid
