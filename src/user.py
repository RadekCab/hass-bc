import json
import uuid


class User:
    """placeholder for processing user location"""

    def __init__(self, topic) -> None:
        self.uuid = uuid.uuid4()
        self._topic = topic
        self._placeholder = 2
        self._placeholder2 = {"dummy": "sofa"}

    def _to_json(self) -> dict:
        return {"name": str(self.uuid)}

    def get_json(self):
        return self._json

    def set_topic(self, topic):
        self._topic = topic

    def get_topic(self):
        return self._topic
