import json
import numpy as np
from sensors import LocationSensor
from datetime import datetime
from agent.agents import TIME_INTERVAL
from datetime import timedelta

# 5 # [x/5] 3 mins intervals instead of 15min
# 2 # half the time and do requests only until 0-12:00 / 12-24 ?
# real
INTERVAL_SHORTENER = 180  # 1min -> 45min

__doc__ = """
package providing custom utility methods
"""


class Observable(object):
    def __call__(self, fun):
        return fun()


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return obj._to_json()
        except AttributeError:
            return super().default(obj)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def get_json_payload(sensor):
    """sensor e.g. sensors.LocationSensor"""
    return json.dumps(sensor, cls=CustomEncoder)


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def temperature_to_index(temperature):
    value = np.argwhere(np.arange(15, 25.5, 0.5) == temperature).flatten()
    return value[0]


def index_to_temperature(index):
    temperatures = np.arange(15, 25.5, 0.5)
    return temperatures[index]


def datetime_to_index(modifier=TIME_INTERVAL, value=None):
    now = None
    if value is None:
        now = datetime.now()
    else:
        now = value
    # minutes = now.minute + now.hour * 60
    seconds = now.minute * 60 + now.hour * 3600 + now.second
    # index = int(round(minutes / (modifier * INTERVAL_SHORTENER))) % 95
    # index = int(round(minutes * INTERVAL_SHORTENER)) % 95

    # index = (int(round(seconds * INTERVAL_SHORTENER)) // 60) % 95
    index = ((int(round(seconds * INTERVAL_SHORTENER)) // 60) // 96) % 96
    # print("UTILS: Calculating index: ( (", seconds, "*", INTERVAL_SHORTENER, ") // 60 ) % 95 =", str(seconds * INTERVAL_SHORTENER), " // 60 ...%95 =", index)
    return index


def smoothen(x: np.ndarray):
    const = 25
    x_ = np.pad(x, (const // 2, const - const // 2), mode="edge")
    # return np.cumsum(x_[const:] - x_[:-const]) / const
    return ((np.cumsum(x_[const:] - x_[:-const])) / 25) + 20
    # return np.cumsum((x_[const:] - x_[:-const]))


def time_index_to_seconds(index: int, modifier=TIME_INTERVAL):
    a = timedelta(minutes=int(index) * modifier)
    return a.seconds
    # return (index * 15 * 60) * INTERVAL_SHORTENER
