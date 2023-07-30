import json
import uuid

class Sensor():
    def __init__(self, topic):
        self.uuid = uuid.uuid4()
        self._topic = topic
        self.mode = "get"

class LocationSensor(Sensor):
     def __init__(self, topic) -> None:
          super().__init__(topic)
          self._residents_count = 2
          self._residents_location = {"dummy": "sofa"}
          
     def _to_json(self) -> dict:
         return {"name": str(self.uuid), "loc": self._residents_location, "count": self._residents_count}
         #self._json = json.JSONEncoder({'count': self._residents_count, 'loc': self._residents_location})
          
     def get_json(self):
         return self._json
     
     def set_topic(self, topic):
         self._topic = topic
     
     def get_topic(self):
         return self._topic
     
class TemperatureSensor(Sensor):
     def __init__(self, topic) -> None:
          super().__init__(topic)
          self._temperature = 0
          self._other = {"thermometer": "wall"}
          
     def _to_json(self) -> dict:
         print("temp. sensor temperature:", self._temperature)
         return {"name": str(self.uuid), "temperature": self._temperature, "count": self._other}
         #self._json = json.JSONEncoder({'count': self._residents_count, 'loc': self._residents_location})
          
     def get_json(self):
         return self._json
     
     def set_topic(self, topic):
         self._topic = topic
     
     def get_topic(self):
         return self._topic
     
     def set_temperature(self,t):
         self._temperature = t
         print(f"new tmeperature == {self._temperature}")
        
     def set_other(self,o):
         self._other = o
        
     
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
    