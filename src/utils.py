import json
import numpy as np
from sensors import LocationSensor

class Observable(object):
    def __call__(self, fun):
        return fun()

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return obj._to_json()
        except AttributeError:
            return super().default(obj)
        
class bcolors():
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_json_payload(sensor : LocationSensor):
    #name = sensor.get_topic().split('/')
    return json.dumps(sensor, cls=CustomEncoder)

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def temperature_to_index(temperature):
    value = np.argwhere( np.arange(15, 25.5, 0.5) == temperature ).flatten()
    return value[0]

def index_to_temperature(index):
    temperatures = np.arange(15,25.5,0.5)
    return temperatures[index]