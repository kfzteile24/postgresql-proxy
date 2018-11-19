import server, client, connection, logging, config_schema as cfg

class Proxy():
    def __init__(self, instance_config: cfg.InstanceSettings, plugins: list):
        self.instance_config : cfg.InstanceSettings = instance_config
        self.plugins : list = plugins


    def __intercept_command(self, command):
        logging.debug("Received command:\n%s", command)

        # startup message that contains info about DB, user, etc.
        if command[0:1] == b'\x00':
            try:
                connect_items = list(b.decode('utf-8') for b in command[8:-2].split(b'\x00'))
                self.connect_params = dict(zip(connect_items[0::2], connect_items[1::2]))
            except Exception as ex:
                logging.error("Could not determine connection details\n%s", command, exc_info=True)

        if self.instance_config.intercept is not None:
            intercept = self.instance_config.intercept
            if intercept.commands is not None:
                intercept_commands = intercept.commands
                if intercept_commands.queries is not None:
                    intercept_queries = intercept_commands.queries
                    if command[0:1] == b'Q':
                        ''' Query commands begin with "Q". Followed by 4 bytes, which are a big-endian representation
                        of an integer that is the length of the query + 5. 5 = 4 + 1. 4 bytes for the header (length),
                        1 byte for the "footer" (zero byte).
                        Take the query text, update if needed, re-assess the length and encode it back into binary.
                        '''
                        length = int.from_bytes(command[1:5], 'big')
                        query = command[5:length]
                        logging.getLogger('intercept').debug("intercepting query\n%s", query)
                        for interceptor in self.instance_config.intercept.commands.queries:
                            if interceptor.plugin in self.plugins:
                                plugin = self.plugins[interceptor.plugin]
                                if hasattr(plugin, interceptor.function):
                                    func = getattr(plugin, interceptor.function)
                                    query = func(query, self)
                                    logging.getLogger('intercept').debug(
                                        "modifying query using interceptor %s.%s\n%s",
                                        interceptor.plugin,
                                        interceptor.function,
                                        query)
                                else:
                                    raise Exception("Can't find function {} in plugin {}".format(
                                        interceptor.function,
                                        interceptor.plugin
                                    ))
                            else:
                                raise Exception("Plugin {} not loaded".format(interceptor.plugin))
                        return b''.join([b'Q', (len(query) + 5).to_bytes(4, byteorder='big'), query, b'\x00'])
        return command


    def __intercept_response(self, response):
        if response[0:1]==b'E':
            # is error. Wait for next message without passing talk token to the other party
            return response, False
        return response, True

    # This method is multi-threaded. A new client_conn is created when someone connects,
    # and it's passed on to this method in its own thread
    def __on_connect(self, client_conn: connection.Connection):
        try:
            redirect_config = self.instance_config.redirect
            with client.Client(redirect_config.host,
                               redirect_config.port,
                               name = redirect_config.name,
                               target = connection.TYPE_SERVER) as pg_conn:
                speaker = client_conn
                listener = pg_conn

                # Pass the talker token in a a loop until someone terminates it with "Z" command
                while True:
                    pass_token = True
                    message = speaker.receive()

                    if len(message) == 0:
                        logging.info("Connection closed for speaker %s", speaker.name)
                        break

                    if speaker.target==connection.TYPE_CLIENT:
                        logging.info("intercepting client command")
                        message = self.__intercept_command(message)
                    elif speaker.target==connection.TYPE_SERVER:
                        logging.info("intercepting server response")
                        message, pass_token = self.__intercept_response(message)

                    logging.debug("Received message. Relaying. Speaker: %s, message:\n%s", speaker.name, message)
                    listener.send(message)

                    # If the client sends an 'X' request, it wants to terminate the session. Close the connection
                    if speaker.target==connection.TYPE_CLIENT and message[0:1]==b'X':
                        break

                    if pass_token:
                        tmp = listener
                        listener = speaker
                        speaker = tmp
        except Exception as ex:
            logging.error("Error communicating\n%s", redirect_config.__dict__, exc_info=True)
        finally:
            client_conn.sock.close()

    def start(self):
        listen_config = self.instance_config.listen
        serv = server.Server(self.__on_connect)
        serv.listen(listen_config.host, listen_config.port, name=listen_config.name)


if(__name__=='__main__'):
    import importlib, yaml, os

    path = os.path.dirname(os.path.realpath(__file__))
    config : cfg.Config = None
    with open(path + '/' + 'config.yml', 'r') as fp:
        config = cfg.Config(yaml.load(fp))

    logging.basicConfig(
        filename=config.settings.general_log,
        level=getattr(logging, config.settings.log_level.upper()),
        format='%(asctime)s : %(levelname)s : %(message)s'
    )

    qlog = logging.getLogger('intercept')
    qformat = logging.Formatter('%(asctime)s : %(message)s')
    qhandler = logging.FileHandler(config.settings.intercept_log, mode = 'w')
    qhandler.setFormatter(qformat)
    qlog.addHandler(qhandler)
    qlog.setLevel(logging.DEBUG)

    print('general log, level {}: {}'.format(config.settings.log_level, config.settings.general_log))
    print('intercept log: {}'.format(config.settings.intercept_log))
    print('further messages directed to log')

    plugins = {}
    for plugin in config.plugins:
        logging.info("Loading module %s", plugin)
        module = importlib.import_module('plugins.' + plugin)
        plugins[plugin] = module

    for instance in config.instances:
        logging.info("Starting proxy instance")
        proxy = Proxy(instance, plugins)
        proxy.start()
