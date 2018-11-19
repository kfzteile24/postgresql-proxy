import logging

from connection import Connection

class PgConnection(Connection):
    def __receive_raw(self, length):
        total_received = 0
        chunks = []
        while total_received < length:
            chunk = self.sock.recv(min([length - total_received]), 4096)
            chunks.append(chunk)
            total_received += len(chunk)
        return b''.join(chunks)


    def __receive_packet(self):
        pack_type = self.__receive_raw(1)
        if pack_type == b'N':
            # Stupid exceptions like these, with messages that have no length
            return pack_type, pack_type
        pack_length = self.__receive_raw(4)
        pack_header = b''.join([pack_type, pack_length])
        pack_length = int.from_bytes(pack_length, 'big')
        pack_body = self.__receive_raw(pack_length - 4)
        pack = b''.join([pack_header, pack_body])
        return pack, pack_type


    def receive(self):
        logging.debug("receive messages from {}".format(self.name))
        packets = []
        while True:
            packet, pack_type = self.__receive_packet()
            packets.append(packet)
            # If the packet is "Ready for Query", break and return result
            if pack_type in (b'Z', b'N'):
                break
            
        return b''.join(packets)
