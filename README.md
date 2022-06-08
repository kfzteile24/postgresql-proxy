# Postgresql Proxy

Serves as a proper server that Postgresql clients can connect to. Can modify packets that pass through.

Currently used for rewriting queries to force proper use of postgres-hll module by external proprietary software that doesn't know about that functionality

## Installing
### Linux
1. Make sure you have [python3 and pip3 installed on your system](https://stackoverflow.com/questions/6587507/how-to-install-pip-with-python-3#6587528). It has been tested with Python3.6 but should also run on Python3.5.
2. Clone it locally and cd to that directory
  ```
  git clone git@github.com:kfzteile24/postgresql-proxy.git
  cd postgresql-proxy
  ```
3. Run [setup.sh](setup.sh)
  ```
  source setup.sh
  ```

## Configuring
In the `config.yml` file you can define the following things
### Plugins
A list of dynamically loaded modules that reside in the [plugins](plugins) directory. These plugins can be used in later configuration, to intercept queries, commands, or responses. View plugin documentation for example plugins for more details on how to do that.
### Settings
General application settings. Currently the following settings are used
* `log-level` - the log level for the general log. See [python logging](https://docs.python.org/3.6/library/logging.html) for more details about the logging functionality
* `general-log` - the location for the general log. All general messages go in there.
* `intercept-log` - the location for the intercept log. Intercepted messages and return values from various enabled plugins will be written there. This log can be quite verbose as it contains the full binary messages being circulated.

Make sure to manage the logs yourself, as they accumulate and take up disk space.

### Instances
`instances` is a list of instance definitions. Each instance has a listening port and redirects to a different postgresql instance. They have individual configurations for which message interceptors to use. It **requires**, for every instance, a `listen` directive and `redirect` directive.
* `listen` directive, that must contain a `name` (for logging purposes), `host` and `port` for the listening socket. This is the host and port that external tools will connect to, as if it were the actual PostgreSql server.
* `redirect` directive, that must contain the same components as `listen`, is the address of the actual PostgreSql server that this instance redirects to.
* `intercept` - defines message interceptors
  * `commands` - interceptors for commands (messages from the client)
    * `queries` - interceptors for queries.
    * `connects` - interceptors for connection requests. *Not implemented yet*
  * `responses` - interceptors for responses (messages from PostgreSql server). *Not implemented yet*
  
  Each interceptor definition must have a `plugin`, which should also be present in the [plugins](#Plugins) configuration, and a `function`, that is found directly in that module, that will be called each time with the intercepted message as a byte string, and a context variable that is an instance of the `Proxy` class, that contains connection information and other useful stuff.

## Running in testing mode
If you want to test it, do this. Otherwise scroll down for instructions on how to install it as a service
### Linux
1. Activate the virtual environment
  ```
  source .venv/bin/activate
  ```
2. Run it
  ```
  python proxy.py
  ```
