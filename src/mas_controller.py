""" controller obeys the logic defined for smart layer of the system
    seperated to different units getting data
    with the central agent at the top of the iceberg
    it's output is new requests to the HASS
    it's input is sensor states from HASS
""" 

import asyncio
import time
from spade.agent import Agent as SpadeAgent
from spade.behaviour import CyclicBehaviour
from agent.agents import DeviceAgent

def set_agent(self, agent) -> None:
        """
        Links behaviour with its owner agent

        Args:
          agent (spade.agent.Agent): the agent who owns the behaviour

        """
        self.agent = agent
        self.queue = asyncio.Queue()
        self.presence = agent.presence
        self.web = agent.web

class TestAgent(SpadeAgent):
    def __init__(self, text, jid, password) -> None:
        super().__init__(jid=jid,password=password)
        self.text = text
        
    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            print("Starting behaviour . . .")
            self.counter = 0

        async def run(self):
            print("Counter: {}".format(self.counter))
            self.counter += 1
            await asyncio.sleep(1)
        
    async def setup(self):
        print("Agent starting . . .")
        self.MyBehav.set_agent = set_agent
        b = self.MyBehav()
        self.add_behaviour(b)
    

def distribute_data_to_agents():
    # states_of_devices = get_devices_states()
    # present_users = get_users_states()
    # environmental_states = get_environmental_states()
    # environmental_states = get_environmental_states()
    # environmental_states = get_environmental_states()
    states_of_devices = []
    present_users = []
    environmental_states = []
    devc_agent = DeviceAgent(states_of_devices)
    #user_agent = Agent(present_users)
    #envm_agent = Agent(environmental_states)

# TODO Logic for processing reflex agents outputs
# (Data processing unit from diagram)

# Where do these abstract agents run? XMPP server



if __name__ == "__main__":
    jid = "artifact01@sure.im"
    pw = "artifact01"
    dummy = TestAgent("text", jid=jid, password=pw)
    future = dummy.start()
    future.result()
    print("Wait until user interrupts with ctrl+C")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    dummy.stop()