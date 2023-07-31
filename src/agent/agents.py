import json
import asyncio
import uuid
from spade.agent import Agent as SpadeAgent
from spade.behaviour import CyclicBehaviour

sem = asyncio.Semaphore()
TIME_INTERVAL = 15


def set_agent(self, agent) -> None:
    """
    Spade v3.2.3 (or lower - not tested) method override for python 3.10 compatibility
    """

    self.agent = agent
    self.queue = asyncio.Queue()
    self.presence = agent.presence
    self.web = agent.web


class ReflexAgent:
    """Works like a blueprint supporting .json serialization of agent outputs"""

    def __init__(self, topic, uuid) -> None:
        self.uuid = uuid
        self.topic = topic
        self._attribute1 = 0
        self._attribute2 = {"dummy": "sofa"}

    def _to_json(self) -> dict:
        return {
            "name": str(self.uuid),
            "loc": self._attribute2,
            "count": self._attribute1,
        }

    def get_json(self):
        return self._json

    def set_topic(self, topic):
        self.topic = topic

    def get_topic(self):
        return self.topic

    def set_attribute1(self, attribute):
        self._attribute1 = attribute

    def set_attribute2(self, attribute):
        self._attribute2 = attribute


class DeviceAgent(ReflexAgent, SpadeAgent):
    """Blueprint providing helpful structure for creating
    agent observing any device

    Args:
        ReflexAgent class: Reflex agent
        SpadeAgent class: Agent defined in Spade library
    """

    def __init__(
        self,
        devices: list,
        jid,
        password,
        topic="",
    ) -> None:
        super().__init__(topic, jid=jid, password=password)
        self.devices = devices

    # Spade specific
    class DeviceBehav(CyclicBehaviour):
        async def on_start(self):
            print("Starting xmpp messaging behavior . . .")
            pass

        async def run(self):
            print("DeviceBehav running")
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")
                self.kill()

    async def setup(self):
        print("Spade agent started.")
        self.DeviceBehav.set_agent = set_agent
        behavior = self.DeviceBehav()
        self.add_behaviour(behavior)
