import connection
import logging
import socket
import threading

class Server:
    def __init__(self, on_receive):
        self.clients = 0
        self.on_receive = on_receive
        self.connections = []

    def listen(self, ip, port, max_connections = 8, name = ""):
        '''Listen server socket. On connect launch a new thread with the client connection as an argument
        '''
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
                conn = connection.Connection(clientsocket,
                                             target=connection.TYPE_CLIENT,
                                             name = sock_name)
                new_thread = threading.Thread(target=self.on_receive, args=[conn])
                new_thread.run()
                self.connections.append({'conn': conn, 'thread': new_thread})
        except OSError as ex:
            logging.critical("Can't establish listener", exc_info=ex)
        finally:
            self.sock.close()
            self.sock = None
            logging.info("closed socket")
