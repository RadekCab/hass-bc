import json
import uuid


class Sensor:
    """older way of simulating sensor data"""

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
        return {
            "name": str(self.uuid),
            "loc": self._residents_location,
            "count": self._residents_count,
        }

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
        return {
            "name": str(self.uuid),
            "temperature": self._temperature,
            "count": self._other,
        }

    def get_json(self):
        return self._json

    def set_topic(self, topic):
        self._topic = topic

    def get_topic(self):
        return self._topic

    def set_temperature(self, t):
        self._temperature = t
        print(f"new tmeperature == {self._temperature}")

    def set_other(self, o):
        self._other = o
