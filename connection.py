import logging

TYPE_SERVER=0
TYPE_CLIENT=1

class Connection:
    def __init__(self, sock, target, name):
        self.sock = sock
        self.target = target
        self.name = name

    def send(self, message):
        logging.debug("{} sends message".format(self.name))
        self.sock.sendall(message)

    def receive(self):
        logging.debug("receive messages from {}".format(self.name))
        chunks = []
        total_bytes = 0
        while True:
            chunk = self.sock.recv(2048)
            chunks.append(chunk)
            bytes_recd = len(chunk)
            total_bytes += bytes_recd
            if bytes_recd < 2048:
                break

        return b''.join(chunks)
