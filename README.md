# Postgresql Proxy

Serves as a proper server that Postgresql clients can connect to. Can modify packets that pass through.

Currently used for rewriting queries to force proper use of postgres-hll module by external proprietary software that doesn't know about that functionality
