import importlib

#tmp = importlib.import_module('plugins.tableau_hll')

class A:
    def _foo(self):
        print("a")

    def bar(self):
        print(self.__dict__)
        self._foo()


class B(A):
    def __init__(self):
        self.pfoo = ""
        self.pbar = 1

    def _foo(self):
        print(__class__.__name__)
        print("b")

b = B()
b.bar()
b._foo()
print(b.__dict__)
