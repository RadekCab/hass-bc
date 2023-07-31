import asyncio
import uuid
from spade.agent import Agent as SpadeAgent
from spade.behaviour import CyclicBehaviour
from agents import ReflexAgent
from agents import set_agent


class EnvironmentalAgent(ReflexAgent, SpadeAgent):
    """Placeholder for environmental agent to be used.
    Not present in simulation model

    Args:
        ReflexAgent class: Reflex agent
        SpadeAgent class: Agent defined in Spade library
    """

    def __init__(
        self,
        devices: list,
        jid="environment11@sure.im",
        password="environment66",
        topic="",
    ) -> None:
        super().__init__(topic, jid=jid, password=password)
        self.devices = devices

    # Spade specific
    class EnvironmentalBehav(CyclicBehaviour):
        async def on_start(self):
            print("Starting device nehavior . . .")
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
        print("Environmetal agent not implemented and cant be used.")
        raise NotImplementedError()
        # 3.10 compatibility
        # self.EnvironmentalBehav.set_agent = set_agent
        # behavior = self.EnvironmentalBehav()
        # self.add_behaviour(behavior)
