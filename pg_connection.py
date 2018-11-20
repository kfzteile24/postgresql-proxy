import logging

from connection import Connection

class PgConnection(Connection):
    def receive(self):
        '''Overriding method because Postgresql sends more than one packet per message
        '''
        logging.debug("receive messages from {}".format(self.name))
        packets = []
        while True:
            packet, pack_type = self.receive_packet()
            packets.append(packet)
            # If the packet is "Ready for Query", break and return result
            if pack_type in (b'Z', b'N'):
                break
            
        message = b''.join(packets)
        logging.debug("received messages from {}\n".format(self.name), message)
        return message
