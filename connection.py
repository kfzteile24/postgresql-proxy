import logging

TYPE_SERVER=0
TYPE_CLIENT=1

class Connection:
    def __init__(self, sock, target, name):
        self.sock = sock
        self.target = target
        self.name = name

    def send(self, message):
        logging.debug("sending message to {}:\n{}".format(self.name, message))
        total = len(message)
        total_sent = 0
        remaining = message
        while total_sent < total:
            sent = self.sock.send(remaining)
            total_sent += sent
            remaining = remaining[sent:]

    def __receive_raw(self, length):
        total_received = 0
        chunks = []
        while total_received < length:
            chunk = self.sock.recv(min([length - total_received]), 4096)
            if chunk==b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            total_received += len(chunk)
        return b''.join(chunks)


    def receive_packet(self):
        pack_type = self.__receive_raw(1)
        if pack_type == b'N':
            # Null message? This message has no length. Just a single byte. Weird.
            return pack_type, pack_type
        if pack_type == b'\x00':
            # Initialization packet. No type. This, and the next 3 bytes are the length
            pack_length = self.__receive_raw(3)
            pack_length = b''.join([pack_type, pack_length])
            pack_header = pack_length
        else:
            pack_length = self.__receive_raw(4)
            pack_header = b''.join([pack_type, pack_length])
        pack_length = int.from_bytes(pack_length, 'big')
        pack_body = self.__receive_raw(pack_length - 4)
        pack = b''.join([pack_header, pack_body])
        return pack, pack_type


    def receive(self):
        packets = []
        logging.debug("receive message from {}:".format(self.name))
        while True:
            logging.debug("receive packet from {}:".format(self.name))
            packet, pack_type = self.receive_packet()
            packets.append(packet)
            logging.debug("received packet from {}:\n{}".format(self.name, packet))
            if not pack_type in (b'B', b'D', b'P', b'E'):
                break
        message = b''.join(packets)
        logging.debug("received message from {}:\n{}".format(self.name, message))
        return message
