import socket, ssl, pprint

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ssl_sock = ssl.wrap_socket(s,
                           ca_certs="dummy.crt",
                           )

ssl_sock.connect(('localhost', 10023))


ssl_sock.write("boo!")

