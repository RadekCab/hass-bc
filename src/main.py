# from __future__ import annotations

""" class Observable(object):
    def __call__(self, fun):
        return fun()


class Callback(object):
    def docallback(self):
        inp = "haha"
        return inp    


if __name__ == "__main__":
    # f(a, b)
    # inside f
    # c = neco
    # g(b, c)
    # inside g
    # print(a) -> error
    a = Observable()(Callback().docallback)
    print (a)
    print (type(a))
    pass """


class C(object):
    def __init__(self):
        self._x = None

    def getx(self):
        return self._x

    def setx(self, value):
        self._x = value

    def delx(self):
        del self._x

    # def logic(self):
    x = property(getx, setx, delx, "I'm the 'x' property.")


if __name__ == "__main__":
    c = C()
    c.x = 30
    print(C.x.__doc__)
    print(c.x.fset(30))
    print(c.x)
    del c
