import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

if __name__ == "__main__":
    # x = np.full(5, -1)
    # print(x)
    # # We wish to mark the fourth entry as invalid. The easiest is to create a masked array:

    # mx = np.ma.masked_array(x, mask=[0, 1, 0, 1, 0])
    # # print(mx)
    # # print(mx.filled(4))

    # fig, axs = plt.subplots(2, 1, layout="constrained")

    # smoothen = 10
    # x = np.random.random_integers(size=100, low=0, high=1)
    # print(x)
    # h = np.asarray(x)
    # yh = np.arange(0, x.size, 1)
    # axs[0].plot(yh, h)
    # x_ = np.pad(x, (smoothen // 2, smoothen - smoothen // 2), mode="edge")
    # x_ = np.cumsum(x_[smoothen:] - x_[:-smoothen]) / smoothen
    # print(x_)

    # hx = np.asarray(x_)
    # yhx = np.arange(0, x_.size, 1)

    # axs[1].plot(yhx, hx)
    # # plt.show()
    # plt.tight_layout()
    # fig.savefig("test")

    # index to seconds
    x = 5
    a = timedelta(minutes=int(x) * 15)
    print(a.seconds)
