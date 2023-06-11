import json
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

def get_json_payload(sensor : LocationSensor):
    #name = sensor.get_topic().split('/')
    return json.dumps(sensor, cls=CustomEncoder)