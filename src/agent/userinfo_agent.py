import asyncio
import uuid
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour
from spade.template import Template
from spade.message import Message
from asyncio_paho import AsyncioPahoClient
from datetime import datetime
from agent.agents import sem

from agent.device_agent import DeviceAgent

# from agents import set_agent
import mqtt

PROPERTY_TIMEPLAN_NOHEAT = "timeplan_noheat"
PROPERTY_TIMEPLAN_HEAT = "timeplan_heat"
LEARNING_CONTACT = "learning11@sure.im"


class UserAgent(DeviceAgent):
    """Agent managing user requests and timeplan setting

    Args:
        DeviceAgent class: device object blueprint
    """

    def __init__(
        self,
        users: list,
        devices=[],
        jid="userinfo11@sure.im",
        password="userinfo66",
        topic="",
    ) -> None:
        DeviceAgent.__init__(self, devices, jid, password, uuid, topic)
        self.users = users

    # Spade specific
    class RecvTimeplanNoHeatBehav(PeriodicBehaviour):
        async def run(self):
            await self.activate_mqqt_topic_listening(
                self.get("mqtt_timeplan_noheat_topic")
            )

        async def activate_mqqt_topic_listening(self, topic):
            async with sem:
                await UserAgent.activate_mqqt_timeplan_topic_listening(
                    self, topic, PROPERTY_TIMEPLAN_NOHEAT
                )
                await asyncio.sleep(2)

    class RecvTimeplanHeatBehav(PeriodicBehaviour):
        async def run(self):
            await self.activate_mqqt_topic_listening(
                self.get("mqtt_timeplan_heat_topic")
            )

        async def activate_mqqt_topic_listening(self, topic):
            async with sem:
                await UserAgent.activate_mqqt_timeplan_topic_listening(
                    self, topic, PROPERTY_TIMEPLAN_HEAT
                )
                await asyncio.sleep(2)

    class RecvMessagesBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=6)  # wait for a message
            if msg:
                if self.template.body == "timeplan":
                    enriched_heat_dict = self.get(PROPERTY_TIMEPLAN_HEAT)
                    enriched_heat_dict[-1] = "heat"
                    enriched_noheat_dict = self.get(PROPERTY_TIMEPLAN_NOHEAT)
                    enriched_noheat_dict[-1] = "noheat"
                    reply = Message(
                        to=str(self.template.sender),
                        sender=str(self.agent.jid),
                        body="timeplan_reply:"
                        + f"{self.get(PROPERTY_TIMEPLAN_HEAT)}; {self.get(PROPERTY_TIMEPLAN_NOHEAT)}",
                    )
                    # Set the message content
                    reply.set_metadata("performative", "inform")
                    await self.send(reply)
                    print("User Agent: Reply sent to Learning Agent!")
                else:
                    print("WARN User Agent: Received unknown message")

    class ParametersCheckBehav(PeriodicBehaviour):
        async def run(self):
            pass

    async def setup(self):
        print("User agent started.")
        self.set(PROPERTY_TIMEPLAN_NOHEAT, {})
        self.set(PROPERTY_TIMEPLAN_HEAT, {})

        template_timeplan_request = Template()
        template_timeplan_request.sender = LEARNING_CONTACT
        template_timeplan_request.body = "timeplan"
        template_timeplan_request.set_metadata("performative", "query")

        timeplan_recv_heat_behav = self.RecvTimeplanHeatBehav(period=3)
        timeplan_recv_noheat_behav = self.RecvTimeplanNoHeatBehav(period=4)
        periodic_timeplan_duplicates_check = self.ParametersCheckBehav(period=10)
        receive_timeplan_message_behav = self.RecvMessagesBehav()

        self.add_behaviour(timeplan_recv_heat_behav)
        self.add_behaviour(timeplan_recv_noheat_behav)
        self.add_behaviour(periodic_timeplan_duplicates_check)
        self.add_behaviour(receive_timeplan_message_behav, template_timeplan_request)

    async def activate_mqqt_timeplan_topic_listening(self, topic, property):
        async with AsyncioPahoClient(str(uuid.uuid4())) as client:
            client._userdata = None
            client.username_pw_set(username="hass", password="nimda")
            _ = await mqtt.listen_to_topic(client, topic)
            await asyncio.sleep(2)
            if client._userdata != "nothing":
                index = get_time_index(client._userdata)
                heat_dict = self.get(property)
                heat_dict[index] = "index"

                self.set(property, heat_dict)
            client.user_data_set("nothing")


def get_time_index(date: str):
    time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    minutes = time.minute + time.hour * 60
    return int(round(minutes / 15))
