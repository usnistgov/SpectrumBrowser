# A list of base URLS where this server will REGISTER
# the sensors that it manages. This contains pairs of server 
# base URL and server key. TODO - put this into mongod. We need an admin
# interface for this.

PEERS=[{"protocol":"http", "host":"pwct3.antd.nist.gov" ,"port":8000, "key":"efgh"} ,
       {"protocol":"http", "host":"77-140.antd.nist.gov" ,"port":8000, "key":"abcd"} ]
