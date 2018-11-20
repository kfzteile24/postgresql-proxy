import importlib
import sys

plugin = sys.argv[1]
test = importlib.import_module('plugins.' + plugin + '.test')

test.run()
