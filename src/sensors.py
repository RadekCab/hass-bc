import json
import uuid

class Sensor():
    pass

class LocationSensor(Sensor):
     def __init__(self, topic) -> None:
          self._residents_count = 2
          self._residents_location = {"dummy": "sofa"}
          self.uuid = uuid.uuid4()
          self._topic = topic
          
     def _to_json(self) -> dict:
         return {"name": str(self.uuid), "loc": self._residents_location, "count": self._residents_count}
         #self._json = json.JSONEncoder({'count': self._residents_count, 'loc': self._residents_location})
          
     def get_json(self):
         return self._json
     
     def set_json(data : str): 
         pass
     
     def set_topic(self, topic):
         self._topic = topic
     
     def get_topic(self):
         return self._topic
     
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return obj._to_json()
        except AttributeError:
            return super().default(obj)
        
     
if __name__ == "__main__":
    a=3
    p="pepa"
    q=["pompo", "rumburak"]
    #print(json.JSONEncoder().encode({a: [p,q]}))
    # r = Room1LocationSensor()
    # r.create_json()
    # print(r.get_json())
    # try:
    #     print(json.dumps(Room1LocationSensor(), cls=CustomEncoder))
    # except TypeError as exc:
    #     print(exc)
        
    # {"Sensor1": {"loc": {"dummy": "sofa", "dummie": "window"}, "count": 2}, "Sensor2": {"loc": {"dummy": "sofa", "dummie": "window"}, "count": 2}}
    try:
        print(json.dumps({"Sensor1": LocationSensor(), "Sensor2": LocationSensor()}, cls=CustomEncoder))
    except TypeError as exc:
        print(exc)
    