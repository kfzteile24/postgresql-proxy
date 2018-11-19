import logging

TYPE_SERVER=0
TYPE_CLIENT=1

class Connection:
    def __init__(self, sock, target, name):
        self.sock = sock
        self.target = target
        self.name = name

    def send(self, message):
        logging.debug("sending message to {}".format(self.name))
        total = len(message)
        total_sent = 0
        remaining = message
        while total_sent < total:
            sent = self.sock.send(remaining)
            total_sent += sent
            remaining = remaining[sent:]

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
