import socket, connection, logging

class Client:
    def __init__(self, ip, port, target, name = ''):
        self.ip = ip
        self.port = port
        self.target = target
        self.name = name

    def __enter__(self) -> connection.Connection:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        logging.info("initiated client connection to %s:%s called %s", self.ip, self.port, self.name)
        return connection.Connection(self.sock, self.target, name = self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()
        logging.info("closed client socket %s", self.name)
