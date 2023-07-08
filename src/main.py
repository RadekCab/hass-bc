# from __future__ import annotations

import numpy as np

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


def state_space_tests():
    # a = np.zeros((4, 2, 3))
    # print(a)
    # print("4 pole, 2 radky, 3 sloupce")
    # print(a[0])
    m = np.zeros((96, 20, 2))
    # increase reward for 15 degrees
    m[0][0][0] = 100
    print(m)
    # for 16 degrees
    print("get q value for 0:00 - 0:15 increase 15deg")
    print(m[0][0][0])
    print("get q value for 0:00 - 0:15 decrease 15deg")
    print(m[0][0][1])
    print("get q value for 23:45 - 0:00 decrease 25deg")
    print(m[95][19][1])
    print("get error")
    try:
        print(m[0][20][0])
    except IndexError as e:
        print("X")


if __name__ == "__main__":
    # state_space_tests()
    # x = np.random.randint(3, size=(3, 2))
    
    #x = np.array([[1, 2], [3, 4], [4, 5]])
    #print(x)
    #print(np.array_split(x, np.flatnonzero(np.diff(x[:, 0])) + 1))
    
    #print(np.zeros((96, 20, 3, 2)))
    
    target_temp_time = {28: 21, 66: 20}
    if 54 in target_temp_time:
        print(target_temp_time[54])

    # h = np.argwhere((x[:, 1]) > 1)
    # print(h)
    pass
