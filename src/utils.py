import json
from sensors import LocationSensor, CustomEncoder

def get_json_payload(sensor : LocationSensor):
    #name = sensor.get_topic().split('/')
    return json.dumps(sensor, cls=CustomEncoder)