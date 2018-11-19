import socket, threading, connection, logging

class Server:
    def __init__(self, on_receive):
        self.clients = 0
        self.on_receive = on_receive


    def listen(self, ip, port, max_connections = 8, name = ""):
        try:
            logging.info("listening to {}:{}".format(ip, port))
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((ip, port))
            self.sock.listen(max_connections)
            while True:
                (clientsocket, address) = self.sock.accept()
                self.clients+=1
                sock_name = '{}_{}'.format(name, self.clients)
                logging.info("connection from {}, connection initiated {}".format(address, sock_name))
                new_thread = threading.Thread(
                    target=self.on_receive,
                    args=[
                        connection.Connection(
                            clientsocket,
                            target=connection.TYPE_CLIENT,
                            name = sock_name
                        )
                    ])
                new_thread.run()
        except OSError as ex:
            logging.critical("Can't establish listener", exc_info=ex)
        finally:
            self.sock.close()
            self.sock = None
            logging.info("closed socket")
