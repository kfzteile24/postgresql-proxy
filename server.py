import connection
import logging
import pg_connection
import selectors
import socket
import threading
import types

class Server:
    def __init__(self, on_receive, instance_config):
        self.num_clients = 0
        self.instance_config = instance_config
        self.on_receive = on_receive
        self.connections = []
        self.selector = selectors.DefaultSelector()
        self.selector_lock = threading.Lock()


    def __create_pg_connection(self, address):
        redirect_config = self.instance_config.redirect

        pg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pg_sock.setblocking(False)
        pg_sock.connect((redirect_config.host, redirect_config.port))

        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        pg_conn = pg_connection.PgConnection(pg_sock,
                                             target  = connection.TYPE_SERVER,
                                             name    = redirect_config.name + '_' + str(self.num_clients),
                                             address = address,
                                             events  = events)

        logging.info("initiated client connection to %s:%s called %s",
                     redirect_config.host, redirect_config.port, redirect_config.name)
        return pg_conn


    def __register_conn(self, conn):
        with self.selector_lock:
            self.selector.register(conn.sock, conn.events, data=conn)


    def __unregister_conn(self, conn):
        with self.selector_lock:
            self.selector.unregister(conn.sock)


    def accept_wrapper(self, sock):
        clientsocket, address = sock.accept()  # Should be ready to 
        clientsocket.setblocking(False)
        self.num_clients+=1
        sock_name = '{}_{}'.format(name, self.num_clients)
        logging.info("connection from {}, connection initiated {}".format(address, sock_name))

        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        conn = connection.Connection(clientsocket,
                                     target  = connection.TYPE_CLIENT,
                                     name    = sock_name,
                                     address = address,
                                     events  = events)

        pg_conn = self.__create_pg_connection(address)

        # TODO: Map IO between connections. Maybe also initiate the interceptors here and put them as middle
        # TODO: Merge this with proxy.py
        # TODO: Remove older code from proxy.py with speaker token, as it's deprecated by this functionality
        pg_conn.map_io(conn)

        self.__register_conn(conn)
        self.__register_conn(pg_conn)


    def threaded_io(self, mask, sock, conn):
        if mask & selectors.EVENT_READ:
            if not conn.is_reading:
                logging.debug('{} can receive'.format(conn.name))
                recv_data = sock.recv(4096)  # Should be ready to read
                if recv_data:
                    logging.debug('{} received data:\n'.format(conn.name, recv_data))
                    conn.received(recv_data)
                else:
                    logging.info('{} connection closing {}'.format(conn.name, conn.address))
                    sock.close()
                    # Make sure we don't add the sock to the selector again
                    return
        if mask & selectors.EVENT_WRITE:
            if conn.out_bytes:
                if not conn.is_writing:
                    logging.debug('{} can receive'.format(conn.name))
                    sent = sock.send(conn.out_bytes)  # Should be ready to write
                    conn.sent(sent)
                    #conn.outb = conn.outb[sent:]
        self.__register_conn(conn)


    def service_connection(self, key, mask):
        sock = key.fileobj
        conn = key.data
        # Do threaded IO, in case time to process interceptors is big enough to care.
        # This means that processing can happen at the same time as stuff is received.
        # This way IO and processing won't block each other's resources.
        # To ensure TCP integrity, manage one sock in a single thread.
        self.__unregister_conn(conn)
        new_thread = threading.Thread(target=self.threaded_read, args=[mask, sock, conn])
        new_thread.start()


    def listen(self, ip, port, max_connections = 8, name = ""):
        '''Listen server socket. On connect launch a new thread with the client connection as an argument
        '''
        try:
            logging.info("listening to {}:{}".format(ip, port))
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((ip, port))
            self.sock.listen(max_connections)
            self.sock.setblocking(False)
            self.selector.register(self.sock, selectors.EVENT_READ, data=None)
            while True:
                logging.info("Wait for new connection on {}:{}".format(ip, port))
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except OSError as ex:
            logging.critical("Can't establish listener", exc_info=ex)
        finally:
            self.sock.close()
            self.sock = None
            logging.info("closed socket")
